"""Model/task instructions must differ without changing the user's design."""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location("aw_prompt_contracts",Path(__file__).parents[1]/"prompt_contracts.py")
prompts=importlib.util.module_from_spec(spec)
spec.loader.exec_module(prompts)


class PromptContractTests(unittest.TestCase):
    def test_creation_editing_and_description_are_separate_contracts(self):
        klein=prompts.contract("klein4", "enhance", False, "props")
        qwen=prompts.contract("qwen21", "enhance", True, "vehicles")
        flux=prompts.contract("flux3_base", "enhance", True, "characters")
        self.assertEqual(len({c["id"] for c in (klein,qwen,flux)}),3)
        self.assertIn("subject",klein["instruction"])
        self.assertIn("<image1>",qwen["instruction"])
        self.assertIn("ordinal",flux["instruction"])
        self.assertNotEqual(klein["max_tokens"],qwen["max_tokens"])
        describe=prompts.contract("qwen21","describe",True,"creatures")
        self.assertIn("visible",describe["instruction"])
        self.assertIn("Never invent",describe["instruction"])
        self.assertNotIn("propose",describe["instruction"])
        with self.assertRaisesRegex(ValueError,"needs an image"):
            prompts.contract("qwen2511","enhance",False,"props")

    def test_guided_angle_keeps_side_facts_without_redundant_camera_instructions(self):
        parts={"identity":"a turquoise wrench","front":"one orange inset","back":"three grooves",
               "left":"plain metal edge","right":"one silver seam","top":"open jaw",
               "underside":"rounded end","pose":""}
        direction={"azimuth":90,"elevation":0}
        output=prompts.angle_text("klein4_base",parts,direction,"klein_depth")
        self.assertIn("one silver seam",output)
        self.assertNotIn("three grooves",output)
        self.assertNotIn("one orange inset",output)
        self.assertNotIn("azimuth",output)
        self.assertNotIn("camera",output)
        plain=prompts.angle_text("klein4_base",parts,direction)
        qwen=prompts.angle_text("qwen2511",parts,direction)
        self.assertNotEqual(plain,qwen)
        self.assertIn("right",plain)
        self.assertIn("Change",qwen)

    def test_categories_preserve_anatomy_or_structure_without_sampler_changes(self):
        creature=prompts.contract("qwen21","enhance",False,"creatures")
        building=prompts.contract("qwen21","enhance",False,"environment")
        self.assertIn("limb",creature["instruction"])
        self.assertIn("openings",building["instruction"])
        self.assertNotIn("CFG",creature["instruction"])
        with self.assertRaises(ValueError):
            prompts.contract("typo","enhance",False,"props")

    def test_bad_or_truncated_helper_output_cannot_replace_description(self):
        for value in ("", "<think>reasoning</think>prompt", "```json\n{}\n```", "Here is your prompt:"):
            with self.subTest(value=value),self.assertRaises(ValueError):
                prompts.validate_output(value)
        self.assertEqual(prompts.validate_output(" A red wrench. "),"A red wrench.")
        with self.assertRaises(ValueError):
            prompts.validate_output("A red wrench",finish_reason="length")


if __name__=="__main__": unittest.main()
