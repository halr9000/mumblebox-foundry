import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const source=readFileSync(new URL('../material_lab/material_editor.js',import.meta.url),'utf8');
const initSource=source.slice(source.indexOf('async function init(){'),source.lastIndexOf('init().catch(fail);'));
let release,started;
const loading=new Promise(resolve=>release=resolve),entered=new Promise(resolve=>started=resolve),notifications=[];
let fitted=false;
class ImageFixture {set src(value){queueMicrotask(()=>this.onload());}}
const env={session:'a'.repeat(24),meta:null,colors:null,patches:null,patchSizes:null,triangleMap:null,guidePixels:null,ready:false,
 fetch:async name=>({ok:!name.endsWith('status.json'),json:async()=>({faces:10,guide_size:1,regions:[],patch_count:0}),arrayBuffer:async()=>new ArrayBuffer(4)}),
 asset:name=>name,Image:ImageFixture,document:{createElement:()=>({getContext:()=>({drawImage(){},getImageData:()=>({data:new Uint8Array(4)})})})},
 renderRegions(){},post:type=>notifications.push({type,fitted,ready:env.ready}),loadModel:async()=>{started();await loading;fitted=true;},
 selectedRegions:new Map(),updateSelectionUI(){},$:()=>({textContent:''})};
const init=new Function('env','with(env){'+initSource+';return init;}')(env);
const pending=init();await entered;
assert.equal(notifications.length,0,'The host must not send a saved result before the initial guide has established its camera');
release();await pending;
assert.deepEqual(notifications,[{type:'material-editor-ready',fitted:true,ready:true}]);
console.log('Saved material results arrive only after the guide is framed and ready for picking.');
// Twenty replacement/close cycles must dispose each owned resource exactly once.
const disposeSource=source.slice(source.indexOf('function disposeModel(){'),source.indexOf('function fit(){'));
for(let cycle=0;cycle<20;cycle++){
 const counts={geometry:0,bvh:0,source:0,guide:0,texture:0};
 const texture={isTexture:true,dispose(){counts.texture++;}};
 const original={map:texture,dispose(){counts.source++;}},guide={dispose(){counts.guide++;}};
 const mesh={isMesh:true,geometry:{dispose(){counts.geometry++;},disposeBoundsTree(){counts.bvh++;}},material:original,userData:{sourceMaterial:original,guideMaterial:guide}};
 const model={traverse:visit=>visit(mesh)};
 const fixture={model,overlayTexture:null,scene:{remove(){}}};
 const dispose=new Function('fixture','with(fixture){'+disposeSource+';return disposeModel;}')(fixture);
 dispose();dispose();
 assert.deepEqual(counts,{geometry:1,bvh:1,source:1,guide:1,texture:1});
}
console.log('Twenty editor disposal cycles release geometry, BVH, source/guide materials and maps exactly once.');
