# Mumblebox 3D Asset Foundry

A local ComfyUI interface for turning reference images into textured 3D assets. A guided workflow connects four-view image generation, Pixal3D/TRELLIS.2 geometry, Hi3D refinement, measured cleanup, texturing and selected exports.

**Preview 0.1.0-preview.6 — Windows / NVIDIA beta.** Install through [Pinokio](docs/PINOKIO.md) for automated software setup, or use the [manual installation](INSTALL.md). Pinokio opens the Foundry interface directly. Original Foundry code is Apache-2.0; models and third-party tools retain their own terms. Read [third-party notices](THIRD-PARTY.md), particularly before commercial use.

## Included

- One working image-to-3D wizard, accepting an overall reference plus optional described references.
- A separate image creator: front/back pairs for assets, or single background/general images. References, compatible installed LoRAs and model defaults are available on one scrolling page.
- Side-by-side image editing with rectangle, ellipse, brush, erase, polygon and magnetic selections. Edits are previews until accepted; original revisions remain available.
- Image Gallery with grouped pairs, filters, revision restore, download and confirmed removal. Deleting entries and deleting their files are separate choices.
- Save an accepted pair and send it into the 3D wizard, retaining reference roles and generation provenance.
- Supported Qwen, FLUX and Klein turnaround choices with model-specific settings and license information.
- Four-view review, mesh/refinement controls, final mesh preview, export choices and a downloadable package.
- Detailed and reduced triangle meshes, optional quad retopology, UVs and detail baking. Available formats: GLB, FBX, OBJ, BLEND, STL, PNG and ZIP.
- Rocket Mode continues from the current step using your settings and selected output versions.
- A package README, file catalog, measurements and resources/licensing record that reflect the selected outputs.
- Asset history, light/dark themes, system telemetry, model unloading and first-use model downloads.
- A Civitai browser for installing image models and LoRAs. These are initial-image resources; downloads do not expand the supported turnaround models.
- A [local MCP server](docs/AGENT-SETUP.md) for agents using the same workflow services as the interface.

Future workflow cards are labeled Coming soon. Standalone mesh repair, video reconstruction, turntable capture and action figures are not shipped as completed workflows.

## Workflow

Supply images → generate/review four views → build the fully decoded mesh → refine with Hi3D → clean geometry → texture and bake selected versions → export.

The detailed master is retained. Optional quad retopology provides an editing starting point, not a rig or an animation-ready guarantee. GLB uses triangles; quad-preserving authoring formats are available. A print export includes geometry checks, but physical printability still depends on dimensions, material and printer.

## Get started

1. In Pinokio, install this repository: https://github.com/mumblebox-gpt/mumblebox-foundry
2. Choose **Install**, then **Start Foundry**. **Open Foundry** shows the interface inside Pinokio.
3. Select **Open Wizard** and supply your own image, or **Images → Create Images** to create starting references first.

The [Pinokio guide](docs/PINOKIO.md) covers installation, updates, repair and MCP setup. Existing ComfyUI users can follow [INSTALL.md](INSTALL.md) and open the packaged `Mumblebox 3D Asset Foundry.json` workflow instead.

The public workflow contains no saved test images, meshes, textures, project history or credentials. Model weights are not included. They download from their upstream hosts when a selected stage first needs them; opening the interface does not download models. Access-gated models may require an account/token and acceptance of their upstream terms.

## Compatibility and validation

The reference system uses an NVIDIA RTX 4080 SUPER (16 GB VRAM), 64 GB system RAM and Windows. This is not an 8 GB compatibility claim. Additional memory profiles remain placeholders; Default uses the tested settings.

See [dependencies.json](dependencies.json) for pinned reference versions and [release validation](docs/RELEASE-VALIDATION.md) for the exact evidence and remaining limits. New asset categories and alternate turnaround models are enabled; their generation quality has not been exhaustively qualified.

## Project

- [Public releases and downloads](https://github.com/mumblebox-gpt/mumblebox-foundry/releases)
- [Issues](https://github.com/mumblebox-gpt/mumblebox-foundry/issues)
- [Mumblebox projects](https://github.com/mumblebox-gpt?tab=repositories)

Settings offers **Check for updates** and an automatic startup check. In Pinokio, stop Foundry and choose **Update** to install an eligible published release. Updates are deliberate and preserve saved assets, settings and model weights; a GitHub push does not silently change your installation.

Powered by Hi3D 1.0 - http://hi3d.ai/ . Thanks to the researchers and developers behind ComfyUI, Pixal3D, TRELLIS.2, Hi3D, the image models, Blender and the mesh-processing tools.
