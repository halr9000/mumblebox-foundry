import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import vm from "node:vm";

const source=readFileSync(new URL("../web/creator.js",import.meta.url),"utf8");
const methods=source.slice(source.indexOf("        async waitForCancellation("),source.indexOf("        async stop()"));
const states=[
    {resource_cleanup:{pending_jobs:1,status:"releasing"}},
    {resource_cleanup:{pending_jobs:1,status:"releasing"}},
    {resource_cleanup:{pending_jobs:0,status:"released"}},
];
let reads=0;
const controller=vm.runInNewContext(`new (class { updateProgress(){} ${methods} })`,{
    api:{getQueue:async()=>({Running:[],Pending:[]})},
    request:async()=>states[Math.min(reads++,2)],sleep:async()=>{},
});
await controller.waitForCancellation({promptId:"ours",cancelled:true});
assert.equal(reads,3,"Stop must retain ownership until backend memory recovery finishes, even after the prompt leaves the queue");
assert.equal(controller.server.resource_cleanup.status,"released");
console.log("Cancellation waits for backend resource recovery.");
