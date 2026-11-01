"""Selected image-model recipes for the existing four-panel extraction contract.

No model tensors or downloads live here. Shared profiles/lock own weights and
sampling defaults; this owner supplies native conditioning and the sheet canvas.
"""
import importlib
import json
from functools import lru_cache
from pathlib import Path

_root = __package__.split(".foundry", 1)[0] if ".foundry" in __package__ else ""
PROFILES = importlib.import_module((_root + "." if _root else "") + "profiles").PROFILES
MODEL_IDS = ("qwen21", "qwen2511", "klein4", "klein4_base", "flux3_distilled", "flux3_base",
             "klein_distilled", "klein_base", "klein_kv")
RECIPE_VERSION = "four-view/2026-11-01.2"
WIDTH, HEIGHT = 4096, 1024

@lru_cache(maxsize=1)
def model_lock():
    return json.loads(Path(__file__).resolve().parents[3].joinpath("models.lock.json").read_text(encoding="utf-8"))["models"]

def model_spec(model_id="qwen21"):
    if model_id not in MODEL_IDS:
        raise ValueError("Choose an available turnaround model.")
    profile = PROFILES[model_id]
    keys = (profile["model"], profile["encoder"], profile["vae"])
    if model_id == "qwen21":
        license_name = "Qwen Research License"
        license_url = "https://huggingface.co/Qwen/Qwen-Image-2.1/blob/main/LICENSE"
        summary = "Research and evaluation use. Commercial use requires separate authorization from Qwen."
        resources = ["qwen21"]
        source = "https://docs.comfy.org/tutorials/image/qwen/qwen-image-2-1"
    elif model_id == "qwen2511":
        license_name = "Apache 2.0"
        license_url = "https://huggingface.co/Qwen/Qwen-Image-Edit-2511#license-agreement"
        summary = "Permits commercial use under Apache 2.0 terms. Retain applicable notices."
        resources = ["qwen2511", "qwen25vl"]
        source = "https://docs.comfy.org/tutorials/image/qwen/qwen-image-edit-2511"
    elif model_id.startswith("klein4"):
        license_name = "Apache 2.0"
        license_url = "https://huggingface.co/black-forest-labs/FLUX.2-klein-" + ("base-" if model_id.endswith("base") else "") + "4B"
        summary = "Permits commercial use under Apache 2.0 terms. Other pipeline components have their own terms."
        resources = [model_id, "qwen3_4b", "flux_vae"]
        source = "https://docs.comfy.org/tutorials/flux/flux-2-klein"
    elif model_id.startswith("flux3"):
        license_name = "FLUX Kommunity License"
        license_url = "https://huggingface.co/black-forest-labs/flux-3-image-klein/blob/main/LICENSE.md"
        summary = "Commercial use is available to qualifying users under the Kommunity terms; other users need a separate license. Review the eligibility conditions."
        resources = [model_id, "qwen3vl_encoder", "flux_vae"]
        source = "https://docs.comfy.org/tutorials/flux/flux-3-klein"
    else:
        license_name = "FLUX Non-Commercial License"
        license_url = "https://github.com/black-forest-labs/flux2/blob/main/model_licenses/LICENSE-FLUX-NON-COMMERICAL"
        summary = "Model operation is noncommercial unless separately licensed. Output provisions are distinct; consult the agreement."
        resources = [model_id, "qwen3_8b", "flux_vae"]
        source = "https://docs.comfy.org/tutorials/flux/flux-2-klein"
    return dict(id=model_id, name=profile["label"], steps=profile["steps"], cfg=profile["cfg"],
                max_references=min(profile["references"], 10), width=WIDTH, height=HEIGHT,
                clip_type=profile["clip_type"], keys=list(keys),
                files={role:model_lock()[key]["name"] for role,key in zip(("model","encoder","vae"),keys)},
                license=license_name, license_url=license_url, license_summary=summary,
                resources=resources, source=source, recipe=RECIPE_VERSION,
                sampler="euler", scheduler="Flux2Scheduler" if model_id.startswith("klein") else "simple")

def dependency_keys(model_id="qwen21"):
    return tuple(model_spec(model_id)["keys"]) + ("birefnet",)

def public_models():
    """Cheap availability discovery; first-use readiness performs actual hashing."""
    try:
        import folder_paths
    except ImportError:
        folder_paths = None
    result = []
    for model_id in MODEL_IDS:
        spec = model_spec(model_id)
        if folder_paths:
            spec["installed"] = all(folder_paths.get_full_path(model_lock()[key]["category"],model_lock()[key]["name"]) for key in spec["keys"])
        result.append(spec)
    return result

