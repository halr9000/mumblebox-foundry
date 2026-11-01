"""Color-guide regions and color-preserving PBR composition for the native lab."""
import copy
import colorsys
import json
import numpy as np
from PIL import Image
import trimesh
from scipy import sparse
from scipy.sparse.csgraph import connected_components


def make_color_guide(image, size):
    return image.convert('RGB').resize((size, size), Image.Resampling.LANCZOS)


def describe_color(rgb, hint=''):
    r,g,b=[float(c)/255 for c in rgb]
    h,s,v=colorsys.rgb_to_hsv(r,g,b)
    if v<.25: name='Dark';prompt='Matte charcoal rubber, fine grain, nonmetallic'
    elif s<.18: name='Light' if v>.6 else 'Gray';prompt='Brushed silver metal, fine subtle scratches'
    elif h<.04 or h>.95: name='Red';prompt='Matte painted surface, fine grain, nonmetallic'
    elif h<.13: name='Orange';prompt='Matte orange powder coated paint, fine grain, nonmetallic'
    elif h<.2: name='Yellow';prompt='Matte painted surface, fine grain, nonmetallic'
    elif h<.49: name='Green';prompt='Natural smooth organic skin, slightly satin, nonmetallic'
    elif h<.72: name='Blue';prompt='Matte painted surface, fine grain, nonmetallic'
    else: name='Purple';prompt='Matte woven cotton fabric, fine cloth weave, nonmetallic'
    if 'frog' in hint.lower() and name in ('Orange','Yellow'):
        prompt='Natural pumpkin rind, fine pores, slightly waxy rough organic skin, nonmetallic'
    return name+' surfaces',prompt


def build_regions(mesh, guide_size=1024, colors=8, hint=''):
    base=mesh.visual.material.baseColorTexture
    if base is None or mesh.visual.uv is None:
        raise ValueError('Use a textured mesh with UVs for the color guide')
    guide=make_color_guide(base,guide_size)
    uv=np.asarray(mesh.visual.uv)[mesh.faces].mean(axis=1)
    samples=trimesh.visual.color.uv_to_color(uv,base)[:,:3]
    width=min(1024,len(samples));padding=(-len(samples))%width
    packed=np.pad(samples,((0,padding),(0,0)),mode='edge').reshape(-1,width,3)
    quant=Image.fromarray(packed).quantize(colors=colors,method=Image.Quantize.MEDIANCUT)
    quant_labels=np.asarray(quant).ravel()[:len(samples)]
    raw_table=np.array(quant.getpalette(),np.uint8).reshape(-1,3)[:colors]
    histogram=np.bincount(quant_labels,minlength=colors)
    remap=np.zeros(colors,np.uint16);centers=[];weights=[]
    for original in np.argsort(-histogram):
        if not histogram[original]:continue
        rgb=raw_table[original].astype(np.float32)
        distance=np.linalg.norm(np.asarray(centers)-rgb,axis=1) if centers else np.array([])
        if len(distance) and distance.min()<34:
            index=int(distance.argmin());total=weights[index]+histogram[original]
            centers[index]=(centers[index]*weights[index]+rgb*histogram[original])/total;weights[index]=total
        else:
            index=len(centers);centers.append(rgb);weights.append(histogram[original])
        remap[original]=index
    table=np.rint(centers).astype(np.uint8)
    colors=len(table)
    face_colors=remap[quant_labels].astype(np.uint16)
    # Reconnect UV seams for selection only. The exported mesh is never welded.
    _,inverse=np.unique(np.asarray(mesh.vertices),axis=0,return_inverse=True)
    adjacency=trimesh.graph.face_adjacency(faces=inverse[mesh.faces])
    keep=face_colors[adjacency[:,0]]==face_colors[adjacency[:,1]]
    edges=adjacency[keep]
    count=len(mesh.faces)
    graph=sparse.coo_matrix((np.ones(len(edges)*2,np.uint8),
        (np.concatenate([edges[:,0],edges[:,1]]),np.concatenate([edges[:,1],edges[:,0]]))),shape=(count,count)).tocsr()
    patch_count,patch_labels=connected_components(graph,directed=False)
    counts=np.bincount(face_colors,minlength=colors)
    regions=[]
    for i,rgb in enumerate(table):
        if not counts[i]:continue
        name,prompt=describe_color(rgb,hint)
        name+=' '+str(i+1)
        regions.append({'id':int(i),'kind':'color','name':name,'rgb':rgb.tolist(),'faces':int(counts[i]),'prompt':prompt})
    return guide,face_colors,patch_labels.astype(np.uint32),{'regions':regions,'palette_count':colors,'patch_count':int(patch_count),'faces':count,'guide_size':guide_size,'reference_hint':hint,'suggestion_basis':'Color-based starting suggestions and supplied object description; not semantic AI recognition.'}


