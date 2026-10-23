import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import vm from "node:vm";

const source=readFileSync(new URL("../web/creator.js",import.meta.url),"utf8");
const start=source.indexOf("        async mountViewer(");
const end=source.indexOf("        renderResult(",start);
let active=false;
const viewer={
    setLightIntensity() {}, handleResize() {}, fitToViewer() {}, forceRender() {}, remove() {},
    updateStatusMouseOnViewer(value) {active=value;},
    async loadModel() {}, getCurrentModel:()=>({}),
};
const container=new EventTarget();
container.isConnected=true;
container.matches=()=>false;
container.replaceChildren=()=>assert.fail("The viewer should load successfully");
const context={
    window:{comfyAPI:{createLoad3d:{createLoad3d:()=>viewer}}},
    ResizeObserver:class {observe() {}},
    request:async()=>({url:"local-preview.glb"}),
};
const owner=vm.runInNewContext(`({asset:{id:"asset"},${source.slice(start,end)}})`,context);
await owner.mountViewer(container,{id:"export"});
container.dispatchEvent(new Event("pointerenter"));
assert.equal(active,true,"Hovering the preview must activate native rendering during drag and zoom");
container.dispatchEvent(new Event("pointerleave"));
assert.equal(active,false,"Leaving the preview must release idle rendering");
container.matches=()=>true;
await owner.mountViewer(container,{id:"export"});
assert.equal(active,true,"A preview mounted beneath the pointer must already be active");
console.log("Native viewer hover activation and idle release passed.");
