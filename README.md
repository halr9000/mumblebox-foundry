# Mumblebox Foundry

**Mumblebox 3D Game Asset Foundry**

Local image creation, image editing, and image-to-mesh workflows built around ComfyUI, Pixal3D, and TRELLIS. Designed for people and coding agents working together on 3D assets.

## Current foundation

- Create an image from a description, upload an image, or use multiple reference images to develop one approved image.
- Choose image-model profiles, use compatible LoRAs, and edit images with selection and masking tools.
- Send one approved image to mesh reconstruction and export an asset package with references and agent instructions.
- Operate through controls on the ComfyUI canvas or the companion MCP server and skill.

This is a private development repository containing a source snapshot of the existing ComfyUI implementation. The development system has a 16 GB GPU and 64 GB RAM. A clean installation on another computer has not been verified as part of this repository setup.

## Repository contents

- `comfyui_asset_workshop/` — the existing custom-node implementation, model recipes, canvas interface, and dependency metadata.
- `comfyui_asset_workshop/workflows/Mumblebox Single Image.json` — the current single-image workflow entry point.
- `comfyui_asset_workshop/agent/` — the MCP server and client.
- `comfyui_asset_workshop/skills/mumblebox-assets/` — the companion agent skill.
- `comfyui_asset_workshop/tests/` — existing checks.
- `comfyui_asset_workshop/docs/` — research, plans, and recorded validation. Historical proposals are not a list of current features.

The internal `comfyui_asset_workshop` name is retained so this initial import does not change existing code or node identities. Older internal documentation may describe superseded workflows.

## Distribution status

This import is the starting point for packaging the working application. It is not yet a standalone installer or a verified fresh-install release. The installed ComfyUI application was not changed during the import.

Model weights, LoRAs, user images, generated meshes, credentials, caches, local environments, and downloaded third-party research repositories are not included. Models and dependencies remain subject to their own licenses. A license for distributing Mumblebox Foundry itself still needs to be selected before public release.

Photogrammetry from photos or video, turntable capture, integration of the separate WorldSculpt experiment, and cloud-provider handoffs are future work; this repository does not advertise them as finished features.
