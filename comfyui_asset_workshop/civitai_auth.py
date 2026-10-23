"""Installation-private Civitai credentials and public-client authorization."""
import json
import os
import re
import threading
import time
import uuid

import requests

from .civitai_catalog import CatalogClient, CivitaiError, http_error

AUTH = 'https://auth.civitai.com/api/auth/oauth'
SCOPES = 1 | 4 | 32  # Profile identity, browse/download weights, preview media.


class CivitaiAuth:
    def __init__(self, vault, service, config_path, identify=None, transport=None):
        self.vault, self.service, self.config_path = vault, service, config_path
        self.identify = identify or (lambda value: CatalogClient(value).get('/me'))
        self.transport = transport or requests
        self.lock = threading.RLock()
        self.credential = None
        self.error = ''
        self.pending = None

    def _load(self):
        if self.credential is not None:
            return self.credential
        try:
            value = self.vault().get_password(self.service, 'civitai')
            self.credential = json.loads(value) if value else {}
            if not isinstance(self.credential, dict):
                raise ValueError()
            self.error = ''
            return self.credential
        except Exception:
            self.error = 'The operating-system credential vault could not be read. Unlock it before connecting Civitai.'
            return {}

    def _save(self, record):
        try:
            self.vault().set_password(self.service, 'civitai', json.dumps(record))
        except Exception:
            raise CivitaiError('The connection was verified but could not be saved securely. Unlock the operating-system credential vault.', 'storage') from None
        self.credential, self.error = record, ''

    def client_id(self):
        if not self.config_path.is_file():
            return ''
        try:
            return str(json.loads(self.config_path.read_text(encoding='utf-8')).get('client_id', ''))
        except (OSError, ValueError):
            raise CivitaiError('The Civitai app configuration could not be read. Save the public app identifier again.', 'configuration') from None

    def configure(self, value):
        if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,200}', value):
            raise CivitaiError('Enter the public Client ID from the Mumblebox app registration. Do not enter a client secret.')
        with self.lock:
            previous = self.client_id()
            if previous and previous != value and self._load().get('method') == 'oauth':
                raise CivitaiError('Disconnect the current connected app before changing its public identifier.')
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.config_path.with_name(self.config_path.name + '.' + uuid.uuid4().hex + '.tmp')
            try:
                temporary.write_text(json.dumps({'client_id': value}), encoding='utf-8')
                os.replace(temporary, self.config_path)
            finally:
                temporary.unlink(missing_ok=True)
        return self.status()

    def status(self):
        with self.lock:
            credential = self._load()
            return {'connected': bool(credential.get('token')), 'account': credential.get('account', ''),
                    'method': credential.get('method', ''), 'client_id': self.client_id(),
                    'storage': 'Operating system credential vault', 'error': self.error,
                    'oauth': self.pending_status()}

    def connect(self, value):
        value = value.strip() if isinstance(value, str) else ''
        if not re.fullmatch(r'[A-Za-z0-9_.-]{10,512}', value):
            raise CivitaiError('Paste a valid Civitai API key. The existing connection has not changed.', 'authentication', 401)
        identity = self.identify(value)
        account = identity.get('username') or identity.get('name') or str(identity.get('id') or '')
        if not account:
            raise CivitaiError('Civitai did not return a verified account identity. The key was not saved.', 'authentication', 401)
        with self.lock:
            self._save({'token': value, 'account': str(account)[:100], 'method': 'api_key'})
        return self.status()

    def _post(self, operation, data):
        if operation not in ('device', 'device-token', 'token', 'revoke'):
            raise CivitaiError('Unsupported authorization operation.')
        try:
            response = self.transport.post(AUTH + '/' + operation, data=data,
                                           headers={'Accept': 'application/json'}, timeout=(10, 25), allow_redirects=False)
            with response:
                if len(response.content) > 32768:
                    raise CivitaiError('Civitai returned an invalid authorization response.', 'service', 502)
                result = response.json()
                if not isinstance(result, dict):
                    raise ValueError()
                if response.status_code >= 400:
                    reason = result.get('error')
                    if reason in ('authorization_pending', 'slow_down'):
                        return {'pending': True, 'slow_down': reason == 'slow_down'}
                    if reason in ('expired_token', 'access_denied', 'invalid_grant', 'invalid_client', 'invalid_scope'):
                        raise CivitaiError('Civitai could not authorize this app (' + reason + '). Check the registered public app or reconnect.', 'authentication', 401)
                    raise http_error(response.status_code)
                return result
        except CivitaiError:
            raise
        except (requests.RequestException, ValueError):
            raise CivitaiError('Could not reach Civitai authorization. Retry when the service is reachable.', 'service', 502) from None

    def token(self):
        with self.lock:
            record = self._load()
            if record.get('method') == 'oauth' and time.time() >= record.get('expires_at', 0) - 60:
                if not record.get('refresh_token'):
                    raise CivitaiError('Your Civitai connection expired. Open Settings and reconnect.', 'authentication', 401)
                result = self._post('token', {'grant_type': 'refresh_token', 'client_id': record['client_id'],
                                              'refresh_token': record['refresh_token']})
                self._save(self._oauth_record(result, record['client_id'], record['account']))
            return self._load().get('token')

    def test(self):
        value = self.token()
        if not value:
            raise CivitaiError('Connect Civitai in Settings before testing the connection.', 'authentication', 401)
        self.identify(value)
        return self.status()

    def disconnect(self):
        with self.lock:
            record = self._load()
            warning = ''
            if record.get('method') == 'oauth':
                try:
                    self._post('revoke', {'client_id': record['client_id'],
                               'token': record.get('refresh_token') or record['token'], 'token_type_hint': 'refresh_token'})
                except CivitaiError:
                    warning = 'Local connection removed; remote revocation could not be confirmed. You can also revoke Mumblebox in Civitai account settings.'
            try:
                backend = self.vault()
                if backend.get_password(self.service, 'civitai'):
                    backend.delete_password(self.service, 'civitai')
            except Exception:
                raise CivitaiError('The saved connection could not be removed. Unlock the operating-system credential vault and retry.', 'storage') from None
            self.credential, self.pending, self.error = {}, None, ''
            return {**self.status(), 'warning': warning}

    def pending_status(self):
        if not self.pending:
            return {'state': 'idle'}
        return {key: self.pending[key] for key in ('state', 'user_code', 'verification_uri', 'expires_at', 'interval')}

    def begin(self):
        with self.lock:
            client_id = self.client_id()
            if not client_id:
                raise CivitaiError('Mumblebox app registration is pending. Save its public Client ID below, or use an API key.', 'configuration')
            result = self._post('device', {'client_id': client_id, 'scope': str(SCOPES)})
            uri = result.get('verification_uri_complete') or result.get('verification_uri')
            if not isinstance(uri, str) or not uri.startswith('https://auth.civitai.com/login/oauth/device'):
                raise CivitaiError('Civitai returned an unexpected authorization address.', 'service', 502)
            self.pending = {'state': 'pending', 'client_id': client_id, 'device_code': result['device_code'],
                            'user_code': str(result['user_code'])[:64], 'verification_uri': uri,
                            'expires_at': time.time() + min(float(result['expires_in']), 900),
                            'interval': max(5, int(result.get('interval', 5))), 'next_poll': 0}
            return self.pending_status()

    @staticmethod
    def _oauth_record(result, client_id, account):
        if not result.get('access_token') or not result.get('refresh_token'):
            raise CivitaiError('Civitai did not return a complete connected-app credential.', 'service', 502)
        scope = int(result.get('scope', SCOPES))
        if scope & SCOPES != SCOPES:
            raise CivitaiError('This connection lacks the requested model or preview-read permissions. Reconnect with those permissions.', 'access', 403)
        return {'token': result['access_token'], 'refresh_token': result['refresh_token'],
                'expires_at': time.time() + min(int(result.get('expires_in', 3600)), 3600),
                'client_id': client_id, 'account': account, 'method': 'oauth'}

    def poll(self):
        with self.lock:
            pending = self.pending
            if not pending or pending['state'] != 'pending':
                return self.status()
            if time.time() >= pending['expires_at']:
                pending['state'] = 'expired'
                return self.status()
            if time.time() < pending['next_poll']:
                return self.status()
            pending['next_poll'] = time.time() + pending['interval']
            try:
                result = self._post('device-token', {'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
                                    'device_code': pending['device_code'], 'client_id': pending['client_id']})
            except CivitaiError as error:
                if error.kind == 'limit':
                    pending['interval'] += 5
                    pending['next_poll'] = time.time() + pending['interval']
                    return self.status()
                if error.kind == 'authentication':
                    pending['state'] = 'denied'
                raise
            if result.get('pending'):
                if result.get('slow_down'):
                    pending['interval'] += 5
                return self.status()
            identity = self.identify(result.get('access_token'))
            account = str(identity.get('username') or identity.get('name') or identity.get('id') or '')[:100]
            if not account:
                raise CivitaiError('The connected account could not be verified.', 'authentication', 401)
            self._save(self._oauth_record(result, pending['client_id'], account))
            self.pending = None
            return self.status()

    def cancel_authorization(self):
        with self.lock:
            self.pending = None
            return self.status()
