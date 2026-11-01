"""Pure validated-pipeline contracts; no model, filesystem or application imports."""
import copy
import hashlib
import json
import math

VERSION = "validated_v1"
VARIANTS = {"detailed": None, "balanced_250k": 250000, "compact_100k": 100000}
_DEFAULTS = {
    "shape_resolution": 1024, "refine_enabled": True, "refine_resolution": 1536, "refine_steps": 25, "refine_seed": 42,
    "cpu_offload": True, "attention": "sdpa", "intake_faces": 4500000,
    "weld_enabled": True, "weld_epsilon": .00001, "fill_enabled": True,
    "fill_perimeter": .03, "fill_vertices": 16, "remesh_enabled": True,
    "remesh_resolution": 512, "remesh_fill": 20,
    "texture_provider": "trellis2", "texture_steps": 20, "texture_seed": 42,
    "texture_size": 4096, "texture_resolution": 1024, "texture_guidance": 3.,
    "texture_rescale": .2, "texture_sampler": "euler", "reference_lock": 0.,
    "output_variant": "balanced_250k", "guide_size": 1024, "palette_count": 12,
    "material_steps": 4, "material_guidance": 10., "material_seed": 42,
}
_CHOICES = {"shape_resolution":(1024,1536,2048), "refine_resolution": (512,1024,1536), "attention": ("sdpa",),
    "texture_provider": ("trellis2", "pixal3d"), "texture_resolution": (1024,),
    "texture_sampler": ("euler", "heun"), "output_variant": tuple(VARIANTS),
    "guide_size": (512,1024,2048), "texture_size": (512,1024,2048,4096,8192)}
_RANGES = {"refine_steps":(1,100),"refine_seed":(0,2147483647),"intake_faces":(1000,4500000),
    "weld_epsilon":(0,.001),"fill_perimeter":(0,1),"fill_vertices":(3,1000),
    "remesh_resolution":(128,1024),"remesh_fill":(0,100),"texture_steps":(1,100),
    "texture_seed":(0,2147483647),"texture_guidance":(0,20),"texture_rescale":(0,1),
    "reference_lock":(0,1),"palette_count":(2,32),"material_steps":(1,50),
    "material_guidance":(0,20),"material_seed":(0,2147483647)}

def defaults():
    return copy.deepcopy(_DEFAULTS)

def validate_settings(changes):
    if not isinstance(changes, dict) or changes.keys() - _DEFAULTS.keys():
        raise ValueError("Unknown pipeline setting")
    checked = copy.deepcopy(changes)
    for key,value in checked.items():
        default = _DEFAULTS[key]
        if isinstance(default,bool):
            if not isinstance(value,bool): raise ValueError(key+" must be true or false")
        elif key in _CHOICES:
            if value not in _CHOICES[key] or isinstance(value,bool): raise ValueError("Unsupported "+key)
        else:
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
                raise ValueError("Invalid "+key)
            if isinstance(default,int) and not isinstance(value,int): raise ValueError(key+" must be an integer")
            low,high=_RANGES[key]
            if not low<=value<=high: raise ValueError("Out-of-range "+key)
    return checked

def initialize(project):
    state=project.setdefault("pipeline", {"version":VERSION,"settings":defaults(),
        "selected_geometry_id":None,"selected_texture_id":None,"selected_appearance_id":None,"variants":{}})
    if state.get("version") != VERSION: raise ValueError("Unsupported pipeline version")
    state["settings"]={**defaults(),**state.get("settings",{})}
    validate_settings(state["settings"])
    return state

def fingerprint(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()

def descendants(project,artifact_id):
    children={}
    for row in project.get("artifacts",[]):
        parents=[row.get(k) for k in ("parent_artifact_id","geometry_id","source_artifact_id","master")]
        parents+=row.get("parent_artifact_ids",[])
        for parent in filter(None,parents): children.setdefault(parent,set()).add(row["id"])
    result=set();pending=list(children.get(artifact_id,()))
    while pending:
        item=pending.pop()
        if item==artifact_id or item in result:continue
        result.add(item);pending.extend(children.get(item,()))
    return result
