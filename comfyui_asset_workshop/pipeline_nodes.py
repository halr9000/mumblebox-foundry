"""Native checkpoints around isolated workers. Canonical textured GLBs are never re-encoded."""
import json
import time
import uuid
from pathlib import Path
import numpy as np
import torch
import trimesh
from PIL import Image
from comfy_api.latest import IO, Types
from comfy_extras.nodes_save_3d import MeshToFile3D
import comfy.model_management as mm
from .runtime import store, configuration
from .store import digest, atomic_json, identifier
from .pipeline_state import validate_settings, VARIANTS
from .pipeline_capabilities import validate_runtime, inspect_runtime
from .pipeline_workers.refine_client import arrays, mesh_value, Hi3DRefine
from .pipeline_workers.geometry import Hi3DAlignToSource, Hi3DNormalizeMesh, Hi3DRestoreMeshFrame
from .pipeline_workers.trellis_bridge_runtime import run_worker, clean_zero_edges

HERE=Path(__file__).parent

def strings(*names):return [IO.String.Input(n) for n in names]

def checked(library,pid,aid,kind=None):
    row=next((a for a in library.load(pid)["artifacts"] if a["id"]==identifier(aid)),None)
    if not row or row.get("stale") or (kind and row["kind"]!=kind):raise ValueError("Choose a current saved input in this project")
    p=library.path(pid,row["file"])
    if not p.is_file() or digest(p)!=row["sha256"]:raise ValueError("Pipeline input changed on disk")
    return row,p

def runtime():return validate_runtime(configuration().get("pipeline_runtime",{}))

def work(pid,worker,request):
    cfg=runtime();ready=inspect_runtime(cfg)
    if not ready["providers"]["trellis2"]["available"]:raise ValueError(ready["providers"]["trellis2"]["reason"])
    folder=store().path(pid,"pipeline/work/"+uuid.uuid4().hex);folder.mkdir(parents=True)
    req={**cfg,**request};atomic_json(folder/"request.json",req)
    mm.unload_all_models();mm.soft_empty_cache()
    run_worker([cfg["worker_python"],str(HERE/"pipeline_workers"/worker),str(folder/"request.json")],folder/"worker.log",mm.throw_exception_if_processing_interrupted)
    mm.throw_exception_if_processing_interrupted()
    return folder

def reference(library,pid):
    r=library.mesh_input(pid)
    # Hi3D and final-mesh TRELLIS each apply their own validated conditioning.
    # Keep original-frame RGBA; flattened Pixal crops lose alpha and alter apparent scale.
    fg=r.get("foreground")
    if fg:
        path=library.path(pid,fg["cutout_file"])
        if fg.get("source_sha256")!=r["sha256"] or digest(path)!=fg.get("cutout_sha256"):
            raise ValueError("The transparent conditioning reference changed; prepare this image again")
        return path
    return library.path(pid,r["file"])

def variant_mesh(vertices,faces,native_uv,material):
    # Comfy MESH/glTF use image-row V; trimesh's exporter flips its own upward V.
    upward=np.array(native_uv,dtype=np.float32,copy=True)
    upward[:,1]=1.0-upward[:,1]
    return trimesh.Trimesh(vertices,faces,visual=trimesh.visual.TextureVisuals(uv=upward,material=material),process=False)

def material_sidecars(path):
    # Read the canonical GLB; save matching maps without writing it again.
    mesh=trimesh.load(path,force="mesh",process=False)
    material=mesh.visual.material
    images={"base_color.png":getattr(material,"baseColorTexture",None),"normal_opengl.png":getattr(material,"normalTexture",None)}
    mr=getattr(material,"metallicRoughnessTexture",None)
    if mr is not None:
        rgb=mr.convert("RGB");images.update({"metallic.png":rgb.getchannel("B"),"roughness.png":rgb.getchannel("G")})
    occlusion=getattr(material,"occlusionTexture",None)
    if occlusion is not None:images["occlusion.png"]=occlusion.convert("RGB").getchannel("R")
    hashes={path.name:digest(path)}
    for name,image in images.items():
        if image is not None:image.save(path.parent/name);hashes[name]=digest(path.parent/name)
    return {"hashes":hashes,"texture_size":material.baseColorTexture.width,"dimensions_meters":mesh.extents.tolist(),"unit":"meter","material_factors":{"metallic":getattr(material,"metallicFactor",None),"roughness":getattr(material,"roughnessFactor",None)}}

