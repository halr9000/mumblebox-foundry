import {request,PREFIX} from "./job-client.js";
let opened=null;
export async function openMaterialLab(c,appearance){
 if(opened){opened.dialog.focus();return;}
 const pid=c.project.id,path=`/projects/${pid}`;
 let session=appearance.material_session_id?await request(path+`/materials/${appearance.material_session_id}`):await request(path+"/materials",{expected_revision:c.project.revision,source_id:appearance.id,settings:{guide_size:c.project.pipeline.settings.guide_size,palette_count:c.project.pipeline.settings.palette_count}});
 await c.refresh();
 session=await request(path+`/materials/${session.id}?expand_masks=1`);
 if(session.state!=="ready"){
  const job=await c.start("prepare_material_guide",{session_id:session.id});await c.waitJob(job);
  session=await request(path+`/materials/${session.id}?expand_masks=1`);
 }
 const previous=document.activeElement,nonce=crypto.randomUUID(),dialog=document.createElement('dialog');dialog.className='aw aw-material-dialog';dialog.setAttribute('aria-label','Materials Lab');
 const bar=document.createElement('div');bar.className='aw-material-bar';const title=document.createElement('strong');title.textContent='Materials Lab Â· '+session.variant.replaceAll('_',' ');
 const info=document.createElement('span');info.setAttribute('role','status');info.textContent='Changes are saved to this project.';
 const close=document.createElement('button');close.textContent='Save & Close';close.type='button';bar.append(title,info,close);
 const frame=document.createElement('iframe');frame.title='Materials Lab region editor';frame.src=PREFIX+`/material-lab/material_editor.html?project=${encodeURIComponent(pid)}&session=${session.id}&nonce=${nonce}`;
 dialog.append(bar,frame);document.body.append(dialog);opened={dialog,pid,sid:session.id};let queue=Promise.resolve(),timer,latest=null,disposed=false,applying=false;
 const send=(type,more={})=>frame.contentWindow?.postMessage({type,nonce,project:pid,session:session.id,...more},location.origin);
 const enqueue=state=>{
  queue=queue.catch(()=>{}).then(async()=>{session=await request(path+`/materials/${session.id}`,{expected_draft_revision:session.draft_revision,state},'PATCH');info.textContent='Choices saved. Assigned changes need Generate & Preview.';send('material-editor-saved',{busy:applying});});
  queue.catch(e=>{latest??=state;info.textContent=e.message;send('material-editor-status',{message:e.message,busy:false});});return queue;
 };
 const flush=async()=>{clearTimeout(timer);if(latest){const value=latest;latest=null;enqueue(value);}await queue;};
 const apply=async()=>{
  if(applying)return;applying=true;
  try{
  await flush();send('material-editor-status',{message:'Generating assigned materials in ComfyUI…',busy:true});if(c.project.id!==pid)throw Error('Return to this project before generating materials.');
  const job=await c.start('apply_materials',{session_id:session.id});await c.waitJob(job);
  session=await request(path+`/materials/${session.id}?expand_masks=1`);const record=c.project.artifacts.find(a=>a.id===session.rendered_artifact_id);
  if(record)send('material-editor-result',{result:{url:PREFIX+path+`/artifacts/${record.id}`,report:{regions_applied:record.material_region_count??session.draft.regions.length}}});
  }finally{applying=false;}
 };
 const receive=async event=>{
  const d=event.data;if(disposed||event.origin!==location.origin||event.source!==frame.contentWindow||d?.nonce!==nonce||d.project!==pid||d.session!==session.id)return;
  try{
   if(d.type==='material-editor-ready'){send('material-editor-init',{state:session.draft});if(session.rendered_artifact_id)send('material-editor-result',{result:{url:PREFIX+path+`/artifacts/${session.rendered_artifact_id}`,report:{regions_applied:session.draft.regions.length}}});}
   if(d.state){latest=d.state;clearTimeout(timer);timer=setTimeout(()=>{const value=latest;latest=null;if(value)enqueue(value);},350);}
   if(d.type==='material-editor-save')await flush();
   if(d.type==='material-editor-apply')await apply();
  }catch(e){info.textContent=e.message;send('material-editor-status',{message:e.message,busy:false});}
 };
 window.addEventListener('message',receive);
 const finish=async()=>{close.disabled=true;try{await flush();send('material-editor-dispose');disposed=true;window.removeEventListener('message',receive);clearTimeout(timer);dialog.close();frame.src='about:blank';dialog.remove();opened=null;if(c.project.id===pid){await c.refresh();c.render();}previous?.focus();}catch(e){info.textContent=e.message;close.disabled=false;}};
 close.onclick=finish;dialog.addEventListener('cancel',e=>{e.preventDefault();finish();});dialog.showModal();close.focus();
}
