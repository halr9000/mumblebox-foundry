"""Stage-scoped draft conditioning using the installed native Pixal operators.

Final reconstruction stays on Comfy's complete builder. Drafts skip high-resolution
feature allocations for stages that their graph never runs; used features retain
the same DINO, NAF, projection, camera and averaging operations.
"""
import torch


def build_conditioning(clip_vision_model, image, transform_matrix, camera_angle_x,
                       mesh_scale, num_views=1, scope="full"):
    from comfy_extras import nodes_trellis2 as native

    if scope == "full":
        return native._build_pixal3d_conditioning(
            clip_vision_model, image, transform_matrix, camera_angle_x, mesh_scale, num_views=num_views)
    if scope not in ("geometry_draft", "color_draft"):
        raise ValueError("Unknown Pixal conditioning scope.")
    memory = native.comfy.model_management
    out_device, compute_device = memory.intermediate_device(), memory.get_torch_device()
    cond = native._dino_encode_batch(clip_vision_model, image, out_device, want_patches=True)
    batch_size = cond["batch_size"] // num_views
    fm512, fm1024 = cond["patches_512"], cond["patches_1024"]
    shape_hr = native._naf_upsample(clip_vision_model.naf, fm512, cond["composites"],
                                    512, (512, 512), out_device, compute_device)
    stages = {
        "ss": {"feature_map": fm512, "feature_map_hr": None, "image_resolution": 512},
        "shape_512": {"feature_map": fm512, "feature_map_hr": shape_hr, "image_resolution": 512},
    }
    if scope == "color_draft":
        texture_hr = native._naf_upsample(clip_vision_model.naf, fm1024, cond["composites"],
                                          1024, (1024, 1024), out_device, compute_device)
        stages["tex_1024"] = {"feature_map": fm1024, "feature_map_hr": texture_hr,
                              "image_resolution": 1024}
    global512 = cond["global_512"].unflatten(0, (batch_size, num_views)).mean(dim=1)
    global1024 = cond["global_1024"].unflatten(0, (batch_size, num_views)).mean(dim=1)
    pack = {"stages": stages, "transform_matrix": transform_matrix.to(out_device),
            "camera_angle_x": camera_angle_x.to(out_device), "mesh_scale": mesh_scale.to(out_device),
            "num_views": num_views, "patch_size": 16}
    ss = native.compute_stage_proj_feats(pack, "ss", dense_grid_resolution=16,
                                         batch_size=batch_size, device=compute_device)
    extras = {"embeds": global1024, "proj_feat_pack": pack, "trellis2_proj_feats": ss}
    negative_extras = {**extras, "embeds": torch.zeros_like(global1024)}
    return native.IO.NodeOutput([[global512, extras]], [[torch.zeros_like(global512), negative_extras]])
