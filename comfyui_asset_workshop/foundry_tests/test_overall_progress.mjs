import {test} from 'node:test';
import assert from 'node:assert/strict';
import {overallProgress} from '../web/foundry/overall-progress.js';
test('node progress resets cannot reset overall progress or finish the whole run',()=>{
    const p={total:3,stages:['texture','package','cleanup'],completed:[],current:'texture'};
    const a=overallProgress(p,1);
    assert.ok(a<1/3);assert.equal(overallProgress(p,.1,a),a);
    p.completed=['texture','package'];p.current='cleanup';
    assert.ok(overallProgress(p,1)<1);assert.equal(overallProgress(p,0,0,true),1);
});
