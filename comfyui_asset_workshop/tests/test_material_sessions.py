import importlib
import tempfile
import unittest
from test_reference_pair import store
class SessionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.lib=store.AssetStore(self.tmp.name);self.p=self.lib.create_project()
    def module(self):return importlib.import_module("_aw_pair_contract.materials")
    def test_get_never_creates_a_session(self):
        m=self.module();before=self.lib.path(self.p["id"],"asset.json").read_bytes()
        with self.assertRaises(ValueError):m.load_session(self.lib,self.p["id"],"a"*24)
        self.assertEqual(before,self.lib.path(self.p["id"],"asset.json").read_bytes())
    def test_masks_have_boundaries_and_zero_padding(self):
        m=self.module()
        self.assertEqual(m.decode_mask("AQ==",3),[[0,1]])
        for value in ("gA==","bad!",""):
            with self.assertRaises(ValueError):m.decode_mask(value,3)
    def test_source_session_owned_and_verified(self):
        m=self.module();path=self.lib.path(self.p["id"],"source.glb");path.write_bytes(b"mesh")
        self.p["artifacts"].append({"id":"a1","kind":"mesh","file":"source.glb","sha256":store.digest(path),"variant":"detailed","triangles":3})
        self.lib.save(self.p)
        session=m.create_session(self.lib,self.p["id"],self.p["revision"],"a1",{"guide_size":512,"palette_count":8})
        self.assertEqual(session["source_id"],"a1")
        path.write_bytes(b"changed")
        with self.assertRaises(ValueError):m.load_session(self.lib,self.p["id"],session["id"])

    def test_auto_suggestions_keep_bounded_color_metadata(self):
        state={"version":1,"regions":[{"id":0,"kind":"color","name":"Fabric","rgb":[80,30,150],"faces":3,"prompt":"Matte cotton"}]}
        checked,_=self.module().validate_draft(state,{"palette_count":1,"patch_count":1,"faces":3})
        self.assertEqual(checked['regions'][0]['rgb'],[80,30,150])
        state['regions'][0]['rgb']=[0]*500
        with self.assertRaises(ValueError):self.module().validate_draft(state,{"palette_count":1,"patch_count":1,"faces":3})

    def test_painted_masks_are_saved_once_and_referenced_by_id(self):
        import json
        m=self.module();path=self.lib.path(self.p['id'],'source.glb');path.write_bytes(b'mesh')
        self.p['artifacts'].append({'id':'a1','kind':'mesh','file':'source.glb','sha256':store.digest(path),'variant':'detailed','triangles':3});self.lib.save(self.p)
        session=m.create_session(self.lib,self.p['id'],self.p['revision'],'a1',{})
        folder=m.folder(self.lib,self.p['id'],session['id']);folder.mkdir(parents=True)
        (folder/'metadata.json').write_text(json.dumps({'faces':3,'palette_count':1,'patch_count':1}))
        state={'version':1,'regions':[{'kind':'faces','id':0,'face_mask':'AQ==','name':'Eye','prompt':'glossy eye'}]}
        saved=m.save_draft(self.lib,self.p['id'],session['id'],0,state)
        row=saved['draft']['regions'][0]
        self.assertNotIn('face_mask',row)
        self.assertEqual(len(row['mask_id']),64)
        self.assertEqual(m.worker_edits(self.lib,self.p['id'],session['id'])['regions'][0]['face_ranges'],[[0,1]])
        before=self.lib.path(self.p['id'],'asset.json').read_bytes()
        self.assertEqual(m.editor_session(self.lib,self.p['id'],session['id'])['draft']['regions'][0]['face_mask'],'AQ==')
        self.assertEqual(before,self.lib.path(self.p['id'],'asset.json').read_bytes())

    def test_unassigned_form_and_selection_do_not_request_another_material_render(self):
        m=self.module()
        self.assertTrue(callable(getattr(m,'assignment_fingerprint',None)))
        original={'version':1,'regions':[{'kind':'color','id':0,'prompt':'matte cotton','strength':1}], 'selection':[]}
        changed={**original,'editorDraft':{'prompt':'unassigned temporary note'},'selection':[{'kind':'color','id':1}]}
        self.assertEqual(m.assignment_fingerprint(original),m.assignment_fingerprint(changed))
        changed['regions']=[{'kind':'color','id':0,'prompt':'shiny plastic','strength':1}]
        self.assertNotEqual(m.assignment_fingerprint(original),m.assignment_fingerprint(changed))
