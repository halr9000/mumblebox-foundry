"""Local browser adapters; all remote requests and credentials stay server-side."""
import asyncio
import json
from urllib.parse import urlsplit

from aiohttp import web

from . import hf_auth, models
from .store import ProjectConflict
from .single_image_routes import project_public
from .civitai_auth import CivitaiAuth
from .civitai_catalog import CatalogClient, CivitaiError, PROFILE_BASES, normalize_model, positive_id
from .civitai_downloads import Downloader
from .civitai_native import validate_weights

PREFIX = '/asset-workshop/v2/civitai'
AUTH = CivitaiAuth(hf_auth.vault, hf_auth.SERVICE, models.MODEL_ROOT / '.mumblebox-civitai' / 'connection.json')
CLIENT = CatalogClient(AUTH.token)
DOWNLOADS = Downloader(models.MODEL_ROOT, CLIENT.resolve, AUTH.token, models.DOWNLOAD_LOCK, validate=validate_weights)


def boolean(value):
    if value not in ('true', 'false', None):
        raise CivitaiError('Choose on or off for mature-content filtering.')
    return value == 'true'


async def body(request):
    if request.content_length and request.content_length > 16384:
        raise CivitaiError('This request is too large.')
    raw = await request.content.read(16385)
    if len(raw) > 16384:
        raise CivitaiError('This request is too large.')
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise CivitaiError('Send one browser operation.')
    return data


def register(routes):
    def endpoint(function):
        async def wrapped(request):
            # Browser clients on unrelated sites must not operate local credentials/downloads.
            origin = request.headers.get('Origin')
            if origin and urlsplit(origin).netloc != request.host:
                return web.json_response({'error': 'Use the existing Comfy interface for this operation.'}, status=403)
            try:
                return web.json_response(await function(request), headers={'Cache-Control': 'no-store'})
            except CivitaiError as error:
                return web.json_response(error.public(), status=error.status, headers={'Cache-Control': 'no-store'})
            except ProjectConflict as error:
                return web.json_response({'error': str(error), 'kind': 'conflict'}, status=409, headers={'Cache-Control': 'no-store'})
            except (ValueError, KeyError, TypeError):
                return web.json_response({'error': 'The Civitai request was incomplete or invalid.', 'kind': 'request'}, status=400)
            except Exception:
                return web.json_response({'error': 'The Civitai operation could not finish. Check storage and retry.', 'kind': 'service'}, status=500)
        return wrapped

    @routes.get(PREFIX + '/status')
    @endpoint
    async def status(request):
        return {'connection': await asyncio.to_thread(AUTH.status), 'download': DOWNLOADS.status()}

    @routes.get(PREFIX + '/search')
    @endpoint
    async def search(request):
        q = request.query
        return await asyncio.to_thread(CLIENT.search, q.get('profile', 'klein4'), q.get('kind', 'LORA'),
            q.get('query', ''), q.get('sort', 'Highest Rated'), q.get('period', 'AllTime'),
            q.get('cursor', ''), boolean(q.get('nsfw')))

    @routes.get(PREFIX + '/model/{model_id}')
    @endpoint
    async def detail(request):
        profile = request.query.get('profile', 'klein4')
        if profile not in PROFILE_BASES:
            raise CivitaiError('Choose a supported image model.')
        data = await asyncio.to_thread(CLIENT.model, positive_id(request.match_info['model_id']))
        if data.get('type') not in ('LORA', 'Checkpoint'):
            raise CivitaiError('Only LoRAs and supported checkpoints are available in this browser.')
        return normalize_model(data, profile, boolean(request.query.get('nsfw')))

    @routes.post(PREFIX + '/resolve-url')
    @endpoint
    async def resolve_url(request):
        data = await body(request)
        return await asyncio.to_thread(CLIENT.from_url, data.get('url'), data.get('profile'), data.get('nsfw') is True)

    @routes.post(PREFIX + '/connection')
    @endpoint
    async def connection(request):
        data = await body(request)
        action = data.get('action')
        if action == 'connect':
            return await asyncio.to_thread(AUTH.connect, data.get('token'))
        if action == 'test':
            return await asyncio.to_thread(AUTH.test)
        if action == 'disconnect':
            return await asyncio.to_thread(AUTH.disconnect)
        if action == 'configure':
            return await asyncio.to_thread(AUTH.configure, data.get('client_id'))
        if action == 'begin':
            return await asyncio.to_thread(AUTH.begin)
        if action == 'poll':
            return await asyncio.to_thread(AUTH.poll)
        if action == 'cancel':
            return await asyncio.to_thread(AUTH.cancel_authorization)
        raise CivitaiError('Choose a connection operation.')

    @routes.get(PREFIX + '/installed')
    @endpoint
    async def installed(request):
        return {'items': await asyncio.to_thread(DOWNLOADS.installed)}

    @routes.post(PREFIX + '/download')
    @endpoint
    async def download(request):
        data = await body(request)
        for key in ('model_id', 'version_id', 'file_id'):
            positive_id(data.get(key))
        if data.get('profile') not in PROFILE_BASES or data.get('kind') not in ('LORA', 'Checkpoint'):
            raise CivitaiError('Choose a supported model and resource type.')
        return DOWNLOADS.start(data)

    @routes.post(PREFIX + '/download/control')
    @endpoint
    async def control(request):
        return DOWNLOADS.control((await body(request)).get('action'))

    @routes.post(PREFIX + '/apply')
    @endpoint
    async def apply(request):
        data = await body(request)
        # Verify current project ownership/revision through the existing store owner.
        from .runtime import store
        library = store()
        project = library.load(data['project_id'])
        item = await asyncio.to_thread(DOWNLOADS.verify_selected, data['file_id'], project['profile'], data['kind'])
        if item['kind'] == 'LORA':
            values = [v for v in project['loras'] if v['name'] != item['relative_path']]
            values.append({'name': item['relative_path'], 'profile': project['profile'], 'enabled': True,
                           'strength': 1, 'strength_clip': 1, 'trigger': ', '.join(item.get('triggers', []))})
            changes = {'loras': values}
        else:
            changes = {'settings': {'image_checkpoint': str(item['file_id'])}}
        return project_public(library.update_project(project['id'], int(data['expected_revision']), changes))
