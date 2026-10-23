"""Civitai discovery and resource identity; no model execution or credential storage."""
import html
import json
import re
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

import requests

API = 'https://civitai.com/api/v1'
PROFILE_BASES = {
    'sdxl_base': ('SDXL 1.0',), 'sdxl_juggernaut': ('SDXL 1.0',),
    'klein4': ('Flux.2 Klein 4B',), 'klein4_base': ('Flux.2 Klein 4B-base',),
    'klein_base': ('Flux.2 Klein 9B-base',), 'klein_distilled': ('Flux.2 Klein 9B',),
    'klein_kv': ('Flux.2 Klein 9B',),
    'qwen21': ('Qwen 2.1', 'Qwen 2'),
    'qwen2511': ('Qwen', 'Qwen Image Edit 2511'),
    'flux3_base': ('Flux.3 Klein-base',), 'flux3_distilled': ('Flux.3 Klein',),
}
FAMILIES = {
    'sdxl_base': 'sdxl', 'sdxl_juggernaut': 'sdxl', 'klein4': 'klein4',
    'klein4_base': 'klein4', 'klein_base': 'klein9', 'klein_distilled': 'klein9',
    'klein_kv': 'klein9', 'qwen21': 'qwen21', 'qwen2511': 'qwen2511',
    'flux3_base': 'flux3', 'flux3_distilled': 'flux3',
}
SORTS = ('Highest Rated', 'Most Downloaded', 'Most Liked', 'Newest')
PERIODS = ('AllTime', 'Year', 'Month', 'Week', 'Day')
RESOURCE_HOSTS = {'civitai.com', 'www.civitai.com', 'civitai.red', 'www.civitai.red'}


class CivitaiError(ValueError):
    def __init__(self, message, kind='request', status=400, retry_after=None):
        super().__init__(message)
        self.message, self.kind, self.status, self.retry_after = message, kind, status, retry_after

    def public(self):
        return {'error': self.message, 'kind': self.kind, 'http_status': self.status,
                'retry_after': self.retry_after,
                'settings': 'civitai' if self.kind == 'authentication' else None}


def http_error(status, retry_after=None):
    messages = {
        401: ('authentication', 'Civitai could not verify this connection. Open Civitai Settings to connect or replace the key.'),
        403: ('access', 'Civitai denied access to this resource. Check its access conditions on Civitai; a valid key may still lack access.'),
        404: ('missing', 'This Civitai resource or file is unavailable. Open its source page or choose another version.'),
        410: ('missing', 'This resource has been archived and is no longer downloadable.'),
        429: ('limit', 'Civitai has temporarily limited requests. Wait before retrying; changing your key is not required.'),
    }
    kind, message = messages.get(status, ('service', 'Civitai is temporarily unavailable. Your saved connection has not changed.'))
    return CivitaiError(message, kind, status if status in messages else 502, retry_after)


def plain_text(value, limit=6000):
    text = str(value or '')[:100000]
    text = re.sub(r'<(script|style)\b[^>]*>.*?</\1>', '', text, flags=re.I | re.S)
    text = re.sub(r'</?(?:p|div|br|li|ul|ol|h[1-6])\b[^>]*>', '\n', text, flags=re.I)
    text = html.unescape(re.sub(r'<[^>]*>', '', text))
    return '\n'.join(line.strip() for line in text.splitlines() if line.strip())[:limit]


def positive_id(value):
    if isinstance(value, bool) or not str(value).isdigit() or not 0 < int(value) <= 2147483647:
        raise CivitaiError('Choose a valid Civitai resource, version and file.')
    return int(value)


def parse_resource_url(value):
    try:
        url = urlsplit(str(value).strip())
        if url.scheme != 'https' or url.hostname not in RESOURCE_HOSTS or url.username or url.password or url.port:
            raise ValueError()
        version = re.fullmatch(r'/api/download/models/(\d+)/?', url.path)
        model = re.match(r'^/models/(\d+)(?:/|$)', url.path)
        if version:
            return {'version_id': positive_id(version[1])}
        if model:
            result = {'model_id': positive_id(model[1])}
            selected = parse_qs(url.query).get('modelVersionId', [])
            if selected:
                result['version_id'] = positive_id(selected[0])
            return result
    except (ValueError, TypeError):
        pass
    raise CivitaiError('Paste an HTTPS Civitai model or version link from civitai.com or civitai.red.')