def output_record(library,pid,sid,path,**fields):
    record={"id":uuid.uuid4().hex[:16],"kind":"mesh","file":path.relative_to(library.directory(pid)).as_posix(),"sha256":digest(path),"created":time.time(),"normal_convention":"OpenGL +Y","up_axis":"Y",**fields}
    if record["kind"]=="mesh" and path.is_file():record.update(material_sidecars(path))
    result=library.record_pipeline_artifact(pid,sid,record)
    library.complete_job(pid,sid,{"export" if result["kind"]=="mesh" else "geometry":result["id"]})
    return result

class LoadGeometry(IO.ComfyNode):
    @classmethod
    def define_schema(cls):return IO.Schema(node_id="AW_LoadGeometry",display_name="Load verified geometry checkpoint",category="Asset Workshop/Pipeline",inputs=strings("asset_id","artifact_id"),outputs=[IO.Mesh.Output()])
    @classmethod
    def execute(cls,asset_id,artifact_id):
        _,path=checked(store(),asset_id,artifact_id,"geometry")
        with np.load(path,allow_pickle=False) as data:mesh=mesh_value(data["vertices"].copy(),data["faces"].copy())
        return IO.NodeOutput(mesh)

class SaveGeometry(IO.ComfyNode):
    @classmethod
    def define_schema(cls):return IO.Schema(node_id="AW_SaveGeometry",display_name="Preserve geometry and native preview",category="Asset Workshop/Pipeline",is_output_node=True,inputs=[IO.Mesh.Input("mesh"),*strings("asset_id","stage_id","geometry_stage","parent_id","recipe")],outputs=[IO.Mesh.Output()])
    @classmethod
    def execute(cls,mesh,asset_id,stage_id,geometry_stage,parent_id,recipe):
        if geometry_stage not in ("coarse","refined","clean"):raise ValueError("Unknown geometry checkpoint")
        library=store();aid=uuid.uuid4().hex[:16];base="pipeline/geometry/"+aid;folder=library.path(asset_id,base);folder.mkdir(parents=True)
        v,f=arrays(mesh);np.savez_compressed(folder/"geometry.npz",vertices=v,faces=f)
        MeshToFile3D.execute(mesh)[0].save_to(str(folder/"preview.glb"))
        row=output_record(library,asset_id,stage_id,folder/"geometry.npz",kind="geometry",geometry_stage=geometry_stage,parent_artifact_id=parent_id or None,preview_file=base+"/preview.glb",preview_sha256=digest(folder/"preview.glb"),triangles=len(f),vertices=len(v),recipe=json.loads(recipe))
        return IO.NodeOutput(mesh,ui={"asset_workshop":[row]})

class RefineGeometry(IO.ComfyNode):
    @classmethod
    def define_schema(cls):return IO.Schema(node_id="AW_RefineGeometry",display_name="Hi3D refine and restore source frame",category="Asset Workshop/Pipeline",inputs=[IO.Mesh.Input("mesh"),*strings("asset_id","settings")],outputs=[IO.Mesh.Output()])
    @classmethod
    def execute(cls,mesh,asset_id,settings):
        s=validate_settings(json.loads(settings));cfg=runtime()
        if not cfg.get("hi3d_url"):raise ValueError("Configure the local Hi3D service")
        im=Image.open(reference(store(),asset_id)).convert("RGBA")
        tensor=torch.from_numpy(np.asarray(im,dtype=np.float32).copy()/255).unsqueeze(0)
        refined,report,jid=Hi3DRefine().refine({"url":cfg["hi3d_url"]},tensor,mesh,s["refine_resolution"],s["refine_steps"],s["refine_seed"],s["cpu_offload"],s["attention"])
        aligned,alignment=Hi3DAlignToSource().align(refined,mesh)
        folder=store().path(asset_id,"pipeline/refine-reports");folder.mkdir(parents=True,exist_ok=True)
        atomic_json(folder/(uuid.uuid4().hex+".json"),{"hi3d":json.loads(report),"alignment":json.loads(alignment),"job_id":jid})
        return IO.NodeOutput(aligned)

