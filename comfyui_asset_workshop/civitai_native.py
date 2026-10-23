"""Header-only architecture checks and owned installed-weight selection."""
import json
from pathlib import Path
import struct
from types import SimpleNamespace

import folder_paths
from safetensors import safe_open

from .civitai_catalog import CivitaiError
from .civitai_downloads import file_hash


def root():
    return Path(folder_paths.base_path).resolve() / 'models'


def read_header(path):
    with Path(path).open('rb') as handle:
        prefix = handle.read(8)
        if len(prefix) != 8:
            raise CivitaiError('The weight file has no SafeTensor header.', 'integrity')
        size = struct.unpack('<Q', prefix)[0]
        if not 0 < size <= 16 * 1024**2:
            raise CivitaiError('The weight file has an invalid or oversized SafeTensor header.', 'integrity')
        try:
            result = json.loads(handle.read(size))
        except (ValueError, UnicodeError):
            raise CivitaiError('The downloaded file is not a valid SafeTensor weight file.', 'integrity') from None
    if not isinstance(result, dict):
        raise CivitaiError('The weight file header is invalid.', 'integrity')
    return result


def validate_weights(path, item):
    header = read_header(path)
    try:
        with safe_open(str(path), framework='numpy') as weights:
            keys = list(weights.keys())
    except Exception:
        raise CivitaiError('The file failed SafeTensor validation. It was not installed.', 'integrity') from None
    if item['kind'] == 'LORA':
        if not any(any(term in k.lower() for term in ('.lora_', '.lora.', 'lora_down', 'lora_up', '.hada_', '.lokr_', '.diff', '.dora_')) for k in keys):
            raise CivitaiError('This file does not contain recognizable adapter weights. It was not installed as a LoRA.', 'compatibility')
        return
    # Native detection reads shapes, not model tensors; no GPU model is loaded.
    from comfy import model_detection
    shapes = {key: SimpleNamespace(shape=tuple(value['shape'])) for key, value in header.items()
              if key != '__metadata__' and isinstance(value, dict) and 'shape' in value}
    prefix = model_detection.unet_prefix_from_state_dict(shapes)
    try:
        config = model_detection.detect_unet_config(shapes, prefix, metadata=header.get('__metadata__'))
    except (KeyError, AttributeError, TypeError, ValueError, IndexError):
        config = None
    family = item['family']
    valid = False
    if config:
        if family == 'sdxl':
            valid = config.get('context_dim') == 2048 and config.get('adm_in_channels') == 2816
            valid = valid and any(k.startswith('conditioner.embedders.0.') for k in keys)
            valid = valid and any(k.startswith('conditioner.embedders.1.') for k in keys)
            valid = valid and any(k.startswith('first_stage_model.') for k in keys)
        else:
            expected = {'klein4': ('flux2', 'img_in.weight', 3072),
                        'klein9': ('flux2', 'img_in.weight', 4096),
                        'qwen21': ('qwen_image21', 'img_in.weight', 4096),
                        'qwen2511': ('qwen_image', 'img_in.weight', 3072),
                        'flux3': ('flux3', 'txt_in.weight', 3072)}.get(family)
            if expected:
                image_model, anchor, width = expected
                shape = shapes.get(prefix + anchor)
                valid = config.get('image_model') == image_model and shape is not None and shape.shape[0] == width
                # Native UNETLoader expects a component checkpoint, not an SGM bundle.
                valid = valid and prefix == ''
    if not valid:
        raise CivitaiError('The downloaded architecture or packaging does not match this workflow. Choose a native component checkpoint, or a complete SDXL checkpoint with both text encoders and VAE. No weights were installed.', 'compatibility')


def installed_records():
    path = root() / '.mumblebox-civitai' / 'installed.json'
    if not path.is_file():
        return []
    values = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(values, list) or len(values) > 1000:
        raise CivitaiError('The installed resource catalog is invalid.', 'storage')
    return values


def selected_model(asset, verify=False):
    choice = asset.get('settings', {}).get('image_checkpoint')
    if not choice:
        return None
    item = next((v for v in installed_records() if str(v['file_id']) == str(choice) and v['kind'] == 'Checkpoint'), None)
    if not item:
        raise CivitaiError('This checkpoint is no longer registered. Select an installed checkpoint or the official model.', 'missing')
    if item['profile'] != asset['profile'] and not (item['family'] == 'sdxl' and asset['profile'] in ('sdxl_base', 'sdxl_juggernaut')):
        raise CivitaiError('The selected checkpoint belongs to another model variant.', 'compatibility')
    path = (root() / item['category'] / item['relative_path']).resolve()
    if not path.is_relative_to(root()) or not path.is_file():
        raise CivitaiError('The selected checkpoint is missing or outside this Comfy installation.', 'missing')
    if verify and file_hash(path) != item['sha256']:
        raise CivitaiError('The selected checkpoint changed after verification. It has not been replaced; select verified weights.', 'integrity')
    return {**item, 'path': str(path)}
