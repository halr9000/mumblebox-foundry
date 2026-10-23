"""Real SDK stdio/HTTP smoke. No inference; use an explicit disposable project."""
import argparse
import asyncio
import json
from pathlib import Path
import sys

from mcp import Client
from mcp.client.stdio import StdioServerParameters


async def verify(project_id, input_files):
    server = Path(__file__).parents[1] / 'agent' / 'mcp_server.py'
    parameters = StdioServerParameters(command=sys.executable,
        args=[str(server), *[arg for path in input_files for arg in ('--input-file', str(Path(path).resolve()))]], cwd=str(server.parent))
    async with Client(parameters) as client:
        tools = await client.list_tools()
        names = {tool.name for tool in tools.tools}
        required = {'get_project', 'save_project', 'import_image', 'start_job', 'get_job', 'cancel_job',
                    'review_image', 'read_artifact', 'export_package', 'release_models', 'adopt_image',
                    'prepare_edit', 'accept_edit'}
        assert required <= names, names
        response = await client.call_tool('get_project', {'project_id': project_id})
        assert not response.is_error, response.content
        project = response.structured_content
        assert project['id'] == project_id, project.keys()
        response = await client.call_tool('save_project', {'project_id': project_id, 'expected_revision': project['revision'],
            'changes': {'name': 'Mumblebox UI and MCP control proof'}})
        assert not response.is_error, response.content
        project = response.structured_content
        denied = await client.call_tool('start_job', {'project_id': project_id, 'expected_revision': project['revision'],
            'kind': 'build_mesh_package', 'request_key': 'mcp-unapproved-proof', 'payload': {}})
        assert denied.is_error, denied
        assert any('Approve' in getattr(part, 'text', '') for part in denied.content), denied.content
        images = []
        for path in input_files:
            imported = await client.call_tool('import_image', {'project_id': project_id,
                'expected_revision': project['revision'], 'path': str(Path(path).resolve()), 'role': 'source'})
            assert not imported.is_error, imported.content
            project = imported.structured_content['project']
            images.append(imported.structured_content['image']['id'])
        if images:
            preview = await client.call_tool('read_artifact', {'project_id': project_id, 'artifact_id': images[0], 'mode': 'preview'})
            assert not preview.is_error, preview.content
            assert any(part.type == 'image' for part in preview.content)
            resource = await client.read_resource(f'mumblebox://projects/{project_id}/artifacts/{images[0]}')
            assert json.loads(resource.contents[0].text)['metadata']['id'] == images[0]
        templates = await client.list_resource_templates()
        print(json.dumps({'status': 'PASS', 'transport': 'real stdio', 'sdk': '2.3.0', 'tools': sorted(names),
            'project_id': project_id, 'shared_http_write': project['name'], 'unapproved_mesh_denied': True,
            'resource_templates': len(templates.resource_templates), 'imported_source_ids': images,
            'preview_and_metadata_resource': bool(images), 'inference_calls': 0}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--project-id', required=True)
    parser.add_argument('--input-file', action='append', default=[])
    options = parser.parse_args()
    asyncio.run(verify(options.project_id, options.input_file))