class GeometryFrame(IO.ComfyNode):
    @classmethod
    def define_schema(cls):return IO.Schema(node_id="AW_GeometryFrame",display_name="Scale-safe cleanup frame",category="Asset Workshop/Pipeline",inputs=[IO.Mesh.Input("mesh"),IO.Combo.Input("operation",options=["normalize","restore"]),IO.String.Input("frame")],outputs=[IO.Mesh.Output(),IO.String.Output()])
    @classmethod
    def execute(cls,mesh,operation,frame):
        if operation=="normalize":out,record=Hi3DNormalizeMesh().normalize(mesh,.96)
        else:record=json.loads(frame);out=Hi3DRestoreMeshFrame().restore(mesh,record)[0]
        return IO.NodeOutput(out,json.dumps(record))

class ZeroEdges(IO.ComfyNode):
    @classmethod
    def define_schema(cls):return IO.Schema(node_id="AW_ZeroEdges",display_name="Finalize connected zero-edge cleanup",category="Asset Workshop/Pipeline",inputs=[IO.Mesh.Input("mesh")],outputs=[IO.Mesh.Output()])
    @classmethod
    def execute(cls,mesh):
        v,f=arrays(mesh);v,f,report=clean_zero_edges(v,f)
        return IO.NodeOutput(mesh_value(v,f),ui={"text":[json.dumps(report)]})

class TextureSaved(IO.ComfyNode):
    @classmethod
    def define_schema(cls):return IO.Schema(node_id="AW_TextureSaved",display_name="Texture finished geometry (isolated runtime)",category="Asset Workshop/Pipeline",is_output_node=True,inputs=strings("asset_id","stage_id","source_id","settings"),outputs=[IO.File3DGLB.Output()])
    @classmethod
    def execute(cls,asset_id,stage_id,source_id,settings):
        s=validate_settings(json.loads(settings));library=store();row,mesh=checked(library,asset_id,source_id,"geometry")
        ready=inspect_runtime(runtime())["providers"][s["texture_provider"]]
        if not ready["available"]:raise ValueError(ready["reason"])
        dest=library.path(asset_id,"pipeline/appearances/"+uuid.uuid4().hex+"/textured.glb");dest.parent.mkdir(parents=True)
        req={"mesh":str(mesh),"image":str(reference(library,asset_id)),"output":str(dest),"seed":s["texture_seed"],"steps":s["texture_steps"],"resolution":s["texture_resolution"],"texture_size":s["texture_size"],"guidance":s["texture_guidance"],"sampler":s["texture_sampler"],"guidance_rescale":s["texture_rescale"],"reference_lock":s["reference_lock"],"reference_substeps":2}
        work(asset_id,"trellis_texture_worker.py",req)
        report=json.loads(dest.with_suffix(".report.json").read_text());r=output_record(library,asset_id,stage_id,dest,parent_artifact_id=source_id,geometry_id=source_id,appearance_stage="texture",variant="detailed",master=source_id,export_kind="master",triangles=report["output_faces"],recipe={"pipeline_version":"validated_v1","texture_provider":s["texture_provider"],"settings":s,"runtime_report":{k:v for k,v in report.items() if k!="output"}})
        return IO.NodeOutput(Types.File3D(str(dest),"glb"),ui={"asset_workshop":[r]})

