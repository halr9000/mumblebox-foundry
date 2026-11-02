"""Real stdio -> installed HTTP hair controls; does not generate or delete assets."""
import argparse
import asyncio
import json
import sys
from pathlib import Path
from mcp import Client
from mcp.client.stdio import StdioServerParameters

async def check(server,ident):
    parameters=StdioServerParameters(command=sys.executable,args=[str(server)],cwd=str(server.parent))
    async with Client(parameters) as client:
        names={t.name for t in (await client.list_tools()).tools}
        required={'foundry_hair_'+name for name in ('capabilities','create','update','status','start','cancel','show')}
        assert required<=names
        async def call(name,data):
            value=await client.call_tool(name,data);assert not value.is_error,value.content;return value.structured_content
        cap=await call('foundry_hair_capabilities',{})
        current=await call('foundry_hair_status',{'creation_id':ident})
        assert current['package'] and len(current['variants'])==2
        config={**current['config'],'name':'MCP hair contract check'}
        draft=await call('foundry_hair_create',{'configuration':config})
        draft=await call('foundry_hair_update',{'creation_id':draft['id'],'configuration':{**config,'color':'#553311'}})
        assert draft['config']['color']=='#553311'
        await call('foundry_hair_cancel',{'creation_id':draft['id']})
        rejected=await client.call_tool('foundry_hair_start',{'creation_id':draft['id'],'request_id':'invalid','operation':'shell'})
        assert rejected.is_error
        await call('foundry_hair_show',{'creation_id':ident})
        print(json.dumps(dict(status='PASS',transport='real stdio and installed HTTP',tools=len(names),hair_tools=sorted(required),
            installed_result=current['id'],draft=draft['id'],invalid_operation_denied=True,inference_calls=0)))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--server',type=Path,required=True);p.add_argument('--id',required=True);a=p.parse_args()
    asyncio.run(check(a.server.resolve(),a.id))
