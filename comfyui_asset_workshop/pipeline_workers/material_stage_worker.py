"""Isolated native-node worker: UV guide preparation and StableMaterials application."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time

os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1',DO_NOT_TRACK='1')
import numpy as np
from PIL import Image
import trimesh
from material_regions import build_regions,compose_material,region_mask,validate_edits

ROOT=Path(__file__).parent
REVISION='4d452731535bd5c74261d6645623a573326f6f36'

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write_json(path,data):
    temporary=Path(str(path)+'.tmp');temporary.write_text(json.dumps(data,indent=2),encoding='utf-8');temporary.replace(path)

def raster_faces(mesh,size):
    import torch
    import nvdiffrast.torch as dr
    uv=torch.as_tensor(np.asarray(mesh.visual.uv),dtype=torch.float32,device='cuda')
    position=torch.cat([uv*2-1,torch.zeros_like(uv[:,:1]),torch.ones_like(uv[:,:1])],dim=1).unsqueeze(0)
    faces=torch.as_tensor(np.asarray(mesh.faces),dtype=torch.int32,device='cuda')
    context=dr.RasterizeCudaContext()
    raster,_=dr.rasterize(context,position,faces,resolution=[size,size])
    return np.flipud(raster[0,:,:,3].cpu().numpy().astype(np.uint32)).copy()

def prepare(request):
    started=time.monotonic();folder=Path(request['folder']);folder.mkdir(parents=True,exist_ok=True)
    metadata_path=folder/'metadata.json'
    if metadata_path.is_file():return json.loads(metadata_path.read_text())
    source=Path(request['mesh']);before=digest(source)
    print('Preparing color guide from saved mesh; no mesh or color regeneration',flush=True)
    mesh=trimesh.load(source,force='mesh',process=False)
    material=mesh.visual.material
    if len(mesh.faces)>2000000 or getattr(mesh.visual,'uv',None) is None or not np.isfinite(mesh.visual.uv).all():raise ValueError('Choose a valid UV mesh below two million triangles')
    if getattr(material,'baseColorTexture',None) is None or getattr(material,'metallicRoughnessTexture',None) is None:raise ValueError('Materials Lab needs base color and metallic/roughness maps')
    if (getattr(material,'baseColorFactor',None) is not None and not np.allclose(material.baseColorFactor,[255]*4)) or getattr(material,'metallicFactor',1) not in (None,1) or getattr(material,'roughnessFactor',1) not in (None,1):raise ValueError('Normalize non-unity material factors before using this version of Materials Lab')
    guide,colors,patches,meta=build_regions(mesh,request['guide_size'],request['palette_count'],request.get('reference_hint',''))
    guide.save(folder/'guide.png')
    colors.tofile(folder/'colors.bin');patches.tofile(folder/'patches.bin')
    np.bincount(patches).astype(np.uint32).tofile(folder/'patch-sizes.bin')
    print('Rasterize the existing UV layout for surface-anchored selections',flush=True)
    size=mesh.visual.material.baseColorTexture.width
    if mesh.visual.material.baseColorTexture.height!=size:raise ValueError('Material lab currently requires a square source color atlas')
    full_map=raster_faces(mesh,size)
    np.savez_compressed(folder/'uv-faces.npz',faces=full_map)
    small=np.asarray(Image.fromarray(full_map.astype(np.int32)).resize((request['guide_size'],request['guide_size']),Image.Resampling.NEAREST)).astype(np.uint32)
    small.tofile(folder/'triangles.bin')
    low=mesh.copy();low.visual.material=trimesh.visual.material.PBRMaterial(baseColorTexture=guide,metallicFactor=0,roughnessFactor=1)
    low.export(folder/'guide.glb')
    probe=trimesh.load(folder/'guide.glb',force='mesh',process=False)
    preserved=bool(np.array_equal(probe.vertices,mesh.vertices) and np.array_equal(probe.faces,mesh.faces) and np.array_equal(probe.visual.uv,mesh.visual.uv))
    if not preserved:raise RuntimeError('Guide export changed mesh/UV identities')
    meta.update(session_id=request['session_id'],source_mesh=str(source),source_sha256=before,full_texture_size=size,source_vertices=len(mesh.vertices),guide_geometry_uvs_preserved=preserved,prepare_seconds=time.monotonic()-started,source_hash_unchanged=digest(source)==before)
    if not meta['source_hash_unchanged']:raise RuntimeError('Source changed during guide preparation')
    write_json(metadata_path,meta);return meta

def generate_maps(prompts,request,folder):
    import torch
    from diffusers import DiffusionPipeline,UNet2DConditionModel,LCMScheduler
    model=Path(request['stable_materials'])
    cache=Path(request['material_cache']);cache.mkdir(parents=True,exist_ok=True)
    paths={};missing=[]
    for prompt in prompts:
        key=hashlib.sha256(json.dumps([REVISION,prompt,request['seed'],request['steps'],request['guidance']],ensure_ascii=False).encode()).hexdigest()[:24]
        target=cache/key;paths[prompt]=target
        if not (target/'report.json').is_file():missing.append(prompt)
    if missing:
        print('Loading official StableMaterials LCM model',flush=True)
        unet=UNet2DConditionModel.from_pretrained(str(model),subfolder='unet_lcm',torch_dtype=torch.float16,local_files_only=True)
        pipeline=DiffusionPipeline.from_pretrained(str(model),trust_remote_code=True,unet=unet,torch_dtype=torch.float16,local_files_only=True)
        pipeline.scheduler=LCMScheduler.from_config(pipeline.scheduler.config)
        pipeline=pipeline.to('cuda');pipeline.set_progress_bar_config(disable=False)
        torch.cuda.reset_peak_memory_stats()
        for index,prompt in enumerate(missing):
            write_json(folder/'status.json',{'state':'generating','index':index+1,'total':len(missing),'prompt':prompt})
            print('MATERIAL '+str(index+1)+'/'+str(len(missing))+': '+prompt,flush=True)
            start=time.monotonic()
            material=pipeline(prompt=prompt,num_inference_steps=request['steps'],guidance_scale=request['guidance'],tileable=True,generator=torch.Generator(device='cuda').manual_seed(request['seed'])).images[0]
            target=paths[prompt];target.mkdir(exist_ok=True)
            for name in ['basecolor','roughness','metallic','normal','height']:getattr(material,name).save(target/(name+'.png'))
            write_json(target/'report.json',{'implementation':'gvecchio/StableMaterials','revision':REVISION,'prompt':prompt,'seed':request['seed'],'steps':request['steps'],'guidance':request['guidance'],'mode':'LCM','seconds':time.monotonic()-start,'peak_cuda_allocated_bytes':torch.cuda.max_memory_allocated(),'peak_cuda_reserved_bytes':torch.cuda.max_memory_reserved()})
        del pipeline,unet
    return {prompt:{name:Image.open(path/(name+'.png')).copy() for name in ['roughness','metallic','normal']} for prompt,path in paths.items()},paths

def apply(request):
    started=time.monotonic();folder=Path(request['folder']);meta=json.loads((folder/'metadata.json').read_text())
    source=Path(meta['source_mesh'])
    if digest(source)!=meta['source_sha256']:raise RuntimeError('Preserved source mesh changed; prepare a fresh guide')
    edits=validate_edits(request['edits'],meta['palette_count'],meta['patch_count'],faces=meta['faces'])
    rows=[r for r in edits.get('regions',[]) if r.get('prompt','').strip() and r.get('enabled',True)]
    destination=Path(request['output']);destination.parent.mkdir(parents=True,exist_ok=True)
    if not rows:
        shutil.copy2(source,destination)
        report={'source_mesh':str(source),'output':str(destination),'regions_applied':0,'source_sha256':meta['source_sha256'],'mesh_colors_uvs_preserved':True,'message':'No material assignments yet. Open the region editor and choose a surface.'}
        write_json(destination.with_suffix('.report.json'),report);write_json(folder/'status.json',{'state':'ready','report':report,'output':str(destination)})
        return report
    write_json(folder/'status.json',{'state':'loading','total':len(rows)})
    prompts=list(dict.fromkeys(r['prompt'].strip() for r in rows))
    maps,cache_paths=generate_maps(prompts,request,folder)
    write_json(folder/'status.json',{'state':'applying','total':len(rows)})
    mesh=trimesh.load(source,force='mesh',process=False)
    palette=np.fromfile(folder/'colors.bin',dtype=np.uint16);patches=np.fromfile(folder/'patches.bin',dtype=np.uint32)
    face_map=np.load(folder/'uv-faces.npz')['faces'];assignments=[];union=np.zeros(face_map.shape,bool);coverage=[]
    for row in rows:
        mask=region_mask(face_map,palette,patches,row['kind'],row['id'],face_ranges=row.get('face_ranges'));union|=mask
        item=dict(row);item.update(mask=mask,maps=maps[row['prompt'].strip()]);assignments.append(item)
        coverage.append({'kind':row['kind'],'id':row['id'],'name':row.get('name',''),'prompt':row['prompt'],'pixels':int(mask.sum()),'cache_report':str(cache_paths[row['prompt'].strip()]/'report.json')})
    output=compose_material(mesh,assignments)
    output.export(destination)
    probe=trimesh.load(destination,force='mesh',process=False)
    geometry=bool(np.array_equal(probe.vertices,mesh.vertices) and np.array_equal(probe.faces,mesh.faces))
    uvs=bool(np.array_equal(probe.visual.uv,mesh.visual.uv))
    colors=bool(np.array_equal(np.asarray(probe.visual.material.baseColorTexture),np.asarray(mesh.visual.material.baseColorTexture)))
    old=np.asarray(mesh.visual.material.metallicRoughnessTexture.convert('RGB'));new=np.asarray(probe.visual.material.metallicRoughnessTexture.convert('RGB'))
    untouched=bool(np.array_equal(old[~union],new[~union]));changed=int(np.any(old!=new,axis=2)[union].sum())
    if not (geometry and uvs and colors and untouched and digest(source)==meta['source_sha256']):raise RuntimeError('Material export failed mesh/color/UV/unselected-region preservation')
    report={'source_mesh':str(source),'output':str(destination),'source_sha256':meta['source_sha256'],'triangles':len(probe.faces),'vertices':len(probe.vertices),'geometry_arrays_identical':geometry,'uv_arrays_identical':uvs,'base_color_pixels_identical':colors,'unselected_mr_pixels_identical':untouched,'source_file_unchanged':True,'regions_applied':len(rows),'selected_pixels':int(union.sum()),'changed_selected_mr_pixels':changed,'maps':{'base_color':list(probe.visual.material.baseColorTexture.size),'metallic_roughness':list(probe.visual.material.metallicRoughnessTexture.size),'normal':list(probe.visual.material.normalTexture.size) if probe.visual.material.normalTexture else None},'materials':coverage,'seconds':time.monotonic()-started,'limits':['Color/connected regions are not semantic segmentation.','Generated material details are tiled in existing UV coordinates; weave direction is not aligned to garment seams.','Appearance may contain highlights already painted into unchanged base color.']}
    write_json(destination.with_suffix('.report.json'),report);write_json(folder/'status.json',{'state':'ready','output':str(destination),'report':report})
    return report

if __name__=='__main__':
    request=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8-sig'))
    try:
        result=prepare(request) if request['action']=='prepare' else apply(request)
        write_json(Path(sys.argv[1]).with_name('result.json'),result)
        print(json.dumps(result,indent=2),flush=True)
    except Exception as error:
        folder=Path(request['folder']);folder.mkdir(parents=True,exist_ok=True)
        write_json(folder/'status.json',{'state':'error','message':str(error)})
        raise