class OptimizeSaved(IO.ComfyNode):
    @classmethod
    def define_schema(cls):return IO.Schema(node_id="AW_OptimizeSaved",display_name="Prepare final variant geometry and color maps",category="Asset Workshop/Pipeline",inputs=strings("asset_id","source_id","variant","settings"),outputs=[IO.Mesh.Output(),IO.String.Output()])
    @classmethod
    def execute(cls,asset_id,source_id,variant,settings):
        s=validate_settings(json.loads(settings));library=store();row,path=checked(library,asset_id,source_id,"mesh")
        if variant not in VARIANTS or variant=="detailed":raise ValueError("Detailed is already available; choose a reduced variant")
        if row.get("material_revision"):raise ValueError("Prepare variants before Materials Lab; choose the original textured master")
        geo,gpath=checked(library,asset_id,row["geometry_id"],"geometry")
        # Worker returns arrays and rebaked maps; native normal bake follows in this visible graph.
        folder=work(asset_id,"mesh_optimize_worker.py",{"mesh":str(gpath),"texture_source":str(path),"target_triangles":VARIANTS[variant],"method":"quadric","texture_size":row.get("texture_size",row.get("recipe",{}).get("settings",{}).get("texture_size",4096))})
        with np.load(folder/"result.npz",allow_pickle=False) as d:
            mesh=mesh_value(d["vertices"].copy(),d["faces"].copy());mesh.uvs=torch.from_numpy(d["uvs"].copy()).float().unsqueeze(0);mesh.normals=torch.from_numpy(d["normals"].copy()).float().unsqueeze(0)
        return IO.NodeOutput(mesh,str(folder))

class SaveVariant(IO.ComfyNode):
    @classmethod
    def define_schema(cls):return IO.Schema(node_id="AW_SaveVariant",display_name="Save canonical optimized GLB with baked detail",category="Asset Workshop/Pipeline",is_output_node=True,inputs=[IO.Mesh.Input("mesh"),IO.Image.Input("normal"),*strings("folder","asset_id","stage_id","source_id","variant")],outputs=[IO.File3DGLB.Output()])
    @classmethod
    def execute(cls,mesh,normal,folder,asset_id,stage_id,source_id,variant):
        library=store();row,_=checked(library,asset_id,source_id,"mesh")
        folder=Path(folder).resolve()
        if not folder.is_relative_to(library.path(asset_id,"pipeline/work").resolve()):raise ValueError("Invalid worker output")
        v,f=arrays(mesh);uv=mesh.uvs[0].detach().cpu().numpy()
        material=trimesh.visual.material.PBRMaterial(baseColorTexture=Image.open(folder/"baked-base-color.png").copy(),metallicRoughnessTexture=Image.open(folder/"baked-metallic-roughness.png").copy(),normalTexture=Image.fromarray((normal[0].detach().cpu().clamp(0,1).numpy()*255).round().astype(np.uint8)),metallicFactor=1,roughnessFactor=1,alphaMode="OPAQUE")
        out=variant_mesh(v,f,uv,material)
        dest=library.path(asset_id,"pipeline/appearances/"+uuid.uuid4().hex+"/"+variant+".glb");dest.parent.mkdir(parents=True);out.export(dest)
        r=output_record(library,asset_id,stage_id,dest,parent_artifact_id=source_id,geometry_id=row["geometry_id"],appearance_stage="variant",variant=variant,master=row["master"],export_kind="game",triangles=len(f),recipe={"pipeline_version":"validated_v1","variant":variant,"optimization":json.loads((folder/"report.json").read_text())})
        return IO.NodeOutput(Types.File3D(str(dest),"glb"),ui={"asset_workshop":[r]})

