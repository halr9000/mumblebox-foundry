import test from "node:test";
import assert from "node:assert/strict";
import {installOrbitInput} from "../web/foundry/wizard/preview.js";

function input(target,type,values={}){
    const event=new Event(type);Object.assign(event,values);target.dispatchEvent(event);
}
test("camera accepts drag and wheel but never idle or stale hover",async()=>{
    const surface=new EventTarget(),host=new EventTarget();
    const controls={enabled:true,autoRotate:true,enableDamping:true};
    const dispose=installOrbitInput(surface,controls,host);
    assert.equal(controls.enabled,false);
    assert.equal(controls.autoRotate,false);assert.equal(controls.enableDamping,false);
    input(surface,"pointermove",{pointerType:"mouse",buttons:0});
    assert.equal(controls.enabled,false);
    input(surface,"pointerdown",{pointerType:"mouse",button:0});
    assert.equal(controls.enabled,true);
    input(host,"pointerup");await new Promise(resolve=>setTimeout(resolve,5));
    assert.equal(controls.enabled,false);
    input(surface,"pointerdown",{pointerType:"mouse",button:0});
    input(surface,"pointermove",{pointerType:"mouse",buttons:0});
    assert.equal(controls.enabled,false,"a missed pointer-up must not turn hover into drag");
    input(surface,"wheel");assert.equal(controls.enabled,true);
    await new Promise(resolve=>setTimeout(resolve,5));assert.equal(controls.enabled,false);
    dispose();input(surface,"pointerdown",{pointerType:"mouse",button:0});
    assert.equal(controls.enabled,false,"disposed previews must not keep listeners");
});
