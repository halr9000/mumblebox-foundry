import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { computeBoundsTree, disposeBoundsTree, acceleratedRaycast } from './vendor/three-mesh-bvh.module.js';
THREE.BufferGeometry.prototype.computeBoundsTree=computeBoundsTree;
THREE.BufferGeometry.prototype.disposeBoundsTree=disposeBoundsTree;
THREE.Mesh.prototype.raycast=acceleratedRaycast;
const $ = id => document.getElementById(id);
const query=new URLSearchParams(location.search),session=query.get('session'),project=query.get('project'),nonce=query.get('nonce');
const asset = name => `/asset-workshop/v2/projects/${encodeURIComponent(project)}/materials/${session}/assets/${name}`;
function packedState(value){
 const copy=structuredClone(value);
 for(const rows of [copy.regions??[],copy.selection??[]])for(const row of rows)if(row.kind==='faces'){
  const bits=new Uint8Array(Math.ceil(meta.faces/8));for(const [start,end] of row.face_ranges??[])for(let i=start;i<end;i++)bits[i>>3]|=1<<(i&7);
  let text='';for(let i=0;i<bits.length;i+=8192)text+=String.fromCharCode(...bits.subarray(i,i+8192));row.face_mask=btoa(text);delete row.face_ranges;delete row.mask_id;
 }
 return copy;
}
function unpackState(value){
 const copy=structuredClone(value);
 for(const rows of [copy.regions??[],copy.selection??[]])for(const row of rows)if(row.kind==='faces'&&row.face_mask){
  const bits=atob(row.face_mask);row.face_ranges=[];let start=null;
  for(let i=0;i<meta.faces;i++){const on=bits.charCodeAt(i>>3)&(1<<(i&7));if(on&&start===null)start=i;if(!on&&start!==null){row.face_ranges.push([start,i]);start=null;}}
  if(start!==null)row.face_ranges.push([start,meta.faces]);delete row.face_mask;
 }
 return copy;
}
const post=(type,more={})=>parent.postMessage({type,nonce,project,session,...more,...(more.state?{state:packedState(more.state)}:{})},location.origin);
let meta, colors, patches, patchSizes, triangleMap, guidePixels, selected=null, model, currentView='guide', afterUrl=null, ready=false;
let state={version:1,regions:[]};let disposed=false,modelLoadVersion=0;
let brushFaces=new Set();let painting=false,lastPaint=0;
const selectedRegions=new Map(),visitedRegions=new Map();let restoring=false;
const canvas=$('modelCanvas'), wrap=$('canvasWrap');
const renderer=new THREE.WebGLRenderer({canvas,antialias:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.setClearColor(0x252c37);
const scene=new THREE.Scene();
scene.add(new THREE.HemisphereLight(0xffffff,0x718095,2.5));
for (const [position,intensity] of [[[3,5,4],4],[[-4,2,-3],2],[[0,-3,2],.7]]) {const light=new THREE.DirectionalLight(0xffffff,intensity);light.position.set(...position);scene.add(light);}
const camera=new THREE.PerspectiveCamera(38,1,.001,100);
const controls=new OrbitControls(camera,canvas);controls.enableDamping=false;controls.addEventListener('change',render);
const raycaster=new THREE.Raycaster(), pointer=new THREE.Vector2();raycaster.firstHitOnly=true;
const textureCanvas=document.createElement('canvas');let overlayTexture;
function render(){if(!disposed)renderer.render(scene,camera);}
function resize(){const w=wrap.clientWidth,h=wrap.clientHeight;if(!w||!h)return;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();render();}
const observer=new ResizeObserver(resize);observer.observe(wrap);
function status(message,busy=false){if(disposed)return;$('status').textContent=message;$('busy').classList.toggle('show',busy);for(const id of ['generateButton','autoButton'])$(id).disabled=busy;}
function sourceMaterials(){model?.traverse(mesh=>{if(mesh.isMesh&&mesh.userData.sourceMaterial)mesh.material=mesh.userData.sourceMaterial;});}
function disposeModel(){if(!model)return;scene.remove(model);disposeTree(model);model=null;}
function disposeTree(root){
 const geometries=new Set(),materials=new Set(),textures=new Set();
 root.traverse(mesh=>{if(mesh.isMesh){
  geometries.add(mesh.geometry);
  for(const material of [mesh.material,mesh.userData.sourceMaterial,mesh.userData.guideMaterial].flat())if(material)materials.add(material);
 }});
 for(const geometry of geometries){geometry.disposeBoundsTree?.();geometry.dispose();}
 for(const material of materials){for(const value of Object.values(material))if(value?.isTexture&&value!==overlayTexture)textures.add(value);material.dispose();}
 for(const texture of textures)texture.dispose();
}
function fit(){if(!model)return;const box=new THREE.Box3().setFromObject(model),center=box.getCenter(new THREE.Vector3()),size=box.getSize(new THREE.Vector3());const d=Math.max(size.x,size.y,size.z)*1.9;controls.target.copy(center);camera.position.copy(center).add(new THREE.Vector3(d*.9,d*.6,d));camera.near=d/1000;camera.far=d*100;camera.updateProjectionMatrix();controls.update();render();}
async function loadModel(url,view,keepCamera=false){
  const loadVersion=++modelLoadVersion;
  status('Loading mesh preview…',true);
  const oldPos=camera.position.clone(),oldTarget=controls.target.clone();
  const gltf=await new GLTFLoader().loadAsync(url,event=>{if(event.total)status(`Loading mesh preview ${Math.round(event.loaded/event.total*100)}%…`,true);});
  if(disposed||loadVersion!==modelLoadVersion){disposeTree(gltf.scene);return;}
  disposeModel();model=gltf.scene;scene.add(model);let offset=0;
  model.traverse(mesh=>{if(mesh.isMesh){const preservedIndex=mesh.geometry.index?.array.slice();mesh.geometry.computeBoundsTree({indirect:true});if(preservedIndex&&!preservedIndex.every((v,i)=>v===mesh.geometry.index.array[i]))throw Error('Picking accelerator changed triangle identities');mesh.userData.faceOffset=offset;offset+=(mesh.geometry.index?.count??mesh.geometry.attributes.position.count)/3;mesh.userData.sourceMaterial=mesh.material;}});
  currentView=view;
  if(view==='guide'||view==='regions')applyOverlay();
  if(keepCamera){camera.position.copy(oldPos);controls.target.copy(oldTarget);controls.update();}else fit();
  resize();render();status('Ready. Click a surface, choose a material, then use it on that region.');
}
function selectedTest(face){for(const r of selectedRegions.values()){if(r.kind==='faces'?r.faceSet?.has(face):r.kind==='color'?colors[face]===r.id:patches[face]===r.id)return true;}return false;}
function applyOverlay(){
  if(!model||!guidePixels)return;
  textureCanvas.width=meta.guide_size;textureCanvas.height=meta.guide_size;
  const ctx=textureCanvas.getContext('2d'),pixels=new Uint8ClampedArray(guidePixels.data);
  for(let i=0;i<triangleMap.length;i++){
    const face=triangleMap[i]-1;if(face<0)continue;const p=i*4;
    if(currentView==='regions'){
      const rgb=meta.regions.find(r=>r.id===colors[face])?.rgb??[70,70,70];pixels[p]=rgb[0];pixels[p+1]=rgb[1];pixels[p+2]=rgb[2];
    }
    if(selectedTest(face)){pixels[p]=Math.round(pixels[p]*.35+255*.65);pixels[p+1]=Math.round(pixels[p+1]*.35+225*.65);pixels[p+2]=Math.round(pixels[p+2]*.35+70*.65);}
  }
  ctx.putImageData(new ImageData(pixels,meta.guide_size,meta.guide_size),0,0);
  overlayTexture?.dispose();overlayTexture=new THREE.CanvasTexture(textureCanvas);overlayTexture.flipY=false;overlayTexture.colorSpace=THREE.SRGBColorSpace;overlayTexture.magFilter=THREE.NearestFilter;
  model.traverse(mesh=>{if(mesh.isMesh){mesh.userData.guideMaterial?.dispose();mesh.userData.guideMaterial=new THREE.MeshBasicMaterial({map:overlayTexture,side:THREE.DoubleSide});mesh.material=mesh.userData.guideMaterial;}});render();
}
const presets={eyes:['Smooth glossy eye surface, low roughness, clear polished appearance, nonmetallic','nonmetal'],cotton:['Matte woven cotton fabric, fine subtle cloth weave, nonmetallic','nonmetal'],velvet:['Soft matte velvet fabric, fine fibrous texture, nonmetallic','nonmetal'],rind:['Natural pumpkin rind, fine pores, slightly waxy rough organic skin, nonmetallic','nonmetal'],rubber:['Matte charcoal rubber, fine grain, nonmetallic','nonmetal'],metal:['Brushed silver metal, subtle fine scratches','metal'],paint:['Matte powder coated paint, subtle fine grain, nonmetallic','nonmetal'],skin:['Natural organic skin, fine pores, slightly satin, nonmetallic','nonmetal']};
const key=r=>`${r.kind}:${r.id}`;
function entries(){return state.regions??[];}
function storeSelection(){
  state.editorOptions={pickMode:$('pickMode').value,brushSize:$('brushSize').value};
  state.selection=[...selectedRegions.values()].map(r=>({kind:r.kind,id:r.id,name:r.name,faces:r.faces,...(r.kind==='faces'?{face_ranges:rangesOf(r.faceSet)}:{})}));
  if(selectedRegions.size)state.editorDraft={name:$('regionName').value,prompt:$('description').value,strength:$('strength').value,detail:$('detail').value,tiles:$('tiles').value,metallic:$('metallic').value};
}
function sync(){storeSelection();if(!restoring)post('material-editor-edits',{state});renderAssignments();}

function renderAssignments(){
  const box=$('assignments');box.replaceChildren();if(!entries().length){box.textContent='None yet — original materials are retained.';return;}
  for(const row of entries()){
    const div=document.createElement('div');div.className='assignment';const text=document.createElement('button');text.className='assigned-choice';text.textContent=`${row.name}: ${row.prompt}`;text.title='Select this assigned region';text.onclick=()=>{visitedRegions.set(key(row),row);select(row.kind,row.id,0);};
    const remove=document.createElement('button');remove.textContent='×';remove.setAttribute('aria-label','Remove '+row.name);remove.onclick=()=>{state.regions=entries().filter(r=>key(r)!==key(row));sync();};div.append(text,remove);box.append(div);
  }
}
function regionColor(id){return meta.regions.find(r=>r.id===id)??meta.regions[0];}
function facesFromRanges(ranges){const set=new Set();for(const[a,b]of ranges??[])for(let i=a;i<b;i++)set.add(i);return set;}
function updateSelectionUI(){
  const count=selectedRegions.size;$('assignButton').disabled=count===0;$('assignButton').textContent=count>1?`Use on ${count} Regions`:'Use on This Region';$('regionName').readOnly=count>1;
  if(count>1){$('regionName').value=`${count} regions selected`;$('selectionSummary').textContent=`${count} regions selected — the material will apply to all of them.`;}
  else if(selected){$('selectionSummary').textContent=`Selected: ${selected.name} · ${selected.faces.toLocaleString()} triangles · ${selected.kind==='faces'?'fine painted region':selected.kind==='color'?'matching color across object':'one connected patch'}`;}
  else $('selectionSummary').textContent='No regions selected. Click a surface or check the regions you want.';
  for(const row of document.querySelectorAll('.region')){const active=selectedRegions.has(row.dataset.key);row.classList.toggle('active',active);const check=row.querySelector('input');if(check)check.checked=active;}
}
function select(kind,id,face=0,additive=false){
  const k=`${kind}:${id}`,saved=entries().find(r=>key(r)===k),old=visitedRegions.get(k);
  if(kind==='patch'&&patches[face]!==id)face=patches.indexOf(id);
  if(kind==='faces')face=saved?.face_ranges?.[0]?.[0]??old?.face_ranges?.[0]?.[0]??face;
  const palette=regionColor(kind==='color'?id:colors[face]);
  let candidate;
  if(kind==='faces'){
    const set=old?.faceSet??(saved?.face_ranges?facesFromRanges(saved.face_ranges):old?.face_ranges?facesFromRanges(old.face_ranges):brushFaces);
    brushFaces=set;candidate={kind,id,name:saved?.name??old?.name??`Painted region ${id+1}`,faces:set.size,faceSet:set};
  }else candidate={kind,id,name:saved?.name??old?.name??(kind==='color'?palette.name:`${palette.name.replace(' surfaces','')} patch ${id}`),faces:kind==='color'?palette.faces:patchSizes[id]};
  if(!additive)selectedRegions.clear();
  if(additive&&selectedRegions.has(k)){selectedRegions.delete(k);selected=[...selectedRegions.values()].at(-1)??null;}
  else{selected=candidate;selectedRegions.set(k,candidate);}
  if(kind!=='color')visitedRegions.set(k,candidate);
  if(selected){
    const existing=entries().find(r=>key(r)===key(selected));const color=regionColor(selected.kind==='color'?selected.id:colors[face]);
    $('regionName').value=selected.name;$('description').value=existing?.prompt??color.prompt;
    $('strength').value=existing?.strength??1;$('detail').value=existing?.detail??.12;$('tiles').value=existing?.tiles??8;
    $('metallic').value=existing?.metallic??(/silver metal/i.test(color.prompt)?'metal':'nonmetal');$('preset').value='custom';
  }
  renderRegions();updateSelectionUI();if(['guide','regions'].includes(currentView))applyOverlay();sync();
}
function renderRegions(){
  if(!meta)return;const list=$('regionList');list.replaceChildren();const all=[...meta.regions,...visitedRegions.values()];
  for(const region of all){
    const row=document.createElement('div');row.className='region';row.dataset.key=key(region);const checked=selectedRegions.has(key(region));
    const check=document.createElement('input');check.type='checkbox';check.checked=checked;check.setAttribute('aria-label','Include '+region.name);check.onchange=()=>select(region.kind,region.id,0,true);
    const button=document.createElement('button');button.className='region-choice';button.setAttribute('aria-label','Select '+region.name+' '+region.id);
    const swatch=document.createElement('span');swatch.className='swatch';swatch.style.background=region.rgb?`rgb(${region.rgb.join(',')})`:'#e7cc62';
    const name=document.createElement('span');name.textContent=region.name;const count=document.createElement('small');count.textContent=(region.faces??0).toLocaleString();button.append(swatch,name,count);button.onclick=event=>select(region.kind,region.id,0,event.ctrlKey||event.metaKey);row.append(check,button);row.classList.toggle('active',checked);list.append(row);
  }
}
let down;
canvas.addEventListener('pointerdown',event=>{down={x:event.clientX,y:event.clientY};if($('pickMode').value==='faces'&&event.button===0){painting=true;paintSurface(event);}});
canvas.addEventListener('click',event=>{
  if($('pickMode').value==='faces'||!ready||!model||!down||Math.hypot(event.clientX-down.x,event.clientY-down.y)>6)return;
  const rect=canvas.getBoundingClientRect();pointer.set((event.clientX-rect.left)/rect.width*2-1,-(event.clientY-rect.top)/rect.height*2+1);
  raycaster.setFromCamera(pointer,camera);const hit=raycaster.intersectObject(model,true).find(h=>h.object.isMesh&&h.faceIndex!=null);
  if(!hit){$('selectionSummary').textContent='Click on the object to select a surface.';return;}
  const face=hit.faceIndex+(hit.object.userData.faceOffset??0),kind=$('pickMode').value;
  select(kind,kind==='color'?colors[face]:patches[face],face,event.ctrlKey||event.metaKey);
});

function rangesOf(set){
  const list=[...set].sort((a,b)=>a-b),ranges=[];
  for(const face of list){const last=ranges[ranges.length-1];if(last&&last[1]===face)last[1]=face+1;else ranges.push([face,face+1]);}
  return ranges;
}
function paintSurface(event){
  if(!ready||!model)return;
  const rect=canvas.getBoundingClientRect();pointer.set((event.clientX-rect.left)/rect.width*2-1,-(event.clientY-rect.top)/rect.height*2+1);
  raycaster.setFromCamera(pointer,camera);
  const hit=raycaster.intersectObject(model,true).find(h=>h.object.isMesh&&h.faceIndex!=null);if(!hit)return;
  const mesh=hit.object,local=mesh.worldToLocal(hit.point.clone());
  const radius=camera.position.distanceTo(hit.point)*Math.tan(THREE.MathUtils.degToRad(camera.fov/2))*2*Number($('brushSize').value)/rect.height;
  const sphere=new THREE.Sphere(local,radius),normal=hit.face.normal,nearest=new THREE.Vector3(),n=new THREE.Vector3();
  const erase=event.shiftKey||$('eraseBrush').checked,first=selected?.kind!=='faces';
  if(first)brushFaces=new Set();
  mesh.geometry.boundsTree.shapecast({intersectsBounds:box=>box.intersectsSphere(sphere),intersectsTriangle:(triangle,index)=>{
    triangle.getNormal(n);if(n.dot(normal)<.25)return false;triangle.closestPointToPoint(local,nearest);
    if(nearest.distanceToSquared(local)<=radius*radius){const face=index+(mesh.userData.faceOffset??0);if(erase)brushFaces.delete(face);else brushFaces.add(face);}return false;
  }});
  if(first){const id=Math.max(-1,...entries().filter(r=>r.kind==='faces').map(r=>r.id),...[...visitedRegions.values()].filter(r=>r.kind==='faces').map(r=>r.id))+1;select('faces',id,hit.faceIndex+(mesh.userData.faceOffset??0),event.ctrlKey||event.metaKey);}
  else{selected.faces=brushFaces.size;updateSelectionUI();}
  if(!['guide','regions'].includes(currentView))currentView='guide';applyOverlay();
}
canvas.addEventListener('pointermove',event=>{
  const cursor=$('brushCursor'),rect=canvas.getBoundingClientRect();
  if($('pickMode').value==='faces'){
    const size=Number($('brushSize').value)*2;cursor.style.cssText=`position:absolute;display:block;left:${event.clientX-rect.left-size/2}px;top:${event.clientY-rect.top-size/2}px;width:${size}px;height:${size}px;border:1px solid white;border-radius:50%;box-shadow:0 0 2px black;pointer-events:none;z-index:2`;
    if(painting&&performance.now()-lastPaint>30){lastPaint=performance.now();paintSurface(event);}
  }else cursor.style.display='none';
});
function endStroke(){if(painting){painting=false;sync();}}window.addEventListener('pointerup',endStroke);window.addEventListener('pointercancel',endStroke);window.addEventListener('blur',endStroke);canvas.addEventListener('pointerleave',()=>{$('brushCursor').style.display='none';endStroke();});
$('pickMode').onchange=()=>{const brush=$('pickMode').value==='faces';controls.mouseButtons.LEFT=brush?null:THREE.MOUSE.ROTATE;controls.mouseButtons.RIGHT=brush?THREE.MOUSE.ROTATE:THREE.MOUSE.PAN;canvas.style.cursor=brush?'crosshair':'grab';status(brush?'Paint with left-drag. Shift or Erase removes selection. Right-drag orbits; wheel zooms. Choose Use on This Region when ready.':'Click the object to select a region.');};

$('brushSize').addEventListener('input',()=>sync());
$('pickMode').addEventListener('change',()=>sync());
$('preset').onchange=()=>{const p=presets[$('preset').value];if(p){$('description').value=p[0];$('metallic').value=p[1];if($('preset').value==='eyes')$('detail').value=0;sync();}};
for(const id of ['regionName','description','strength','detail','tiles','metallic'])$(id).addEventListener('input',()=>sync());
$('assignButton').onclick=()=>{
  if(!selectedRegions.size)return;const prompt=$('description').value.trim();if(!prompt){status('Enter a material description first.');return;}
  for(const selection of selectedRegions.values()){
    const row={kind:selection.kind,id:selection.id,name:selectedRegions.size===1?$('regionName').value.trim()||selection.name:selection.name,prompt,strength:Number($('strength').value),detail:Number($('detail').value),tiles:Number($('tiles').value),metallic:$('metallic').value};
    if(selection.kind==='faces'){row.face_ranges=rangesOf(selection.faceSet);if(!row.face_ranges.length)continue;}
    selection.name=row.name;state.regions=entries().filter(r=>key(r)!==key(row));state.regions.push(row);
  }
  sync();renderRegions();updateSelectionUI();status(`Material assigned to ${selectedRegions.size} region(s). Generate & Preview applies it while preserving colors.`);
};
$('clearButton').onclick=()=>{brushFaces=new Set();selectedRegions.clear();selected=null;renderRegions();updateSelectionUI();state.selection=[];sync();if(['guide','regions'].includes(currentView))applyOverlay();};
$('saveButton').onclick=()=>{storeSelection();post('material-editor-save',{state});};
$('generateButton').onclick=()=>{if(!entries().length){status('Choose a surface and use a material first, or choose Auto Complete.');return;}status('Queuing material generation in ComfyUI…',true);post('material-editor-apply',{state});};
$('autoButton').onclick=()=>{const existing=new Map(entries().filter(r=>r.kind==='color').map(r=>[r.id,r]));state.regions=meta.regions.map(r=>existing.get(r.id)??({...r,strength:1,detail:.12,tiles:8,metallic:/silver metal/i.test(r.prompt)?'metal':'nonmetal'})).concat(entries().filter(r=>r.kind!=='color'));sync();status('Using suggested materials and your overrides…',true);post('material-editor-apply',{state});};
$('guideView').onclick=()=>{currentView='guide';applyOverlay();};$('regionsView').onclick=()=>{currentView='regions';applyOverlay();};
$('beforeView').onclick=()=>loadModel(asset('source.glb'),'before',true).catch(fail);
$('afterView').onclick=()=>afterUrl&&loadModel(afterUrl,'after',true).catch(fail);
$('fitView').onclick=fit;
function fail(error){console.error(error);status(error.message??String(error),false);}
window.addEventListener('message',event=>{if(event.origin!==location.origin||event.source!==parent)return;const data=event.data;if(data.nonce!==nonce||data.project!==project||data.session!==session)return;if(data.type==='material-editor-flush'){storeSelection();post('material-editor-save',{state});}if(data.type==='material-editor-dispose'){disposed=true;modelLoadVersion++;endStroke();observer.disconnect();controls.dispose();disposeModel();overlayTexture?.dispose();renderer.dispose();renderer.forceContextLoss();return;}if(data.type==='material-editor-init'){
  state=data.state?unpackState(data.state):state;const restore=state.selection??[],draft=state.editorDraft,options=state.editorOptions;restoring=true;
  selectedRegions.clear();visitedRegions.clear();selected=null;brushFaces=new Set();
  if(options){$('pickMode').value=options.pickMode??'color';$('brushSize').value=options.brushSize??12;$('pickMode').dispatchEvent(new Event('change'));}
  for(const row of entries())if(row.kind!=='color')visitedRegions.set(key(row),row);
  for(const row of restore){if(row.kind!=='color')visitedRegions.set(key(row),row);select(row.kind,row.id,0,true);}
  if(draft&&restore.length){$('regionName').value=draft.name;$('description').value=draft.prompt;$('strength').value=draft.strength;$('detail').value=draft.detail;$('tiles').value=draft.tiles;$('metallic').value=draft.metallic;}
  restoring=false;renderRegions();updateSelectionUI();renderAssignments();
}if(data.type==='material-editor-saved')status(data.busy?'Generating assigned materials in ComfyUI�':'Choices saved in this project. Generate & Preview applies assigned material changes.',data.busy??false);if(data.type==='material-editor-status')status(data.message,data.busy);if(data.type==='material-editor-result'){afterUrl=data.result.url;$('afterView').disabled=false;const r=data.result.report;if(r.regions_applied){loadModel(afterUrl,'after',true).then(()=>status(`Applied ${r.regions_applied} material region(s). Geometry, UVs and full-resolution color pixels verified unchanged.`)).catch(fail);}else status('Guide ready. Click a surface to choose its material.');}});
async function init(){
  if(!/^[0-9a-f]{24}$/.test(session))throw Error('Invalid material guide session');
  meta=await(await fetch(asset('metadata.json'))).json();
  const buffers=await Promise.all(['colors.bin','patches.bin','patch-sizes.bin','triangles.bin'].map(async name=>{const r=await fetch(asset(name));if(!r.ok)throw Error('Could not load '+name);return r.arrayBuffer();}));
  colors=new Uint16Array(buffers[0]);patches=new Uint32Array(buffers[1]);patchSizes=new Uint32Array(buffers[2]);triangleMap=new Uint32Array(buffers[3]);
  const image=await new Promise((resolve,reject)=>{const i=new Image();i.onload=()=>resolve(i);i.onerror=reject;i.src=asset('guide.png');});
  const temp=document.createElement('canvas');temp.width=temp.height=meta.guide_size;const ctx=temp.getContext('2d');ctx.drawImage(image,0,0);guidePixels=ctx.getImageData(0,0,temp.width,temp.height);
  renderRegions();await loadModel(asset('guide.glb'),'guide');ready=true;post('material-editor-ready');if(selectedRegions.size)updateSelectionUI();else $('selectionSummary').textContent=`${meta.faces.toLocaleString()} triangles · ${meta.regions.length} color groups · ${meta.patch_count.toLocaleString()} connected patches. Click a surface.`;
  try{const response=await fetch(asset('status.json'));if(response.ok){const s=await response.json();if(s.output){const path=s.output.replaceAll('\\','/'),index=path.lastIndexOf('/output/');if(index>=0){const relative=path.slice(index+8),slash=relative.lastIndexOf('/');afterUrl='/view?filename='+encodeURIComponent(relative.slice(slash+1))+'&subfolder='+encodeURIComponent(relative.slice(0,slash))+'&type=output';$('afterView').disabled=false;}}}}catch{}
}
init().catch(fail);
