import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
const source=readFileSync(new URL('../web/single-image.js',import.meta.url),'utf8');
const el=(tag,props,...children)=>({tag,props,children:children.flat()});
const Controls=vm.runInNewContext(source.slice(source.indexOf('class SingleImageControls'),source.indexOf('export function renderSingleControls'))+';SingleImageControls',{el,names:{design:'Chosen design'}});
const c=Object.create(Controls.prototype),writes=[];
c.project={images:{design:{current:null,revisions:[
    {id:'original'},
    {id:'pending',recipe:{edit:{source:{id:'original'}}}},
    {id:'old-preview',recipe:{edit:{source:{id:'older'}}}},
]}}};
c.current=()=>null;c.hint=text=>el('p',{},text);c.blocked=()=>'';c.url=r=>r.id;
c.link=(text,url)=>el('a',{url},text);
c.post=async(path,payload)=>writes.push({path,payload});
c.select=(label,options,value,change)=>({label,options,value,change});
c.button=(label,action)=>({label,action});
const restore=c.savedImages('design').children.find(e=>e?.options);
assert.deepEqual(Object.keys(restore.options),['','original'],'Unaccepted edits must not bypass preview review');
await restore.change('original');
assert.equal(writes[0].payload.revision_id,'original');
const previews=c.savedEdits('design',{id:'original'});
const article=previews.children.find(e=>e?.tag==='article');
assert.equal(previews.children.filter(e=>e?.tag==='article').length,1,'Only previews matching the current source can be kept');
const keep=article.children.find(e=>e?.tag==='div').children.find(e=>e?.label==='Keep this edit');
await keep.action();
assert.equal(writes[1].path,'/edits/accept');
assert.equal(writes[1].payload.revision_id,'pending');
console.log('Cleared-image recovery excludes unaccepted edits; saved previews keep their source guard.');
