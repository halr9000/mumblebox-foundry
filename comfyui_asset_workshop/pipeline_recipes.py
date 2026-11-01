"""Small visible graphs for the versioned, saved-geometry pipeline."""
import json
from .recipes import Graph, single_image_mesh_recipe
from .pipeline_state import defaults, VARIANTS, validate_settings

def settings(snapshot):
    result={**defaults(),**snapshot.get("pipeline",{}).get("settings",{})}
    validate_settings(result)
    return result

def source(project, snapshot, key, explicit=None, kind=None):
    aid=explicit or snapshot.get("pipeline",{}).get(key)
    row=next((a for a in project["artifacts"] if a["id"]==aid),None)
    if not row or row.get("stale") or (kind and row["kind"]!=kind):raise ValueError("Choose a current saved pipeline input from this project")
    return row

def build_stage_recipe(project,snapshot,stage,job):
    name=stage["name"];s=settings(snapshot);payload=job["payload"];g=Graph();p=project["id"]
    if name=="geometry":return single_image_mesh_recipe(snapshot,project,stage["id"],geometry_only=True)
    if name in ("refine","cleanup"):
        # Completed upstream stages update selection within this same owned job.
        row=source(project,project,"selected_geometry_id",payload.get("source_id"),"geometry")
        mesh=g.add("AW_LoadGeometry",asset_id=p,artifact_id=row["id"])
        if name=="refine" and s["refine_enabled"]:
            mesh=g.add("DecimateMesh",mesh=mesh,target_face_count=s["intake_faces"],placement_mode="midpoint")
            mesh=g.add("AW_RefineGeometry",mesh=mesh,asset_id=p,settings=json.dumps(s))
        if name=="cleanup":
            norm=g.add("AW_GeometryFrame",mesh=mesh,operation="normalize",frame="")
            mesh=norm
            if s["weld_enabled"]:mesh=g.add("WeldVertices",mesh=mesh,epsilon_rel=s["weld_epsilon"],epsilon_abs=0)
            if s["fill_enabled"]:mesh=g.add("FillHoles",mesh=mesh,max_perimeter=s["fill_perimeter"],weld_epsilon_rel=0,max_vertices=s["fill_vertices"],fill_chains=False)
            if s["remesh_enabled"]:mesh=g.add("RemeshMesh",mesh=mesh,resolution=s["remesh_resolution"],sign_mode="solid",**{"sign_mode.fill":s["remesh_fill"],"sign_mode.qef":False},band=1,project_back=0,fix_poles=False,smooth_iters=0,drop_small_components=0,precluster_max_verts=20000000)
            restored=g.add("AW_GeometryFrame",mesh=mesh,operation="restore",frame=g.out(norm,1))
            mesh=g.add("AW_ZeroEdges",mesh=restored)
        saved=g.add("AW_SaveGeometry",mesh=mesh,asset_id=p,stage_id=stage["id"],geometry_stage="refined" if name=="refine" else "clean",parent_id=row["id"],recipe=json.dumps({"pipeline_version":"validated_v1","settings":s}))
        glb=g.add("MeshToFile3D",mesh=saved)
    elif name=="texture":
        row=source(project,snapshot,"selected_geometry_id",payload.get("source_id"),"geometry")
        if row.get("geometry_stage")!="clean":raise ValueError("Texture the clean geometry checkpoint")
        glb=g.add("AW_TextureSaved",asset_id=p,stage_id=stage["id"],source_id=row["id"],settings=json.dumps(s))
    elif name=="variant":
        row=source(project,snapshot,"selected_texture_id",payload.get("source_id"),"mesh")
        variant=payload.get("variant",s["output_variant"])
        if variant not in VARIANTS:raise ValueError("Choose a supported output detail")
        cached=row if variant=="detailed" else next((a for a in reversed(project["artifacts"]) if a.get("kind")=="mesh" and not a.get("stale") and a.get("parent_artifact_id")==row["id"] and a.get("appearance_stage")=="variant" and a.get("variant")==variant),None)
        if cached:
            glb=g.add("AW_UseSavedStage",asset_id=p,stage_id=stage["id"],artifact_id=cached["id"])
            g.add("Preview3DAdvanced",model_3d=glb,viewport_state="",width=1024,height=1024)
            return {"graph":g.nodes,"details":{"pipeline_version":"validated_v1","reused_artifact_id":cached["id"],"variant":variant},"bindings":["Reuse saved verified output; no optimizer or texture generation"]}
        op=g.add("AW_OptimizeSaved",asset_id=p,source_id=row["id"],variant=variant,settings=json.dumps(s))
        high=g.add("AW_LoadGeometry",asset_id=p,artifact_id=row["geometry_id"])
        normal=g.add("BakeNormalMapFromMesh",low_poly=op,high_poly=high,resolution=row.get("texture_size",row.get("recipe",{}).get("settings",{}).get("texture_size",4096)),cage_distance=.01,ignore_backfaces=True)
        glb=g.add("AW_SaveVariant",mesh=op,folder=g.out(op,1),normal=normal,asset_id=p,stage_id=stage["id"],source_id=row["id"],variant=variant)
    elif name in ("material_guide","materials"):
        from .materials import assignment_fingerprint
        glb=g.add("AW_MaterialStage",asset_id=p,stage_id=stage["id"],session_id=payload["session_id"],operation="prepare" if name=="material_guide" else "apply",settings=json.dumps(s),draft_revision=snapshot["pipeline"]["material_sessions"][payload["session_id"]]["draft_revision"],assignment_key=assignment_fingerprint(snapshot["pipeline"]["material_sessions"][payload["session_id"]]["draft"]))
    else:raise ValueError("Unknown pipeline stage")
    g.add("Preview3DAdvanced",model_3d=glb,viewport_state="",width=1024,height=1024)
    return {"graph":g.nodes,"details":{"pipeline_version":"validated_v1","stage":name,"settings":s},"bindings":["Saved, project-bound "+name+" stage"]}
