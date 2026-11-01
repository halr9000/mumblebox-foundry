"""The independent image creator's public contract, not a second mesh wizard."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from foundry.workflows.image_creation.definition import validate, catalog
from foundry.workflows.image_creation.prompts import compile_prompt


class CreationContractTests(unittest.TestCase):
    def data(self, **changes):
        return dict(name="Explorer", description="A friendly blue explorer", category="characters",
                    model="klein4", **changes)

    def test_general_image_is_standalone_and_unmodified(self):
        data=self.data();data.update(category="general",description="A busy city at night")
        config=validate(data)
        self.assertFalse(config["paired"])
        self.assertEqual(compile_prompt(config,"single")["prompt"],"A busy city at night")
        self.assertEqual(catalog()["categories"][-1]["id"],"general")

    def test_front_and_back_have_distinct_semantics(self):
        config=validate(self.data(front="Silver badge",back="A red backpack"))
        front=compile_prompt(config,"front")["prompt"]
        back=compile_prompt(config,"back")["prompt"]
        self.assertIn("Silver badge",front);self.assertNotIn("red backpack",front)
        self.assertIn("exact same",back);self.assertIn("behind",back);self.assertIn("red backpack",back)
        self.assertNotIn("Silver badge",back)

    def test_limits_reserve_front_for_rear_conditioning(self):
        data=self.data();data["model"]="qwen2511"
        with self.assertRaisesRegex(ValueError,"reference"):validate(data)
        data["references"]=[{"filename":f"ref{i}.png","description":"Appearance","role":"detail"} for i in range(3)]
        with self.assertRaisesRegex(ValueError,"2"):validate(data)
        data["references"]=data["references"][:2]
        self.assertTrue(validate(data)["paired"])

    def test_nonhuman_categories_do_not_inherit_humanoid_pose(self):
        for category in ("creatures","vehicles","props","environment"):
            data=self.data();data["category"]=category
            prompt=compile_prompt(validate(data),"front")["prompt"].lower()
            self.assertNotIn("a-pose",prompt);self.assertNotIn("humanoid",prompt)

    def test_model_and_lora_validation(self):
        data=self.data();data["model"]="arbitrary-checkpoint"
        with self.assertRaises(ValueError):validate(data)
        data=self.data(loras=[{"name":"thing.safetensors","profile":"sdxl_base","strength":1}])
        with self.assertRaisesRegex(ValueError,"compatible"):validate(data)
        data["model"]="sdxl_juggernaut"
        self.assertEqual(validate(data)["loras"][0]["profile"],"sdxl_base")

    def test_invalid_numeric_options_and_paths_rejected(self):
        for settings in ({"cfg":float("nan")},{"seed":True},{"resolution":1057},{"steps":0}):
            with self.subTest(settings=settings),self.assertRaises(ValueError):validate(self.data(settings=settings))
        for name in ("../secret.png","C:/secret.png","safe/../../x","x.png [output]"):
            with self.subTest(name=name),self.assertRaises(ValueError):
                validate(self.data(references=[{"filename":name}]))

    def test_background_is_single_and_asset_edit_contract_is_local(self):
        data=self.data();data["category"]="background"
        self.assertFalse(validate(data)["paired"])
        contract=compile_prompt(validate(self.data()),"front",edit="Make the badge gold")
        self.assertIn("selected area",contract["prompt"])
        self.assertNotIn("A-pose",contract["prompt"])


if __name__=="__main__":unittest.main()
