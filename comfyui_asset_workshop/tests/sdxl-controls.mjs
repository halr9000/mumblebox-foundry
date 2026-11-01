import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const source=readFileSync(new URL('../web/single-image.js',import.meta.url),'utf8');
const Controls=vm.runInNewContext(source.slice(source.indexOf('class SingleImageControls'),
    source.indexOf('export function renderSingleControls'))+';SingleImageControls',{
    active:job=>job?.state==='running',crypto:{randomUUID:()=> 'request1'},clone:value=>JSON.parse(JSON.stringify(value)),
    request:async()=>({id:'job1'})
});
function controls(profile='sdxl_base') {
    const c=Object.create(Controls.prototype);
    Object.assign(c,{project:{id:'project1',revision:1,profile,prompt:'my asset',loras:[],settings:{sdxl_negative_prompt:'extra handles'}},
        capabilities:{profiles:{sdxl_base:{lora:{architecture:'sdxl'}},sdxl_juggernaut:{lora:{architecture:'sdxl'}},
            klein4:{lora:{architecture:'klein4'}}}},loraList:{files:['local.safetensors','sdxl-style','klein-style','unknown'],
            items:[{name:'sdxl-style',profiles:['sdxl_base','sdxl_juggernaut']},{name:'klein-style',profiles:['klein4']},{name:'unknown',profiles:[]}],
            downloadable:[{name:'sdxl-pixel-art-xl.safetensors',family:'sdxl',profiles:['sdxl_base','sdxl_juggernaut'],trigger:'pixel art'}]},
        refresh:async()=>{},status:()=>{},render:()=>{}});
    return c;
}
{
    const c=controls();
    c.project.loras=[{profile:'sdxl_juggernaut',enabled:true,strength:.8,name:'sdxl-style'}];
    assert.equal(c.imageBlocked(),'','The other SDXL checkpoint must accept an SDXL-declared LoRA');
    c.project.loras[0].name='klein-style';
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
    assert.deepEqual(Object.keys(c.loraOptions()),['klein-style']);
    c.project.loras=[{profile:'klein4',enabled:true,strength:1,name:'sdxl-style'}];
    assert.match(c.imageBlocked(),/saved LoRA/,'Declaring an SDXL file as Klein must not bypass filtering');
    assert.equal(c.loraOptions().unknown,undefined,'Unknown files must be withheld');
}
{
    const c=controls();c.save=async changes=>Object.assign(c.project,changes);
    await Promise.all([c.setLoraEnabled('sdxl-style',true),c.setLoraEnabled('sdxl-pixel-art-xl.safetensors',true)]);
    assert.equal(c.project.loras.length,2);assert.ok(c.project.loras.every(item=>item.enabled));
    c.project.loras[1].strength=.35;
    await c.setLoraEnabled('sdxl-style',false);
    assert.equal(c.project.loras.filter(item=>item.enabled).length,1);assert.equal(c.project.loras[1].strength,.35,'Unchecking one LoRA must preserve the other settings');
    await c.setLoraEnabled('sdxl-style',true);
    assert.equal(c.project.loras.length,2,'Rechecking must reuse the saved settings rather than duplicate the LoRA');
    await c.selectImageProfile('klein4');
    assert.ok(c.project.loras.every(item=>!item.enabled),'Changing model must turn off incompatible saved LoRAs');
    assert.equal(c.project.loras[1].strength,.35,'Keep saved settings when switching models');
    await assert.rejects(()=>c.setLoraEnabled('sdxl-style',true),/compatible/);
}
{
    const c=controls(),checked=[];
    c.downloadModels=async(stage,action)=>{checked.push({stage,action});return true;};
    await c.start('three_quarter');
    assert.equal(checked[0].stage,'image');
    assert.equal(checked[0].action,'three_quarter','Implicit chosen-image references need adapter dependency checks too');
}
console.log('SDXL family LoRA controls, sampling reset, optional downloads and exact first-use task passed.');
