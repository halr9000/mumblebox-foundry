"""Conservative local LoRA choices from headers and installed source metadata.

No tensors are loaded. Unknown, conflicting, or unsupported formats are withheld
from the picker; native matching remains the final check during execution.
"""
from functools import lru_cache
from itertools import islice
from pathlib import Path
import re


FAMILY_PROFILES = {
    'sdxl': ('sdxl_base', 'sdxl_juggernaut'),
    'klein4': ('klein4', 'klein4_base'),
    'klein9': ('klein_base', 'klein_distilled', 'klein_kv'),
    'qwen21': ('qwen21',), 'qwen2511': ('qwen2511',),
    'flux3': ('flux3_base', 'flux3_distilled'),
}


def identify(header, source=None):
    """Recognize supported training metadata or distinctive adapter shapes."""
    tensors = {key: value.get('shape', []) for key, value in header.items()
               if key != '__metadata__' and isinstance(value, dict)}
    if not any(re.search(r'lora_|\.lora\.|hada_|lokr_|dora_', key, re.I) for key in tensors):
        return []
    metadata = header.get('__metadata__') or {}
    base = str(metadata.get('ss_base_model_version', '')).lower().replace('-', '_')
    family = None
    if base.startswith('sdxl'):
        family = 'sdxl'
    elif base in ('flux2_klein_4b', 'flux2_klein_base_4b', 'flux2_klein_4b_base'):
        family = 'klein4'
    elif base in ('flux2_klein_9b', 'flux2_klein_base_9b', 'flux2_klein_9b_base'):
        family = 'klein9'
    elif base in ('qwen_image_2', 'qwen_image_2.1', 'qwen_image_21'):
        family = 'qwen21'
    elif base in ('qwen_image_edit_2511', 'qwen_image_2511'):
        family = 'qwen2511'
    elif base in ('flux3', 'flux3_klein', 'flux3_klein_base'):
        family = 'flux3'

    shapes = set()
    qwen_blocks = family in ('qwen21', 'qwen2511') or any('.img_mlp.' in name for name in tensors)
    for key, shape in tensors.items():
        if len(shape) != 2:
            continue
        # FLUX.2's fused attention/MLP output distinguishes this from FLUX.1.
        if re.search(r'single_transformer_blocks\.\d+\.attn\.to_out\.lora_A(?:\.default)?\.weight$', key):
            if shape[1] in (12288, 16384):
                shapes.add('klein4' if shape[1] == 12288 else 'klein9')
        if re.search(r'(?:mode_blocks\.(?:image|image_cond)|txt_mode_blocks)\.\d+\.attn\.to_[qkv]\.lora_A(?:\.default)?\.weight$', key):
            if shape[1] == 3072:
                shapes.add('flux3')
        if qwen_blocks and re.search(r'(?:^|\.)transformer_blocks\.\d+\.attn\.(?:to_[qkv]|add_[qkv]_proj)\.lora_A(?:\.default)?\.weight$', key):
            if shape[1] in (3072, 4096):
                shapes.add('qwen21' if shape[1] == 4096 else 'qwen2511')
        if 'lora_unet_' in key and 'attn2_to_k.lora_down.weight' in key and shape[1] == 2048:
            shapes.add('sdxl')
    if family:
        shapes.add(family)
    if len(shapes) != 1:
        return []
    family = shapes.pop()
    profiles = list(FAMILY_PROFILES[family])
    # Preserve explicit base/distilled restrictions when provided by the author.
    if 'base' in base and family in ('klein4', 'klein9', 'flux3'):
        profiles = [{'klein4': 'klein4_base', 'klein9': 'klein_base', 'flux3': 'flux3_base'}[family]]
    if source:
        if source.get('family') != family or source.get('profile') not in profiles:
            return []
        if family != 'sdxl':
            profiles = [source['profile']]
    return profiles


@lru_cache(maxsize=512)
def _inspect(path, size, modified, changed):
    # Stat fields invalidate the cache after replacement; never cache tensors.
    from .civitai_native import read_header
    return identify(read_header(path))


def entry(path, relative_name, source=None):
    result = {'name': relative_name, 'profiles': []}
    if path.suffix.lower() != '.safetensors':
        return result
    try:
        stat = path.stat()
        profiles = _inspect(str(path), stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
        if source:
            family = next((key for key, members in FAMILY_PROFILES.items() if source.get('profile') in members), None)
            if source.get('family') != family or source.get('profile') not in profiles:
                profiles = []
            elif family != 'sdxl':
                profiles = [profile for profile in source.get('profiles', [source['profile']]) if profile in profiles]
        result['profiles'] = list(profiles)
    except (OSError, ValueError, TypeError, AttributeError):
        pass
    return result


def catalog(root, installed=()):
    root = Path(root).resolve()
    sources = {item['relative_path']: item for item in installed
               if item.get('kind') == 'LORA' and item.get('relative_path')}
    entries = []
    scanned = 0
    for path in islice(root.rglob('*'), 10001):
        scanned += 1
        if scanned > 10000:
            break
        if path.suffix.lower() not in ('.safetensors', '.ckpt', '.pt') or not path.is_file():
            continue
        if not path.resolve().is_relative_to(root):
            continue
        name = path.relative_to(root).as_posix()
        entries.append(entry(path, name, sources.get(name)))
    entries.sort(key=lambda item: item['name'].casefold())
    return {'folders': [str(root)], 'files': [item['name'] for item in entries],
            'items': entries, 'unidentified': sum(not item['profiles'] for item in entries),
            'truncated': scanned > 10000}