def validate_edits(edits,colors,patches,faces=None):
    data=json.loads(edits) if isinstance(edits,str) else edits
    if not isinstance(data,dict) or not isinstance(data.get('regions',[]),list):
        raise ValueError('Region edits must contain a regions list')
    for r in data.get('regions',[]):
        kind=r.get('kind');idx=r.get('id')
        limit=colors if kind=='color' else patches if kind=='patch' else 2147483647 if kind=='faces' else 0
        if not isinstance(idx,int) or isinstance(idx,bool) or not 0<=idx<limit:
            raise ValueError('Selected region is outside this guide')
        if kind=='faces':
            ranges=r.get('face_ranges')
            if faces is None or not isinstance(ranges,list) or not ranges:
                raise ValueError('Painted region needs face ranges')
            for pair in ranges:
                if not isinstance(pair,list) or len(pair)!=2 or not all(isinstance(x,int) for x in pair) or not 0<=pair[0]<pair[1]<=faces:
                    raise ValueError('Painted selection is outside this mesh')
        if not isinstance(r.get('prompt',''),str):raise ValueError('Material description must be text')
        for key,lo,hi in [('strength',0,1),('detail',0,1),('tiles',.125,128)]:
            val=r.get(key,1 if key=='strength' else .15 if key=='detail' else 8)
            if not isinstance(val,(float,int)) or not np.isfinite(val) or not lo<=val<=hi:
                raise ValueError('Invalid material '+key)
        if r.get('metallic','auto') not in ('auto','nonmetal','metal'):raise ValueError('Invalid metallic choice')
    return data


def region_mask(face_map,colors,patches,kind,idx,face_ranges=None):
    visible=face_map>0
    result=np.zeros(face_map.shape,bool)
    if kind=='faces':
        chosen=np.zeros(len(colors),bool)
        for start,end in face_ranges:chosen[start:end]=True
        result[visible]=chosen[face_map[visible].astype(np.int64)-1]
    else:
        labels=colors if kind=='color' else patches
        result[visible]=labels[face_map[visible].astype(np.int64)-1]==idx
    return result


def tile_pixels(image,size,tiles,mode):
    a=np.asarray(image.convert(mode))
    yy=(np.arange(size[0])*a.shape[0]*tiles/size[0]).astype(np.int64)%a.shape[0]
    xx=(np.arange(size[1])*a.shape[1]*tiles/size[1]).astype(np.int64)%a.shape[1]
    return a[yy[:,None],xx[None,:]]


def compose_material(mesh,assignments):
    out=mesh.copy()
    out.visual.material=copy.deepcopy(mesh.visual.material)
    base=mesh.visual.material.baseColorTexture
    out.visual.material.baseColorTexture=base.copy()
    h,w=np.asarray(base).shape[:2]
    old=mesh.visual.material.metallicRoughnessTexture
    if old is None:
        old=Image.new('RGB',(w,h),(0,round(mesh.visual.material.roughnessFactor*255),round(mesh.visual.material.metallicFactor*255)))
    mr=np.asarray(old.convert('RGB').resize((w,h),Image.Resampling.NEAREST)).copy()
    normal_image=mesh.visual.material.normalTexture
    use_normal=any(a.get('detail',.15)>0 for a in assignments)
    if use_normal:
        normal=np.asarray(normal_image.convert('RGB').resize((w,h)) if normal_image else Image.new('RGB',(w,h),(128,128,255))).copy()
    for item in assignments:
        mask=item['mask'];maps=item['maps'];strength=float(item.get('strength',1));tiles=float(item.get('tiles',8))
        rough=tile_pixels(maps['roughness'],(h,w),tiles,'L')
        metal=tile_pixels(maps['metallic'],(h,w),tiles,'L')
        override=item.get('metallic','auto')
        if override!='auto':metal=np.full_like(metal,0 if override=='nonmetal' else 255)
        mr[mask,1]=np.rint(mr[mask,1]*(1-strength)+rough[mask]*strength).astype(np.uint8)
        mr[mask,2]=np.rint(mr[mask,2]*(1-strength)+metal[mask]*strength).astype(np.uint8)
        detail=float(item.get('detail',.15))
        if use_normal and detail>0:
            fine=tile_pixels(maps['normal'],(h,w),tiles,'RGB')[mask].astype(np.float32)/127.5-1
            prior=normal[mask].astype(np.float32)/127.5-1
            xy=prior[:,:2]+fine[:,:2]*detail
            z=np.maximum(prior[:,2:3],.01)*np.maximum(fine[:,2:3],.01)
            vector=np.concatenate([xy,z],axis=1)
            vector/=np.maximum(np.linalg.norm(vector,axis=1,keepdims=True),1e-8)
            normal[mask]=np.rint(np.clip((vector+1)*127.5,0,255)).astype(np.uint8)
    out.visual.material.metallicRoughnessTexture=Image.fromarray(mr)
    out.visual.material.metallicFactor=1.;out.visual.material.roughnessFactor=1.
    if use_normal:out.visual.material.normalTexture=Image.fromarray(normal)
    return out
