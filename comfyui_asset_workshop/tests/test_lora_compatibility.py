"""The FLUX 3 Diffusers adapter must address real native layers and QKV slices."""
import importlib.util
from pathlib import Path
import unittest

source = Path(__file__).parents[1] / "lora_compatibility.py"
spec = importlib.util.spec_from_file_location("aw_lora_compatibility", source)
compatibility = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compatibility)
aliases = compatibility.flux3_aliases


class Flux3LoRACompatibilityTests(unittest.TestCase):
    def test_diffusers_attention_targets_the_correct_fused_slice(self):
        native = {
            "diffusion_model.single_blocks.4.q_proj": ("weight", (0, 0, 3072)),
            "diffusion_model.single_blocks.4.k_proj": ("weight", (0, 3072, 3072)),
            "diffusion_model.single_blocks.4.v_proj": ("weight", (0, 6144, 3072)),
        }
        result = aliases(native)
        for name, offset in (("q", 0), ("k", 3072), ("v", 6144)):
            self.assertEqual(result.get(f"transformer.single_transformer_blocks.4.attn.to_{name}"),
                             ("weight", (0, offset, 3072)))
        self.assertEqual(len(native), 3, "Do not mutate Comfy's original mapping.")

    def test_reference_image_and_text_blocks_keep_their_own_weights(self):
        result = aliases({
            "diffusion_model.content_mode_blocks.image_cond.2.attn_out": "reference_weight",
            "diffusion_model.content_mode_blocks.image.2.attn_out": "image_weight",
            "diffusion_model.txt_mode_blocks.2.attn_out": "text_weight",
        })
        self.assertEqual(result.get("transformer.mode_blocks.image_cond.2.attn.to_out.0"), "reference_weight")
        self.assertEqual(result.get("transformer.mode_blocks.image.2.attn.to_out.0"), "image_weight")
        self.assertEqual(result.get("transformer.txt_mode_blocks.2.attn.to_out.0"), "text_weight")

    def test_feedforward_mapping_retains_input_and_output_direction(self):
        result = aliases({
            "diffusion_model.single_blocks.0.mlp_in": "input_weight",
            "diffusion_model.single_blocks.0.mlp_out": "output_weight",
        })
        self.assertEqual(result.get("transformer.single_transformer_blocks.0.ff.linear_in"), "input_weight")
        self.assertEqual(result.get("transformer.single_transformer_blocks.0.ff.linear_out"), "output_weight")

    def test_existing_upstream_mapping_and_unrelated_models_are_untouched(self):
        native = {
            "diffusion_model.single_blocks.0.q_proj": "native",
            "transformer.single_transformer_blocks.0.attn.to_q": "upstream",
            "diffusion_model.other_block.0.q_proj": "other",
        }
        result = aliases(native)
        self.assertEqual(result["transformer.single_transformer_blocks.0.attn.to_q"], "upstream")
        self.assertFalse(any(key.startswith("transformer.other_block") for key in result))


if __name__ == "__main__":
    unittest.main()
