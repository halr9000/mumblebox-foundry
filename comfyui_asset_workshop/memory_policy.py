"""Hardware-based starting settings using Comfy's existing memory controls."""

import copy

import psutil

import comfy.model_management as memory

from .profiles import PROFILES, SOURCES, model_id
from .recipes import MODELS, required_models

GB = 1024**3
MEMORY_KEYS = ("extra_vram_headroom_gb", "min_ram_free_gb", "cache_device",
               "tiled_vae", "image_precision", "cache_precision", "helper_precision",
               "release_between_stages")


def preset_settings(preset_id: str, hardware: dict) -> dict:
    if preset_id not in ("standard_16gb", "experimental_8gb"):
        raise ValueError("Choose Standard or the experimental Low memory preset.")
    low = preset_id == "experimental_8gb"
    ram = hardware["ram_total_gb"]
    values = {"resolution": 768 if low else 1024, "shape_resolution": 1024 if low else 1536,
              "master_texture": 1024 if low else 4096, "master_faces": 100000 if low else 700000,
              "game_texture": 1024 if low else 2048, "game_faces": 100000,
              "normal_resolution": 1024 if low else 2048, "ao_resolution": 1024,
              "extra_vram_headroom_gb": 2 if low else 1,
              "min_ram_free_gb": min(8, max(2, round(ram/8))) if low else 8,
              "min_vram_free_gb": 1.5, "cache_device": "cpu" if ram >= 28 else "off",
              "tiled_vae": True, "release_between_stages": True, "remesh": False, "uv_method": "pec",
              "helper_precision": "q4" if low else "q8", "image_precision": "native", "cache_precision": "default"}
    return {"id": preset_id, "label": "Low memory — 8 GB VRAM (Experimental)" if low else "Standard — 16 GB VRAM",
            "profile": "klein4", "settings": values,
            "validation": {"status": "experimental" if low else "primary_target", "hardware_validated": False,
                "message": "Needs tester validation on real 8 GB hardware; system RAM requirements are unproven."
                           if low else "Primary target is the 16 GB GPU / 64 GB RAM host; see recorded validation results."},
            "explanations": {
                "resolution": "Smaller generated images need less memory and carry less fine detail. Original uploads stay untouched.",
                "shape_resolution": "Lower density reduces reconstruction memory and can lose thin or small shapes.",
                "master_texture": "Smaller texture, normal and AO maps reduce baking memory and surface detail, not all earlier material inference.",
                "master_faces": "Fewer exported faces simplify the result; this does not reduce earlier reconstruction memory. The raw master is preserved.",
                "extra_vram_headroom_gb": "Estimated extra sampler headroom encourages offloading to system RAM. It is not an allocation cap.",
                "cache_device": "A CPU reference cache trades GPU memory for system RAM. Off recomputes rather than retaining the cache.",
                "helper_precision": "The optional smaller Q4 helper must already be available or explicitly downloaded. Manual prompting needs no helper.",
                "release_between_stages": "Unload between heavy stages. Extra transfers can make low-memory operation slower.",
                "model": "Klein 4B is the starting choice. Other models and LoRAs stay selectable; this preset does not prove they fit."}}


def apply_preset(asset: dict, preset_id: str, hardware: dict) -> dict:
    preset = preset_settings(preset_id, hardware)
    result = {**asset, "settings": copy.deepcopy(asset["settings"]), "profile": preset["profile"],
              "memory_preset_id": preset_id, "preset_overrides": []}
    result["settings"].update(preset["settings"])
    result["settings"]["memory_overrides"] = [key for key in MEMORY_KEYS if key != "release_between_stages"]
    return result


def project_patch(asset: dict, changes: dict, hardware: dict) -> dict:
    result = copy.deepcopy(changes)
    requested_settings = changes.get("settings", {})
    preset_id = changes.get("memory_preset_id")
    if preset_id in ("standard_16gb", "experimental_8gb"):
        applied = apply_preset(asset, preset_id, hardware)
        result["settings"] = {**applied["settings"], **requested_settings}
        result["profile"] = changes.get("profile", applied["profile"])
        result["preset_overrides"] = [key for key, value in requested_settings.items()
                                      if value != applied["settings"].get(key)]
        if result["profile"] != applied["profile"]:
            result["preset_overrides"].append("profile")
    else:
        overrides = set(asset.get("preset_overrides", []))
        overrides.update(key for key, value in requested_settings.items() if value != asset["settings"].get(key))
        if "profile" in changes and changes["profile"] != asset["profile"]:
            overrides.add("profile")
            result["settings"] = {"steps": None, "cfg": None, "image_precision": "native", **requested_settings}
        if overrides:
            result["preset_overrides"] = sorted(overrides)
    if any(key in MEMORY_KEYS for key in requested_settings):
        settings = result.setdefault("settings", {})
        settings["memory_overrides"] = sorted(set(asset["settings"].get("memory_overrides", [])) |
                                              (set(requested_settings) & set(MEMORY_KEYS) - {"release_between_stages"}))
    return result


