import assert from 'node:assert/strict';
import {test} from 'node:test';
const behavior = await import('../web/foundry/activity-state.js').catch(() => ({}));

test('download completion stops activity without treating downloaded files as loaded models', () => {
    assert.equal(typeof behavior.activityState, 'function');
    assert.equal(behavior.activityState({download:{status:'running',name:'Qwen'}}).busy,true);
    assert.equal(behavior.activityState({download:{status:'completed'}}).busy,false);
    assert.equal(behavior.loadedState({download:{status:'completed'}}).state,'unknown');
});
test('loaded indicator uses explicit residency and never assumes failed polling means empty', () => {
    assert.equal(typeof behavior.loadedState, 'function');
    assert.equal(behavior.loadedState({loaded_models:2}).state,'loaded');
    assert.equal(behavior.loadedState({loaded_models:0}).state,'empty');
    assert.equal(behavior.loadedState(null).state,'unknown');
    assert.equal(behavior.loadedState({loaded_models:0,helper_loaded:true}).state,'loaded');
});
test('work and model release keep feedback active, interrupted downloads need attention', () => {
    assert.equal(typeof behavior.activityState, 'function');
    assert.equal(behavior.activityState({running:true}).busy,true);
    assert.equal(behavior.activityState({resource_cleanup:{status:'releasing'}}).busy,true);
    const paused=behavior.activityState({download:{status:'paused'}});
    assert.equal(paused.busy,false);
    assert.match(paused.label,/paused/i);
    const failed=behavior.activityState({download:{status:'failed',error:'Connection lost'}});
    assert.equal(failed.busy,false);
    assert.match(failed.label,/Connection lost/);
});
test('meters reject missing and invalid totals rather than drawing an invented zero', () => {
    assert.equal(typeof behavior.utilization, 'function');
    assert.equal(behavior.utilization(8,16),.5);
    assert.equal(behavior.utilization(30,16),1);
    assert.equal(behavior.utilization(undefined,16),null);
    assert.equal(behavior.utilization(0,0),null);
});
