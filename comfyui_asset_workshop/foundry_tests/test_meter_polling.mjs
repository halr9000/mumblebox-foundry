import {test} from 'node:test';
import assert from 'node:assert/strict';
import {pollResources} from '../web/foundry/services.js';

test('polls every second without overlapping and backs off when offline',async()=>{
    const old={fetch:globalThis.fetch,setTimeout:globalThis.setTimeout,clearTimeout:globalThis.clearTimeout};
    const timers=[];let resolve,requests=0;
    globalThis.setTimeout=(fn,ms)=>{const timer={fn,ms};timers.push(timer);return timer;};
    globalThis.clearTimeout=()=>{};
    globalThis.fetch=()=>{requests++;return new Promise(r=>resolve=r);};
    try{
        const stop=pollResources(()=>{},()=>{});
        assert.equal(requests,1);assert.equal(timers.filter(t=>t.ms===1000).length,0);
        resolve({ok:true,json:async()=>({cpu_percent:12})});
        await new Promise(r=>setImmediate(r));
        const next=timers.find(t=>t.ms===1000);assert.ok(next);
        globalThis.fetch=async()=>{throw Error('offline');};await next.fn();
        assert.ok(timers.some(t=>t.ms===2000));
        stop();await timers.find(t=>t.ms===2000).fn();
        // A disposed timer should never issue another request.
    }finally{Object.assign(globalThis,old);}
});
