import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
import types
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
package = types.ModuleType('aw_civitai_auth_test')
package.__path__ = [str(ROOT)]
sys.modules[package.__name__] = package
for name in ('civitai_catalog', 'civitai_auth'):
    spec = importlib.util.spec_from_file_location(package.__name__ + '.' + name, ROOT / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
Auth = sys.modules[package.__name__ + '.civitai_auth'].CivitaiAuth
Error = sys.modules[package.__name__ + '.civitai_catalog'].CivitaiError


class Vault:
    saved = None
    def get_password(self, *args): return self.saved
    def set_password(self, service, account, value): self.saved = value
    def delete_password(self, *args): self.saved = None


class AuthTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.vault = Vault()
        self.identity = Mock(return_value={'username': 'test-account'})
        self.auth = Auth(lambda: self.vault, 'test-service', Path(self.temp.name) / 'connection.json', self.identity)

    def test_verified_key_is_only_saved_in_vault_and_status_is_secret_free(self):
        result = self.auth.connect('test_private_key_12345')
        self.assertTrue(result['connected'])
        self.assertNotIn('test_private_key_12345', str(result))
        self.assertFalse(self.auth.config_path.exists())
        self.assertEqual(self.auth.token(), 'test_private_key_12345')

    def test_invalid_replacement_preserves_existing_connection(self):
        self.auth.connect('existing_private_key_12345')
        self.identity.side_effect = Error('Invalid connection', 'authentication', 401)
        with self.assertRaises(Error): self.auth.connect('replacement_private_key_12345')
        self.assertEqual(self.auth.token(), 'existing_private_key_12345')

    def test_vault_failure_has_no_plaintext_fallback(self):
        self.vault.set_password = Mock(side_effect=RuntimeError('vault unavailable'))
        with self.assertRaises(Error): self.auth.connect('test_private_key_12345')
        self.assertFalse(self.auth.status()['connected'])
        self.assertFalse(self.auth.config_path.exists())

    def test_public_client_configuration_contains_no_account_token(self):
        self.auth.connect('test_private_key_12345')
        self.auth.configure('public-client-id')
        self.assertNotIn('test_private_key_12345', self.auth.config_path.read_text())
        self.assertEqual(self.auth.status()['client_id'], 'public-client-id')

    def test_disconnect_removes_vault_connection(self):
        self.auth.connect('test_private_key_12345')
        self.auth.disconnect()
        self.assertFalse(self.auth.status()['connected'])
        self.assertIsNone(self.vault.saved)

    def device(self):
        self.auth.configure('public-client-id')
        self.auth._post = Mock(return_value={'device_code': 'private-device-code', 'user_code': 'ABCD-EFGH',
            'verification_uri': 'https://auth.civitai.com/login/oauth/device', 'expires_in': 600, 'interval': 5})
        public = self.auth.begin()
        self.assertNotIn('private-device-code', str(public))
        return self.auth._post

    def test_device_poll_waits_and_saves_only_verified_credentials(self):
        post = self.device()
        post.return_value = {'pending': True}
        self.auth.poll()
        calls = post.call_count
        self.auth.poll()
        self.assertEqual(post.call_count, calls, 'Polling must obey the server interval')
        self.auth.pending['next_poll'] = 0
        post.return_value = {'access_token': 'private-access', 'refresh_token': 'private-refresh', 'scope': 37, 'expires_in': 3600}
        status = self.auth.poll()
        self.assertTrue(status['connected'])
        self.assertEqual(status['method'], 'oauth')
        self.assertNotIn('private-', str(status))

    def test_missing_permissions_preserve_previous_key(self):
        self.auth.connect('previous_key_123456')
        post = self.device()
        post.return_value = {'access_token': 'private-access', 'refresh_token': 'private-refresh', 'scope': 1}
        with self.assertRaises(Error): self.auth.poll()
        self.assertEqual(self.auth.token(), 'previous_key_123456')

    def test_refresh_rotates_secure_record_and_disconnect_revokes(self):
        self.auth._save({'token': 'old-access', 'refresh_token': 'old-refresh', 'account': 'test-account',
            'client_id': 'public-client-id', 'expires_at': 0, 'method': 'oauth'})
        self.auth._post = Mock(return_value={'access_token': 'new-access', 'refresh_token': 'new-refresh', 'scope': 37})
        self.assertEqual(self.auth.token(), 'new-access')
        self.assertIn('new-refresh', self.vault.saved)
        self.auth.disconnect()
        self.assertEqual(self.auth._post.call_args.args[0], 'revoke')
        self.assertFalse(self.auth.status()['connected'])

    def test_rate_limited_device_poll_backs_off(self):
        post = self.device()
        post.side_effect = Error('Wait', 'limit', 429)
        self.assertEqual(self.auth.poll()['oauth']['interval'], 10)
        self.assertGreater(self.auth.pending['next_poll'], 0)

    def test_denied_device_does_not_replace_existing_connection(self):
        self.auth.connect('previous_key_123456')
        post = self.device()
        post.side_effect = Error('Denied', 'authentication', 401)
        with self.assertRaises(Error): self.auth.poll()
        self.assertEqual(self.auth.pending_status()['state'], 'denied')
        self.assertEqual(self.auth.token(), 'previous_key_123456')


if __name__ == '__main__': unittest.main()
