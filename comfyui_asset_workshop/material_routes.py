"""Explicit material mutations; reads never prepare guides or load models."""
import json
from pathlib import Path
from aiohttp import web
from .runtime import store
from . import materials
PREFIX="/asset-workshop/v2"
ASSETS={"guide.glb","guide.png","colors.bin","patches.bin","patch-sizes.bin","triangles.bin"}
def register(routes,endpoint,coordinator):
    @routes.post(PREFIX+"/projects/{project}/materials")
    @endpoint
    async def create(request):
        b=await request.json();session=materials.create_session(store(),request.match_info["project"],b["expected_revision"],b["source_id"],b.get("settings",{}))
        return web.json_response(session)
    @routes.get(PREFIX+"/projects/{project}/materials/{session}")
    @endpoint
    async def get(request):
        read=materials.editor_session if request.query.get("expand_masks")=="1" else materials.load_session
        return web.json_response(read(store(),request.match_info["project"],request.match_info["session"]))
    @routes.patch(PREFIX+"/projects/{project}/materials/{session}")
    @endpoint
    async def save(request):
        if request.content_length and request.content_length>24*1024**2:raise ValueError("Material draft exceeds the bounded 24 MiB limit")
        b=await request.json();return web.json_response(materials.save_draft(store(),request.match_info["project"],request.match_info["session"],b["expected_draft_revision"],b["state"]))
    @routes.get(PREFIX+"/projects/{project}/materials/{session}/assets/{name}")
    @endpoint
    async def asset(request):
        library=store();pid=request.match_info["project"];sid=request.match_info["session"];name=request.match_info["name"];session=materials.load_session(library,pid,sid)
        if name=="source.glb":return web.FileResponse(materials.source(library,pid,session["source_id"])[2])
        folder=materials.folder(library,pid,sid)
        if name=="metadata.json":
            meta=json.loads((folder/name).read_text());meta.pop("source_mesh",None);return web.json_response(meta)
        if name=="status.json":return web.json_response({"state":session["state"]})
        if name not in ASSETS:raise ValueError("Unsupported material preview resource")
        return web.FileResponse(library.path(pid,"pipeline/materials/"+sid+"/"+name))
    @routes.get(PREFIX+"/projects/{project}/materials/{session}/selections/{mask}")
    @endpoint
    async def selection(request):
        import base64
        library=store();pid=request.match_info["project"];sid=request.match_info["session"];session=materials.load_session(library,pid,sid)
        key=request.match_info["mask"]
        if not any(r.get("mask_id")==key for rows in (session["draft"].get("regions",[]),session["draft"].get("selection",[])) for r in rows):raise ValueError("Selection is not recorded in this session")
        return web.json_response({"mask_id":key,"encoding":"base64 packed little-endian bits","face_mask":base64.b64encode(materials.mask_bytes(library,pid,sid,key)).decode("ascii")})
    routes.static(PREFIX+"/material-lab",str(Path(__file__).parent/"material_lab"),show_index=False)
