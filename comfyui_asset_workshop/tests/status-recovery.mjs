import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import vm from "node:vm";

const source=readFileSync(new URL("../web/creator.js",import.meta.url),"utf8");
const method=source.slice(source.indexOf("        async refreshStatus()"),source.indexOf("        updateProgress()"));
let jobStatus="complete";
const instance=vm.runInNewContext(`new(class {
    graph={};asset={id:"saved"};lastJob="one";messageError=true;
    message="The next stage failed to save.";
    updateProgress(){} mergeResults(){} render(){}
    status(text,error){this.message=text;this.messageError=error;}
    ${method}
})`,{document:{hidden:false},operation:()=>null,terminal:new Set(["failed"]),
    request:async path=>path==="/status"?{running:false}:{jobs:[{id:"one",status:jobStatus,error:"Actual stage failed"}]}});
await instance.refreshStatus();
assert.equal(instance.message,"The next stage failed to save.","A completed earlier job must not erase the batch error");
assert.equal(instance.lastJob,null);
instance.lastJob="one";instance.messageError=false;
await instance.refreshStatus();
assert.equal(instance.message,"Finished. Your result has been saved.");
instance.lastJob="one";jobStatus="failed";
await instance.refreshStatus();
assert.equal(instance.message,"Actual stage failed");
assert.equal(instance.messageError,true);
console.log("Completed stages retain later batch errors; real failures remain visible.");

const waitMethod=source.slice(source.indexOf("        async waitForJob(op)"),source.indexOf("        async generateImage("));
const recovered=vm.runInNewContext(`new(class {
    asset={id:"saved"};lastJob="one";merged=null;
    async readWhileWorking(path){return path==="/status"
        ?{running:false,resource_cleanup:{status:"failed",error:"Release failed"}}
        :{id:"saved",views:[{current:"new-result"}],jobs:[{id:"one",status:"complete"}]};}
    mergeResults(asset){this.merged=asset;} changed(){} render(){} updateProgress(){}
    ${waitMethod}
})`,{sleep:async()=>{},terminal:new Set(["failed"])});
await assert.rejects(()=>recovered.waitForJob({}),/Release failed/);
assert.equal(recovered.merged?.views[0].current,"new-result","Cleanup failure must not discard a saved image before final persistence");
assert.equal(recovered.lastJob,null);
console.log("Saved result survives a later cleanup failure.");
