import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
const {chromium}=createRequire(import.meta.url)('playwright');
const css=readFileSync(new URL('../web/creator.css',import.meta.url),'utf8')+'\n'+readFileSync(new URL('../web/single-image.css',import.meta.url),'utf8');
const browser=await chromium.launch({headless:true,channel:'chrome'});
try{const page=await browser.newPage({viewport:{width:1280,height:863}});await page.route('https://foundry.test/**',r=>r.fulfill({contentType:'text/html',body:'<!doctype html><html><body></body></html>'}));await page.goto('https://foundry.test/');await page.setContent('<dialog class="aw aw-material-dialog"><div class="aw-material-bar"><strong>Materials Lab</strong><span role="status">Saved</span><button>Save & Close</button></div><iframe title="Materials Lab"></iframe></dialog>');await page.addStyleTag({content:css});await page.evaluate(()=>document.querySelector('dialog').showModal());
const dimensions=await page.evaluate(()=>({dialog:document.querySelector('dialog').getBoundingClientRect().height,iframe:document.querySelector('iframe').getBoundingClientRect().height,viewport:innerHeight}));
assert.ok(dimensions.dialog>dimensions.viewport*.8,'Material dialog must remain a full workspace under the existing dialog CSS');assert.ok(dimensions.iframe>dimensions.viewport*.7,'3D editor must have a usable canvas height');
console.log('Materials Lab dialog remains a full workspace with existing styles.');
await page.evaluate(()=>document.querySelector('dialog').remove());
const host=readFileSync(new URL('../web/material-lab-host.js',import.meta.url),'utf8').replace(/^import .*;$/gm,'').replace('export async function','async function');
await page.addScriptTag({content:`const PREFIX='/asset-workshop/v2';window.attempts=0;window.paths=[];const request=async(path,body,method)=>{paths.push(path);if(method==='PATCH'){window.attempts++;if(attempts===1)throw Error('Save temporarily failed');return {...window.session,draft_revision:1,draft:body.state};}return window.session;};`+host+`
window.session={id:'a'.repeat(24),state:'ready',variant:'detailed',draft_revision:0,draft:{version:1,regions:[]}};
window.c={project:{id:'p1',revision:1,pipeline:{settings:{guide_size:1024,palette_count:12}}},refresh:async()=>{},render:()=>{}};
openMaterialLab(c,{id:'mesh1'});`});
await page.getByRole('button',{name:'Save & Close',exact:true}).waitFor();
await page.evaluate(()=>{const f=document.querySelector('iframe'),q=new URL(f.src).searchParams;window.dispatchEvent(new MessageEvent('message',{origin:location.origin,source:f.contentWindow,data:{type:'material-editor-save',project:'p1',session:session.id,nonce:q.get('nonce'),state:{version:1,regions:[]}}}));});
await page.waitForFunction(()=>document.querySelector('.aw-material-bar span').textContent==='Save temporarily failed');
await page.getByRole('button',{name:'Save & Close',exact:true}).click();
await page.waitForFunction(()=>!document.querySelector('.aw-material-dialog'),null,{timeout:1500});
assert.equal(await page.evaluate(()=>attempts),2,'Retry must save the preserved draft before closing');
console.log('A failed draft save retains the editor and retries successfully.');
await page.evaluate(()=>{paths.length=0;openMaterialLab(c,{id:'edited1',material_session_id:session.id});});
await page.getByRole('button',{name:'Save & Close',exact:true}).waitFor();
assert.ok((await page.evaluate(()=>paths[0])).endsWith('/materials/'+ 'a'.repeat(24)),'Reopen must reuse the original exact-variant session');
await page.getByRole('button',{name:'Save & Close',exact:true}).click();
console.log('Edited mesh reopens its original region session.');}finally{await browser.close();}
