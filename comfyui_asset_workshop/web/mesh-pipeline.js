import {request} from './job-client.js';
import {openMaterialLab} from './material-lab-host.js';
export const pipelineDefaults={shape_resolution:1024,refine_enabled:true,refine_resolution:1536,refine_steps:25,refine_seed:42,cpu_offload:true,attention:'sdpa',intake_faces:4500000,weld_enabled:true,weld_epsilon:.00001,fill_enabled:true,fill_perimeter:.03,fill_vertices:16,remesh_enabled:true,remesh_resolution:512,remesh_fill:20,texture_provider:'trellis2',texture_steps:20,texture_seed:42,texture_size:4096,texture_resolution:1024,texture_guidance:3,texture_rescale:.2,texture_sampler:'euler',reference_lock:0,output_variant:'balanced_250k',guide_size:1024,palette_count:12,material_steps:4,material_guidance:10,material_seed:42};
const detailNames={detailed:'Detailed — retain the full mesh',balanced_250k:'Balanced — about 250,000 triangles',compact_100k:'Compact — about 100,000 triangles'};
export function pipelineSelection(project){
 const state=project.pipeline??{},current=id=>project.artifacts.find(a=>a.id===id&&!a.stale);
 return {geometry:current(state.selected_geometry_id),texture:current(state.selected_texture_id),appearance:current(state.selected_appearance_id)};
}
export async function savePipeline(c,changes){
 await c.saveQueue;await c.pipelineSaveQueue;
 const pid=c.project.id;
 const pending=request(`/projects/${pid}/pipeline`,{expected_revision:c.project.revision,changes},'PATCH');c.pipelineSaveQueue=pending;
 try{const p=await pending;if(c.project.id===pid)c.project=p;}finally{c.pipelineSaveQueue=null;}
}
export async function prepareVariant(c){
 const s={...pipelineDefaults,...c.project.pipeline?.settings},chosen=pipelineSelection(c.project),texture=chosen.texture;
 if(!texture)throw Error('Texture the finished geometry first.');
 const existing=s.output_variant==='detailed'?texture:[...c.project.artifacts].reverse().find(a=>!a.stale&&a.parent_artifact_id===texture.id&&a.variant===s.output_variant&&a.appearance_stage==='variant');
 if(existing){c.project=await request(c.path('/pipeline/select'),{expected_revision:c.project.revision,artifact_id:existing.id});return;}
 await c.start('prepare_variant',{source_id:texture.id,variant:s.output_variant});
}
export function renderMeshPipeline(c,content,el){
 const p=c.project,s={...pipelineDefaults,...p.pipeline?.settings},chosen=pipelineSelection(p),caps=c.capabilities.pipeline??{},blocked=c.blocked();
 const approved=c.current('mesh_input')&&p.images.mesh_input.approved===c.current('mesh_input').id;
 const change=(key,value)=>savePipeline(c,{[key]:value});
 const number=(label,key,min,max,step=1)=>c.input(label,s[key],v=>change(key,Number(v)),{type:'number',min,max,step});
 const toggle=(label,key)=>c.select(label,{yes:'Enabled',no:'Disabled'},s[key]?'yes':'no',v=>change(key,v==='yes'));
 content.append(el('div',{class:'step-heading'},el('h3',{},'Build, texture and export'),c.hint('Generate clean geometry, add color and materials, then export your chosen result. Saved versions stay available.')));
 const refinements=c.disclosure('Refinement & cleanup settings',c.hint('Recommended settings are loaded. Changes apply to the next run; saved geometry is retained.'),
  c.select('Initial mesh resolution',{1024:'1024 — recommended',1536:'1536 — more memory',2048:'2048 — experimental memory use'},s.shape_resolution,v=>change('shape_resolution',Number(v))),
  c.grid(2,toggle('Hi3D refinement','refine_enabled'),c.select('Hi3D resolution',{512:'512',1024:'1024',1536:'1536 — recommended'},s.refine_resolution,v=>change('refine_resolution',Number(v)))),
  c.grid(2,number('Refinement steps','refine_steps',1,100),number('Refinement seed','refine_seed',0,2147483647)),
  c.grid(2,toggle('Weld duplicate vertices','weld_enabled'),number('Weld tolerance (relative)','weld_epsilon',0,.001,.00001)),
  c.grid(2,toggle('Fill small holes','fill_enabled'),number('Maximum hole perimeter','fill_perimeter',0,1,.01)),
  c.grid(2,toggle('Solid remesh','remesh_enabled'),number('Remesh resolution','remesh_resolution',128,1024)));
 content.append(c.panel('Build your asset','Pixal3D creates the shape. Hi3D refines it, then cleanup prepares the final surface. Four additional pictures communicate design intent and do not enter reconstruction.',
  el('div',{class:'action-bar'},c.button('Generate mesh & reference images',()=>c.start('build_geometry'),c.imageBlocked()||(!approved?'Approve one image in Prepare for 3D first.':''),'primary')),refinements));
 content.append(el('p',{class:'hint'},el('a',{href:'http://hi3d.ai/',target:'_blank',rel:'noopener noreferrer'},'Powered by Hi3D 1.0'),' · Pixal3D shape generation · TRELLIS.2 final-mesh texturing · StableMaterials optional material refinement.'));
 const geometries=p.artifacts.filter(a=>a.kind==='geometry'&&!a.stale);
 if(geometries.length)content.append(c.select('Saved geometry checkpoint',Object.fromEntries(geometries.map(a=>[a.id,`${a.geometry_stage} · ${a.triangles?.toLocaleString()} triangles`])),chosen.geometry?.id,async id=>{c.project=await request(c.path('/pipeline/select'),{expected_revision:p.revision,artifact_id:id});}));
 const providers=caps.providers??{trellis2:{label:'TRELLIS.2 (recommended)',available:false,reason:'Reconnect to read runtime availability.'},pixal3d:{label:'Pixal3D texture only',available:false,reason:'Qualification pending.'}};
 const providerControl=c.select('Texture Generator',Object.fromEntries(Object.entries(providers).map(([k,v])=>[k,v.label])),s.texture_provider,v=>change('texture_provider',v));
 for(const option of providerControl.querySelectorAll('option')){option.disabled=!providers[option.value]?.available;option.title=providers[option.value]?.reason??'';}
 const ready=providers[s.texture_provider];
 content.append(c.panel('Texture the finished mesh','TRELLIS.2 colors and textures the cleaned mesh using your approved image. This keeps texturing after geometry changes.',providerControl,
  ...Object.values(providers).filter(v=>!v.available).map(v=>c.hint(v.label+': '+v.reason)),
  c.button('Proceed with Texturing',()=>c.start('texture_mesh',{source_id:chosen.geometry.id}),blocked||(!chosen.geometry||chosen.geometry.geometry_stage!=='clean'?'Generate or select the clean geometry first.':!ready?.available?ready?.reason||'Provider unavailable.':''),'primary'),
  c.disclosure('Texture settings',c.grid(2,number('Texture steps','texture_steps',1,100),number('Texture seed','texture_seed',0,2147483647)),c.grid(2,number('Texture guidance','texture_guidance',0,20,.1),c.select('Texture size',{1024:'1024 px',2048:'2048 px',4096:'4096 px — recommended'},s.texture_size,v=>change('texture_size',Number(v)))))));
 const appearance=chosen.appearance??[...p.artifacts].reverse().find(a=>a.kind==='mesh'&&!a.stale&&!a.pipeline_version);
 const visible=appearance??chosen.geometry;
 if(visible){const viewer=el('div',{class:'viewer',role:'application',tabIndex:0,'aria-label':appearance?'Current textured mesh preview':'Clean geometry preview'});content.append(c.panel(appearance?'Your current mesh':'Geometry preview',`${visible.triangles?.toLocaleString()??'Recorded'} triangles · ${visible.variant??visible.geometry_stage}`,viewer,c.hint('Drag to rotate; scroll to zoom. Inspect all sides.')));requestAnimationFrame(()=>c.mountViewer(viewer,visible).catch(e=>viewer.replaceChildren(c.hint(e.message))));}
 else content.append(el('div',{class:'empty'},'No mesh yet. Approve an image, then build your asset above.'));
 const matching=appearance&&appearance.variant===s.output_variant;
 content.append(c.panel('Output detail','Detailed retains the full mesh. Balanced is a general prop starting point. Compact reduces the triangle cost further. Choose for your target; collision and LODs still need checking.',
  c.select('Output detail',detailNames,s.output_variant,v=>change('output_variant',v)),
  c.button('Prepare selected detail',()=>prepareVariant(c),blocked||(!chosen.texture?'Texture the clean mesh first.':'')),c.hint('Choosing a preset does not start work. Prepare creates a separate version and keeps the detailed master.')));
 const sessions=Object.values(p.pipeline?.material_sessions??{}).filter(v=>v.source_id===appearance?.id||v.rendered_artifact_id===appearance?.id),session=sessions.at(-1);
 const pending=session&&(session.assignments_pending??(session.rendered_revision!==session.draft_revision&&session.draft.regions.length));
 content.append(c.panel('Materials Lab (optional)','Keep your colors and shape. Click color groups, connected patches or paint small regions, then describe fabric, skin, metal and other materials.',
  c.button('Open Materials Lab',()=>openMaterialLab(c,appearance),blocked||(!appearance?'Texture a mesh first.':!matching?'Prepare the selected output detail first.':appearance.triangles>2000000?'Choose Balanced or Compact; Materials Lab supports up to two million triangles.':!caps.materials_available?'Configure StableMaterials in the isolated runtime.':'')),
  c.hint(pending?'Saved material assignments have changes that have not been generated. Export uses the latest rendered result.':appearance?.material_revision?'Rendered material changes are included in the current mesh.':'Current mesh uses its original generated materials.'),
  ...(session?[c.button('Use original materials',async()=>{c.project=await request(c.path('/pipeline/select'),{expected_revision:c.project.revision,artifact_id:session.source_id});},blocked)]:[])));
 if(chosen.texture)content.append(el('div',{class:'row'},c.link('Download detailed master (.glb)',c.url(chosen.texture,true))));
 const legacyMaster=[...p.artifacts].reverse().find(a=>a.kind==='master'&&!a.stale);
 if(legacyMaster)content.append(c.disclosure('Previous reconstruction',c.hint('This saved legacy checkpoint remains available.'),c.button('Finish legacy saved mesh',()=>c.start('finish_mesh',{master_id:legacyMaster.id}),blocked)));
 const cards=el('div',{class:'cards'});for(const role of ['reference_front','reference_back','reference_left','reference_right']){const image=c.current(role);if(image)cards.append(c.imageCard(role,image));}content.append(c.disclosure('Reference pictures',c.hint('Optional design references; unmeasured viewpoints.'),cards));
 content.append(c.panel('Export asset',pending?'Exports the latest rendered mesh shown above. Assigned draft changes are not yet applied.':'Download the current mesh and its source/settings together, or open the same result in Blender.',
  ...(appearance?[c.link('Download current mesh (.glb)',c.url(appearance,true))]:[]),
  c.disclosure('Export notes (optional)',c.text('Notes for you, a collaborator or a coding agent',p.target.user_instructions,v=>c.save({target:{user_instructions:v}}))),
  el('div',{class:'action-bar'},c.button('Download asset (.zip)',()=>c.exportAsset(appearance,null),blocked||(!appearance?'Texture a mesh first.':''),'primary'),c.button('Open in Blender',async()=>{await c.saveQueue;await request(c.path('/blender'),{expected_revision:c.project.revision,artifact_id:appearance.id});},blocked||(!appearance?'Texture a mesh first.':'')))));
 for(const a of p.artifacts.filter(a=>a.kind==='package'&&!a.stale))content.append(c.link('Download saved ZIP',c.url(a,true)));
}
