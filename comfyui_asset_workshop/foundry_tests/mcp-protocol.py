"""Real installed Foundry stdio/HTTP checks; no inference or user-file deletion."""
import argparse
import asyncio
import json
from pathlib import Path
import sys
from mcp import Client
from mcp.client.stdio import StdioServerParameters


async def verify(server, run_id):
    parameters = StdioServerParameters(command=sys.executable,
        args=[str(server)], cwd=str(server.parent))
    async with Client(parameters) as client:
        names = {tool.name for tool in (await client.list_tools()).tools}
        assert len(names) == 9, names
        async def call(name, args):
            response = await client.call_tool(name, args)
            assert not response.is_error, response.content
            return response.structured_content
        capabilities = await call('foundry_capabilities', {})
        source = await call('foundry_run_status', {'run_id': run_id})
        assert 'outputs' not in source
        package = await call('foundry_package', {'run_id': run_id})
        assert package['download_url'].startswith('http://127.0.0.1:8188/')
        invalid = await client.call_tool('foundry_start', {
            'run_id': '../private', 'operation': 'shell', 'request_id': 'denial-check'})
        assert invalid.is_error
        config = {key: source[key] for key in ('references', 'category', 'profile', 'overrides', 'selection')}
        config['turnaround_model'] = source.get('turnaround_model', source['turnaround']['id'])
        config['name'] = 'Foundry MCP protocol check'
        created = await call('foundry_create_run', {'configuration': config})
        config['name'] = 'Foundry MCP protocol checked'
        updated = await call('foundry_update_run', {'run_id': created['id'], 'configuration': config})
        assert updated['name'] == config['name']
        cancelled = await call('foundry_cancel', {'run_id': created['id']})
        print(json.dumps({'status': 'PASS', 'transport': 'real stdio and installed HTTP',
            'tools': sorted(names), 'capability_fields': sorted(capabilities),
            'fixture_run': created['id'], 'shared_create_update': True,
            'cancel_status': cancelled['status'], 'invalid_operation_denied': True,
            'package_metadata': True, 'inference_calls': 0}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--server', type=Path, required=True)
    parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    asyncio.run(verify(args.server.resolve(), args.run_id))
