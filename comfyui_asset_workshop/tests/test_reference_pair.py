"""State contracts for the two approved image references; no Comfy process needed."""
import ast
import copy
import hashlib
import io
import importlib
import importlib.util
import json
from pathlib import Path
import tempfile
import sys
import types
import unittest
from unittest.mock import Mock, patch
from PIL import Image

spec = importlib.util.spec_from_file_location("workshop_store", Path(__file__).parents[1] / "store.py")
store = importlib.util.module_from_spec(spec)
spec.loader.exec_module(store)

package = types.ModuleType("_aw_pair_contract")
package.__path__ = [str(Path(__file__).parents[1])]
runtime = types.ModuleType("_aw_pair_contract.runtime")
sys.modules["_aw_pair_contract"] = package
sys.modules["_aw_pair_contract.store"] = store
sys.modules["_aw_pair_contract.runtime"] = runtime
sys.modules.setdefault("folder_paths", types.ModuleType("folder_paths"))
recipe_spec = importlib.util.spec_from_file_location("_aw_pair_contract.recipes", Path(__file__).parents[1] / "recipes.py")
recipes = importlib.util.module_from_spec(recipe_spec)
runtime.store = lambda: None
recipe_spec.loader.exec_module(recipes)
prompt_contracts=importlib.import_module("_aw_pair_contract.prompt_contracts")
foreground=importlib.import_module("_aw_pair_contract.foreground")

helper_source = Path(__file__).parents[1] / "description_helper.py"
helper_tree = ast.parse(helper_source.read_text(encoding="utf-8"))
helper_functions = ast.Module(body=[node for node in helper_tree.body
                                   if isinstance(node, ast.FunctionDef)
                                   and node.name in ("angle_instructions", "side_prompt", "flux3_angle_captions")], type_ignores=[])


class ReferencePairTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.library = store.AssetStore(self.folder.name)
        self.asset = self.library.create("reference-pair contract")
        self.id = self.asset["id"]
        runtime.store = lambda: self.library
        recipes.store = runtime.store

    def image(self, slot, name, select=True):
        path = self.library.path(self.id, f"images/{name}.png")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(name.encode())
        return self.library.add_revision(self.id, slot, {
            "id": name, "file": f"images/{name}.png", "sha256": store.digest(path),
        }, select=select)

    def pair(self):
        self.image("design", "front")
        self.image("view_05", "back")
        return self.library.approve_pair(self.id)

    def guided_pair(self, route="klein_depth", profile="klein4_base"):
        data=self.pair()
        data["profile"]="klein4"
        data["settings"].update(angle_route=route, angle_profile=profile, steps=4, cfg=1)
        data["drafts"]=[{"id":"draft1","sha256":"mesh_hash","approved":True,"stale":False}]
        data["selected_draft"]="draft1"
        files={}
        for kind in ("depth","color"):
            path=self.library.path(self.id,f"guides/g1/{kind}.png")
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(kind.encode())
            files[kind]={"file":f"guides/g1/{kind}.png","sha256":store.digest(path)}
        data["guides"]=[{"id":"g1","slot":"view_03","draft":"draft1","draft_sha256":"mesh_hash",
                         "pose":{"azimuth":90,"elevation":0,"fov":20},"stale":False,
                         "camera":{"position":[-3,0,0],"target":[0,0,0]},"files":files}]
        return data

    def test_depth_guidance_uses_base_model_depth_first_and_own_defaults(self):
        data=self.guided_pair();original=copy.deepcopy(data)
        graph, details, _=recipes.image_recipe(data,{"id":"angle"},"view_03","generate",angle_prompt="A mint service wrench.")
        self.assertEqual(details["profile"],"klein4_base")
        self.assertEqual((details["steps"],details["cfg"]),(20,5))
        self.assertEqual([r["file"] for r in details["references"]],["guides/g1/depth.png","images/front.png"])
        self.assertTrue(details["prompt"].startswith("refcontrol"))
        adapter=next(n for n in graph.nodes.values() if n["class_type"]=="AW_LoadModelLoRA")
        self.assertEqual(adapter["inputs"]["lora_name"],recipes.model_name("klein4_depth"))
        self.assertEqual(details["guide"],"g1")
        self.assertFalse(details["camera"]["known"])
        self.assertTrue(details["preserve_camera_frame"])
        self.assertEqual(data,original)
        self.assertIn("klein4_depth",recipes.required_models(data,"image",slot="view_03"))
        self.assertNotIn("klein4_depth",recipes.required_models(data,"image",slot="design"))

    def test_anyangle_order_trigger_and_explicit_angle_overrides(self):
        data=self.guided_pair("qwen_anyangle","qwen21")
        data["settings"].update(angle_steps=24,angle_cfg=3.2,guide_strength=.9)
        _, details, _=recipes.image_recipe(data,{"id":"angle"},"view_03","generate",angle_prompt="A mint service wrench.")
        self.assertEqual([r["file"] for r in details["references"]],["images/front.png","guides/g1/color.png"])
        self.assertTrue(details["prompt"].startswith("Change the camera angle from <image2> to <image1>."))
        self.assertEqual((details["steps"],details["cfg"]),(24,3.2))
        self.assertEqual(details["loras"][-1]["strength"],.9)
        self.assertNotIn("back_reference",[r["id"] for r in details["references"]])

    def test_klein_9b_depth_uses_published_trigger_without_pose_caption(self):
        data=self.guided_pair(profile="klein_base")
        graph,details,_=recipes.image_recipe(data,{"id":"angle"},"view_03","generate",
                                             angle_prompt="Front-facing technician with arms extended.")
        self.assertEqual(details["prompt"],"refcontrol")
        texts=[n["inputs"]["text"] for n in graph.nodes.values() if n["class_type"]=="CLIPTextEncode"]
        self.assertEqual(texts,["refcontrol",""])
        self.assertEqual([r["file"] for r in details["references"]],["guides/g1/depth.png","images/front.png"])
        self.assertEqual((details["steps"],details["cfg"]),(20,5))
        self.assertEqual(next(n for n in graph.nodes.values() if n["class_type"]=="AW_LoadModelLoRA")["inputs"]["lora_name"],
                         recipes.model_name("klein9_depth"))

    def test_klein_depth_uses_nearest_approved_appearance_without_adding_references(self):
        data=self.guided_pair()
        for azimuth, expected in ((45,"front"),(90,"front"),(135,"back"),(180,"back"),
                                  (225,"back"),(270,"front"),(315,"front")):
            data["views"][2]["azimuth"]=azimuth
            data["guides"][0]["pose"]["azimuth"]=azimuth
            with self.subTest(azimuth=azimuth):
                graph,details,_=recipes.image_recipe(data,{"id":"angle"},"view_03","generate",angle_prompt="Wrench")
                self.assertEqual([r["file"] for r in details["references"]],
                                 ["guides/g1/depth.png",f"images/{expected}.png"])
                self.assertEqual(len([n for n in graph.nodes.values() if n["class_type"]=="AW_LoadImage"]),2)
                self.assertEqual(details["guide"],"g1")
                self.assertEqual((details["steps"],details["cfg"]),(20,5))

    def test_guided_reconstruction_keeps_whole_frame_and_requested_camera(self):
        data=self.guided_pair()
        _, details, _=recipes.image_recipe(data,{"id":"angle"},"view_03","generate",angle_prompt="Wrench")
        self.image("view_03","right")
        current=self.library.load(self.id)
        self.library.revision(current,"view_03")["recipe"]=details
        graph=recipes.Graph()
        _, _, _, cameras=recipes.preparation(graph,current)
        prepared=next(n for n in graph.nodes.values() if n["class_type"]=="AW_PrepareView" and n["inputs"]["slot"]=="view_03")
        self.assertTrue(prepared["inputs"]["preserve_frame"])
        self.assertEqual(next(c for c in cameras if c["id"]=="view_03")["requested_camera"],details["requested_camera"])

    def test_guidance_rejects_missing_stale_or_wrong_model_inputs_before_queueing(self):
        for change in ("stale","missing_color","wrong_model","changed_camera","changed_file"):
            data=self.guided_pair("qwen_anyangle","qwen21")
            if change=="stale":data["guides"][0]["stale"]=True
            if change=="missing_color":data["guides"][0]["files"].pop("color")
            if change=="wrong_model":data["settings"]["angle_profile"]="flux3_base"
            if change=="changed_camera":data["views"][2]["azimuth"]=91
            if change=="changed_file":self.library.path(self.id,"guides/g1/color.png").write_bytes(b"changed")
            with self.subTest(change=change), self.assertRaises(ValueError):
                recipes.image_recipe(data,{"id":"bad"},"view_03","generate",angle_prompt="Object")

    def test_back_and_masked_edit_do_not_receive_camera_guidance_adapter(self):
        data=self.guided_pair()
        _, details, _=recipes.image_recipe(data,{"id":"back"},"view_05","generate",angle_prompt="Rear of a wrench.")
        self.assertEqual(details["profile"],"klein4")
        self.assertNotIn("guide",details)
        data=self.image("view_03","side") | {"profile":data["profile"],"settings":data["settings"]}
        edit={"source":self.library.revision(data,"view_03"),"mask":{"file":"mask.png"},"prompt":"One silver inset."}
        graph, details, _=recipes.image_recipe(data,{"id":"edit"},"view_03","edit",edit=edit)
        self.assertEqual(details["profile"],"klein4_base")
        self.assertNotIn("guide",details)
        self.assertFalse(any(n["class_type"]=="AW_LoadModelLoRA" for n in graph.nodes.values()))

    def test_masked_guided_image_keeps_camera_frame_and_invalidation_dependency(self):
        data=self.guided_pair()
        self.image("view_03","guidedside")
        data=self.library.load(self.id) | {"settings":data["settings"],"profile":data["profile"]}
        source=self.library.revision(data,"view_03")
        source["recipe"]={"guide":"g1","draft":"draft1","preserve_camera_frame":True,
                          "requested_camera":{"position":[-3,0,0],"target":[0,0,0]},"angle_route":"klein_depth"}
        edit={"source":source,"mask":{"file":"mask.png"},"prompt":"Make the inset silver."}
        _,details,_=recipes.image_recipe(data,{"id":"edited"},"view_03","edit",edit=edit)
        self.assertEqual(details["guide"],"g1")
        self.assertTrue(details["preserve_camera_frame"])
        self.assertEqual(details["requested_camera"],source["recipe"]["requested_camera"])
        self.assertEqual(details["loras"],[])

    def test_replacement_mask_reaches_reference_encoders_only_when_requested(self):
        data = self.image("design", "front")
        source = self.library.revision(data, "design")
        edit = {"id": "replace", "source": source, "mask": {"file": "mask.png"},
                "prompt": "Three horizontal vents.", "replace_detail": True}
        for profile in recipes.PROFILES:
            with self.subTest(profile=profile):
                data["profile"] = profile
                graph, details, _ = recipes.image_recipe(data, {"id": "edit"}, "design", "edit", edit=edit)
                composites = {key for key, node in graph.nodes.items() if node["class_type"] == "ImageCompositeMasked"}
                if recipes.PROFILES[profile].get("family") == "sdxl":
                    # Native SDXL inpainting removes the selected source pixels
                    # inside its VAE encoder. Do not also feed the unedited source
                    # back through IP-Adapter and reintroduce the removed detail.
                    self.assertFalse(composites)
                    self.assertTrue(any(n["class_type"] == "VAEEncodeForInpaint" for n in graph.nodes.values()))
                    self.assertFalse(any(n["class_type"] == "IPAdapterAdvanced" for n in graph.nodes.values()))
                    self.assertTrue(details["prompt"].startswith(edit["prompt"]))
                    self.assertTrue(details["edit"]["replace_detail"])
                    continue
                self.assertEqual(len(composites), 1)
                blanked = [next(iter(composites)), 0]
                # Both the vision-language encoder and the reference VAE must see
                # the blanked pixels; masking only the target latent leaves the
                # old structure in the model's reference conditioning.
                image_consumers = [n for n in graph.nodes.values()
                                   if n["class_type"] in ("TextEncodeQwenImage21", "TextEncodeQwenImageEditPlus",
                                                         "ImageScaleToTotalPixels", "ReferenceMultiLatent")]
                self.assertTrue(any(blanked in n["inputs"].values() for n in image_consumers))
                self.assertTrue(details["edit"]["replace_detail"])
                plain = {k: v for k, v in edit.items() if k != "replace_detail"}
                plain_graph, _, _ = recipes.image_recipe(data, {"id": "plain-edit"}, "design", "edit", edit=plain)
                self.assertFalse(any(n["class_type"] == "ImageCompositeMasked" for n in plain_graph.nodes.values()))

    def test_replacement_choice_is_recorded_and_composite_keeps_unselected_pixels(self):
        from PIL import Image
        edits = importlib.import_module("_aw_pair_contract.image_edits")
        self.image("design", "front")
        path = self.library.path(self.id, "images/front.png")
        original = Image.new("RGBA", (16, 16), (20, 120, 130, 255))
        original.save(path)
        asset = self.library.load(self.id)
        asset["design"]["revisions"][0]["sha256"] = store.digest(path)
        self.library.save(asset)
        mask = Image.new("L", (16, 16), 0)
        mask.paste(255, (4, 4, 12, 12))
        buf = io.BytesIO()
        mask.save(buf, format="PNG")
        record = edits.create(self.library, self.id, "design", "front", "New detail",
                              buf.getvalue(), 0, replace_detail=True)
        loaded = edits.load(self.library, asset, record["id"], "design")
        self.assertTrue(loaded["replace_detail"])
        result = edits.composite(self.library, self.id, Image.new("RGBA", (16, 16), "red"), loaded)
        self.assertEqual(result.getpixel((0, 0)), original.getpixel((0, 0)))
        self.assertEqual(result.getpixel((8, 8)), (255, 0, 0, 255))
        with self.assertRaisesRegex(ValueError, "true or false"):
            edits.create(self.library, self.id, "design", "front", "New detail",
                         buf.getvalue(), replace_detail="false")

    def test_pair_requires_both_images(self):
        self.image("design", "front")
        with self.assertRaises(ValueError):
            self.library.approve_pair(self.id)
        self.assertFalse(store.pair_approved(self.library.load(self.id)))

    def test_atomic_save_retries_temporary_windows_sharing_lock_without_losing_data(self):
        target=self.library.path(self.id,"sharing.json")
        store.atomic_json(target,{"value":"old"})
        replace=store.os.replace
        locked=PermissionError("temporary Windows reader lock")
        locked.winerror=5
        with patch.object(store.os,"replace",side_effect=[locked,locked,None]) as attempt, patch.object(store.time,"sleep"):
            # Use the real final replacement, retaining atomicity.
            attempt.side_effect=lambda src,dst: (_ for _ in ()).throw(locked) if attempt.call_count<3 else replace(src,dst)
            store.atomic_json(target,{"value":"new"})
        self.assertEqual(json.loads(target.read_text()),{"value":"new"})
        self.assertEqual(attempt.call_count,3)
        with patch.object(store.os,"replace",side_effect=locked) as attempt, patch.object(store.time,"sleep"):
            with self.assertRaises(PermissionError):
                store.atomic_json(target,{"value":"lost"})
        self.assertLessEqual(attempt.call_count,8)
        self.assertEqual(json.loads(target.read_text()),{"value":"new"})
        self.assertFalse(list(target.parent.glob("sharing.json.*.part")))

    def test_draft_and_guides_follow_reference_masks_but_not_unrelated_angle_attempts(self):
        data = self.pair()
        data["drafts"] = [{"id":"draft1", "dependencies":store.draft_inputs(data), "stale":False, "approved":True}]
        data["guides"] = [{"id":"guide1", "draft":"draft1", "slot":"view_03",
                          "pose":{"azimuth":90,"elevation":0,"fov":20}, "stale":False}]
        data["selected_draft"] = "draft1"
        self.library.save(data)
        self.image("view_03", "right")
        current = self.library.load(self.id)
        self.assertFalse(current["drafts"][0]["stale"])
        self.assertFalse(current["guides"][0]["stale"])
        self.library.revision(current,"design")["foreground"] = {"id":"new_mask", "mask_sha256":"new_mask_hash"}
        self.library.save(current)
        current = self.library.load(self.id)
        self.assertTrue(current["drafts"][0]["stale"])
        self.assertFalse(current["drafts"][0]["approved"])
        self.assertTrue(current["guides"][0]["stale"])
        self.assertIsNone(current["selected_draft"])

    def test_camera_change_retires_only_its_guides_and_candidates(self):
        data = self.pair()
        data["drafts"] = [{"id":"draft1", "dependencies":store.draft_inputs(data), "stale":False, "approved":True}]
        data["guides"] = [{"id":"right_guide", "draft":"draft1", "slot":"view_03",
                          "pose":{"azimuth":90,"elevation":0,"fov":20}, "stale":False},
                         {"id":"left_guide", "draft":"draft1", "slot":"view_07",
                          "pose":{"azimuth":270,"elevation":0,"fov":20}, "stale":False}]
        self.library.save(data)
        self.image("view_03", "right")
        data=self.library.load(self.id)
        self.library.revision(data,"view_03")["recipe"]={"guide":"right_guide"}
        next(v for v in data["views"] if v["id"]=="view_03")["azimuth"]=91
        self.library.save(data)
        updated=self.library.load(self.id)
        self.assertFalse(updated["drafts"][0]["stale"])
        self.assertTrue(updated["guides"][0]["stale"])
        self.assertFalse(updated["guides"][1]["stale"])
        self.assertTrue(next(v for v in updated["views"] if v["id"]=="view_03")["stale"])

    def test_foreground_stage_does_not_require_an_approved_pair(self):
        data = self.image("initial", "upload")
        graph, details, _ = recipes.build(data, {"id":"cutout"}, "foreground", "initial")
        prepare = next(n for n in graph.nodes.values() if n["class_type"] == "AW_PrepareView")
        self.assertEqual(prepare["inputs"]["revision_id"], "upload")
        self.assertEqual(prepare["inputs"]["slot"], "initial")
        self.assertEqual(details["revision"]["id"], "upload")
        self.assertFalse(any(n["class_type"] in ("UNETLoader", "KSampler") for n in graph.nodes.values()))

    def test_geometry_draft_uses_pair_and_skips_refinement_material_and_uv_models(self):
        self.pair()
        data = self.image("view_03", "right")
        graph, details, _ = recipes.build(data, {"id":"draft"}, "draft")
        types = [n["class_type"] for n in graph.nodes.values()]
        self.assertIn("AW_SaveDraft", types)
        self.assertEqual(types.count("AW_PrepareView"), 2)
        conditioning = next(n for n in graph.nodes.values() if n["class_type"] == "AW_PixalViews")
        self.assertEqual(conditioning["inputs"]["scope"], "geometry_draft")
        for stage in ("Trellis2UpsampleStage", "Trellis2TextureStage", "UnwrapMesh", "BakeTextureFromVoxel"):
            self.assertNotIn(stage, types)
        self.assertNotIn("texture_vae", recipes.required_models(data, "draft"))
        self.assertEqual({i["slot"] for i in details["inputs"]}, {"view_01", "view_05"})

    def test_four_source_draft_tracks_all_inputs_independently_of_later_views(self):
        self.pair()
        self.image("view_02", "front_quarter")
        self.image("view_06", "back_quarter")
        data = self.library.update(self.id, {"settings": {
            "draft_source_views": ["view_01", "view_02", "view_05", "view_06"],
            "draft_appearance": "color"}})
        graph, details, _ = recipes.build(data, {"id":"four_source_draft"}, "draft")
        prepared = [n for n in graph.nodes.values() if n["class_type"] == "AW_PrepareView"]
        self.assertEqual({n["inputs"]["slot"] for n in prepared},
                         {"view_01", "view_02", "view_05", "view_06"})
        self.assertEqual(len(details["dependencies"]["inputs"]), 4)
        data["drafts"] = [{"id":"draft1", "dependencies":store.draft_inputs(data),
                           "stale":False, "approved":True}]
        self.library.save(data)
        self.image("view_03", "later_angle")
        self.assertFalse(self.library.load(self.id)["drafts"][0]["stale"])
        self.image("view_02", "changed_front_quarter")
        self.assertTrue(self.library.load(self.id)["drafts"][0]["stale"])

    def test_multiview_keeps_source_pixels_and_matching_estimated_cameras(self):
        self.pair()
        self.image("view_02", "front_quarter")
        self.image("view_06", "back_quarter")
        data = self.library.load(self.id)
        slots = ["view_01", "view_02", "view_05", "view_06"]
        data["settings"]["draft_source_views"] = slots
        data["settings"]["mesh_backend"] = "pixal_multiview"
        for view in data["views"]:
            view["enabled"] = view["id"] in slots
        # Different silhouettes at the same camera scale must not each be
        # stretched to fill the frame. These bounds deliberately differ.
        bounds = [(88,245,926,780), (117,244,878,824),
                  (109,242,924,784), (107,218,889,865)]
        for stage in ("draft", "mesh"):
            graph, _, _ = recipes.build(data, {"id":"framing"}, stage)
            conditioning = next(n["inputs"] for n in graph.nodes.values()
                                if n["class_type"] == "AW_PixalViews")
            cameras = json.loads(conditioning["cameras"])
            self.assertEqual([c["id"] for c in cameras], slots)
            self.assertEqual([c["azimuth"] for c in cameras], [0,45,180,225])
            for index, (slot, bbox) in enumerate(zip(slots, bounds)):
                with self.subTest(stage=stage, slot=slot):
                    prepared = graph.nodes[conditioning[f"images.view{index}"][0]]["inputs"]
                    loaded = graph.nodes[prepared["image"][0]]["inputs"]
                    self.assertEqual(prepared["slot"], cameras[index]["id"])
                    self.assertEqual(loaded["relative_path"], self.library.revision(data, slot)["file"])
                    source = Image.new("RGB", (1024,1024), "cyan")
                    alpha = Image.new("L", source.size)
                    alpha.paste(255, bbox)
                    rgb, rgba, metadata = foreground.frame(source, alpha,
                        padding=prepared["padding"], preserve_frame=prepared["preserve_frame"])
                    self.assertEqual(rgba.getchannel("A").getbbox(), bbox)
                    self.assertEqual(metadata["source_to_prepared"], [1,0,0,0,1,0])
                    self.assertEqual(rgb.getpixel((bbox[0],bbox[1])), (0,255,255))
                    self.assertEqual(rgb.getpixel((0,0)), (0,0,0))

    def test_single_image_preparation_still_frames_the_foreground(self):
        data = self.pair()
        for backend in ("pixal_single", "trellis2"):
            data["settings"]["mesh_backend"] = backend
            graph = recipes.Graph()
            recipes.preparation(graph, data)
            prepared = next(n["inputs"] for n in graph.nodes.values()
                            if n["class_type"] == "AW_PrepareView")
            source = Image.new("RGB", (1024,1024), "cyan")
            alpha = Image.new("L", source.size)
            alpha.paste(255, (400,400,600,600))
            _, _, metadata = foreground.frame(source, alpha, padding=prepared["padding"],
                                              preserve_frame=prepared["preserve_frame"])
            self.assertNotEqual(metadata["source_to_prepared"], [1,0,0,0,1,0])

    def test_color_draft_preserves_material_appearance_without_final_texture_bake(self):
        data=self.pair();data["settings"]["draft_appearance"]="color"
        graph, _, _ = recipes.build(data, {"id":"draft_color"}, "draft")
        types=[n["class_type"] for n in graph.nodes.values()]
        self.assertIn("Trellis2TextureStage",types)
        self.assertIn("PaintMesh",types)
        conditioning = next(n for n in graph.nodes.values() if n["class_type"] == "AW_PixalViews")
        self.assertEqual(conditioning["inputs"]["scope"], "color_draft")
        self.assertNotIn("UnwrapMesh",types)
        self.assertIn("texture_vae",recipes.required_models(data,"draft"))

    def test_mesh_stage_controls_reach_samplers_without_changing_draft_or_images(self):
        data=self.pair()
        changes={"mesh_structure_steps":13,"mesh_structure_cfg":6.2,"mesh_shape_steps":21,
                 "mesh_shape_cfg":6.3,"mesh_refine_steps":14,"mesh_refine_cfg":6.4,
                 "mesh_material_steps":15,"mesh_material_cfg":1.2,"mesh_seed":123,
                 "shape_resolution":1664,"mesh_requested_seed":123}
        data=self.library.update(self.id,{"settings":changes})
        self.assertTrue(store.pair_approved(data))
        graph,details,_=recipes.build(data,{"id":"full_mesh"},"mesh")
        samplers=[n["inputs"] for n in graph.nodes.values() if n["class_type"]=="KSampler"]
        self.assertEqual([(s["steps"],s["cfg"],s["seed"]) for s in samplers],
                         [(13,6.2,137),(21,6.3,123),(14,6.4,123),(15,1.2,124)])
        up=next(n for n in graph.nodes.values() if n["class_type"]=="Trellis2UpsampleStage")
        self.assertEqual(up["inputs"]["target_resolution"],1664)
        self.assertEqual(details["settings"]["mesh_seed"],123)
        draft,_,_=recipes.build(data,{"id":"draft"},"draft")
        self.assertEqual([(n["inputs"]["steps"],n["inputs"]["cfg"]) for n in draft.nodes.values()
                          if n["class_type"]=="KSampler"],[(12,7.5),(20,7.5)])
        self.assertEqual(data["settings"]["seed"],0)
        with self.assertRaises(ValueError):
            self.library.update(self.id,{"settings":{"mesh_shape_steps":0}})

    def test_normal_detail_can_be_disabled_without_removing_color_or_rebuilding_shape(self):
        data=self.pair()
        data["masters"]=[{"id":"raw", "approved":True, "stale":False}]
        for kind in ("master", "game"):
            for enabled in (True, False):
                with self.subTest(kind=kind, enabled=enabled):
                    data["settings"]["bake_normal"]=enabled
                    graph,details,_=recipes.export_recipe(data,{"id":"finish"},kind,"raw")
                    types=[n["class_type"] for n in graph.nodes.values()]
                    material=next(n["inputs"] for n in graph.nodes.values() if n["class_type"]=="ApplyTextureToMesh")
                    self.assertEqual("BakeNormalMapFromMesh" in types, enabled)
                    self.assertEqual("normal_map" in material, enabled)
                    self.assertIn("base_color", material)
                    self.assertIn("BakeTextureFromVoxel", types)
                    self.assertNotIn("KSampler", types)
                    self.assertEqual(details["settings"]["bake_normal"],enabled)

    def test_normal_detail_choice_persists_and_retires_exports_only(self):
        data=self.pair()
        data["masters"]=[{"id":"raw", "approved":True, "stale":False}]
        data["exports"]=[{"id":"detailed", "kind":"master", "master":"raw", "stale":False},
                         {"id":"game", "kind":"game", "master":"raw", "stale":False}]
        self.library.save(data)
        saved=self.library.update(self.id,{"settings":{"bake_normal":False}})
        self.assertFalse(saved["settings"].get("bake_normal",True))
        self.assertFalse(self.library.load(self.id)["settings"]["bake_normal"])
        self.assertTrue(all(e["stale"] for e in saved["exports"]))
        self.assertFalse(saved["masters"][0]["stale"])
        self.assertTrue(store.pair_approved(saved))

    def test_single_image_fov_is_explicit_and_multiview_keeps_per_view_cameras(self):
        data=self.pair();data["settings"].update(mesh_backend="pixal_single",mesh_fov=31)
        graph,_,_=recipes.build(data,{"id":"single"},"mesh")
        conditioning=next(n for n in graph.nodes.values() if n["class_type"]=="Pixal3DConditioning")
        record=graph.nodes[conditioning["inputs"]["camera_angle_x"][0]]
        self.assertEqual(record["inputs"]["fov"],31)
        data["settings"]["mesh_backend"]="pixal_multiview"
        graph,_,_=recipes.build(data,{"id":"multi"},"mesh")
        conditioning=next(n for n in graph.nodes.values() if n["class_type"]=="AW_PixalViews")
        self.assertEqual([v["fov"] for v in json.loads(conditioning["inputs"]["cameras"])],[20,20])

    def test_auto_fov_uses_native_moge_horizontal_degrees_only_for_unknown_single_camera(self):
        data=self.pair();data["settings"].update(mesh_backend="pixal_single",mesh_fov_mode="auto")
        graph,details,_=recipes.build(data,{"id":"auto"},"mesh")
        fov_id,fov=next((key,n) for key,n in graph.nodes.items() if n["class_type"]=="MoGeGeometryToFOV")
        self.assertEqual((fov["inputs"]["axis"],fov["inputs"]["unit"]),("horizontal","degrees"))
        record_id,record=next((key,n) for key,n in graph.nodes.items() if n["class_type"]=="AW_RecordSourceFOV")
        self.assertEqual(record["inputs"]["fov"],[fov_id,0])
        cond=next(n for n in graph.nodes.values() if n["class_type"]=="Pixal3DConditioning")
        self.assertEqual(cond["inputs"]["camera_angle_x"],[record_id,0])
        self.assertEqual(details["source_camera"]["record"],"jobs/auto-camera.json")
        self.assertIn("moge2",recipes.required_models(data,"mesh"))
        data["settings"]["mesh_backend"]="pixal_multiview"
        graph,_,_=recipes.build(data,{"id":"multi"},"mesh")
        self.assertNotIn("MoGeInference",[n["class_type"] for n in graph.nodes.values()])
        self.assertNotIn("moge2",recipes.required_models(data,"mesh"))

    def test_auto_fov_retains_requested_perspective_for_single_guided_image(self):
        data=self.pair()
        self.image("view_03","guided-side")
        data=self.library.load(self.id)
        data["settings"].update(mesh_backend="pixal_single",mesh_fov_mode="auto",include_design=False)
        for view in data["views"]:
            view["enabled"]=view["id"]=="view_03"
        side=next(v for v in data["views"] if v["id"]=="view_03")
        side["revisions"][-1]["recipe"]={"preserve_camera_frame":True,"requested_camera":{"fov":20}}
        graph,details,_=recipes.build(data,{"id":"guided-single"},"mesh")
        self.assertNotIn("MoGeInference",[n["class_type"] for n in graph.nodes.values()])
        record=next(n for n in graph.nodes.values() if n["class_type"]=="AW_RecordSourceFOV")
        self.assertEqual(record["inputs"]["fov"],20)
        self.assertEqual(record["inputs"]["mode"],"guide")
        self.assertNotIn("moge2",recipes.required_models(data,"mesh"))
        # An explicit manual override must remain usable.
        data["settings"].update(mesh_fov_mode="manual",mesh_fov=31)
        graph,_,_=recipes.build(data,{"id":"manual"},"mesh")
        record=next(n for n in graph.nodes.values() if n["class_type"]=="AW_RecordSourceFOV")
        self.assertEqual(record["inputs"]["fov"],31)

    def test_guides_render_native_maps_from_approved_draft_without_generation_models(self):
        data = self.pair()
        data["drafts"] = [{"id":"shape", "approved":True, "stale":False, "sha256":"shape_hash",
                           "appearance":"geometry", "bounds_min":[-.2,-.5,-.1], "bounds_max":[.2,.5,.1]}]
        data["selected_draft"] = "shape"
        graph, details, _ = recipes.build(data, {"id":"guide"}, "guide", "view_03")
        types = [node["class_type"] for node in graph.nodes.values()]
        self.assertIn("AW_LoadDraft", types)
        self.assertIn("Get3DComponents", types)
        self.assertIn("CreateCameraInfo", types)
        self.assertIn("AW_SaveGuide", types)
        self.assertEqual({node["inputs"]["mode"] for node in graph.nodes.values() if node["class_type"]=="RenderMesh"}, {"depth", "normal"})
        self.assertEqual(recipes.required_models(data,"guide"), [])
        self.assertEqual(details["draft"], "shape")
        self.assertLess(details["camera"]["position"][0], 0)
        data["drafts"][0]["appearance"] = "color"
        colored, _, _ = recipes.build(data, {"id":"guide_color"}, "guide", "view_03")
        self.assertIn("vertex colors", [node["inputs"].get("mode") for node in colored.nodes.values()])
        data["drafts"][0]["approved"] = False
        with self.assertRaisesRegex(ValueError, "approve"):
            recipes.build(data, {"id":"unapproved"}, "guide", "view_03")

    def test_mesh_preparation_reuses_exact_saved_masks_without_loading_removal_model(self):
        data = self.pair()
        for slot in ("design", "view_01", "view_05"):
            self.library.revision(data, slot)["foreground"] = {"id": "mask_"+slot}
        graph = recipes.Graph()
        recipes.preparation(graph, data)
        inputs = [n["inputs"] for n in graph.nodes.values() if n["class_type"] == "AW_PrepareView"]
        self.assertEqual({n["foreground_id"] for n in inputs}, {"mask_view_01", "mask_view_05"})
        self.assertFalse(any(n["class_type"] == "LoadBackgroundRemovalModel" for n in graph.nodes.values()))
        self.assertTrue(all("bg_removal_model" not in n for n in inputs))

    def test_selection_save_preserves_newer_images_and_pair(self):
        self.pair()
        self.image("view_07", "left_old")
        self.image("view_07", "left_new")
        data = self.library.load(self.id)
        data["masters"] = [{"id": "master", "stale": False}]
        self.library.save(data)
        self.library.update(self.id, {"view_selection": {"view_07": False}})
        saved = self.library.load(self.id)
        self.assertFalse(self.library.slot(saved, "view_07")["enabled"])
        self.assertEqual(self.library.slot(saved, "view_07")["current"], "left_new")
        self.assertEqual(len(self.library.slot(saved, "view_07")["revisions"]), 2)
        self.assertTrue(store.pair_approved(saved))
        self.assertTrue(saved["masters"][0]["stale"])
        self.assertTrue(self.library.slot(saved, "view_05")["enabled"])

    def test_selection_save_rejects_unknown_ids_and_non_booleans(self):
        self.pair()
        for selection in ({"missing": False}, {"view_01": "false"}, []):
            with self.subTest(selection=selection), self.assertRaises(ValueError):
                self.library.update(self.id, {"view_selection": selection})

    def test_mesh_input_changes_retire_exports_but_keep_saved_records(self):
        self.pair()
        self.image("view_07", "left")
        for change in ("selection", "camera", "new_revision"):
            with self.subTest(change=change):
                data = self.library.load(self.id)
                data["masters"] = [{"id": "master", "stale": False}]
                data["exports"] = [{"id": "game", "master": "master", "kind": "game", "stale": False}]
                data.update(selected_master="master", selected_export="game")
                self.library.save(data)
                if change == "selection":
                    saved = self.library.update(self.id, {"view_selection": {"view_07": False}})
                elif change == "camera":
                    views = copy.deepcopy(data["views"])
                    next(v for v in views if v["id"] == "view_07")["azimuth"] = 271
                    saved = self.library.update(self.id, {"views": views})
                else:
                    saved = self.image("view_07", "left_replacement")
                self.assertEqual([m["id"] for m in saved["masters"]], ["master"])
                self.assertEqual([e["id"] for e in saved["exports"]], ["game"])
                self.assertTrue(saved["masters"][0]["stale"])
                self.assertTrue(saved["exports"][0]["stale"])
                self.assertIsNone(saved.get("selected_master"))
                self.assertIsNone(saved.get("selected_export"))

    def test_saving_unchanged_selection_keeps_current_export(self):
        data = self.pair()
        data["masters"] = [{"id": "master", "stale": False}]
        data["exports"] = [{"id": "game", "master": "master", "kind": "game", "stale": False}]
        data.update(selected_master="master", selected_export="game")
        self.library.save(data)
        saved = self.library.update(self.id, {"view_selection": {"view_01": True}})
        self.assertFalse(saved["exports"][0]["stale"])
        self.assertEqual(saved["selected_export"], "game")

    def test_flux3_captions_use_references_and_validate_output(self):
        scope = {"json": json, "complete": Mock(return_value=json.dumps({"view_07": "A left side view with one connector."}))}
        exec(compile(helper_functions, str(helper_source), "exec"), scope)
        self.assertIn("flux3_angle_captions", scope)
        image = {"type": "image_url", "image_url": {"url": "local-test-image"}}
        result = scope["flux3_angle_captions"](
            self.asset, {"view_07": "The left side faces the camera."}, [image])
        self.assertIn("connector", result["view_07"])
        content = scope["complete"].call_args.args[1]
        self.assertIn(image, content)
        self.assertIn("view_07", content[0]["text"])
        scope["complete"].return_value = '{"view_07": ""}'
        with self.assertRaises(ValueError):
            scope["flux3_angle_captions"](self.asset, {"view_07": "left"}, [image])
        scope["complete"].return_value = '{"wrong_slot": "Some caption."}'
        with self.assertRaises(ValueError):
            scope["flux3_angle_captions"](self.asset, {"view_07": "left"}, [image])

    def test_explicit_approval_copies_front_to_mesh_slot(self):
        self.image("design", "front")
        data = self.image("view_05", "back")
        self.assertFalse(store.pair_approved(data))
        data = self.library.approve_pair(self.id)
        self.assertTrue(store.pair_approved(data))
        self.assertEqual(self.library.revision(data, "view_01")["file"], "images/front.png")
        self.assertEqual(self.library.revision(data, "view_05", approved=True)["id"], "back")

    def test_new_back_invalidates_other_angles_but_retains_files(self):
        self.pair()
        self.image("view_02", "quarter")
        data = self.image("view_05", "back2")
        self.assertFalse(store.pair_approved(data))
        self.assertTrue(self.library.slot(data, "view_02")["stale"])
        self.assertEqual(self.library.slot(data, "view_02")["current"], "quarter")
        self.assertTrue(self.library.path(self.id, "images/quarter.png").exists())
        self.assertTrue(self.library.path(self.id, "images/back.png").exists())

    def test_new_front_resets_back_and_dependents(self):
        self.pair()
        self.image("view_02", "quarter")
        data = self.image("design", "front2")
        self.assertFalse(store.pair_approved(data))
        self.assertIsNone(self.library.slot(data, "view_05")["current"])
        self.assertIsNone(self.library.slot(data, "view_02")["current"])
        self.assertTrue(self.library.path(self.id, "images/back.png").exists())

    def test_edit_preview_does_not_invalidate_until_accepted(self):
        self.pair()
        data = self.image("view_05", "preview", select=False)
        self.assertTrue(store.pair_approved(data))
        data = self.library.approve(self.id, "view_05", "preview")
        self.assertFalse(store.pair_approved(data))

    def test_clear_back_and_changed_prompt_invalidate_approval(self):
        data = self.pair()
        patch = copy.deepcopy(data["views"])
        next(v for v in patch if v["id"] == "view_05")["current"] = None
        data = self.library.update(self.id, {"views": patch})
        self.assertFalse(store.pair_approved(data))
        self.image("view_05", "back2")
        self.library.approve_pair(self.id)
        data = self.library.update(self.id, {"prompt": "A changed design"})
        self.assertFalse(store.pair_approved(data))

    def test_modified_file_cannot_be_approved(self):
        self.image("design", "front")
        self.image("view_05", "back")
        self.library.path(self.id, "images/back.png").write_bytes(b"changed")
        with self.assertRaises(ValueError):
            self.library.approve_pair(self.id)

    def test_next_image_model_controls_preserve_reviewed_pair(self):
        self.pair()
        self.image("view_02", "quarter")
        data = self.library.update(self.id, {
            "profile": "klein_kv",
            "loras": [{"name": "camera.safetensors", "profile": "klein_kv",
                       "strength": .9, "trigger": "<sks>", "enabled": True}],
            "settings": {"steps": 4, "cfg": 1, "camera_lora": True},
        })
        self.assertTrue(store.pair_approved(data))
        self.assertFalse(data["design"].get("stale", False))
        self.assertFalse(self.library.slot(data, "view_02").get("stale", False))
        self.assertEqual(self.library.slot(data, "view_02")["current"], "quarter")

    def test_back_uses_front_but_remaining_angles_require_approval(self):
        data = self.image("design", "front")
        refs = recipes.active_references(data, "view_05", "generate")
        self.assertEqual([r["file"] for r in refs], ["images/front.png"])
        with self.assertRaises(ValueError):
            recipes.active_references(data, "view_02", "generate")

    def test_both_images_are_connected_to_output_for_every_profile(self):
        data = self.pair()
        for profile in recipes.PROFILES:
            with self.subTest(profile=profile):
                data["profile"] = profile
                caption = "A front-right view of the same object from the first and second reference images."
                graph, details, _ = recipes.image_recipe(data, {"id": "connection-check"}, "view_02", "generate",
                                                         angle_prompt=caption)
                loads = {key: node["inputs"]["relative_path"] for key, node in graph.nodes.items()
                         if node["class_type"] == "AW_LoadImage"}
                self.assertEqual(set(loads.values()), {"images/front.png", "images/back.png"})
                seen = set()

                def visit(value):
                    if isinstance(value, dict):
                        for child in value.values():
                            visit(child)
                    elif isinstance(value, list):
                        if len(value) == 2 and isinstance(value[0], str) and value[0] in graph.nodes:
                            key = value[0]
                            if key not in seen:
                                seen.add(key)
                                visit(graph.nodes[key]["inputs"])
                        else:
                            for child in value:
                                visit(child)

                output = next(n for n in graph.nodes.values() if n["class_type"] == "AW_SaveImage")
                visit(output["inputs"])
                self.assertTrue(set(loads) <= seen)
                if recipes.PROFILES[profile].get("family") == "sdxl":
                    self.assertIn(caption, details["prompt"])
                    self.assertTrue(any(n["class_type"] == "IPAdapterAdvanced" for n in graph.nodes.values()))
                elif profile.startswith("flux3"):
                    self.assertEqual(details["prompt"], caption)
                else:
                    self.assertIn("front_reference", details["prompt"])
                    self.assertIn("back_reference", details["prompt"])

    def test_pair_counts_toward_reference_limit(self):
        data = self.pair()
        data["profile"] = "qwen2511"
        data["references"] = [{"id": str(i), "file": "images/front.png", "enabled": True} for i in range(2)]
        with self.assertRaisesRegex(ValueError, "accepts 3 active images"):
            recipes.image_recipe(data, {"id": "limit-check"}, "view_02", "generate", angle_prompt="Right quarter")

    def test_single_image_mesh_remains_available_before_pair_approval(self):
        data = self.image("design", "front")
        for backend in ("pixal_single", "trellis2"):
            data["settings"]["mesh_backend"] = backend
            self.assertEqual(recipes.approved_views(data)[0][1]["id"], "front")
        data["settings"]["mesh_backend"] = "pixal_multiview"
        with self.assertRaises(ValueError):
            recipes.approved_views(data)

    def test_history_restores_exact_pair_not_latest_replacements(self):
        data = self.pair()
        snapshot = copy.deepcopy(data)
        self.image("view_02", "quarter")
        data = self.library.load(self.id)
        data["jobs"].append({"id": "historyrun", "stage": "image", "status": "complete",
                             "result": {"slot": "view_02", "revision": "quarter"}})
        self.library.save(data)
        store.atomic_json(self.library.path(self.id, "jobs/historyrun.json"), {"asset": snapshot})
        self.image("view_05", "back2")
        restored = self.library.restore_generation(self.id, "historyrun")
        self.assertTrue(store.pair_approved(restored))
        self.assertEqual(restored["pair_approval"], {"front": "front", "back": "back"})
        self.assertEqual(self.library.slot(restored, "view_02")["current"], "quarter")

    def test_history_restores_result_freshness_for_exact_saved_inputs(self):
        data = self.pair()
        data["masters"] = [{"id": "raw"}]
        data["exports"] = [{"id": "detailed", "master": "raw", "kind": "master",
                            "file": "detailed.glb"}]
        snapshot = copy.deepcopy(data)
        data["exports"].append({"id": "game", "master": "raw", "kind": "game",
                                "file": "game.glb", "stale": False})
        self.library.path(self.id, "game.glb").write_bytes(b"saved export")
        data["jobs"].append({"id": "savedgame", "stage": "game", "status": "complete",
                             "result": {"export": "game"}})
        store.invalidate_pair(data)
        data["masters"].append({"id": "newerraw", "stale": False})
        data["exports"].append({"id": "newergame", "master": "newerraw", "kind": "game",
                                "file": "newer.glb", "stale": False})
        self.library.save(data)
        store.atomic_json(self.library.path(self.id, "jobs/savedgame.json"), {"asset": snapshot})
        restored = self.library.restore_generation(self.id, "savedgame")
        self.assertEqual(restored["selected_export"], "game")
        self.assertEqual(restored["selected_master"], "raw")
        self.assertEqual({m["id"]: m["stale"] for m in restored["masters"]},
                         {"raw": False, "newerraw": True})
        self.assertEqual({e["id"]: e["stale"] for e in restored["exports"]},
                         {"detailed": False, "game": False, "newergame": True})
        self.assertTrue(store.pair_approved(restored))

    def test_history_reuses_exact_foreground_draft_and_guides_and_retains_newer_files(self):
        data = self.pair()
        for name in ("oldmask", "oldcutout", "newmask", "newcutout", "draft.glb", "depth.png"):
            self.library.path(self.id,name).write_bytes(name.encode())
        old = {"id":"old", "mask_file":"oldmask", "mask_sha256":store.digest(self.library.path(self.id,"oldmask")),
               "cutout_file":"oldcutout", "cutout_sha256":store.digest(self.library.path(self.id,"oldcutout"))}
        for slot in ("design", "view_01"):
            self.library.revision(data,slot)["foreground"] = copy.deepcopy(old)
        data["drafts"] = [{"id":"draft1", "file":"draft.glb", "sha256":store.digest(self.library.path(self.id,"draft.glb")),
                           "approved":True, "stale":False, "dependencies":store.draft_inputs(data)}]
        data["selected_draft"] = "draft1"
        data["guides"] = [{"id":"guide1", "draft":"draft1", "slot":"view_03", "stale":False,
                          "pose":{"azimuth":90,"elevation":0,"fov":20}, "files":{"depth":{"file":"depth.png"}}}]
        snapshot = copy.deepcopy(data)
        for slot in ("design", "view_01"):
            self.library.revision(data,slot)["foreground"] = {"id":"new", "mask_file":"newmask"}
        data["jobs"].append({"id":"guidehistory", "stage":"guide", "status":"complete", "result":{"guide":"guide1"}})
        self.library.save(data)
        self.assertTrue(self.library.load(self.id)["drafts"][0]["stale"])
        store.atomic_json(self.library.path(self.id,"jobs/guidehistory.json"),{"asset":snapshot})
        restored=self.library.restore_generation(self.id,"guidehistory")
        self.assertEqual(self.library.revision(restored,"design")["foreground"],old)
        self.assertEqual(restored["selected_draft"],"draft1")
        self.assertTrue(restored["drafts"][0]["approved"])
        self.assertFalse(restored["drafts"][0]["stale"])
        self.assertFalse(restored["guides"][0]["stale"])
        self.assertTrue(self.library.path(self.id,"newmask").exists())

    def instruction_helper(self):
        complete = Mock(return_value=json.dumps({
            "identity": "turquoise beacon", "front": "one black screen", "back": "three vents",
            "left": "one connector", "right": "plain panel", "top": "one handle",
            "underside": "four screws", "pose": "",
        }))
        scope = {"store": lambda: self.library, "pair_approved": store.pair_approved,
                 "prompt_contracts":prompt_contracts,
                 "hashlib": hashlib, "json": json, "atomic_json": store.atomic_json,
                 "complete": complete, "image_part": lambda path: {"type": "image", "file": path.name}}
        exec(compile(helper_functions, str(helper_source), "exec"), scope)
        return scope["angle_instructions"], complete

    def test_back_instructions_work_before_front_approval(self):
        data = self.image("design", "front")
        helper, complete = self.instruction_helper()
        prompts = helper(data, {"view_05": {"azimuth": 180, "elevation": 0}})
        self.assertIn("back: three vents", prompts["view_05"])
        images = [p["file"] for p in complete.call_args.args[1] if p["type"] == "image"]
        self.assertEqual(images, ["front.png"])
        self.assertIsNone(self.library.load(self.id)["design"]["approved"])

    def test_description_review_retains_original_and_rejects_changed_context(self):
        data=self.library.update(self.id,{"prompt":"Six-legged red animal", "category":"creatures"})
        suggestion=self.library.record_description(data,"enhance","A red animal with six legs.",{"id":"qwen21-create-v1"})
        self.assertEqual(self.library.load(self.id)["prompt"],"Six-legged red animal")
        self.library.update(self.id,{"profile":"klein4"})
        with self.assertRaisesRegex(ValueError,"changed"):
            self.library.accept_description(self.id,suggestion["id"],"A red animal with six legs.")
        data=self.library.update(self.id,{"profile":"qwen21"})
        accepted=self.library.accept_description(self.id,suggestion["id"],"A red animal with six legs and a short tail.")
        self.assertEqual(accepted["prompt"],"A red animal with six legs and a short tail.")
        record=json.loads(self.library.path(self.id,f"descriptions/{suggestion['id']}.json").read_text())
        self.assertEqual(record["original_prompt"],"Six-legged red animal")
        self.assertEqual(record["suggested"],"A red animal with six legs.")
        self.assertEqual(record["accepted"],accepted["prompt"])
        self.assertEqual(accepted["prompt_provenance"]["category"],"creatures")
        edited=self.library.update(self.id,{"prompt":"A blue animal."})
        self.assertIsNone(edited["prompt_provenance"])
        self.assertTrue(self.library.path(self.id,f"descriptions/{suggestion['id']}.json").exists())

    def test_camera_toggle_cannot_reuse_plain_flux3_caption(self):
        data = self.pair()
        data["profile"] = "flux3_base"
        data["settings"]["camera_lora"] = False
        helper, complete = self.instruction_helper()
        parts = complete.return_value
        complete.side_effect = [parts, '{"view_07":"Expanded left-side caption."}', parts]
        directions = {"view_07": {"azimuth": 270, "elevation": 0}}
        self.assertEqual(helper(data, directions)["view_07"], "Expanded left-side caption.")
        data["settings"]["camera_lora"] = True
        camera = helper(data, directions)["view_07"]
        self.assertIn("left: one connector", camera)
        self.assertNotEqual(camera, "Expanded left-side caption.")
        data["settings"]["camera_lora"] = False
        self.assertEqual(helper(data, directions)["view_07"], "Expanded left-side caption.")

    def test_first_front_instructions_need_no_existing_design(self):
        helper, complete = self.instruction_helper()
        prompts = helper(self.asset, {"design": {"azimuth": 0, "elevation": 0}}, source_slot="initial")
        self.assertIn("front: one black screen", prompts["design"])
        self.assertNotIn("three vents", prompts["design"])
        images = [p for p in complete.call_args.args[1] if p["type"] == "image"]
        self.assertEqual(images, [])

    def test_front_recipe_uses_visible_details_without_hidden_side_specification(self):
        data = self.library.update(self.id, {"prompt": "FRONT: screen. BACK: three vents."})
        _, details, _ = recipes.image_recipe(data, {"id": "front-prompt"}, "design", "generate",
                                             angle_prompt="Front view with one screen. Hide the back.")
        self.assertIn("one screen", details["prompt"])
        self.assertNotIn("three vents", details["prompt"])

    def test_angle_instructions_include_approved_back_and_refresh_cache(self):
        data = self.pair()
        helper, complete = self.instruction_helper()
        directions = {"view_04": {"azimuth": 135, "elevation": 0}}
        helper(data, directions)
        images = [p["file"] for p in complete.call_args.args[1] if p["type"] == "image"]
        self.assertEqual(images, ["front.png", "back.png"])
        helper(data, directions)
        self.assertEqual(complete.call_count, 1)
        self.image("view_05", "back2")
        data = self.library.approve_pair(self.id)
        helper(data, directions)
        self.assertEqual(complete.call_count, 2)
        images = [p["file"] for p in complete.call_args.args[1] if p["type"] == "image"]
        self.assertEqual(images, ["front.png", "back2.png"])


if __name__ == "__main__":
    unittest.main()
