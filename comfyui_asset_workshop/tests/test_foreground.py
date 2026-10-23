import importlib.util
from pathlib import Path
import sys
import tempfile
import types
import unittest
from PIL import Image

package = types.ModuleType("_aw_foreground_test")
package.__path__ = [str(Path(__file__).parents[1])]
sys.modules[package.__name__] = package
from importlib import import_module
foreground = import_module("_aw_foreground_test.foreground")
store = import_module("_aw_foreground_test.store")


class ForegroundTests(unittest.TestCase):
    def test_soft_thin_foreground_is_not_cropped_to_opaque_center(self):
        image = Image.new("RGB", (10, 8), "red")
        alpha = Image.new("L", image.size)
        alpha.putpixel((1, 3), 64)
        alpha.putpixel((8, 4), 255)
        rgb, rgba, meta = foreground.frame(image, alpha, padding=1, size=8)
        self.assertEqual(meta["bounding_box_xyxy"], [1, 3, 9, 5])
        self.assertEqual(meta["crop_box_xyxy"], [1, 0, 9, 8])
        self.assertEqual(meta["source_to_prepared"], [1, 0, -1, 0, 1, 0])
        self.assertEqual(rgba.getpixel((0, 3))[3], 64)
        self.assertEqual(rgb.getpixel((0, 3)), (64, 0, 0))

    def test_known_camera_keeps_frame_and_offcenter_object(self):
        image = Image.new("RGB", (8, 8), "cyan")
        alpha = Image.new("L", image.size)
        alpha.putpixel((6, 3), 255)
        _, rgba, meta = foreground.frame(image, alpha, padding=1.1, size=8, preserve_frame=True)
        self.assertEqual(meta["crop_box_xyxy"], [0, 0, 8, 8])
        self.assertEqual(meta["source_to_prepared"], [1, 0, 0, 0, 1, 0])
        self.assertEqual(rgba.getchannel("A").getbbox(), (6, 3, 7, 4))

    def test_empty_and_wrong_size_masks_fail_without_inverting(self):
        image = Image.new("RGB", (8, 8))
        for mask in (Image.new("L", (8, 8)), Image.new("L", (4, 4), 255)):
            with self.assertRaises(ValueError):
                foreground.frame(image, mask)

    def test_cutout_preserves_original_and_acceptance_invalidates_mesh(self):
        with tempfile.TemporaryDirectory() as directory:
            library = store.AssetStore(directory)
            asset = library.create("cutout")
            path = library.path(asset["id"], "images/source.png")
            path.parent.mkdir(parents=True)
            Image.new("RGB", (8, 8), "red").save(path)
            original = store.digest(path)
            library.add_revision(asset["id"], "design", {"id": "source", "file": "images/source.png", "sha256": original})
            asset = library.load(asset["id"])
            asset["masters"].append({"id":"old", "stale":False})
            library.save(asset)
            mask=Image.new("L", (8,8));mask.paste(255,(2,2,6,6))
            candidate=foreground.create(library,asset["id"],"design","source",mask,origin="manual")
            self.assertNotIn("foreground",library.revision(library.load(asset["id"]),"design"))
            updated=foreground.accept(library,asset["id"],"design",candidate["id"])
            self.assertTrue(updated["masters"][0]["stale"])
            self.assertEqual(updated["design"]["current"],"source")
            self.assertEqual(store.digest(path),original)
            saved=library.revision(updated,"design")["foreground"]
            with Image.open(library.path(asset["id"],saved["cutout_file"])) as cutout:
                self.assertEqual(cutout.getpixel((0,0))[3],0)
                self.assertEqual(cutout.getpixel((3,3)),(255,0,0,255))

    def test_replaced_source_cannot_accept_old_cutout(self):
        with tempfile.TemporaryDirectory() as directory:
            library=store.AssetStore(directory);asset=library.create("cutout")
            for name in ("first","second"):
                path=library.path(asset["id"],f"images/{name}.png");path.parent.mkdir(exist_ok=True)
                Image.new("RGB",(8,8),"red").save(path)
                library.add_revision(asset["id"],"design",{"id":name,"file":f"images/{name}.png","sha256":store.digest(path)})
                if name=="first":
                    candidate=foreground.create(library,asset["id"],"design",name,Image.new("L",(8,8),255),origin="manual")
            with self.assertRaisesRegex(ValueError,"changed"):
                foreground.accept(library,asset["id"],"design",candidate["id"])


if __name__ == "__main__": unittest.main()
