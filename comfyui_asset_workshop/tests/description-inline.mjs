import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
const source=readFileSync(new URL('../web/single-image.js',import.meta.url),'utf8');
const Controls=vm.runInNewContext(source.slice(source.indexOf('class SingleImageControls'),source.indexOf('export function renderSingleControls'))+';SingleImageControls',{
    request:async()=>({text:'one detailed toy fish',input_revision:4})
});
const c=Object.create(Controls.prototype);
c.project={id:'current',prompt:'toy fish',revision:4};c.path=()=>'/describe';c.render=()=>{};c.status=()=>{};
c.save=async(changes,revision)=>{assert.equal(revision,4);Object.assign(c.project,changes);};
await c.describe('enhance');
assert.equal(c.project.prompt,'one detailed toy fish','Enhance must replace the description without an acceptance dialog');
assert.equal(c.descriptionUndo.previous,'toy fish');
assert.equal(c.descriptionUndo.enhanced,c.project.prompt);
assert.equal(c.descriptionUndo.projectId,c.project.id);
assert.equal(c.helperBusy,false);
console.log('Description enhancement applies inline and retains the previous text for Undo.');
