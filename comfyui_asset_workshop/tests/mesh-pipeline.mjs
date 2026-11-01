import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url),{chromium}=require('playwright');
const source=readFileSync(new URL('../web/mesh-pipeline.js',import.meta.url),'utf8').replace(/^import .*;$/gm,'').replaceAll('export ','');
const browser=await chromium.launch({headless:true,channel:process.env.FOUNDRY_BROWSER_CHANNEL||"chrome"});
try{
 const page=await browser.newPage();await page.goto('about:blank');
 await page.addScriptTag({content:`const request=async(...args)=>{window.calls.push(args);return window.project;};const openMaterialLab=()=>{};`+source+`
 window.calls=[];window.starts=[];window.project={id:'p1',revision:1,artifacts:[],images:{mesh_input:{approved:null}},target:{user_instructions:''}};
 const el=(tag,attrs={},...children)=>{const e=document.createElement(tag);Object.assign(e,attrs);e.append(...children.flat().filter(c=>c!=null));return e;};
 const c={project:window.project,capabilities:{pipeline:{providers:{trellis2:{available:true,label:'TRELLIS.2'},pixal3d:{available:false,label:'Pixal3D',reason:'Not qualified'}}}},blocked:()=>'',imageBlocked:()=>'',current:()=>null,hint:t=>el('p',{},t),panel:(t,d,...more)=>el('section',{},el('h2',{},t),d,...more),disclosure:(t,...more)=>el('details',{},el('summary',{},t),...more),grid:(n,...more)=>el('div',{},...more),input:()=>el('input'),select:(label,values,value,change)=>{const s=el('select',{'ariaLabel':label});for(const [v,t]of Object.entries(values))s.append(el('option',{value:v},t));s.value=value;s.onchange=()=>change(s.value);return el('label',{},label,s);},button:(label,click,reason='')=>el('button',{disabled:!!reason,onclick:click},label),start:(...args)=>starts.push(args),path:s=>'/projects/p1'+s,text:()=>el('textarea'),link:(t)=>el('a',{},t)};
 window.c=c;renderMeshPipeline(c,document.body,el);`});
 const headings=await page.locator('h2').allTextContents();assert.deepEqual(headings,['Build your asset','Texture the finished mesh','Output detail','Materials Lab (optional)','Export asset']);
 assert.equal(await page.getByRole('button',{name:'Proceed with Texturing',exact:true}).isDisabled(),true);
 assert.equal(await page.locator('option[value=pixal3d]').evaluate(e=>e.disabled),true);
 await page.getByLabel('Output detail',{exact:true}).selectOption('compact_100k');
 assert.equal(await page.evaluate(()=>starts.length),0,'Changing a preset must never launch generation');
 assert.deepEqual(await page.evaluate(()=>calls[0][1].changes),{output_variant:'compact_100k'});
 await page.evaluate(async()=>{window.project=c.project={id:'p1',revision:2,pipeline:{settings:{output_variant:'detailed'},selected_texture_id:'t1'},artifacts:[{id:'t1',kind:'mesh',variant:'detailed'}]};await prepareVariant(c);});
 assert.equal(await page.evaluate(()=>calls.at(-1)[1].artifact_id),'t1','Preparing detailed must select its saved original');
 assert.equal(await page.evaluate(()=>starts.length),0,'Saved detailed output is selected without generation');
 await page.evaluate(async()=>{c.project.pipeline.settings.output_variant='balanced_250k';await prepareVariant(c);});
 assert.deepEqual(await page.evaluate(()=>starts[0]),['prepare_variant',{source_id:'t1',variant:'balanced_250k'}]);
 console.log('Current pipeline placement, unavailable provider, disabled stale actions and preference-only detail change pass.');
}finally{await browser.close();}
