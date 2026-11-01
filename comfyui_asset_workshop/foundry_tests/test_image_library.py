import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from foundry.workflows.image_creation.library import ImageLibrary
from foundry.workflows.image_creation.definition import validate

class ImageLibraryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.library=ImageLibrary(self.root/'state',self.root/'output')
    def tearDown(self):self.temp.cleanup()
    def creation(self,name='Test'):
        return self.library.create(validate({'name':name,'description':'An explorer','model':'klein4'}))
    def add(self,record,side='front'):
        path=self.library.directory(record['id'])/(side+'.png');Image.new('RGB',(16,16),'blue').save(path)
        return self.library.add_revision(record,side,path,{'model':'klein4'},accepted=True)
    def test_pair_is_one_gallery_entry_and_save_is_idempotent(self):
        record=self.creation();self.add(record);self.add(record,'back')
        self.library.publish(record);self.library.publish(record)
        self.assertEqual(len(self.library.list()['items']),1)
        self.assertEqual(len(self.library.get(record['id'])['revisions']),2)
    def test_draft_is_not_in_gallery_and_incomplete_pair_cannot_save(self):
        record=self.creation();self.add(record)
        self.assertEqual(self.library.list()['items'],[])
        with self.assertRaises(ValueError):self.library.publish(record)
    def test_accepted_revision_keeps_original_and_other_side(self):
        record=self.creation();front=self.add(record);back=self.add(record,'back')
        path=self.library.directory(record['id'])/'edit.png';Image.new('RGB',(16,16),'green').save(path)
        edited=self.library.add_revision(record,'front',path,{},accepted=False,source=front['id'])
        self.assertEqual(record['accepted']['front'],front['id'])
        self.library.accept(record,edited['id'],front['id'])
        self.assertEqual(record['accepted']['front'],edited['id']);self.assertEqual(record['accepted']['back'],back['id'])
        self.assertTrue(self.library.file(record,front['id']).exists())
        with self.assertRaisesRegex(ValueError,'changed'):self.library.accept(record,edited['id'],front['id'])
    def test_removal_is_reviewed_and_entry_only_preserves_files(self):
        record=self.creation();front=self.add(record);self.add(record,'back');self.library.publish(record)
        path=self.library.file(record,front['id'])
        review=self.library.preview_removal([record['id']],False)
        self.assertTrue(path.exists());self.assertEqual(review['image_count'],2)
        self.library.remove(review['token'])
        self.assertTrue(path.exists());self.assertEqual(self.library.list()['items'],[])
    def test_file_deletion_refuses_changed_or_unowned_files(self):
        record=self.creation();front=self.add(record);self.add(record,'back');self.library.publish(record)
        review=self.library.preview_removal([record['id']],True)
        self.library.file(record,front['id']).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'changed'):self.library.remove(review['token'])
        self.assertEqual(len(self.library.list()['items']),1)
        with self.assertRaises(ValueError):self.library.directory('../outside')
    def test_filters_and_pagination_are_bounded(self):
        for name in ('Blue one','Red two','Blue three'):
            record=self.creation(name);self.add(record);self.add(record,'back');self.library.publish(record)
        first=self.library.list(search='Blue',limit=1)
        second=self.library.list(search='Blue',limit=1,cursor=first['next_cursor'])
        self.assertEqual(len(second['items']),1);self.assertNotEqual(first['items'][0]['id'],second['items'][0]['id'])
        self.assertEqual(self.library.list(kind='single')['items'],[])
        with self.assertRaises(ValueError):self.library.list(limit=1000)

if __name__=='__main__':unittest.main()
