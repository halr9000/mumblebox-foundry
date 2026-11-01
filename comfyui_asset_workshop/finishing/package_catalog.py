"""Selected asset inventory shared by package publication and its root README."""
from dataclasses import dataclass, field, asdict
from pathlib import PurePosixPath
import json,re
from urllib.parse import urlsplit
VARIANTS={
"detailed":("Detailed/",("glb","fbx"),"Contains the high-detail textured master, retained as the source for detailed modeling and further derived assets."),
"game_balanced":("Game/Balanced/",("glb","fbx"),"Contains a reduced triangle mesh and matching baked material maps, prepared as a higher-detail game-development derivative."),
"game_compact":("Game/Compact/",("glb","fbx"),"Contains a reduced triangle mesh and matching baked material and surface-detail maps, prepared as a compact game-development derivative."),
"quad_light":("Editable_Quads/Light/",("blend","obj","authoring_fbx","runtime_glb","runtime_fbx"),"Contains the editable retopologized mesh, prepared for further modeling and topology editing. Authoring files preserve polygon faces; runtime files contain the triangulated derivative with matching material maps."),
"quad_detail":("Editable_Quads/Detail/",("blend","obj","authoring_fbx","runtime_glb","runtime_fbx"),"Contains an independently supplied detailed retopology variant, with authoring geometry and its triangulated runtime derivative."),
"print":("Print/",("stl",),"Contains the print-oriented geometry derivative. Its dimensions and recorded geometry checks describe this file; physical fabrication requires separate validation.")}
@dataclass
class Selection:
    mode:str
    variants:dict
@dataclass
class SourceArtifact:
    variant_id:str
    files:dict
    receipts:tuple=()
    lineage:tuple=()
@dataclass
class FileRecord:
    path:str
    kind:str
    variant_id:str|None
    description:str
    format:str
    role:str
    depends_on:tuple=()
    bytes:int=0
    sha256:str=""
@dataclass
class ValidationRecord:
    name:str
    status:str
    artifact_path:str
    artifact_sha256:str
    method:str=""
    note:str=""
@dataclass
class VariantRecord:
    id:str
    directory:str
    description:str
    intended_use:str=""
    file_paths:list=field(default_factory=list)
    measurements:dict=field(default_factory=dict)
    validations:list=field(default_factory=list)
    limitations:list=field(default_factory=list)
@dataclass
class PackageCatalog:
    schema:str
    asset_name:str
    export_id:str
    created_utc:str
    workflow_version:str|None
    files:list
    variants:list
    resources:list
    project_identity:dict
    warnings:list=field(default_factory=list)
    production:dict=field(default_factory=dict)
    def to_dict(self):return asdict(self)
def safe_relative(path):
    if not isinstance(path,str) or not path or "\\" in path or ":" in path or "//" in path:raise ValueError("Unsafe package path: "+repr(path))
    p=PurePosixPath(path)
    if p.is_absolute() or any(x in ("..",".","") or x.rstrip(". ")!=x or re.search(r'[<>|?*\x00-\x1f]',x) for x in path.split("/")):raise ValueError("Unsafe package path: "+repr(path))
    reserved={"CON","PRN","AUX","NUL",*(f"COM{i}" for i in range(1,10)),*(f"LPT{i}" for i in range(1,10))}
    if any(x.split(".")[0].upper() in reserved for x in p.parts):raise ValueError("Reserved package path: "+path)
    return p.as_posix()
def validate_paths(paths):
    seen=set()
    for p in paths:
        key=safe_relative(p).casefold()
        if key in seen:raise ValueError("Package path collision: "+p)
        seen.add(key)
def parse_selection(raw,available):
    if not raw.strip():
        chosen={k:tuple(x for x in VARIANTS[k][1] if x in available[k]) for k in VARIANTS if k in available and available[k]};mode="auto"
    else:
        try:d=json.loads(raw)
        except (TypeError,ValueError) as e:raise ValueError("Selection must be valid JSON") from e
        if not isinstance(d,dict) or set(d)!={"schema","variants"} or d["schema"]!="mumblebox.export-selection/1" or not isinstance(d["variants"],dict):raise ValueError("Unsupported export selection schema")
        chosen={}
        for k,v in d["variants"].items():
            if k not in VARIANTS:raise ValueError("Unavailable export variant: "+str(k))
            if not isinstance(v,dict) or set(v)!={"formats"} or not isinstance(v["formats"],list) or not v["formats"] or any(not isinstance(x,str) for x in v["formats"]):raise ValueError("Formats required for "+k)
            if len(v["formats"])!=len(set(v["formats"])):raise ValueError("Duplicate selected format: "+k)
            for fmt in v["formats"]:
                if fmt not in VARIANTS[k][1]:raise ValueError("Unsupported format: "+k+"/"+fmt)
                if fmt not in available.get(k,set()):raise ValueError("Selected output missing: "+k+"/"+fmt)
            chosen[k]=tuple(x for x in VARIANTS[k][1] if x in v["formats"])
        mode="explicit"
    if not chosen:raise ValueError("Select at least one available asset output")
    return Selection(mode,chosen)
def file_closure(paths,files):
    by={f.path:f for f in files};done=set();pending=list(paths)
    while pending:
        p=pending.pop()
        if p in done:continue
        if p not in by:raise ValueError("Required package dependency missing: "+p)
        done.add(p);pending.extend(by[p].depends_on)
    return done
def dependency_closure(selection,sources):
    for k in selection.variants:
        if k not in sources:raise ValueError("Selected variant missing: "+k)
    return {k:sources[k] for k in selection.variants}
def bind_measurements(files,receipts):
    result=[]
    for key in VARIANTS:
        owned=[f for f in files if f.variant_id==key]
        if not owned:continue
        hashes={f.sha256 for f in owned if f.sha256};measurements={}
        for r in receipts:
            if r.get("variant_id")==key and r.get("sha256") in hashes:measurements.update(r.get("measurements",{}))
        result.append(VariantRecord(key,VARIANTS[key][0],VARIANTS[key][2],file_paths=[f.path for f in owned],measurements=measurements))
    return result
def safe_url(url):
    if not url:return None
    if not isinstance(url,str):raise ValueError("Invalid project URL")
    p=urlsplit(url)
    if p.scheme not in ("https","http") or not p.netloc or p.username or p.password or any(c in url for c in "\r\n<>"):raise ValueError("Invalid project URL")
    return url
def build_catalog(files,variants,resources,identity,metadata):
    validate_paths([f.path for f in files])
    for f in files:file_closure([f.path],files)
    ident={k:identity.get(k) for k in ("name","description","terms")}
    for k in ("github_url","homepage_url","pinokio_url"):ident[k]=safe_url(identity.get(k))
    name=metadata.get("asset_name") or "Asset"
    if not isinstance(name,str) or len(name)>200:raise ValueError("Asset name must be text of at most 200 characters")
    return PackageCatalog("mumblebox.asset-catalog/2",name,str(metadata["export_id"]),str(metadata["created_utc"]),metadata.get("workflow_version"),files,variants,resources,ident,list(metadata.get("warnings",[])),metadata.get("production",{}))
