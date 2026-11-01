import importlib
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from foundry.preferences import Preferences


def release(tag, prerelease=False, **patch):
    return dict(tag_name=tag, draft=False, prerelease=prerelease,
                html_url='https://github.com/mumblebox-gpt/mumblebox-foundry/releases/tag/'+tag,
                body='Changes and installation notes.', assets=[dict(name='mumblebox-foundry-'+tag+'.zip',
                browser_download_url='https://github.com/mumblebox-gpt/mumblebox-foundry/releases/download/'+tag+'/mumblebox-foundry.zip')], **patch)

class UpdatesTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.preferences=Preferences(self.root/'preferences.json')
        self.calls=[];self.clock=[100000.0];self.response=(200,[release('v0.1.0-preview.3',True)],{'ETag':'tag-a'})

    def service(self,current='0.1.0-preview.2'):
        try: module=importlib.import_module('foundry.updates')
        except ModuleNotFoundError:self.fail('Foundry update service has not been implemented')
        def fetch(headers):
            self.calls.append(dict(headers));return self.response
        return module.ReleaseUpdates(self.root/'updates.json',self.preferences,current=current,fetch=fetch,clock=lambda:self.clock[0])

    def test_startup_can_be_disabled_and_manual_check_still_works(self):
        service=self.service()
        self.preferences.update({'auto_check_updates':False})
        self.assertEqual(service.check()['state'],'disabled');self.assertEqual(self.calls,[])
        self.assertEqual(service.check(manual=True)['state'],'available')
        self.assertFalse(self.preferences.read()['auto_check_updates'])

    def test_semantic_version_channels_and_download(self):
        service=self.service()
        self.response=(200,[release('v0.1.0-preview.10',True),release('v0.1.0-preview.3',True),release('v0.2.0',draft_override=True)],{})
        self.response[1][-1]['draft']=True
        result=service.check(manual=True)
        self.assertEqual(result['latest'],'0.1.0-preview.10')
        self.assertTrue(result['download_url'].startswith('https://github.com/mumblebox-gpt/mumblebox-foundry/releases/download/'))
        self.assertEqual(self.service(current='0.1.0').check(manual=True)['state'],'no_release')

    def test_repeated_startup_is_cached_and_manual_is_conditionally_requested(self):
        service=self.service();service.check();service.check();self.service().check()
        self.assertEqual(len(self.calls),1)
        self.clock[0]+=61;self.response=(304,None,{})
        self.assertEqual(service.check(manual=True)['state'],'available')
        self.assertEqual(self.calls[-1]['If-None-Match'],'tag-a')

    def test_rate_limit_and_unavailable_never_claim_up_to_date(self):
        service=self.service();self.response=(403,{}, {'Retry-After':'120'})
        self.assertEqual(service.check(manual=True)['state'],'unavailable')
        self.clock[0]+=61;service.check(manual=True);self.assertEqual(len(self.calls),1)
        self.clock[0]+=60;self.response=(200,[],{})
        self.assertEqual(service.check(manual=True)['state'],'no_release')

    def test_unsafe_release_links_are_not_exposed(self):
        service=self.service();entry=release('v0.1.0-preview.3',True)
        entry['html_url']='https://evil.example/release';entry['assets'][0]['browser_download_url']='javascript:bad()'
        self.response=(200,[entry],{})
        self.assertEqual(service.check()['state'],'no_release')

    def test_offline_retains_last_result_but_reports_failure(self):
        service=self.service();service.check();self.clock[0]+=86401
        def offline(headers):raise OSError('offline')
        service.fetch=offline
        result=service.check(manual=True)
        self.assertEqual(result['state'],'unavailable');self.assertEqual(result['latest'],'0.1.0-preview.3')

    def test_preference_rejects_non_boolean(self):
        service=self.service()
        with self.assertRaises(ValueError):self.preferences.update({'auto_check_updates':'false'})

if __name__=='__main__':unittest.main()
