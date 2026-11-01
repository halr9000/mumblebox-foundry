import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const source=readFileSync(new URL('../web/single-image.js',import.meta.url),'utf8');
let requests=0,reply;
const Controls=vm.runInNewContext(source.slice(source.indexOf('class SingleImageControls'),source.indexOf('export function renderSingleControls'))+';SingleImageControls',{
    active:job=>['queued','running'].includes(job?.state),
    request:async()=>{requests++;return reply();}
});
const deferred=()=>{let resolve,reject;const promise=new Promise((yes,no)=>{resolve=yes;reject=no;});return {promise,resolve,reject};};
function controls() {
    const c=Object.create(Controls.prototype);
    Object.assign(c,{project:{id:'test',revision:1,prompt:'original'},helperBusy:false,
        workingNode:{dataset:{}},workingLabel:{},resources:{},civitai:{download:{status:'idle'}},
        render(){this.updateWorkingIndicator();},updateDescriptionStatus(){},
        save:async changes=>{Object.assign(c.project,changes);}});
    return c;
}
{
    const c=controls(),saving=deferred(),response=deferred();requests=0;
    c.saveQueue=saving.promise;reply=()=>response.promise;
    const first=c.describe('enhance'),duplicate=c.describe('enhance');
    await duplicate;assert.equal(requests,0,'Description must await pending edits');
    assert.equal(c.helperBusy,true);assert.match(c.workingLabel.textContent,/Enhancing/);
    c.project.prompt='latest edit';saving.resolve();await Promise.resolve();await Promise.resolve();
    assert.equal(requests,1,'Repeated Enhance clicks must not start another request');
    response.resolve({text:'enhanced',input_revision:1});await first;
    assert.equal(c.project.prompt,'enhanced');assert.equal(c.descriptionUndo.previous,'latest edit');
    assert.equal(c.helperBusy,false);assert.equal(c.workingNode.dataset.busy,'false');
    assert.match(c.descriptionMessage.text,/updated/);
}
{
    const c=controls();reply=async()=>{throw Error('Download failed. Connect Hugging Face.');};
    await assert.rejects(()=>c.describe('enhance'),/Download failed/);
    assert.equal(c.project.prompt,'original');assert.equal(c.descriptionMessage.error,true);
    assert.match(c.descriptionMessage.text,/Connect Hugging Face/);assert.equal(c.helperBusy,false);
    reply=async()=>{throw Error('Description assistant stopped');};
    await c.describe('enhance');assert.equal(c.project.prompt,'original');assert.match(c.descriptionMessage.text,/Stopped/);
}
{
    const c=controls(),pending=deferred();let starts=0;
    c.root={querySelectorAll:()=>[]};c.start=async()=>{starts++;await pending.promise;};
    const first=c.generateImage();await c.generateImage();assert.equal(starts,1,'Both Generate actions share one request guard');
    pending.resolve();await first;assert.equal(c.generatingImage,false);
    c.start=async()=>{throw Error('Failed');};await assert.rejects(()=>c.generateImage(),/Failed/);
    assert.equal(c.generatingImage,false,'Failed preflight must release the button guard');
}
{
    const c=controls();c.updateWorkingIndicator();assert.equal(c.workingNode.dataset.busy,'false');
    c.resources.download={status:'running'};c.generatingImage=true;c.updateWorkingIndicator();
    assert.equal(c.workingLabel.textContent,'Downloading asset…','Download takes precedence over a pending generation');
    c.resources.download.status='complete';c.generatingImage=false;
    for(const [kind,phase,label] of [
        ['create_image','1/1: design image','Rendering image…'],
        ['build_mesh_package','1/6: mesh','Rendering mesh…'],
        ['build_mesh_package','3/6: reference_front','Rendering image…'],
        ['finish_mesh','1/1: GPU finishing','Finishing mesh…'],
        ['build_mesh_package','6/6: export package','Exporting assets…']]) {
        c.job={kind,phase,state:'running'};c.updateWorkingIndicator();assert.equal(c.workingLabel.textContent,label);
    }
    c.job.state='failed';c.updateWorkingIndicator();assert.equal(c.workingNode.dataset.busy,'false');
    c.civitai.download.status='running';c.updateWorkingIndicator();assert.equal(c.workingLabel.textContent,'Downloading asset…');
    c.civitai.download.status='completed';c.updateWorkingIndicator();assert.equal(c.workingNode.dataset.busy,'false');
}
console.log('UI activity: pending edits, duplicate requests, inline success/error/cancellation, and truthful stage/idle states passed.');