def public_url(value):
    try:
        url = urlsplit(str(value or ''))
        if url.scheme != 'https' or url.username or url.password or url.port:
            return ''
        host = (url.hostname or '').lower()
        if host not in RESOURCE_HOSTS and not host.endswith(('.civitai.com', '.civitai.red')):
            return ''
        query = {key: vals[0] for key, vals in parse_qs(url.query).items()
                 if key in ('fileId', 'modelVersionId', 'type', 'format', 'size', 'fp', 'quantType')}
        return urlunsplit(('https', url.netloc, url.path, urlencode(query), ''))
    except ValueError:
        return ''


def compatible(profile, base, version_name=''):
    if profile not in PROFILE_BASES or base not in PROFILE_BASES[profile]:
        return False
    # Civitai's generic Qwen label covers incompatible image/edit generations.
    if profile == 'qwen2511' and base == 'Qwen':
        return bool(re.search(r'\b2511\b', version_name))
    return True


def filename(value):
    name = str(value or '')
    if (not name or len(name) > 180 or re.search(r'[<>:"/\\|?*\x00-\x1f]', name)
            or name.endswith((' ', '.')) or name in ('.', '..')
            or re.match(r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)', name, re.I)):
        raise CivitaiError('Civitai returned a filename that cannot be installed safely.')
    return name


def resolve_file(model, version_id, file_id, profile, kind):
    if profile not in PROFILE_BASES or kind not in ('LORA', 'Checkpoint'):
        raise CivitaiError('Choose a supported image model and LoRAs or checkpoints.')
    if str(model.get('type', '')).casefold() != kind.casefold():
        raise CivitaiError(f'This resource is not a {kind}. Choose the matching resource type.')
    version_id, file_id = positive_id(version_id), positive_id(file_id)
    version = next((v for v in model.get('modelVersions', []) if v.get('id') == version_id), None)
    if not version:
        raise CivitaiError('This version does not belong to the selected resource.')
    if not compatible(profile, version.get('baseModel'), version.get('name', '')):
        raise CivitaiError('This version is not confirmed compatible with the selected model variant. Choose matching weights.', 'compatibility')
    file = next((f for f in version.get('files', []) if f.get('id') == file_id), None)
    if not file:
        raise CivitaiError('This file does not belong to the selected version.')
    name = filename(file.get('name'))
    if not name.lower().endswith('.safetensors') or file.get('metadata', {}).get('format') != 'SafeTensor':
        raise CivitaiError('Choose an individual SafeTensor weight file. Archives, pickle files and other formats are not supported.', 'format')
    if file.get('type') not in ('Model', 'Pruned Model'):
        raise CivitaiError('Choose the LoRA or checkpoint weights, not an accompanying component file.', 'format')
    sha = str(file.get('hashes', {}).get('SHA256', '')).lower()
    if not re.fullmatch('[a-f0-9]{64}', sha):
        raise CivitaiError('Civitai has not supplied a SHA-256 for this file. It cannot be verified yet.', 'integrity')
    url = public_url(file.get('downloadUrl'))
    if not url or urlsplit(url).hostname not in RESOURCE_HOSTS:
        raise CivitaiError('Civitai did not supply a supported file-download endpoint.')
    # Preserve exact file selection rather than allowing version defaults to choose.
    parts = urlsplit(url)
    query = parse_qs(parts.query)
    query['fileId'] = [str(file_id)]
    url = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query, doseq=True), ''))
    size = file.get('sizeKB')
    size = max(0, int(float(size) * 1024)) if isinstance(size, (int, float)) else 0
    family = FAMILIES[profile]
    return {'model_id': positive_id(model.get('id')), 'version_id': version_id, 'file_id': file_id,
            'profile': profile, 'family': family, 'kind': kind,
            'category': 'loras' if kind == 'LORA' else 'checkpoints' if family == 'sdxl' else 'diffusion_models',
            'name': name, 'model_name': plain_text(model.get('name'), 180),
            'version_name': plain_text(version.get('name'), 180), 'base_model': version.get('baseModel'),
            'size_bytes': size, 'sha256': sha, 'download_url': url,
            'source_url': f'https://civitai.com/models/{model["id"]}?modelVersionId={version_id}',
            'triggers': [str(w)[:200] for w in version.get('trainedWords', [])[:20] if isinstance(w, str)],
            'notes': plain_text(version.get('description') or model.get('description')),
            'permissions': {k: model.get(k) for k in ('allowNoCredit', 'allowCommercialUse', 'allowDerivatives', 'allowDifferentLicense')}}


