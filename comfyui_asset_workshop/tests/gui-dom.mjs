import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const {chromium}=require('playwright');
const root=new URL('../',import.meta.url);
const source=readFileSync(new URL('web/single-image.js',root),'utf8');
const editor=readFileSync(new URL('web/image-editor.js',root),'utf8');
const pipeline=readFileSync(new URL('web/mesh-pipeline.js',root),'utf8').replace(/^import .*;$/gm,'').replaceAll('export ','');
const usage=readFileSync(new URL('web/model-usage.js',root),'utf8').replace('export function','function');
const css=readFileSync(new URL('web/creator.css',root),'utf8')+'\n'+readFileSync(new URL('web/single-image.css',root),'utf8');
const logo=readFileSync(new URL('web/assets/mumblebox-star.png',root));
const browser=await chromium.launch({headless:true,...(process.env.FOUNDRY_BROWSER_CHANNEL?{channel:process.env.FOUNDRY_BROWSER_CHANNEL}:{})});
try {
  const page=await browser.newPage({viewport:{width:1100,height:1000}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.route('https://foundry.test/**',route=>route.fulfill(route.request().resourceType()==='image'
    ?{contentType:'image/png',body:logo}:{contentType:'text/html',body:'<!doctype html><html><body></body></html>'}));
  await page.goto('https://foundry.test/');
  await page.addStyleTag({content:css});
  const script=source.slice(0,source.indexOf('export function renderSingleControls'))
    .replace(/^import .*;\r?$/gm,'').replace('export class SingleImageControls','class SingleImageControls')
    .replaceAll('import.meta.url',JSON.stringify('https://foundry.test/extensions/workshop/single-image.js'));
  await page.addScriptTag({content:
    'const app={};const PREFIX="/asset-workshop/v2";const downloadProgress=()=>null;'+
    'const request=(...args)=>window.serviceRequest(...args);const api={fetchApi:(...args)=>window.serviceFetch(...args)};'+
    pipeline+'\n'+usage+'\n'+editor.replace('export async function','async function')+'\n'+script+
    '\nwindow.Controls=SingleImageControls;window.element=el;'});
  await page.evaluate(()=>{
    const slot=()=>({current:null,approved:null,revisions:[]});
    window.serverProject={id:'fixture',revision:1,name:'DOM behavior check',category:'props',profile:'klein4',prompt:'',
      sources:[],loras:[],settings:{requested_seed:-1,resolution:1024},images:Object.fromEntries(
        ['source','design','mesh_input','reference_front','reference_back','reference_left','reference_right'].map(k=>[k,slot()])),
      artifacts:[],target:{user_instructions:'',requested_dimensions_m:{}}};
    window.assistantCalls=[];window.acceptFails=false;
    window.serviceRequest=async(path,body,method)=>{
      if(method==='PATCH'){await new Promise(r=>setTimeout(r,25));Object.assign(serverProject,structuredClone(body.changes));serverProject.revision++;return structuredClone(serverProject);}
      if(path.endsWith('/describe')){assistantCalls.push({prompt:serverProject.prompt,action:body.action});await new Promise(r=>setTimeout(r,25));return {text:'Enhanced: '+serverProject.prompt,input_revision:serverProject.revision};}
      if(path.endsWith('/reviews')){serverProject.images[body.role].approved=body.revision_id;return structuredClone(serverProject);}
      if(path==='/projects/fixture')return structuredClone(serverProject);
      throw Error('Unexpected fixture request: '+path);
    };
    window.serviceFetch=async(path)=>{
      if(path.endsWith('/foreground/accept'))return {ok:!acceptFails,json:async()=>acceptFails?{error:'Save failed; retry.'}:{}};
      if(path.endsWith('/foreground'))return {ok:true,json:async()=>({id:'candidate1',cutout_file:'cutout.png'})};
      throw Error('Unexpected fixture fetch: '+path);
    };
    const profile={label:'FLUX.2 Klein 4B',source_required:false,max_references:10,license:{url:'https://example.com/license',label:'Fixture license'},
      lora:{architecture:'klein4'},defaults:{steps:4,cfg:1},help:{purpose:'Fixture purpose.',steps:'Steps help.',cfg:'Guidance help.'}};
    const c=Object.create(Controls.prototype);
    Object.assign(c,{node:{},root:element('section',{class:'aw aw-single-controls'}),tab:'Create image',project:structuredClone(serverProject),
      capabilities:{profiles:{klein4:profile}},loraList:{files:[],items:[],downloadable:[]},
      civitai:{installed:[],download:{status:'idle'},progress:()=>element('section',{hidden:true})},undo:[],offset:0,
      resources:{cpu_percent:0,ram_used:0,ram_total:1,vram_used:0,vram_total:1,download:{status:'idle'}}});
    document.body.append(c.root);window.controls=c;c.render();
  });
  const description=page.getByRole('textbox',{name:'Object description',exact:true});
  const enhance=page.getByRole('button',{name:'Enhance description',exact:true});
  assert.equal(await enhance.isDisabled(),true);
  await description.fill('A bronze lantern');
  assert.equal(await description.evaluate(e=>e===document.activeElement),true,'Text must remain focused');
  assert.equal(await enhance.isEnabled(),true,'Enhance must enable before blur');
  await enhance.click();
  await page.waitForFunction(()=>window.assistantCalls.length===1&&!window.controls.helperBusy);
  assert.deepEqual(await page.evaluate(()=>assistantCalls),[{prompt:'A bronze lantern',action:'enhance'}]);
  await description.fill('   ');
  assert.equal(await enhance.isDisabled(),true,'Whitespace must disable Enhance immediately');
  await description.fill('A brass lamp');
  assert.equal(await enhance.isEnabled(),true);
  await enhance.click();
  await page.waitForFunction(()=>window.assistantCalls.length===2&&!window.controls.helperBusy);
  assert.equal(await page.evaluate(()=>assistantCalls[1].prompt),'A brass lamp');
  assert.equal(await page.getByRole('button',{name:'Generate image',exact:true}).count(),2);
  assert.equal(await page.locator('.image-settings input[type=range]').count(),0);
  console.log('PASS: focused typing enables Enhance; immediate click uses latest text; clearing disables; two Generate actions; numeric sampling.');

  await page.evaluate(()=>{
    const c=controls;
    c.loraList={files:[],items:[],downloadable:[]};c.civitai.installed=[];
    for(let n=1;n<=7;n++){
      const name='compatible-'+n+'.safetensors';
      c.loraList.files.push(name);c.loraList.items.push({name,profiles:['klein4']});
      c.civitai.installed.push({kind:'LORA',relative_path:name,model_name:'Style '+n,creator:'Example author',base_model:'Klein 4B',
        notes:'Makes a paper diorama.',guide:{Inputs:'Text or reference image.',Strength:'Start at 1.'},triggers:['paper style'],
        license:'Apache 2.0',permissions:{allowNoCredit:false,allowCommercialUse:['Image'],allowDerivatives:false,allowDifferentLicense:false},source_url:'https://example.com/author'});
    }
    c.loraList.files.push('incompatible.safetensors');c.loraList.items.push({name:'incompatible.safetensors',profiles:['sdxl_base']});
    c.render();
  });
  const loras=page.locator('details.lora-stack');
  assert.equal(await loras.evaluate(e=>e.open),false);
  assert.ok((await loras.locator('summary').textContent()).includes('LoRAs Optional'),'The optional label needs a word boundary for screen readers');
  await loras.locator('summary').click();
  assert.equal(await loras.locator('input[type=checkbox]').count(),7);
  assert.equal(await loras.locator('.lora-picker').evaluate(e=>e.scrollHeight>e.clientHeight),true);
  assert.equal(await loras.locator('.lora-choice-row').first().evaluate(e=>e.firstElementChild.classList.contains('lora-info-wrap')),true);
  await loras.locator('input[type=checkbox]').nth(0).check();
  await page.waitForFunction(()=>controls.project.loras.filter(l=>l.enabled).length===1);
  await loras.locator('input[type=checkbox]').nth(1).check();
  await page.waitForFunction(()=>controls.project.loras.filter(l=>l.enabled).length===2);
  const about=loras.getByRole('button',{name:'About compatible-1',exact:true});
  await about.hover();
  await page.waitForFunction(()=>document.querySelectorAll('.lora-tooltip:popover-open').length===1);
  const tooltip=page.locator('.lora-tooltip:popover-open');
  assert.match(await tooltip.textContent(),/Example author/);
  assert.match(await tooltip.textContent(),/paper diorama/);
  assert.match(await tooltip.textContent(),/Apache 2.0/);
  assert.match(await tooltip.textContent(),/Required by creator/,'Saved credit requirements must be visible');
  assert.match(await tooltip.textContent(),/Restricted by creator/,'Saved derivative restrictions must be visible');
  await page.keyboard.press('Escape');
  assert.equal(await page.locator('.lora-tooltip:popover-open').count(),0);
  assert.equal(await page.evaluate(()=>controls.project.loras.filter(l=>l.enabled).length),2);
  console.log('PASS: collapsed matching-only multiselect, scroll cap, help on the left, shared author/usage/license guide, Escape without selection changes.');

  await page.evaluate(()=>{
    const c=controls;
    c.project.images.mesh_input={current:'image1',approved:null,revisions:[{id:'image1',sha256:'fixture-hash',
      file:'image.png',review:{decision:'unreviewed'},foreground:{mask_file:'mask.png',cutout_file:'cutout.png'}}]};
    serverProject=structuredClone(c.project);c.tab='Approve image';c.render();
  });
  await page.getByRole('button',{name:'Approve this image',exact:true}).click();
  await page.getByRole('heading',{name:'Background removal — Image for the mesh'}).waitFor();
  const remove=page.getByRole('button',{name:'Remove Background',exact:true});
  const keep=page.getByRole('button',{name:'Keep Cutout and Continue to Create Mesh',exact:true});
  await remove.click();await keep.waitFor({state:'visible'});
  await page.waitForFunction(()=>!document.querySelector('.aw-image-editor button')?.disabled);
  await page.waitForFunction(()=>[...document.querySelectorAll('.aw-image-editor button')].some(e=>e.textContent==='Keep Cutout and Continue to Create Mesh'&&!e.disabled));
  await page.getByRole('button',{name:'Select whole image',exact:true}).click();
  assert.equal(await keep.isDisabled(),true,'Changing a selection invalidates its previous cutout');
  await remove.click();
  await page.waitForFunction(()=>[...document.querySelectorAll('.aw-image-editor button')].some(e=>e.textContent==='Keep Cutout and Continue to Create Mesh'&&!e.disabled));
  await page.evaluate(()=>{window.acceptFails=true;});
  await keep.click();await page.getByText('Save failed; retry.',{exact:true}).waitFor();
  assert.equal(await page.evaluate(()=>controls.tab),'Approve image');
  await page.evaluate(()=>{window.acceptFails=false;});
  await keep.click();
  await page.waitForFunction(()=>controls.tab==='Mesh & agent package'&&!document.querySelector('.aw-image-editor'));
  assert.equal(await page.getByRole('heading',{name:'Export asset',exact:true}).count(),1);
  assert.equal(errors.length,0,errors.join('\n'));
  console.log('PASS: approval opens background removal; edited masks invalidate previews; failed save stays; successful Keep opens mesh/export.');
  await page.evaluate(()=>{
    const c=controls,surface=document.createElement('canvas');document.body.append(surface);
    const orbit={domElement:surface,_pointers:[],autoRotate:true,enableDamping:true,
      _onPointerUp(event){this._pointers=this._pointers.filter(id=>id!==event.pointerId);}};
    c.guardViewerDrag({controlsManager:{controls:orbit}});
    if(orbit.autoRotate||orbit.enableDamping)throw Error('Viewer must stop moving on release');
    orbit._pointers=[1];surface.dispatchEvent(new PointerEvent('pointermove',{pointerId:1,buttons:0,bubbles:true,pointerType:'mouse'}));
    if(orbit._pointers.length)throw Error('Hover must clear a stuck drag');
    orbit._pointers=[2];window.dispatchEvent(new PointerEvent('pointerup',{pointerId:2,buttons:0}));
    if(orbit._pointers.length)throw Error('Release outside the preview must finish the drag');
    orbit._pointers=[3];window.dispatchEvent(new Event('blur'));
    if(orbit._pointers.length)throw Error('Window blur must finish the drag');
    c.viewerInteractionCleanup();surface.remove();
  });
  console.log('PASS: viewer glue clears stale hover, outside release and window-blur drag state.');

} finally {if(browser.isConnected())await Promise.race([new Promise(resolve=>browser.once('disconnected',resolve)),browser.close()]);}
process.exit(0);
