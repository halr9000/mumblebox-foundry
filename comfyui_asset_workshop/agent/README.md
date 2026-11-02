# Foundry agent connection

Use `foundry_server.py` for the current Mumblebox 3D Asset Foundry image creator, Gallery, 3D wizard and independent HairDeck wizard. Its tools share the application's workflow services, including paired generation, selected-area editing, accepted-image handoff and saved hair generations/exports. Setup, tool descriptions and example client configuration are in the release's `docs/AGENT-SETUP.md`.

`mcp_server.py` and its companion client are retained for older image-project integrations. They are not the entry point for the current five-page Foundry workflow. Both adapters use local HTTP services and their own lightweight environment; neither should install its MCP dependencies into ComfyUI's inference Python.
