"""Owned Civitai transfers: streamed bytes, range resume and verified publication."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import threading
import time
import uuid
from urllib.parse import urljoin, urlsplit

import requests

from .civitai_catalog import CivitaiError, RESOURCE_HOSTS, filename, http_error

INDEX_LOCK = threading.RLock()


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def file_hash(path):
    result = hashlib.sha256()
    with path.open('rb') as handle:
        while data := handle.read(4 * 1024**2):
            result.update(data)
    return result.hexdigest()


def installed_records(root):
    """One installed-information store for Civitai and included model weights."""
    root = Path(root).resolve()
    path = (root / '.mumblebox-civitai' / 'installed.json').resolve()
    if not path.is_relative_to(root):
        raise CivitaiError('The model information store points outside this installation.', 'path')
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, list) or len(data) > 1000:
        raise CivitaiError('The installed model catalog is invalid or exceeds 1,000 entries.', 'storage')
    result = []
    for item in data:
        target = (root / item['category'] / item['relative_path']).resolve()
        if not target.is_relative_to(root):
            raise CivitaiError('The model information points outside this installation.', 'path')
        if target.is_file():
            result.append(item)
    return result


def publish_model_info(root, target, item):
    """Preserve the existing index/sidecar format, with explicit source ownership."""
    root, target = Path(root).resolve(), Path(target).resolve()
    category = (root / item['category']).resolve()
    index = (root / '.mumblebox-civitai' / 'installed.json').resolve()
    sidecar = target.with_suffix('.civitai.json').resolve()
    if (item['category'] not in ('loras', 'checkpoints', 'diffusion_models')
            or not target.is_relative_to(category) or not category.is_relative_to(root)
            or not index.is_relative_to(root) or not sidecar.is_relative_to(root)):
        raise CivitaiError('The model information destination is outside this installation.', 'path')
    with INDEX_LOCK:
        records = installed_records(root)
        relative = target.relative_to(category).as_posix()
        previous = next((r for r in records if r['category'] == item['category'] and r['relative_path'] == relative), {})
        records = [r for r in records if not (r['category'] == item['category'] and r['relative_path'] == relative)
                   and str(r['file_id']) != str(item['file_id'])]
        if len(records) >= 1000:
            raise CivitaiError('The installed model catalog has reached 1,000 entries.', 'storage')
        record = {**previous, **{k: v for k, v in item.items() if k != 'download_url'},
                  'relative_path': relative, 'installed_at': previous.get('installed_at', time.time()),
                  'size_bytes': target.stat().st_size}
        record.setdefault('source_provider', 'civitai')
        atomic_json(sidecar, record)
        atomic_json(index, records + [record])
        return record


def register_included_lora_info(root, names=None):
    """Explicit refresh/install operation; matching hashes prevent guessed identities."""
    root = Path(root).resolve()
    directory = Path(__file__).parent
    guides = json.loads((directory / 'lora_guides.json').read_text(encoding='utf-8'))['guides']
    pinned = json.loads((directory / 'models.lock.json').read_text(encoding='utf-8'))['models']
    existing = installed_records(root)
    registered, skipped = [], []
    for guide in guides:
        model = pinned.get(guide.get('model_key'), {})
        name = guide.get('name') or model.get('name')
        if names is not None and name not in names:
            continue
        path = (root / 'loras' / name).resolve()
        if not path.is_relative_to(root / 'loras') or not path.is_file():
            continue
        sha = guide.get('sha256') or model['sha256']
        stat = path.stat()
        fingerprint = [stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns]
        previous = next((item for item in existing if item['category'] == 'loras' and item['relative_path'] == name), {})
        if (previous.get('sha256') == sha and previous.get('guide_revision') == guide['guide_revision']
                and previous.get('verified_file_stat') == fingerprint):
            continue
        if file_hash(path) != sha:
            skipped.append(name)
            continue
        repo = guide.get('repo') or model['repo']
        revision = guide.get('revision') or model['revision']
        item = {**guide, 'source_provider': 'huggingface', 'model_id': repo,
                'version_id': revision, 'version_name': guide.get('version_name', revision[:8]),
                'file_id': 'hf:' + sha, 'kind': 'LORA', 'category': 'loras', 'name': name,
                'sha256': sha, 'verified_file_stat': fingerprint, 'source_url': 'https://huggingface.co/' + repo,
                'license_url': guide.get('license_url') or model.get('license_url') or 'https://huggingface.co/' + repo,
                'profile': guide['profiles'][0], 'notes': guide['description'], 'permissions': {}}
        publish_model_info(root, path, item)
        registered.append(name)
    return {'registered': registered, 'unrecognized': skipped}


class TransferStopped(Exception):
    pass


class Downloader:
    def __init__(self, root, resolve, token, gate, transport=None, validate=None):
        self.root = Path(root).resolve()
        self.cache = self.root / '.mumblebox-civitai'
        self.resolve, self.token, self.gate = resolve, token, gate
        self.transport = transport or requests
        self.validate = validate
        self.lock = threading.RLock()
        self.stop_event = threading.Event()
        self.worker = None
        self.record = {'status': 'idle', 'bytes': 0, 'total': 0}
        state = self.cache / 'transfer.json'
        if state.is_file():
            try:
                self.record = json.loads(state.read_text(encoding='utf-8'))
                if self.record.get('status') in ('running', 'pausing', 'cancelling'):
                    self.record.update(status='paused', phase='Interrupted; retry to resume verified bytes.')
            except (OSError, ValueError):
                self.record = {'status': 'idle', 'bytes': 0, 'total': 0}

    def contained(self, path):
        result = Path(path).resolve()
        if not result.is_relative_to(self.root):
            raise CivitaiError('The destination points outside this Comfy installation.', 'path')
        return result

    def partial_path(self, item):
        return self.contained(self.cache / (item['sha256'] + '.part'))

    def target(self, item):
        category = item['category']
        if category not in ('loras', 'checkpoints', 'diffusion_models') or not re.fullmatch(r'[a-z0-9]+', item['family']):
            raise CivitaiError('Unsupported installation folder.')
        stem = Path(filename(item['name'])).stem[:100]
        name = f'{stem}-v{int(item["version_id"])}-f{int(item["file_id"])}.safetensors'
        return self.contained(self.root / category / 'Mumblebox' / item['family'] / name)

    def status(self):
        with self.lock:
            return json.loads(json.dumps(self.record))

    def update(self, persist=False, **values):
        with self.lock:
            self.record.update(values)
            if persist:
                atomic_json(self.contained(self.cache / 'transfer.json'), self.record)

    def installed(self):
        return installed_records(self.root)

    def selected(self, file_id, profile=None, kind=None):
        item = next((v for v in self.installed() if str(v['file_id']) == str(file_id)), None)
        if not item or kind and item['kind'] != kind:
            raise CivitaiError('Choose an installed Civitai resource. It may have been moved or removed.')
        if profile and profile not in item.get('profiles', [item['profile']]) and not (item['family'] == 'sdxl' and profile in ('sdxl_base', 'sdxl_juggernaut')):
            raise CivitaiError('The installed resource belongs to another model variant.', 'compatibility')
        return item

    def verify_selected(self, file_id, profile, kind):
        item = self.selected(file_id, profile, kind)
        path = self.contained(self.root / item['category'] / item['relative_path'])
        if file_hash(path) != item['sha256']:
            raise CivitaiError('The installed Civitai weights changed after download. They have not been overwritten; restore or choose verified weights.', 'integrity')
        return item

    def start(self, selection):
        selection = {key: selection[key] for key in ('model_id', 'version_id', 'file_id', 'profile', 'kind')}
        with self.lock:
            if self.worker and self.worker.is_alive():
                if self.record.get('selection') == selection:
                    return self.status()
                raise CivitaiError('A Civitai download is already running. Pause or finish it first.', 'busy', 409)
            if not self.gate.acquire(blocking=False):
                raise CivitaiError('Another model download is running. Wait for it or pause it first.', 'busy', 409)
            self.stop_event.clear()
            self.record = {'status': 'running', 'phase': 'Checking version and access', 'bytes': 0, 'total': 0,
                           'selection': selection, 'started_at': time.time(), 'error': None}
            self.worker = threading.Thread(target=self.run, args=(selection,), daemon=True, name='mumblebox-civitai-download')
            try:
                self.worker.start()
            except Exception:
                self.gate.release()
                raise
            return self.status()

    def control(self, action):
        if action == 'retry':
            if not self.record.get('selection'):
                raise CivitaiError('Choose a file before downloading.')
            return self.start(self.record['selection'])
        if action not in ('pause', 'cancel'):
            raise CivitaiError('Choose Pause, Cancel or Retry.')
        with self.lock:
            if self.record.get('status') == 'running':
                self.record['status'] = 'pausing' if action == 'pause' else 'cancelling'
                self.stop_event.set()
            elif action == 'cancel' and self.record.get('status') in ('paused', 'failed'):
                item = self.record.get('item')
                if item:
                    self.partial_path(item).unlink(missing_ok=True)
                self.update(True, status='cancelled', phase='Cancelled', bytes=0)
            return self.status()

    def open_response(self, url, offset):
        source_host = urlsplit(url).hostname
        token = self.token()
        for _ in range(6):
            parsed = urlsplit(url)
            host = parsed.hostname or ''
            allowed = host in RESOURCE_HOSTS or host.endswith(('.civitai.com', '.civitai.red', '.r2.cloudflarestorage.com'))
            if parsed.scheme != 'https' or parsed.username or parsed.password or parsed.port or not allowed:
                raise CivitaiError('Civitai returned an unsupported download destination.', 'service', 502)
            headers = {'Accept': 'application/octet-stream', 'Accept-Encoding': 'identity',
                       'User-Agent': 'Mumblebox/1.0 (local asset download)'}
            if token and host == source_host and host in RESOURCE_HOSTS:
                headers['Authorization'] = 'Bearer ' + token
            if offset:
                headers['Range'] = f'bytes={offset}-'
            response = self.transport.get(url, headers=headers, timeout=(10, 30), stream=True, allow_redirects=False)
            if response.status_code in (301, 302, 303, 307, 308):
                location = response.headers.get('Location', '')
                response.close()
                url = urljoin(url, location)
                continue
            if response.status_code not in (200, 206):
                error = http_error(response.status_code)
                response.close()
                raise error
            if 'text/' in response.headers.get('Content-Type', '').lower() or 'json' in response.headers.get('Content-Type', '').lower():
                response.close()
                raise CivitaiError('Civitai returned a message instead of model weights. Check resource access before retrying.', 'access', 403)
            return response
        raise CivitaiError('Civitai returned too many download redirects. Retry later.', 'service', 502)

    def run(self, selection):
        response = None
        item = None
        try:
            item = self.resolve(**selection)
            target = self.target(item)
            part = self.partial_path(item)
            target.parent.mkdir(parents=True, exist_ok=True)
            part.parent.mkdir(parents=True, exist_ok=True)
            # Never persist a signed/download URL or an authentication token.
            safe_item = {key: value for key, value in item.items() if key != 'download_url'}
            self.update(True, item=safe_item, name=item['model_name'], total=item['size_bytes'],
                        destination=str(target), phase='Connecting')
            if target.exists():
                if file_hash(target) != item['sha256']:
                    raise CivitaiError('A different file already exists at this destination. It was preserved.', 'collision')
                if self.validate:
                    self.validate(target, item)
                self.publish_index(target, safe_item)
                self.update(True, status='completed', phase='Existing local weights verified; ready to use', bytes=target.stat().st_size, total=target.stat().st_size)
                return
            offset = part.stat().st_size if part.exists() else 0
            if offset and offset >= max(1, item['size_bytes'] - 1024) and file_hash(part) == item['sha256']:
                self.finish_partial(part, target, item, safe_item)
                return
            if shutil.disk_usage(self.root).free < max(0, item['size_bytes'] - offset) + 512 * 1024**2:
                raise CivitaiError('There is not enough free disk space for this download.', 'storage')
            response = self.open_response(item['download_url'], offset)
            resumed = offset > 0 and response.status_code == 206
            if response.status_code == 206:
                match = re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)', response.headers.get('Content-Range', ''))
                if not match or int(match[1]) != offset or int(match[2]) < offset:
                    raise CivitaiError('The server returned an incorrect resume range. Cancel this partial download and retry.', 'integrity')
                total = int(match[3])
            else:
                offset = 0
                length = response.headers.get('Content-Length', '')
                total = int(length) if str(length).isdigit() else 0
            if total and total > item['size_bytes'] + 1024**2:
                raise CivitaiError('The response size differs from the selected file. No weights were installed.', 'integrity')
            self.update(True, phase='Downloading', bytes=offset, total=total)
            limit = item['size_bytes'] + 1024**2 if item['size_bytes'] else 64 * 1024**3
            checkpoint = time.monotonic()
            with part.open('ab' if resumed else 'wb') as handle:
                for data in response.iter_content(1024**2):
                    if self.stop_event.is_set():
                        raise TransferStopped()
                    if not data:
                        continue
                    handle.write(data)
                    offset += len(data)
                    if offset > limit or total and offset > total:
                        raise CivitaiError('The response exceeded the selected file size. No weights were installed.', 'integrity')
                    self.update(bytes=offset)
                    if time.monotonic() - checkpoint > 1:
                        self.update(True)
                        checkpoint = time.monotonic()
                handle.flush()
                os.fsync(handle.fileno())
            if self.stop_event.is_set():
                raise TransferStopped()
            if total and offset != total:
                raise CivitaiError('The transfer ended early. Retry to resume the verified file identity.', 'network', 502)
            self.finish_partial(part, target, item, safe_item)
        except TransferStopped:
            cancelled = self.record.get('status') == 'cancelling'
            if cancelled and item:
                self.partial_path(item).unlink(missing_ok=True)
            self.update(True, status='cancelled' if cancelled else 'paused', phase='Cancelled' if cancelled else 'Paused; downloaded bytes retained')
        except CivitaiError as error:
            self.update(True, status='failed', phase='Download needs attention', error=error.public())
        except Exception:
            self.update(True, status='failed', phase='Download interrupted',
                        error=CivitaiError('The download could not finish. Check network access and free disk space, then retry.', 'network', 502).public())
        finally:
            if response:
                response.close()
            self.gate.release()

    def publish_index(self, target, item):
        publish_model_info(self.root, target, item)

    def finish_partial(self, part, target, item, safe_item):
        self.update(True, phase='Verifying SHA-256')
        if file_hash(part) != item['sha256']:
            part.unlink(missing_ok=True)
            raise CivitaiError('The file failed SHA-256 verification. It was not installed; retry to download a clean copy.', 'integrity')
        self.update(True, phase='Checking weight format and architecture')
        if self.validate:
            try:
                self.validate(part, item)
            except CivitaiError:
                part.unlink(missing_ok=True)
                raise
        with self.lock:
            if self.stop_event.is_set():
                raise TransferStopped()
            # Exclusive creation protects an existing file on every platform.
            try:
                os.link(part, target)
            except FileExistsError:
                raise CivitaiError('The destination appeared during download. It has not been replaced.', 'collision') from None
            size = part.stat().st_size
            part.unlink()
            self.publish_index(target, safe_item)
            self.update(True, status='completed', phase='Ready to use', bytes=size, total=size, error=None)
