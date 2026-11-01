"""Validated creator inputs and capabilities. No downloads or runtime side effects."""
import importlib
import math
from pathlib import PurePosixPath

_root=__package__.split(".foundry",1)[0] if ".foundry" in __package__ else ""
profiles=importlib.import_module((_root+"." if _root else "")+"profiles")
PROFILES=profiles.PROFILES
VERSION="image-creation/1"
CATEGORIES=(
    ("characters","Character","A humanoid character, shown completely from the front and back."),
    ("creatures","Creature","An animal or nonhuman creature; preserve its natural anatomy."),
    ("props","Prop","One complete object or game prop."),
    ("vehicles","Vehicle","One complete vehicle with matching front and rear views."),
    ("environment","Environment piece","One building or set piece, isolated for asset creation."),
    ("background","Background / Scene","One finished scene or background image."),
    ("general","General Image","One image from your description, without asset preparation instructions."),
)

def is_pair(category):
    return category in {row[0] for row in CATEGORIES[:5]}

def text(value, name, maximum=8000, required=False):
    if not isinstance(value,str) or len(value)>maximum or "\x00" in value:
        raise ValueError(f"{name} must be text up to {maximum} characters.")
    value=value.strip()
    if required and not value:raise ValueError(f"Enter {name.lower()}.")
    return value

def number(value, name, low, high, integer=False):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number.")
    if not low<=value<=high or (integer and int(value)!=value):
        raise ValueError(f"{name} must be {'a whole number ' if integer else ''}between {low} and {high}.")
    return int(value) if integer else float(value)

def filename(value):
    value=text(value,"Image filename",512,True).replace("\\","/")
    path=PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or ":" in value or "[" in value or "]" in value:
        raise ValueError("Choose an uploaded image inside the Comfy input folder.")
    if path.suffix.lower() not in (".png",".jpg",".jpeg",".webp"):
        raise ValueError("Use PNG, JPEG or WebP reference images.")
    return path.as_posix()

def reference_limit(model, paired):
    # Practical limit, reserving a native input for generated-front identity.
    return min(10,PROFILES[model]["references"]-int(paired))

def validate(data):
    if not isinstance(data,dict):raise ValueError("Supply image creation options.")
    category=data.get("category","characters")
    if category not in {row[0] for row in CATEGORIES}:raise ValueError("Choose an image category.")
    model=data.get("model","klein4")
    if model not in PROFILES:raise ValueError("Choose a supported image model profile.")
    profile=PROFILES[model];paired=is_pair(category)
    refs=data.get("references",[]);limit=reference_limit(model,paired)
    if not isinstance(refs,list) or len(refs)>limit:
        raise ValueError(f"This selection supports up to {limit} references; paired generation reserves one input for the front.")
    references=[]
    for index,ref in enumerate(refs):
        if not isinstance(ref,dict):raise ValueError("Each reference must be an image card.")
        references.append({"id":f"reference-{index+1}","filename":filename(ref.get("filename","")),
            "role":text(ref.get("role","detail"),"Reference purpose",100),
            "description":text(ref.get("description",""),"Reference description",2000)})
    if profile.get("edit_only") and not references:raise ValueError("This image-editing model needs at least one reference image.")
    description=text(data.get("description",""),"Description")
    if not description and not references:raise ValueError("Describe your image or provide a reference.")
    raw=data.get("settings",{})
    if not isinstance(raw,dict):raise ValueError("Settings must be an object.")
    resolution=number(raw.get("resolution",1024),"Resolution",256,2048,True)
    if resolution%64:raise ValueError("Resolution must be a multiple of 64 pixels.")
    settings={"resolution":resolution,"steps":number(raw.get("steps",profile["steps"]),"Steps",1,150,True),
              "cfg":number(raw.get("cfg",profile["cfg"]),"Guidance",.1,30),
              "seed":number(raw.get("seed",-1),"Seed",-1,2**53-16,True),
              "negative_prompt":text(raw.get("negative_prompt",""),"Negative prompt",4000),
              "reference_strength":number(raw.get("reference_strength",.8),"Reference strength",0,2),
              "edit_denoise":number(raw.get("edit_denoise",.85),"Edit strength",.01,1)}
    checkpoint=text(data.get("checkpoint",""),"Checkpoint",512)
    if checkpoint and (":" in checkpoint or ".." in PurePosixPath(checkpoint.replace("\\","/")).parts or checkpoint.startswith(("/","\\"))):
        raise ValueError("Choose an installed checkpoint from the model catalog.")
    raw_loras=data.get("loras",[])
    if not isinstance(raw_loras,list) or len(raw_loras)>8:raise ValueError("Choose up to eight compatible LoRAs.")
    loras=[]
    for item in raw_loras:
        if not isinstance(item,dict):raise ValueError("Each LoRA needs its model family and strength.")
        declared=item.get("profile")
        if not profiles.lora_compatible(declared,model):raise ValueError("Choose a LoRA compatible with the selected model.")
        name=text(item.get("name",""),"LoRA filename",512,True)
        if ":" in name or ".." in PurePosixPath(name.replace("\\","/")).parts or name.startswith(("/","\\")):
            raise ValueError("Choose an installed LoRA from the model catalog.")
        strength=number(item.get("strength",1),"LoRA strength",-3,3)
        loras.append({"name":name,"profile":declared,"strength":strength,
                      "strength_clip":number(item.get("strength_clip",strength),"LoRA text strength",-3,3),
                      "trigger":text(item.get("trigger",""),"LoRA trigger words",1000),"enabled":True})
    return {"schema":VERSION,"name":text(data.get("name","Untitled image"),"Name",100,True),
            "category":category,"paired":paired,"model":model,"checkpoint":checkpoint,
            "description":description,"front":text(data.get("front",""),"Front details",4000) if paired else "",
            "back":text(data.get("back",""),"Back details",4000) if paired else "",
            "references":references,"settings":settings,"loras":loras}

def catalog():
    return {"schema":VERSION,"default_model":"klein4",
            "categories":[{"id":k,"name":n,"description":d,"paired":is_pair(k)} for k,n,d in CATEGORIES],
            "models":[{**profiles.capabilities(key),"pair_references":reference_limit(key,True),
                       "single_references":reference_limit(key,False)} for key in PROFILES]}