def normalize_model(model, profile, nsfw=False):
    result = {'id': model['id'], 'name': plain_text(model.get('name'), 180), 'type': model.get('type'),
              'creator': plain_text((model.get('creator') or {}).get('username'), 100),
              'description': plain_text(model.get('description')), 'versions': [],
              'source_url': f'https://civitai.com/models/{model["id"]}',
              'permissions': {k: model.get(k) for k in ('allowNoCredit', 'allowCommercialUse', 'allowDerivatives', 'allowDifferentLicense')}}
    for version in model.get('modelVersions', [])[:50]:
        images = []
        for img in version.get('images', [])[:12]:
            rating = img.get('nsfwLevel', 0)
            mature = (isinstance(rating, (int, float)) and rating >= 4) or img.get('nsfw') not in (None, False, 'None')
            url = public_url(img.get('url'))
            if url and (nsfw or not mature) and img.get('type') != 'video':
                images.append({'url': url, 'mature': mature})
            if len(images) == 4:
                break
        entry = {'id': version['id'], 'name': plain_text(version.get('name'), 180),
                 'base_model': version.get('baseModel'), 'images': images,
                 'compatible': compatible(profile, version.get('baseModel'), version.get('name', '')),
                 'triggers': version.get('trainedWords', [])[:20],
                 'notes': plain_text(version.get('description')), 'files': []}
        for file in version.get('files', [])[:30]:
            item = {'id': file.get('id'), 'name': plain_text(file.get('name'), 180),
                    'size_bytes': int(float(file.get('sizeKB') or 0) * 1024),
                    'format': file.get('metadata', {}).get('format', ''), 'eligible': False}
            try:
                resolve_file(model, version['id'], file['id'], profile, model.get('type'))
                item['eligible'] = True
            except CivitaiError as error:
                item['reason'] = error.message
            entry['files'].append(item)
        result['versions'].append(entry)
    return result


class CatalogClient:
    def __init__(self, token=None, transport=None):
        self.token = token
        self.transport = transport or requests

    def get(self, path, params=None):
        if not re.fullmatch(r'/(?:models(?:/\d+)?|model-versions/\d+|me)', path):
            raise CivitaiError('Unsupported Civitai API operation.')
        headers = {'Accept': 'application/json', 'User-Agent': 'Mumblebox/1.0 (local asset browser)'}
        token = self.token() if callable(self.token) else self.token
        if token:
            headers['Authorization'] = 'Bearer ' + token
        try:
            with self.transport.get(API + path, params=params, headers=headers, timeout=(10, 25), stream=True,
                                    allow_redirects=False) as response:
                if response.status_code != 200:
                    retry = response.headers.get('Retry-After', '')
                    raise http_error(response.status_code, min(int(retry), 3600) if retry.isdigit() else None)
                data = bytearray()
                for block in response.iter_content(65536):
                    data.extend(block)
                    if len(data) > 8 * 1024**2:
                        raise CivitaiError('Civitai returned too much metadata. Narrow the search.', 'service', 502)
                return json.loads(data)
        except CivitaiError:
            raise
        except (requests.RequestException, ValueError, UnicodeError):
            raise CivitaiError('Civitai could not complete this request. Check the connection and retry.', 'service', 502) from None

    def search(self, profile, kind='LORA', query='', sort='Highest Rated', period='AllTime', cursor='', nsfw=False):
        if profile not in PROFILE_BASES or kind not in ('LORA', 'Checkpoint') or sort not in SORTS or period not in PERIODS:
            raise CivitaiError('Choose a supported model, resource type and sort.')
        params = {'types': kind, 'baseModels': list(PROFILE_BASES[profile]), 'limit': 12,
                  'sort': sort, 'period': period, 'nsfw': 'true' if nsfw else 'false'}
        if query:
            params['query'] = str(query)[:200]
        if cursor:
            params['cursor'] = str(cursor)[:512]
        data = self.get('/models', params)
        return {'items': [normalize_model(m, profile, nsfw) for m in data.get('items', [])[:12]
                          if str(m.get('type', '')).casefold() == kind.casefold()],
                'next_cursor': data.get('metadata', {}).get('nextCursor')}

    def model(self, model_id):
        return self.get('/models/' + str(positive_id(model_id)))

    def resolve(self, model_id, version_id, file_id, profile, kind):
        return resolve_file(self.model(model_id), version_id, file_id, profile, kind)

    def from_url(self, url, profile, nsfw=False):
        ids = parse_resource_url(url)
        if 'model_id' not in ids:
            ids['model_id'] = self.get('/model-versions/' + str(ids['version_id']))['modelId']
        data = self.model(ids['model_id'])
        if data.get('type') not in ('LORA', 'Checkpoint'):
            raise CivitaiError('This browser supports LoRAs and compatible checkpoints only.')
        result = normalize_model(data, profile, nsfw)
        result['selected_version'] = ids.get('version_id')
        return result
