"""Project-owned, revision-safe material sessions and bounded selection drafts."""
import base64
import binascii
import copy
import hashlib
import json
import math
from .store import LOCK, atomic_json, digest, identifier
from .pipeline_state import initialize, fingerprint, validate_settings
ALGORITHM="color-connected-v2"
MAX_FACES=2_000_000

def decode_mask(value,faces):
    if not isinstance(faces,int) or not 0<faces<=MAX_FACES or not isinstance(value,str) or not value or len(value)>((faces+7)//8+2)*4//3+4:raise ValueError("Invalid packed selection")
    try:raw=base64.b64decode(value,validate=True)
    except (ValueError,binascii.Error) as error:raise ValueError("Malformed packed selection") from error
    if len(raw)!=(faces+7)//8 or faces%8 and raw[-1]>>(faces%8):raise ValueError("Selection has invalid face count or padding")
    ranges=[];start=None
    for i in range(faces):
        on=raw[i//8]&(1<<(i%8))
        if on and start is None:start=i
        if not on and start is not None:ranges.append([start,i]);start=None
    if start is not None:ranges.append([start,faces])
    return ranges

def assignment_fingerprint(draft):
    # Editing a label, selection or unfinished form does not change rendered appearance.
    keys=("kind","id","prompt","strength","detail","tiles","metallic","enabled","mask_id")
    rows=[]
    for row in draft.get("regions",[]):
        item={k:row[k] for k in keys if k in row}
        if row.get("face_mask"):item["mask_id"]=hashlib.sha256(base64.b64decode(row["face_mask"],validate=True)).hexdigest()
        if row.get("face_ranges"):item["face_ranges"]=row["face_ranges"]
        rows.append(item)
    return fingerprint(rows)

def source(library,pid,aid):
    project=library._checked_project(pid)
    row=next((a for a in project["artifacts"] if a["id"]==identifier(aid)),None)
    if not row or row["kind"]!="mesh" or row.get("stale"):raise ValueError("Choose a current textured mesh in this project")
    path=library.path(pid,row["file"])
    if not path.is_file() or digest(path)!=row["sha256"]:raise ValueError("Material source changed on disk")
    if not 0<row.get("triangles",0)<=MAX_FACES:raise ValueError("Materials Lab supports at most two million triangles; choose a reduced variant")
    return project,row,path

def create_session(library,pid,revision,aid,settings):
    validate_settings(settings)
    with LOCK:
        library._checked_project(pid,revision);project,row,path=source(library,pid,aid)
        identity={"algorithm":ALGORITHM,"source_id":aid,"source_sha256":row["sha256"],"variant":row.get("variant","detailed"),"guide_size":settings.get("guide_size",1024),"palette_count":settings.get("palette_count",12)}
        sid=fingerprint(identity)[:24];sessions=initialize(project).setdefault("material_sessions",{})
        if sid in sessions:return copy.deepcopy(sessions[sid])
        session={"id":sid,**identity,"state":"unprepared","draft_revision":0,"rendered_revision":None,"rendered_artifact_id":None,"draft":{"version":1,"regions":[],"selection":[]},"assignment_fingerprint":assignment_fingerprint({}),"rendered_assignment_fingerprint":None,"assignments_pending":False}
        sessions[sid]=session;library.save(project)
        return copy.deepcopy(session)

def load_session(library,pid,sid):
    identifier(sid);project=library._checked_project(pid)
    session=project.get("pipeline",{}).get("material_sessions",{}).get(sid)
    if not session:raise ValueError("This material session is not owned by this project")
    _,row,_=source(library,pid,session["source_id"])
    if row["sha256"]!=session["source_sha256"] or row.get("variant","detailed")!=session["variant"]:raise ValueError("Material session source no longer matches")
    session=copy.deepcopy(session)
    session["assignment_fingerprint"]=assignment_fingerprint(session["draft"])
    if not session.get("rendered_assignment_fingerprint") and session.get("rendered_artifact_id"):
        rendered=next((a for a in project["artifacts"] if a["id"]==session["rendered_artifact_id"]),{})
        recorded=rendered.get("recipe",{}).get("material_assignments")
        if recorded is not None:session["rendered_assignment_fingerprint"]=assignment_fingerprint(recorded)
    session["assignments_pending"]=bool(session["draft"].get("regions")) and session["assignment_fingerprint"]!=session.get("rendered_assignment_fingerprint")
    return session

def folder(library,pid,sid):
    load_session(library,pid,sid)
    return library.path(pid,"pipeline/materials/"+identifier(sid))

def validate_draft(state,meta):
    if not isinstance(state,dict) or state.keys()-{"version","regions","selection","editorDraft","editorOptions"}:raise ValueError("Unknown material draft property")
    if type(state.get("version",1)) is not int or state.get("version",1)!=1:raise ValueError("Unsupported material draft version")
    state=copy.deepcopy(state);regions=state.get("regions",[]);selection=state.get("selection",[])
    if not isinstance(regions,list) or not isinstance(selection,list) or len(regions)>64 or len(selection)>64:raise ValueError("Choose at most 64 material regions")
    expanded=[]
    for rows in (regions,selection):
        for row in rows:
            if not isinstance(row,dict) or len(str(row.get("name","")))>160 or len(str(row.get("prompt","")))>4000:raise ValueError("Material names or descriptions are too long")
            if row.keys()-{"kind","id","name","prompt","strength","detail","tiles","metallic","enabled","faces","face_mask","mask_id","rgb"}:raise ValueError("Unknown region property")
            if "rgb" in row:
                rgb=row["rgb"]
                if not isinstance(rgb,list) or len(rgb)!=3 or any(isinstance(v,bool) or not isinstance(v,int) or not 0<=v<=255 for v in rgb):raise ValueError("Invalid region color metadata")
            kind=row.get("kind");idx=row.get("id")
            limit=meta["palette_count"] if kind=="color" else meta["patch_count"] if kind=="patch" else MAX_FACES if kind=="faces" else 0
            if isinstance(idx,bool) or not isinstance(idx,int) or not 0<=idx<limit:raise ValueError("Region is outside this guide")
            out=copy.deepcopy(row)
            if kind=="faces":out["face_ranges"]=decode_mask(row.get("face_mask"),meta["faces"])
            for key,lo,hi in (("strength",0,1),("detail",0,1),("tiles",.125,128)):
                value=row.get(key,1 if key=="strength" else .12 if key=="detail" else 8)
                if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not lo<=value<=hi:raise ValueError("Invalid material "+key)
            if row.get("metallic","auto") not in ("auto","metal","nonmetal"):raise ValueError("Invalid metallic response")
            if rows is regions:out.pop("face_mask",None);expanded.append(out)
    draft=state.get("editorDraft",{})
    if not isinstance(draft,dict) or len(str(draft.get("prompt","")))>4000 or len(str(draft.get("name","")))>160:raise ValueError("Invalid editor form draft")
    options=state.get("editorOptions",{})
    if not isinstance(options,dict) or len(json.dumps(options))>500:raise ValueError("Invalid editor options")
    return state,{"version":1,"regions":expanded}

def mask_bytes(library,pid,sid,mask_id):
    if not isinstance(mask_id,str) or len(mask_id)!=64 or any(c not in "0123456789abcdef" for c in mask_id):raise ValueError("Invalid selection identity")
    path=library.path(pid,"pipeline/materials/"+identifier(sid)+"/masks/"+mask_id+".bin")
    raw=path.read_bytes()
    if len(raw)>250000 or hashlib.sha256(raw).hexdigest()!=mask_id:raise ValueError("Saved selection changed on disk")
    return raw

def expanded_draft(library,pid,sid,draft):
    state=copy.deepcopy(draft)
    for rows in (state.get("regions",[]),state.get("selection",[])):
        for row in rows:
            if row.get("kind")=="faces" and not row.get("face_mask") and row.get("mask_id"):
                row["face_mask"]=base64.b64encode(mask_bytes(library,pid,sid,row["mask_id"])).decode("ascii")
    return state

def editor_session(library,pid,sid):
    session=load_session(library,pid,sid)
    session["draft"]=expanded_draft(library,pid,sid,session["draft"])
    return session

def persist_masks(library,pid,sid,state):
    state=copy.deepcopy(state)
    for rows in (state.get("regions",[]),state.get("selection",[])):
        for row in rows:
            if row.get("kind")!="faces":continue
            raw=base64.b64decode(row.pop("face_mask"),validate=True);key=hashlib.sha256(raw).hexdigest()
            if row.get("mask_id") and row["mask_id"]!=key:raise ValueError("Packed selection does not match its immutable ID")
            path=library.path(pid,"pipeline/materials/"+identifier(sid)+"/masks/"+key+".bin")
            if not path.exists():
                path.parent.mkdir(parents=True,exist_ok=True);temporary=path.with_suffix(".part");temporary.write_bytes(raw);temporary.replace(path)
            row["mask_id"]=key
    return state

def save_draft(library,pid,sid,expected_draft_revision,state):
    with LOCK:
        session=load_session(library,pid,sid)
        if session["draft_revision"]!=expected_draft_revision:raise ValueError("Material choices changed; reopen this session before overwriting")
        meta=json.loads((folder(library,pid,sid)/"metadata.json").read_text())
        checked,_=validate_draft(expanded_draft(library,pid,sid,state),meta)
        checked=persist_masks(library,pid,sid,checked)
        if fingerprint(checked)==fingerprint(session["draft"]):return session
        project=library._checked_project(pid);session.update(draft=checked,draft_revision=session["draft_revision"]+1)
        session["assignment_fingerprint"]=assignment_fingerprint(checked)
        session["assignments_pending"]=bool(checked.get("regions")) and session["assignment_fingerprint"]!=session.get("rendered_assignment_fingerprint")
        project["pipeline"]["material_sessions"][sid]=session;library.save(project)
        return copy.deepcopy(session)

def worker_edits(library,pid,sid):
    session=load_session(library,pid,sid);meta=json.loads((folder(library,pid,sid)/"metadata.json").read_text())
    return validate_draft(expanded_draft(library,pid,sid,session["draft"]),meta)[1]
