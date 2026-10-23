import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import vm from "node:vm";

const source=readFileSync(new URL("../web/creator.js",import.meta.url),"utf8");
const start=source.indexOf("        field(label,");
const end=source.indexOf("        select(",start);
const view={id:"view_07",enabled:true};
const writes=[];
const owner=vm.runInNewContext(`({
    asset:{id:"saved-job",views:[view]},
    changed(){},updateMeshButtons(){},
    persistSelection(item){writes.push({id:item.id,enabled:item.enabled});return Promise.resolve();},
    status(message){throw Error(message);},
    ${source.slice(start,end)}
})`,{view,writes,el:(tag,props,...children)=>({tag,props,children})});
const label=owner.field("Include in mesh",view,"enabled","checkbox");
label.children[0][0].props.oninput({target:{checked:false}});
assert.equal(writes.length,1,"Unchecking a view must save the exclusion without another generation or navigation");
assert.equal(writes[0].enabled,false);
const lora={enabled:true};
owner.field("Use LoRA",lora,"enabled","checkbox").children[0][0].props.oninput({target:{checked:false}});
assert.equal(writes.length,1,"A LoRA checkbox is not a mesh selection");
owner.asset.id=null;
label.children[0][0].props.oninput({target:{checked:true}});
assert.equal(writes.length,1,"Do not create a job just by checking an empty draft");
const saveStart=source.indexOf("        async persistSelection(");
const saveEnd=source.indexOf("        async persist() {",saveStart);
const requests=[];
let release;
const pending=new Promise(resolve=>{release=resolve;});
const saver=vm.runInNewContext(`({
    asset:{id:"saved-job",prompt:"Unsaved description",selected_export:"old-export"},historyLoaded:true,
    properties:{tab:"Views"},
    ${source.slice(saveStart,saveEnd)}
})`,{request:async(path,patch,method)=>{
    requests.push({path,patch,method});
    if(requests.length===1) await pending;
    return {masters:[{id:"old-master",stale:true}],exports:[{id:"old-export",stale:true}],
        selected_master:null,selected_export:null,prompt:"Older description"};
}});
const first=saver.persistSelection({id:"view_07",enabled:false});
await new Promise(resolve=>setImmediate(resolve));
const second=saver.persistSelection({id:"view_07",enabled:true});
await new Promise(resolve=>setImmediate(resolve));
assert.equal(requests.length,1,"Rapid selection changes must be saved in order");
release();
await Promise.all([first,second]);
assert.deepEqual(JSON.parse(JSON.stringify(requests.map(r=>r.patch))),[
    {view_selection:{view_07:false}},{view_selection:{view_07:true}},
],"Selection saves must not overwrite current images, prompts or settings");
assert.equal(saver.historyLoaded,false);
assert.equal(saver.asset.selected_export,null,"A changed selection must retire the displayed export immediately");
assert.equal(saver.asset.exports[0].stale,true);
assert.equal(saver.asset.prompt,"Unsaved description","Selection response must preserve unrelated draft inputs");
console.log("Immediate mesh selection persistence passed.");
