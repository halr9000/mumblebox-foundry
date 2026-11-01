# Install Mumblebox 3D Asset Foundry

This preview runs locally on Windows with an NVIDIA GPU. It uses three Python environments: the existing ComfyUI host, an isolated texture/finishing worker, and a local Hi3D workbench. Keep their PyTorch installations separate. All example paths below are examples, not required machine paths.

Use a local directory outside OneDrive. Install Git, Python 3.13, Python 3.10, a current NVIDIA driver, and Blender 5.2.2 LTS. The validated system has 16 GB VRAM and 64 GB RAM; lower-memory machines are not yet qualified.

## 1. ComfyUI

Use a recent ComfyUI with native Qwen Image 2.1 and Pixal3D multiview support. The reference core revision is `483dae4326356b81de05d27aca3f433dd323cc25`, with frontend 0.42.5. An older installation missing these nodes must be updated before loading the workflow. Comfy Desktop and a separately installed ComfyUI both work with the node package; use the actual core directory containing `folder_paths.py` and `custom_nodes`.

Extract this release into a separate folder, for example `C:\Tools\foundry-release`. Install the lightweight host dependencies using **ComfyUI's own Python**:

```powershell
& 'C:\Tools\ComfyUI\.venv\Scripts\python.exe' -m pip install -r 'C:\Tools\foundry-release\comfyui_asset_workshop\requirements.txt'
```

Do not install a second copy of old Foundry/Hi3D wrappers that register the same node names. This package owns its Hi3D bridge and finishing nodes. Native Qwen nodes are supplied by ComfyUI; QwenUnionT8 is not required.

## 2. Isolated texture and finishing worker

Clone the tested TRELLIS.2 wrapper and create a separate Python 3.13 environment:

```powershell
git clone https://github.com/visualbruno/ComfyUI-Trellis2.git C:\Tools\foundry-trellis
git -C C:\Tools\foundry-trellis checkout b0e84c0f29857a444e8bcb5b9be2ea218e96efd0
py -3.13 -m venv C:\Tools\foundry-worker
& 'C:\Tools\foundry-worker\Scripts\python.exe' -m pip install --upgrade pip
& 'C:\Tools\foundry-worker\Scripts\python.exe' -m pip install torch==2.10.0+cu130 torchvision==0.25.0+cu130 --index-url https://download.pytorch.org/whl/cu130
& 'C:\Tools\foundry-worker\Scripts\python.exe' -m pip install -r 'C:\Tools\foundry-release\requirements-worker-windows.txt'
```

Install the five **cp313 / win_amd64** wheels from the checked-out wrapper's `wheels/Windows/Torch2100/CUDA 13.1` directory: cumesh, flex_gemm, nvdiffrast, nvdiffrec_render and o_voxel. Use that directory's exact wheel filenames:

```powershell
$wheelFolder = 'C:\Tools\foundry-trellis\wheels\Windows\Torch2100\CUDA 13.1'
Get-ChildItem -LiteralPath $wheelFolder -Filter '*cp313*win_amd64.whl' | ForEach-Object {
    & 'C:\Tools\foundry-worker\Scripts\python.exe' -m pip install $_.FullName
    if ($LASTEXITCODE -ne 0) { throw 'Worker wheel installation failed' }
}
New-Item -ItemType Directory -Force C:\Tools\foundry-texture-models
```

The wrapper source is used by the isolated worker; do not install it as another active ComfyUI custom-node pack. No model weights need to be downloaded at this point. The texture stage obtains its pinned snapshots on first use. The DINOv3 model may require accepted Hugging Face access terms and a token in Foundry Settings.

## 3. Hi3D workbench

This preview integrates the local [T8 Hi3D workbench](https://github.com/T8mars/Comfyui-Hi3d-T8). It provides the service used by Foundry's bridge. Setup installs code/dependencies, not models unless explicitly requested.

```powershell
git clone https://github.com/T8mars/Comfyui-Hi3d-T8.git C:\Tools\foundry-hi3d
git -C C:\Tools\foundry-hi3d checkout dd5776d720974ca7a4b7a185415be4259da5a50d
& 'C:\Tools\foundry-hi3d\scripts\Setup.ps1' -Python 'C:\Path\To\Python310\python.exe'
```

**Omit `-DownloadModels`.** Foundry requests the workbench's pinned model download when refinement is first used. Start the service before running refinement:

```powershell
Set-Location C:\Tools\foundry-hi3d
& '.\.venv\Scripts\python.exe' -m hi3d_workbench --port 8378
```

Keep it running. It listens on the local computer. The pinned workbench has no model-download cancel endpoint: cancelling a Foundry job prevents refinement submission but an already-started Hi3D model download continues in that service. Completed model files are reused.

## 4. Install Foundry and configure paths

Run the release installer with your actual paths:

```powershell
py -3.13 C:\Tools\foundry-release\scripts\install_foundry.py `
  --comfy C:\Tools\ComfyUI `
  --worker-python C:\Tools\foundry-worker\Scripts\python.exe `
  --trellis-repo C:\Tools\foundry-trellis `
  --trellis-models C:\Tools\foundry-texture-models `
  --blender 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'
```

If ComfyUI uses a custom `--user-directory`, pass the same directory to this installer. It copies the node package and writes private paths to `user/asset-workshop.json`. Existing settings and changed installation files are backed up under `user/mumblebox-foundry/install-backups`. It does not remove models, user outputs or other custom nodes.

Restart ComfyUI, then open:

`custom_nodes/comfyui_asset_workshop/workflows/Mumblebox 3D Asset Foundry.json`

The interface appears in the same graph as the pipeline. Use **Open Wizard** for a new asset. The graph has empty input fields; no sample alien assets are bundled.

## 5. First use and updates

Only the selected stage's models download. The interface shows the first-use message and transfer progress. Native models are stored in ComfyUI's model directories; isolated texture snapshots use the configured texture-model directory; Hi3D owns its own model directory. Model weights are downloaded from upstream providers, not from this project's GitHub archive or another user's PC.

Enter a Hugging Face token in Settings for gated resources. For Civitai downloads, the browser's API-key help links to the account settings and explains where to paste the key. Downloaded Civitai resources are for initial image creation only.

Foundry checks its GitHub Releases feed if automatic checking is enabled. **Check for updates** is also in Settings. Download a new release from GitHub and rerun the installer while ComfyUI is stopped. The checker does not execute downloaded code or overwrite a workflow.

For an update rollback, stop ComfyUI and restore the changed files/config listed in the corresponding install-backup directory. Keep your input/output/model directories.

## Troubleshooting

- **Missing native nodes:** compare your ComfyUI revision with dependencies.json; update ComfyUI rather than installing unrelated nodes.
- **Missing Interface:** verify this package loaded without import errors, then reload the ComfyUI frontend after restart.
- **Hi3D unavailable:** start its local service and check http://127.0.0.1:8378 before retrying.
- **Texture worker import failure:** check the isolated Python version, PyTorch build and matching cp313 wheels. Do not replace the host's PyTorch.
- **Model hash mismatch:** Foundry preserves the existing file and reports it. Resolve that specific file; do not delete the whole model directory.
- **Out of memory:** retry with lower detail/export choices. Only Default is configured; other memory profiles are not active yet.
