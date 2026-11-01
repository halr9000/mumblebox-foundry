"""Recovery and input failures at the durable wizard boundary."""
import asyncio
import copy
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from foundry.workflows.image_to_3d.runs import WizardRuns
from foundry.workflows.image_to_3d.prompts import bind_references

class RecoveryTests(unittest.IsolatedAsyncioTestCase):
    async def test_completed_prompt_is_adopted_after_restart_without_submission(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);out=root/'output';out.mkdir();(out/'mesh.glb').write_bytes(b'preserved result')
            class Native:
                def active_ids(self):return set()
                def history(self,ident):return {'status':{'status_str':'success'},'outputs':{'382':{'3d':[{'filename':'mesh.glb','subfolder':'','type':'output'}]}}}
                async def wait(self,ident,*args):return self.history(ident)
                async def submit(self,*args):raise AssertionError('Recovery resubmitted a completed prompt')
            service=WizardRuns(root/'state',root,out,Native(),None,lambda:False,None,{})
            ident='a'*32
            original={'id':ident,'status':'running','stage':'geometry','stages':{},'outputs':{},'previews':{},'checkpoints':{},'events':[],
                'pending':{'stage':'geometry','prompt_id':'b'*32,'fingerprint':'f','nodes':['382'],'started':time.time()}}
            service.save(original);run=service.get(ident)
            task=service.tasks.get(ident)
            self.assertIsNotNone(task,'Completed queue history must be adopted, not ignored')
            await task
            self.assertIn('geometry',run['stages'])
            self.assertEqual(run['checkpoints']['decoded'],str((out/'mesh.glb').resolve()))
            self.assertFalse(service.tasks)

    def test_malformed_and_ambiguous_references_report_validation_errors(self):
        good={'id':'primary','filename':'image.png','role':'primary','description':''}
        for refs in ([None],[{**good,'description':False}],[good,{'id':'detail','filename':'detail.png','role':'component','description':''}]):
            with self.assertRaises(ValueError):bind_references('characters',refs)


    def test_texture_change_invalidates_finishing_but_retains_geometry(self):
        from PIL import Image
        from types import SimpleNamespace
        from foundry.workflows.image_to_3d.definition import DEFAULTS
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp).resolve();Image.new("RGB",(8,8),"white").save(root/"image.png")
            parser=lambda raw,available:SimpleNamespace(variants={k:v["formats"] for k,v in json.loads(raw)["variants"].items()})
            service=WizardRuns(root/"state",root,root,None,None,lambda:False,parser,{"detailed":("Detailed",["glb"])})
            data={"name":"Alien","references":[{"id":"one","filename":"image.png","role":"primary","description":""}],
                  "selection":{"variants":{"detailed":{"formats":["glb"]}}},"overrides":{}}
            public=service.create(data);run=service.get(public["id"])
            for stage in ("turnaround","geometry","refinement","texture"):
                run["stages"][stage]={"fingerprint":service.fingerprint(run,stage),"files":{}}
            run["previews"]={"decoded":"initial","clean":"clean","texture":"old"}
            data["overrides"]={"texture_seed":99};service.update(run["id"],data)
            self.assertIn("refinement",run["stages"]);self.assertIn("geometry",run["stages"])
            self.assertNotIn("texture",run["stages"]);self.assertNotIn("texture",run["previews"])
            self.assertEqual(run["previews"]["clean"],"clean")

    def test_public_state_retains_audit_from_saved_outputs(self):
        with tempfile.TemporaryDirectory() as temp:
            service=WizardRuns(temp,temp,temp,None,None,lambda:False,None,{})
            audit={"watertight":True,"boundary_edges":0,"faces":100}
            run={"id":"a"*32,"stages":{},"outputs":{"2015":{"text":[json.dumps(audit)]}}}
            public=service.public(run)
            self.assertEqual(public["geometry_audit"],audit)
            self.assertNotIn("geometry_audit",run)

    def test_changing_image_model_invalidates_prior_views_and_downstream_results(self):
        from PIL import Image
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp).resolve();Image.new("RGB",(8,8),"white").save(root/"image.png")
            parser=lambda raw,available:SimpleNamespace(variants={k:v["formats"] for k,v in json.loads(raw)["variants"].items()})
            service=WizardRuns(root/"state",root,root,None,None,lambda:False,parser,{"detailed":("Detailed",["glb"])})
            data={"name":"Contract","references":[{"id":"one","filename":"image.png","role":"primary","description":""}],
                  "selection":{"variants":{"detailed":{"formats":["glb"]}}},"overrides":{}}
            run=service.get(service.create(data)["id"])
            for stage in ("turnaround","geometry","refinement","texture"):
                run["stages"][stage]={"fingerprint":service.fingerprint(run,stage),"files":{}}
            run["previews"]={"front":"old","clean":"old"}
            data["turnaround_model"]="klein4";service.update(run["id"],data)
            self.assertFalse(run["stages"])
            self.assertFalse(run["previews"])
            self.assertEqual(run["turnaround_model"],"klein4")

    def test_cancel_targets_only_the_owned_prompt(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as temp:
            cancelled=[]
            native=SimpleNamespace(cancel=lambda ident:cancelled.append(ident))
            service=WizardRuns(temp,temp,temp,native,None,lambda:False,None,{})
            run={"id":"c"*32,"status":"running","pending":{"prompt_id":"owned"},"stages":{}}
            service.runs[run["id"]]=run;service.cancel(run["id"])
            self.assertEqual(cancelled,["owned"])

if __name__=='__main__':unittest.main()