def hardware_info():
    device = memory.get_torch_device()
    ram = psutil.virtual_memory()
    gpu = device.type != "cpu"
    return {
        "device": str(device), "device_type": device.type,
        "name": memory.get_torch_device_name(device),
        "vram_total_gb": memory.get_total_memory(device) / GB if gpu else 0,
        "vram_free_gb": memory.get_free_memory(device) / GB if gpu else 0,
        "ram_total_gb": ram.total / GB, "ram_free_gb": ram.available / GB,
        "comfy_mode": memory.vram_state.name,
        "startup_reserve_gb": memory.extra_reserved_memory() / GB if gpu else 0,
    }


def recommendations(asset, hardware):
    total = hardware["vram_total_gb"]
    ram = hardware["ram_total_gb"]
    main = MODELS[model_id(asset)]
    small_gpu = total < 11
    model_gb = main["size"] / GB
    extra = (2 if small_gpu else 1 if total < 20 else .5) if total else 0
    if total and model_gb > total:
        extra = min(3, extra + .5)
    values = {
        "extra_vram_headroom_gb": extra,
        "min_ram_free_gb": min(8, max(2, round(ram / 8))),
        "cache_device": "cpu" if ram >= 28 else "off",
        "tiled_vae": True, "image_precision": "native", "cache_precision": "default",
        "helper_precision": "q4" if total < 14 else "q8",
        "release_between_stages": True,
    }
    explanations = {
        "extra_vram_headroom_gb": f"{extra:g} GB of additional sampler headroom encourages Comfy to offload more weights to RAM.",
        "min_ram_free_gb": "Leave system memory available for Windows and other applications.",
        "cache_device": "Keep reference data in RAM to save VRAM." if ram >= 28 else "Recompute reference data to avoid keeping a large cache in limited RAM.",
        "tiled_vae": "Decode images in smaller sections to reduce peak graphics-memory use.",
        "image_precision": "Use the supported native model format already selected for this model.",
        "cache_precision": "Keep reference-cache precision unchanged to preserve quality.",
        "helper_precision": "Use the smaller Q4 assistant on this GPU." if total < 14 else "Use the higher-precision Q8 assistant on this GPU.",
        "release_between_stages": "Release idle Comfy model weights before loading the next stage.",
    }
    warnings = []
    if not total:
        warnings.append("Comfy is using a CPU. The 3D stages require a compatible accelerator; no GPU fit has been established.")
    if total and model_gb > max(0, hardware["vram_free_gb"] - hardware["startup_reserve_gb"]):
        warnings.append(f"The selected image model has {model_gb:.1f} GB of weights. CPU offloading will likely be needed on this device.")
    if hardware["ram_free_gb"] < values["min_ram_free_gb"]:
        warnings.append("Available system RAM is below the recommended reserve. Free some RAM before generating.")
    if memory.vram_state.name == "HIGH_VRAM":
        warnings.append("Comfy was launched in high-VRAM mode. These per-stage controls cannot override that launcher policy.")
    return {"values": values, "explanations": explanations, "warnings": warnings,
            "model_name": main["name"], "model_weights_gb": model_gb,
            "basis": "Conservative starting settings, not measured peak-memory requirements or a guarantee of fit."}


def apply_policy(asset, hardware=None):
    hardware = hardware or hardware_info()
    settings = asset["settings"]
    if "memory_overrides" not in settings:
        # Existing assets keep explicit settings until Restore recommendations is chosen.
        settings["memory_overrides"] = [key for key in MEMORY_KEYS if key in settings]
    proposed = recommendations(asset, hardware)
    for key, value in proposed["values"].items():
        if key not in settings["memory_overrides"]:
            settings[key] = value
    # Required lifecycle contract: no asset may disable cleanup after heavy work.
    settings["release_between_stages"] = True
    settings["memory_overrides"] = [key for key in settings["memory_overrides"] if key != "release_between_stages"]
    return asset


def inspect_policy(asset):
    hardware = hardware_info()
    proposed = recommendations(asset, hardware)
    settings = asset["settings"]
    overrides = settings.get("memory_overrides", [k for k in MEMORY_KEYS if k in settings])
    effective = {key: settings.get(key, value) if key in overrides else value
                 for key, value in proposed["values"].items()}
    return {"hardware": hardware, **proposed, "effective": effective, "overrides": overrides,
            "bf16_supported": PROFILES[asset["profile"]]["model"] + "_bf16" in SOURCES}


def preflight(asset, stage):
    hardware = hardware_info()
    apply_policy(asset, hardware)
    minimum = asset["settings"]["min_ram_free_gb"]
    if hardware["ram_free_gb"] < minimum:
        raise ValueError(f"Only {hardware['ram_free_gb']:.1f} GB of RAM is free; your reserve is {minimum:g} GB. Close other applications or adjust the RAM reserve in Settings.")
    vram_reserve = asset["settings"].get("min_vram_free_gb", 1.5)
    if hardware["vram_free_gb"] < vram_reserve:
        raise ValueError(f"Only {hardware['vram_free_gb']:.1f} GB VRAM is free; your reserve is {vram_reserve:g} GB. Release idle models or close another GPU application before continuing.")
    # Resolve supported model variants before starting downloads or sampling.
    required_models(asset, stage)
    return hardware
