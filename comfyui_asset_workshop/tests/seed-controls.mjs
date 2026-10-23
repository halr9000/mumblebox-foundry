import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
const source=readFileSync(new URL('../web/single-image.js',import.meta.url),'utf8');
let copied;
const Controls=vm.runInNewContext(source.slice(source.indexOf('class SingleImageControls'),source.indexOf('export function renderSingleControls'))+';SingleImageControls',{
    crypto:{getRandomValues:array=>{array[0]=987654;return array;}},Uint32Array,
    navigator:{clipboard:{writeText:async value=>{copied=value;}}}
});
const c=Object.create(Controls.prototype);
c.project={settings:{requested_seed:-1,seed_mode:'randomize'},images:{design:{revisions:[{created:1,recipe:{seed:42}}]},mesh_input:{revisions:[]}}};
c.save=async changes=>Object.assign(c.project.settings,changes.settings);
c.status=()=>{};
assert.equal(typeof c.setSeedMode,'function','Seed modes must be explicit and saved');
await c.setSeedMode('fixed');assert.equal(c.project.settings.requested_seed,42);
assert.equal(c.project.settings.seed_mode,'fixed');
await c.shuffleSeed();assert.equal(c.project.settings.requested_seed,987654);assert.equal(c.project.settings.seed_mode,'fixed');
await c.copySeed();assert.equal(copied,'987654');
await c.setSeedMode('randomize');assert.equal(c.project.settings.requested_seed,-1);
assert.equal(c.project.settings.seed_mode,'randomize');
c.project.images.design.revisions.push({created:2,recipe:{seed:0}});
await c.reuseLastSeed();assert.equal(c.project.settings.requested_seed,0,'Zero is a valid actual seed');
assert.equal(c.project.settings.seed_mode,'fixed');
c.project.images.design.revisions=[];c.project.settings.requested_seed=-1;
await c.setSeedMode('fixed');assert.equal(c.project.settings.requested_seed,987654,'Lock before first generation chooses a real valid seed');
console.log('Seed modes, shuffle without generation, reuse including zero, and copy passed.');
