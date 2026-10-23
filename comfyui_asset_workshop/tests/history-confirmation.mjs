import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
let dialog;
const el=(tag,props={},...children)=>({tag,props,value:'',children:children.flat().filter(Boolean),close(){},showModal(){},addEventListener(){}});
const source=readFileSync(new URL('../web/single-image.js',import.meta.url),'utf8');
const Controls=vm.runInNewContext(source.slice(source.indexOf('class SingleImageControls'),source.indexOf('export function renderSingleControls'))+';SingleImageControls',{
    el,document:{body:{append(value){dialog=value;}}}
});
const c=Object.create(Controls.prototype);c.action=action=>action();let calls=0;
c.confirm('Clear all history?','Move saved jobs to trash.','Clear all history',()=>calls++,'DELETE HISTORY');
const input=dialog.children.find(e=>e.tag==='label').children.find(e=>e.tag==='input');
const proceed=dialog.children.find(e=>e.tag==='div').children.at(-1);
assert.equal(proceed.props.disabled,true);
proceed.props.onclick();assert.equal(calls,0,'A click cannot bypass the required phrase');
input.value='DELETE';input.oninput();assert.equal(proceed.disabled,true);
input.value='DELETE HISTORY';input.oninput();assert.equal(proceed.disabled,false);
proceed.props.onclick();assert.equal(calls,1);
console.log('Clearing all History requires the exact confirmation phrase before its action can execute.');
