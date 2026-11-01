import assert from 'node:assert/strict';
import {initialState,retainSession,copyRunConfiguration} from '../web/foundry/wizard/session.js';
const saved={page:5,runId:'finished',draft:{name:'Alien',references:[{filename:'alien.png'}]}};
const fresh=initialState(saved);
assert.equal(fresh.page,1);assert.equal(fresh.runId,null);assert.equal(fresh.draft.name,'');
assert.equal(saved.page,5);assert.equal(saved.draft.references.length,1);
const resumed=initialState(saved,true);resumed.draft.name='Changed';assert.equal(saved.draft.name,'Alien');
assert.equal(initialState(saved,true).runId,'finished');
assert.equal(retainSession([],saved)[0].runId,'finished');
assert.equal(retainSession([saved],fresh).length,1);
assert.equal(retainSession([saved],saved).length,1);
console.log('Fresh sessions, explicit resume, independent copies and preservation passed.');

// Saved runs from before model selection have no turnaround_model field.
const defaults={...initialState().draft,selection:{variants:{game_compact:{formats:['glb']}}}};
const legacy={name:'Legacy asset',references:[{filename:'reference.png'}],category:'characters',overrides:{refine:false}};
const restored=copyRunConfiguration(defaults,legacy);
assert.equal(restored.turnaround_model,'qwen21');
assert.equal(restored.name,'Legacy asset');
assert.equal(restored.overrides.refine,false);
restored.references[0].filename='changed.png';
assert.equal(legacy.references[0].filename,'reference.png');
assert.equal(defaults.references.length,0);
const modern=copyRunConfiguration(defaults,{...legacy,turnaround_model:'qwen_edit_2511'});
assert.equal(modern.turnaround_model,'qwen_edit_2511');
console.log('Legacy agent-opened runs retain missing-field defaults and independent input copies.');