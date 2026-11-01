import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

class ResourcesTests(unittest.TestCase):
    def inventory(self, root, busy=lambda:False):
        from foundry.resources import ResourceInventory
        return ResourceInventory(root,busy)

    def test_lists_models_and_loras_separately_and_removes_only_confirmed_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'loras').mkdir();(root/'diffusion_models').mkdir()
            a=root/'loras/a.safetensors';a.write_bytes(b'fixture')
            b=root/'diffusion_models/b.safetensors';b.write_bytes(b'preserve')
            inventory=self.inventory(root);items=inventory.list()['items']
            self.assertEqual({i['kind'] for i in items},{'lora','image_model'})
            item=next(i for i in items if i['kind']=='lora')
            preview=inventory.preview(item['id']);inventory.remove(preview['token'])
            self.assertFalse(a.exists());self.assertTrue(b.exists())
            with self.assertRaises(ValueError):inventory.remove(preview['token'])

    def test_busy_or_changed_file_refuses_deletion(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'loras').mkdir();p=root/'loras/a.safetensors';p.write_bytes(b'one')
            busy=[False];inventory=self.inventory(root,lambda:busy[0]);item=inventory.list()['items'][0]
            preview=inventory.preview(item['id']);p.write_bytes(b'changed')
            with self.assertRaises(ValueError):inventory.remove(preview['token'])
            busy[0]=True
            with self.assertRaises(ValueError):inventory.preview(item['id'])
            self.assertTrue(p.exists())

    def test_arbitrary_id_cannot_delete_an_external_file_and_hardlinks_are_protected(self):
        import os
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'loras').mkdir();p=root/'outside.safetensors';p.write_bytes(b'preserve')
            os.link(p,root/'loras/shared.safetensors')
            inventory=self.inventory(root);item=inventory.list()['items'][0]
            self.assertFalse(item['deletable'])
            with self.assertRaises(ValueError):inventory.preview(str(p))
            with self.assertRaises(ValueError):inventory.preview(item['id'])
            self.assertTrue(p.exists())

if __name__=='__main__':unittest.main()
