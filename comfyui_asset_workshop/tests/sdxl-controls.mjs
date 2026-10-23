import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const source=readFileSync(new URL('../web/single-image.js',import.meta.url),'utf8');
const Controls=vm.runInNewContext(source.slice(source.indexOf('class SingleImageControls'),
    source.indexOf('export function renderSingleControls'))+';SingleImageControls',{
    active:job=>job?.state==='running',crypto:{randomUUID:()=> 'request1'},
    request:async()=>({id:'job1'})
});
function controls(profile='sdxl_base') {
    const c=Object.create(Controls.prototype);
    Object.assign(c,{project:{id:'project1',revision:1,profile,prompt:'my asset',loras:[],settings:{sdxl_negative_prompt:'extra handles'}},
        capabilities:{profiles:{sdxl_base:{lora:{architecture:'sdxl'}},sdxl_juggernaut:{lora:{architecture:'sdxl'}},
            klein4:{lora:{architecture:'klein4'}}}},loraList:{files:['local.safetensors'],
            downloadable:[{name:'sdxl-pixel-art-xl.safetensors',family:'sdxl',trigger:'pixel art'}]},
        refresh:async()=>{},status:()=>{},render:()=>{}});
    return c;
}
{
    const c=controls();
    c.project.loras=[{profile:'sdxl_juggernaut',enabled:true,strength:.8,name:'style'}];
    assert.equal(c.imageBlocked(),'','The other SDXL checkpoint must accept an SDXL-declared LoRA');
    c.project.loras[0].profile='klein4';
    assert.match(c.imageBlocked(),/LoRA/);
}
{
    const c=controls();let saved;
    c.save=async changes=>{saved=changes;};
    assert.equal(typeof c.resetModelDefaults,'function');
    await c.resetModelDefaults();
    assert.equal(saved.settings.steps,null);
    assert.equal(saved.settings.cfg,null);
    assert.equal(saved.settings.sdxl_sampler,'dpmpp_2m');
    assert.equal(saved.settings.sdxl_reference_strength,.8);
    assert.equal(saved.settings.sdxl_negative_prompt,undefined,'Sampling reset must preserve the user-written negative prompt');
    assert.equal(c.project.prompt,'my asset');
}
{
    const c=controls();
    assert.equal(typeof c.loraOptions,'function');
    assert.match(c.loraOptions()['sdxl-pixel-art-xl.safetensors'],/download/i);
    c.project.profile='klein4';
    assert.equal(c.loraOptions()['sdxl-pixel-art-xl.safetensors'],undefined,'An SDXL download must not be offered for Klein');
}
{
    const c=controls(),checked=[];
    c.downloadModels=async(stage,action)=>{checked.push({stage,action});return true;};
    await c.start('three_quarter');
    assert.equal(checked[0].stage,'image');
    assert.equal(checked[0].action,'three_quarter','Implicit chosen-image references need adapter dependency checks too');
}
console.log('SDXL family LoRA controls, sampling reset, optional downloads and exact first-use task passed.');
