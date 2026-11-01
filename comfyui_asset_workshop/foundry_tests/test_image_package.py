import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from PIL import Image, PngImagePlugin
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from foundry.workflows.image_creation.library import ImageLibrary
from foundry.workflows.image_creation.definition import validate
from foundry.workflows.image_creation.package import build

class ImagePackageTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        root=Path(self.temp.name)
        self.library=ImageLibrary(root/'state',root/'output')
        self.record=self.library.create(validate({'description':'A blue explorer','name':'Explorer'}))
        for side in ('front','back'):
            path=self.library.directory(self.record['id'])/(side+'.png')
            metadata=PngImagePlugin.PngInfo();metadata.add_text('private','C:/private/reference.png')
            Image.new('RGB',(16,16),'blue').save(path,pnginfo=metadata)
            self.library.add_revision(self.record,side,path,{'profile':'klein4','seed':42,'prompt':'private prompt'},accepted=True)
    def tearDown(self):self.temp.cleanup()
    def test_readme_matches_accepted_pair_and_private_metadata_is_removed(self):
        path=build(self.library,self.record)
        self.assertEqual(path,build(self.library,self.record))
        with zipfile.ZipFile(path) as archive:
            self.assertEqual(set(archive.namelist()),{'README.md','Metadata/creation.json','Images/front.png','Images/back.png'})
            metadata=json.loads(archive.read('Metadata/creation.json'))
            readme=archive.read('README.md').decode()
            self.assertEqual(len(metadata['images']),2)
            self.assertIn('16 × 16',readme);self.assertIn('Apache',readme)
            for name in archive.namelist():
                self.assertNotIn(b'private',archive.read(name)) if name.startswith('Images/') else None
            self.assertNotIn('private prompt',json.dumps(metadata))
    def test_explicit_delete_covers_masks_and_packages_but_preserves_unowned_files(self):
        package=build(self.library,self.record)
        mask=self.library.directory(self.record['id'])/'mask.png';Image.new('L',(16,16),255).save(mask)
        self.library.track_file(self.record,mask)
        unrelated=mask.with_name('unowned.png');unrelated.write_bytes(b'preserve')
        self.library.publish(self.record)
        review=self.library.preview_removal([self.record['id']],True)
        self.library.remove(review['token'])
        self.assertFalse(package.exists());self.assertFalse(mask.exists());self.assertTrue(unrelated.exists())

if __name__=='__main__':unittest.main()