class MaterialStage(IO.ComfyNode):
    @classmethod
    def define_schema(cls):return IO.Schema(node_id="AW_MaterialStage",display_name="Project Materials Lab (keep geometry and colors)",category="Asset Workshop/Pipeline",is_output_node=True,inputs=[*strings("asset_id","stage_id","session_id","operation","settings"),IO.Int.Input("draft_revision",default=0),IO.String.Input("assignment_key",default="",optional=True)],outputs=[IO.File3DGLB.Output()])
    @classmethod
    def execute(cls,asset_id,stage_id,session_id,operation,settings,draft_revision=0,assignment_key=""):
        from . import materials
        from .store import LOCK
        s=validate_settings(json.loads(settings));library=store();session=materials.load_session(library,asset_id,session_id)
        folder=materials.folder(library,asset_id,session_id);folder.mkdir(parents=True,exist_ok=True)
        row,path=checked(library,asset_id,session["source_id"],"mesh")
        if operation=="apply" and assignment_key and materials.assignment_fingerprint(session["draft"])!=assignment_key:raise ValueError("Assigned materials changed after this job was queued; retry with current choices")
        if operation=="prepare":
            work(asset_id,"material_stage_worker.py",{"action":"prepare","session_id":session_id,"folder":str(folder),"mesh":str(path),"guide_size":session["guide_size"],"palette_count":session["palette_count"],"reference_hint":library.load(asset_id)["prompt"][:4000]})
            with LOCK:
                project=library.load(asset_id);current=project["pipeline"]["material_sessions"][session_id];current["state"]="ready";library.save(project)
            library.complete_job(asset_id,stage_id,{"material_session":session_id})
            return IO.NodeOutput(Types.File3D(str(folder/"guide.glb"),"glb"))
        if operation!="apply":raise ValueError("Unknown material operation")
        edits=materials.worker_edits(library,asset_id,session_id)
        dest=library.path(asset_id,"pipeline/appearances/"+uuid.uuid4().hex+"/materials.glb");dest.parent.mkdir(parents=True)
        work(asset_id,"material_stage_worker.py",{"action":"apply","folder":str(folder),"session_id":session_id,"edits":edits,"output":str(dest),"seed":s["material_seed"],"steps":s["material_steps"],"guidance":s["material_guidance"]})
        report=json.loads(dest.with_suffix(".report.json").read_text())
        record=output_record(library,asset_id,stage_id,dest,parent_artifact_id=row["id"],geometry_id=row.get("geometry_id"),appearance_stage="materials",variant=row.get("variant","detailed"),master=row.get("master"),export_kind=row.get("export_kind","master"),triangles=row["triangles"],material_session_id=session_id,material_revision=draft_revision,material_region_count=report["regions_applied"],recipe={"pipeline_version":"validated_v1","material_model":"gvecchio/StableMaterials","material_model_revision":"4d452731535bd5c74261d6645623a573326f6f36","material_settings":{k:v for k,v in s.items() if k.startswith("material_")},"material_assignments":{"version":1,"regions":[{k:v for k,v in r.items() if k!="face_mask"} for r in session["draft"].get("regions",[])]},"preservation":{k:v for k,v in report.items() if k.endswith("identical") or k.endswith("unchanged")}})
        with LOCK:
            project=library.load(asset_id);current=project["pipeline"]["material_sessions"][session_id];current.update(rendered_revision=draft_revision,rendered_artifact_id=record["id"],rendered_assignment_fingerprint=materials.assignment_fingerprint(session["draft"]),assignments_pending=materials.assignment_fingerprint(current["draft"])!=materials.assignment_fingerprint(session["draft"]));library.save(project)
        return IO.NodeOutput(Types.File3D(str(dest),"glb"),ui={"asset_workshop":[record]})

class UseSavedStage(IO.ComfyNode):
    @classmethod
    def define_schema(cls):return IO.Schema(node_id="AW_UseSavedStage",display_name="Reuse verified saved output (no generation)",category="Asset Workshop/Pipeline",is_output_node=True,inputs=strings("asset_id","stage_id","artifact_id"),outputs=[IO.File3DGLB.Output()])
    @classmethod
    def execute(cls,asset_id,stage_id,artifact_id):
        from .store import LOCK,JobConflict
        library=store();row,path=checked(library,asset_id,artifact_id,"mesh")
        with LOCK:
            project=library.load(asset_id)
            job=next(j for j in project["jobs"] if any(s["id"]==stage_id for s in j["stages"]))
            if job.get("cancel_requested") or job["state"] not in ("queued","running"):raise JobConflict("This job no longer owns its stage")
            project=library.select_pipeline_artifact(asset_id,project["revision"],artifact_id)
            job=next(j for j in project["jobs"] if any(s["id"]==stage_id for s in j["stages"]))
            if artifact_id not in job["artifacts"]:job["artifacts"].append(artifact_id)
            if row.get("variant"):project["pipeline"]["settings"]["output_variant"]=row["variant"]
            library.save(project);library.complete_job(asset_id,stage_id,{"export":artifact_id,"reused":True})
        return IO.NodeOutput(Types.File3D(str(path),"glb"),ui={"asset_workshop":[row]})

PIPELINE_NODES=[LoadGeometry,SaveGeometry,RefineGeometry,GeometryFrame,ZeroEdges,TextureSaved,OptimizeSaved,SaveVariant,MaterialStage,UseSavedStage]
