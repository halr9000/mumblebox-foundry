import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
const source=readFileSync(new URL('../web/single-image.js',import.meta.url),'utf8');
let resolveRead;
const Controls=vm.runInNewContext(source.slice(source.indexOf('class SingleImageControls'),source.indexOf('export function renderSingleControls'))+';SingleImageControls',{
    active:()=>false,legacy:async()=>({}),request:()=>new Promise(resolve=>{resolveRead=resolve;})
});
const c=Object.create(Controls.prototype);
Object.assign(c,{root:{isConnected:true,querySelector:()=>null},civitai:{async poll(){}},updateResources(){},render(){},project:{id:'old',revision:1},job:null});
let pending=c.poll();await new Promise(setImmediate);
c.project={id:'opened-from-history',revision:2};resolveRead({id:'old',revision:3,jobs:[]});await pending;
assert.equal(c.project.id,'opened-from-history','A delayed poll must never reopen the previous job');
pending=c.poll();await new Promise(setImmediate);
c.project.revision=5;resolveRead({id:'opened-from-history',revision:4,jobs:[]});await pending;
assert.equal(c.project.revision,5,'A stale poll must not undo a newer saved setting');
console.log('Polling retains the selected job and never replaces newer saved settings with an older response.');