def compile_turnaround(run):
    """Return only the selected native image branch; output 1557 is the sheet.

    References condition the output. They never set its dimensions: all models
    get the same explicit 4096 x 1024 canvas used by the four square crops.
    """
    from .prompts import bind_references
    model_id = run.get("turnaround_model", "qwen21")
    spec = model_spec(model_id)
    bound = bind_references(run["category"],run["references"],model_id)
    graph = {}
    def add(ident, kind, title=None, **inputs):
        graph[str(ident)] = {"class_type":kind,"inputs":inputs,"_meta":{"title":title or kind}}
        return [str(ident),0]
    images = [add(900 if i == 0 else 9200+i,"LoadImage",f"Reference {i+1} — {ref['role']}",image=ref["filename"])
              for i,ref in enumerate(run["references"])]
    model = add(1551,"UNETLoader",spec["name"],unet_name=spec["files"]["model"],weight_dtype="default")
    clip = add(1553,"CLIPLoader","Selected image encoder",clip_name=spec["files"]["encoder"],type=spec["clip_type"],device="default")
    vae = add(1554,"VAELoader","Selected image VAE",vae_name=spec["files"]["vae"])
    seed = run["settings"]["turnaround_seed"]
    if model_id == "qwen21":
        model = add(1569,"QwenImage21Cache","Published Qwen cache",model=model,device="auto",dtype="default")
        positive = add(1574,"TextEncodeQwenImage21","Four-view instruction and ordered references",clip=clip,vae=vae,
                       prompt=bound["prompt"],negative_prompt="",resolution=0,
                       **{f"images.image_{i+1}":image for i,image in enumerate(images)})
        negative = ["1574",1]
        latent = add(1556,"EmptyLatentImage","Four-panel canvas",width=WIDTH,height=HEIGHT,batch_size=1)
    elif model_id == "qwen2511":
        model = add(1569,"ModelSamplingAuraFlow",model=model,shift=3.1,sampling="flow")
        model = add(1570,"CFGNorm",model=model,strength=1.0)
        refs = {f"image{i+1}":image for i,image in enumerate(images)}
        positive = add(1574,"TextEncodeQwenImageEditPlus","Four-view instruction and ordered references",clip=clip,vae=vae,prompt=bound["prompt"],**refs)
        negative = add(1575,"TextEncodeQwenImageEditPlus",clip=clip,vae=vae,prompt="",**refs)
        positive = add(9300,"FluxKontextMultiReferenceLatentMethod",conditioning=positive,reference_latents_method="index_timestep_zero")
        negative = add(9301,"FluxKontextMultiReferenceLatentMethod",conditioning=negative,reference_latents_method="index_timestep_zero")
        latent = add(1556,"EmptySD3LatentImage","Four-panel canvas",width=WIDTH,height=HEIGHT,batch_size=1)
    else:
        positive = add(1574,"CLIPTextEncode","Four-view instruction and ordered references",clip=clip,text=bound["prompt"])
        negative = add(1575,"CLIPTextEncode",clip=clip,text="")
        if model_id.startswith("klein"):
            if model_id == "klein_kv":
                negative = add(9300,"ConditioningZeroOut",conditioning=positive)
                model = add(1569,"FluxKVCache",model=model)
            for i,image in enumerate(images):
                ident = 9310+i*4
                scaled = add(ident,"ImageScaleToTotalPixels",image=image,upscale_method="lanczos",megapixels=1.0,resolution_steps=16)
                encoded = add(ident+1,"VAEEncode",pixels=scaled,vae=vae)
                positive = add(ident+2,"ReferenceLatent",conditioning=positive,latent=encoded)
                negative = add(ident+3,"ReferenceLatent",conditioning=negative,latent=encoded)
        else:
            positive = add(1569,"ReferenceMultiLatent",positive=positive,negative=negative,vae=vae,
                           resolution="resize",**{"resolution.megapixels":1.0},
                           **{f"images.image{i}":image for i,image in enumerate(images)})
            negative = ["1569",1]
        latent = add(1556,"EmptyFlux2LatentImage","Four-panel canvas",width=WIDTH,height=HEIGHT,batch_size=1)
    if model_id.startswith("klein"):
        guider = add(1576,"CFGGuider",model=model,positive=positive,negative=negative,cfg=spec["cfg"])
        noise = add(1577,"RandomNoise",noise_seed=seed)
        sampler = add(1578,"KSamplerSelect",sampler_name="euler")
        sigmas = add(1579,"Flux2Scheduler",steps=spec["steps"],width=WIDTH,height=HEIGHT)
        samples = add(1558,"SamplerCustomAdvanced",noise=noise,guider=guider,sampler=sampler,sigmas=sigmas,latent_image=latent)
    else:
        samples = add(1558,"KSampler",model=model,positive=positive,negative=negative,latent_image=latent,
                      seed=seed,steps=spec["steps"],cfg=spec["cfg"],sampler_name="euler",scheduler="simple",denoise=1.0)
    add(1557,"VAEDecode","Four-view sheet → existing extraction",samples=samples,vae=vae)
    return graph
