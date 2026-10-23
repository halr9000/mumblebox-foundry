# Mumblebox agent connection

The stdio server forwards to the same local project, job and resource owners as the Comfy controls. It has no GPU imports or separate inference process. Keep **Mumblebox Single Image** controls open in the existing Desktop: each native graph must be visibly loaded and acknowledged before submission.

Create an isolated Python environment here and install `requirements.txt`. The implemented adapter uses the official `mcp==2.3.0` SDK. Do not install its dependencies into Comfy's inference environment.

Example MCP host configuration (replace installation paths; do not copy Brian's paths to another machine):

```json
{
  "mcpServers": {
    "mumblebox": {
      "command": "E:\\Comfyui-installs\\ComfyUI (1)\\ComfyUI\\custom_nodes\\comfyui_asset_workshop\\agent\\.venv\\Scripts\\python.exe",
      "args": ["E:\\Comfyui-installs\\ComfyUI (1)\\ComfyUI\\custom_nodes\\comfyui_asset_workshop\\agent\\mcp_server.py", "--comfy-url", "http://127.0.0.1:8188", "--input-root", "E:\\Comfyui-installs\\Mumblebox-inputs"]
    }
  }
}
```

Create or select an existing input folder deliberately. No filesystem input is authorized by default. `--input-file` authorizes one exact file; repeated `--input-root` options authorize images beneath selected directories. Resolved paths prevent symlink escapes. Authorization is not transmitted to another service. The client ignores proxy environment settings and refuses non-loopback addresses and redirects.

`get_project` with no ID reports a fresh state and capabilities. `save_project` creates a job or changes allowed settings. All mutations use an expected revision; reload and inspect a conflict rather than overwriting it. Start image jobs with stable request keys. `three_quarter` creates `mesh_input`; `adopt_image` can use an existing suitable upload directly. `review_image` writes reviewer `agent`; it never impersonates a human. `build_mesh_package` generates four design references, prepares the single approved input, reconstructs once and finishes the saved master on the GPU. Review the references and mesh before `export_package`.

`prepare_edit` saves a full-resolution white-to-edit selection from an authorized mask file. Start `edit_image` with `{"role":"mesh_input","edit":"saved-selection-id"}`. Inspect the preview before `accept_edit`. A kept edit still needs a new review.

`read_artifact` defaults to bounded metadata and a local URL. `preview` explicitly requests a reduced image; `full` returns the original download resource link, not a huge unsolicited mesh/base64 dump. The `mumblebox://projects/.../artifacts/...` resource also returns metadata. Download the GLB or ZIP locally for Blender. Generated references describe intent and may disagree; they did not supply reconstruction geometry.

Install the packaged companion skill at `../skills/mumblebox-assets/SKILL.md` in the agent host's supported skills directory when ready. A protocol smoke test proves the tools are served; it does not prove generated geometry quality. The validation ledger records those separately. No host configuration is changed automatically by this package.
