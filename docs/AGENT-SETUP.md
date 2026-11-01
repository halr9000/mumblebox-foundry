# Foundry MCP

The companion MCP uses the same local HTTP services as the wizard. It does not load GPU models, implement another workflow engine, or require an agent to manipulate individual graph nodes.

## Install

Create a small separate Python environment and install `comfyui_asset_workshop/agent/requirements.txt` (mcp==2.3.0). Start ComfyUI with the Foundry package and open the Foundry graph before using the tools.

Example MCP client configuration; replace every example path with your installation:

```json
{
  "mcpServers": {
    "mumblebox-foundry": {
      "command": "C:\\Tools\\foundry-agent\\Scripts\\python.exe",
      "args": [
        "C:\\Tools\\ComfyUI\\custom_nodes\\comfyui_asset_workshop\\agent\\foundry_server.py",
        "--comfy-url", "http://127.0.0.1:8188",
        "--input-root", "C:\\Assets\\References"
      ]
    }
  }
}
```

Repeat `--input-root` or use `--input-file` to authorize specific reference inputs. No local input paths are allowed by default. Keep the ComfyUI service local; this is not an internet-facing authenticated service.

## Tools

- `foundry_capabilities`: exact models, categories, defaults and export selections.
- `foundry_import_reference`: imports an allowed reference without modifying its source.
- `foundry_create_run` / `foundry_update_run`: configuration only.
- `foundry_start`: turnaround, mesh, finish or rocket.
- `foundry_run_status`: stage, progress, downloads, outputs and errors.
- `foundry_cancel`: cancels the selected job while retaining completed checkpoints.
- `foundry_show_run`: updates the already-open interface without taking OS focus.
- `foundry_package`: finished package metadata and local download URL.

Read capabilities first; do not invent identifiers or format combinations. Label the overall reference primary and describe extra images' purposes. Use a unique request_id for an intentional start; reuse the same request_id and payload when retrying an uncertain request. Poll at sensible intervals. A disconnected MCP client does not cancel a backend job.

Model licenses vary. A successful file export is not proof of animation suitability or physical printability. Inspection tools such as Blender remain useful for reviewing the actual result.
