"""Stdio tools forward to the visible Comfy job API; never load GPU models here."""
import argparse
import base64
import json
from typing import Any
from functools import wraps

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError, ResourceError
from mcp.types import ImageContent, ResourceLink, TextContent

from client import LocalAPI, APIError, identifier


def expected_errors(function):
    @wraps(function)
    def checked(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except APIError as error:
            raise ToolError(json.dumps({'status': error.status, **error.details})) from None
        except ValueError as error:
            raise ToolError(str(error)) from None
    return checked


def create_server(client):
    server = MCPServer('Mumblebox', version='1.0.0', instructions=(
        'Create or upload references, make one image, explicitly review that image, then reconstruct one mesh. '
        'Open the single-image controls in the existing Comfy Desktop for visible execution. '
        'Four additional references are design intentions for the receiving agent; they never enter reconstruction. '
        'Read metadata first; request a preview only when useful. An agent review is labeled agent, not user.'))

    @server.tool(structured_output=True)
    @expected_errors
    def get_project(project_id: str | None = None) -> dict[str, Any]:
        """Read bounded current project metadata, or capabilities without restoring old work."""
        return client.get_project(project_id)

    @server.tool(structured_output=True)
    @expected_errors
    def save_project(project_id: str | None = None, expected_revision: int = 0, changes: dict | None = None) -> dict[str, Any]:
        """Create/update the same project used by the GUI. Fields and revision are checked by its owner."""
        return client.save_project(project_id, expected_revision, changes)

    @server.tool(structured_output=True)
    @expected_errors
    def save_pipeline(project_id:str,expected_revision:int,changes:dict)->dict[str,Any]:
        """Save next-run refinement/cleanup/provider/detail/material settings; never launches work."""
        return client.save_pipeline(project_id,expected_revision,changes)

    @server.tool(structured_output=True)
    @expected_errors
    def select_pipeline_artifact(project_id:str,expected_revision:int,artifact_id:str)->dict[str,Any]:
        """Select an existing verified geometry or appearance for preview/export without generating."""
        return client.select_pipeline_artifact(project_id,expected_revision,artifact_id)

    @server.tool(structured_output=True)
    @expected_errors
    def create_material_session(project_id:str,expected_revision:int,source_id:str,settings:dict|None=None)->dict[str,Any]:
        """Bind a Materials Lab session to an exact prepared variant; then prepare_material_guide through start_job."""
        return client.create_material_session(project_id,expected_revision,source_id,settings)

    @server.tool(structured_output=True)
    @expected_errors
    def get_material_session(project_id:str,session_id:str)->dict[str,Any]:
        """Read saved choices, brush masks, draft revision and latest rendered revision; never generates."""
        return client.get_material_session(project_id,session_id)

    @server.tool(structured_output=True)
    @expected_errors
    def get_material_selection(project_id:str,session_id:str,mask_id:str)->dict[str,Any]:
        """Read one saved packed brush mask when needed; normal session reads return its immutable ID."""
        return client.get_material_selection(project_id,session_id,mask_id)

    @server.tool(structured_output=True)
    @expected_errors
    def save_material_choices(project_id:str,session_id:str,expected_draft_revision:int,state:dict)->dict[str,Any]:
        """Save bounded region choices/form drafts. Fine selections use base64 packed little-endian face_mask. Apply via start_job apply_materials."""
        return client.save_material_choices(project_id,session_id,expected_draft_revision,state)

    @server.tool(structured_output=True)
    @expected_errors
    def import_image(project_id: str, expected_revision: int, path: str, role: str = 'source') -> dict[str, Any]:
        """Upload an explicitly authorized local image. Sources guide creation; mesh_input requires separate review."""
        return client.import_image(project_id, expected_revision, path, role)

    @server.tool(structured_output=True)
    @expected_errors
    def prepare_edit(project_id: str, expected_revision: int, role: str, revision_id: str, mask_path: str,
                     instruction: str, feather: int = 0, replace_detail: bool = False) -> dict[str, Any]:
        """Save a full-resolution white-to-edit mask from an authorized file; then start edit_image with its saved ID."""
        return client.prepare_edit(project_id, expected_revision, role, revision_id, mask_path, instruction, feather, replace_detail)

    @server.tool(structured_output=True)
    @expected_errors
    def adopt_image(project_id: str, expected_revision: int, source_role: str, revision_id: str, role: str = 'mesh_input') -> dict[str, Any]:
        """Use an existing project image directly in another role, without generation or implied approval."""
        return client.request(client.project_path(project_id, '/images/adopt'), {'expected_revision': expected_revision,
            'source_role': source_role, 'revision_id': identifier(revision_id), 'role': role})

    @server.tool(structured_output=True)
    @expected_errors
    def accept_edit(project_id: str, expected_revision: int, role: str, revision_id: str) -> dict[str, Any]:
        """Keep a generated edit preview. This preserves the original and requires fresh image review."""
        return client.request(client.project_path(project_id, '/edits/accept'), {'expected_revision': expected_revision,
            'role': role, 'revision_id': identifier(revision_id)})

    @server.tool(structured_output=True)
    @expected_errors
    def start_job(project_id: str, expected_revision: int, kind: str, request_key: str, payload: dict | None = None) -> dict[str, Any]:
        """Start the shared visible job: build_geometry, texture_mesh, prepare_variant, prepare_material_guide, apply_materials or image/legacy jobs. Use saved source_id/variant/session_id payloads. Retry uncertain requests with the same key and inputs."""
        return client.start_job(project_id, expected_revision, kind, request_key, payload)

    @server.tool(structured_output=True)
    @expected_errors
    def get_job(project_id: str, job_id: str) -> dict[str, Any]:
        """Read saved phases, stage results and errors without generating anything."""
        return client.get_job(project_id, job_id)

    @server.tool(structured_output=True)
    @expected_errors
    def cancel_job(project_id: str, job_id: str) -> dict[str, Any]:
        """Cancel only the recorded project's owned job and preserve completed outputs."""
        return client.cancel_job(project_id, job_id)

    @server.tool(structured_output=True)
    @expected_errors
    def review_image(project_id: str, expected_revision: int, role: str, revision_id: str, sha256: str,
                     decision: str, notes: str = '') -> dict[str, Any]:
        """Record an explicit agent review, never impersonating Brian. Check actual pixels before approval."""
        return client.review_image(project_id, expected_revision, role, revision_id, sha256, decision, notes)

    @server.tool(structured_output=False)
    @expected_errors
    def read_artifact(project_id: str, artifact_id: str, mode: str = 'metadata'):
        """Metadata by default; preview returns a reduced image; full provides its original download link."""
        result = client.read_artifact(project_id, artifact_id, mode)
        preview = result.pop('preview', None)
        content = [TextContent(type='text', text=json.dumps(result))]
        if preview is not None:
            content.append(ImageContent(type='image', data=base64.b64encode(preview).decode(), mimeType='image/png'))
        if mode == 'full':
            content.append(ResourceLink(type='resource_link', uri=result['download_url'], name=artifact_id,
                                        description='Original recorded artifact; download locally for the target application.'))
        return content

    @server.resource('mumblebox://projects/{project_id}/artifacts/{artifact_id}')
    def artifact_metadata(project_id: str, artifact_id: str) -> str:
        """Read recorded metadata and a local download link; no automatic binary dump."""
        try:
            return json.dumps(client.read_artifact(project_id, artifact_id))
        except (APIError, ValueError) as error:
            raise ResourceError(str(error)) from None

    @server.tool(structured_output=True)
    @expected_errors
    def export_package(project_id: str, expected_revision: int, artifact_ids: list[str], audience: str = "agent") -> dict[str, Any]:
        """Export the selected mesh. agent requires five reviewed images; asset matches the GUI and includes available references."""
        return client.export_package(project_id, expected_revision, artifact_ids, audience)

    @server.tool(structured_output=True)
    @expected_errors
    def release_models() -> dict[str, Any]:
        """Ask Comfy's existing lifecycle owner to unload models; foreign work prevents unsafe cleanup."""
        return client.release_models()

    return server


def main():
    parser = argparse.ArgumentParser(description='Mumblebox local stdio MCP adapter')
    parser.add_argument('--comfy-url', default='http://127.0.0.1:8188')
    parser.add_argument('--input-root', action='append', default=[])
    parser.add_argument('--input-file', action='append', default=[])
    options = parser.parse_args()
    create_server(LocalAPI(options.comfy_url, input_roots=options.input_root, input_files=options.input_file)).run(transport='stdio')


if __name__ == '__main__':
    main()



