import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const source=readFileSync(new URL('../web/single-image.js',import.meta.url),'utf8');
const calls=[];
const Controls=vm.runInNewContext(source.slice(source.indexOf('class SingleImageControls'),
    source.indexOf('export function renderSingleControls'))+';SingleImageControls',{
    crypto:{randomUUID:()=> 'request1'},active:job=>job?.state==='running',downloadProgress:()=>null,
    request:async(path,body)=>{calls.push({path,body});return {id:'job1'};},
    legacy:async(path,body)=>{calls.push({path,body});return {status:'running'};}
});
function controls() {
    const c=Object.create(Controls.prototype);
    Object.assign(c,{project:{id:'project1',revision:3},refresh:async()=>{},render:()=>{},
        status:()=>{},poll:async()=>{},downloadModels:async()=>true,
        resources:{download:{status:'failed',request:{kind:'models',asset_id:'project1',stage:'mesh'}}}});
    return c;
}
{
    const c=controls();c.downloadModels=async()=>false;
    const before=calls.length;
    await assert.rejects(c.start('create_image'),/download|model/i);
    assert.equal(calls.length,before,'A missing model must open setup before a generation job is submitted');
}
{
    const c=controls(),stages=[];
    c.downloadModels=async stage=>{stages.push(stage);return true;};
    await c.start('build_mesh_package');
    assert.deepEqual(stages,['image','mesh'],'A package needs both image and reconstruction dependencies');
    const call=calls.at(-1);
    assert.equal(call.body.kind,'build_mesh_package');
    assert.equal(call.body.expected_revision,3);
}
{
    const c=controls();
    assert.equal(typeof c.retryDownload,'function','The actual recovery control needs an owned retry action');
    await c.retryDownload();
    assert.equal(calls.at(-1).path,'/assets/project1/download');
    assert.equal(calls.at(-1).body.retry,true);
    assert.equal(calls.at(-1).body.accept_licenses,true);
    c.project.id='other';
    const before=calls.length;
    await assert.rejects(c.retryDownload(),/job/i);
    assert.equal(calls.length,before,'Retry must not send a different job to the downloader');
}
{
    const c=controls();let action;
    c.resources.download.request={kind:'description',asset_id:'project1',action:'enhance'};
    c.describe=async value=>{action=value;};
    await c.retryDownload();
    assert.equal(action,'enhance','Assistant recovery must preserve the original action');
}
{
    const c=controls();let message='Downloading';
    Object.assign(c,{resourceNode:{},downloadNode:{},lastDownloadStatus:'running',
        updateDownloadRecovery:()=>{},status:text=>{message=text;}});
    c.resources={ram_used:0,ram_total:1,vram_used:0,vram_total:1,cpu_percent:0,download:{status:'complete'}};
    c.updateResources();
    assert.match(message,/ready|finished/i,'A finished transfer must not leave the user waiting on a stale downloading notice');
    assert.match(c.downloadNode.textContent,/ready|finished/i);
}
console.log('Missing-model setup, dependency stages, owned download retry, and helper retry passed.');
