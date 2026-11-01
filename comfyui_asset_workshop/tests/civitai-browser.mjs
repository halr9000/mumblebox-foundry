import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const storage=new Map();
class Element {
    constructor(tag){this.tag=tag;this.children=[];this.isConnected=true;this.value=undefined;this.max=undefined;this.hidden=false;this.disabled=false;}
    append(...children){this.children.push(...children);}
    replaceChildren(...children){this.children=children;}
    setAttribute(key,value){this[key]=value;}
    addEventListener(){}
}
const source=fs.readFileSync(new URL('../web/civitai-browser.js',import.meta.url),'utf8')
    .replace(/^import .*;$/mg,'').replace(/export class /g,'class ');
const {BrowserState,CivitaiBrowser}=vm.runInNewContext(source+';({BrowserState,CivitaiBrowser})',{
    localStorage:{getItem:key=>storage.get(key),setItem:(key,value)=>storage.set(key,value)},
    URLSearchParams,setTimeout,clearTimeout,queueMicrotask,console,
    document:{createElement:tag=>new Element(tag)}});
const state=new BrowserState();
state.items=[{id:1}];state.selected={id:1};state.cursor='old';state.nsfw=true;
const old=state.sequence;
state.changeNsfw(false);
assert.equal(state.items.length,0,'Turning mature content off must immediately clear old previews');
assert.equal(state.selected,null);
assert.equal(state.cursor,null);
assert.equal(state.accept(old,{items:[{id:2}],next_cursor:'stale'},false),false,'A stale mature search must not repopulate results');
assert.equal(new BrowserState().nsfw,false);
state.accept(state.sequence,{items:[{id:2}],next_cursor:'next'},false);
state.accept(state.sequence,{items:[{id:2},{id:3}],next_cursor:null},true);
assert.equal(state.items.length,2,'Load more must deduplicate resources');
const host={project:{profile:'sdxl_base'},root:{scrollTop:40},render(){this.rendered=true;}};
const browser=new CivitaiBrowser(host);
let searches=0;browser.search=async()=>{searches++;browser.state.initialized=true;};
await browser.open('Checkpoint');
assert.equal(host.tab,'Integrations');
assert.equal(browser.state.profile,'sdxl_base');
assert.equal(browser.state.kind,'Checkpoint');
assert.equal(host.root.scrollTop,0);
assert.equal(searches,1);
await browser.open('LORA');
assert.equal(browser.state.kind,'LORA');
assert.equal(searches,2);
let focused=false,scrolled=false;
host.root.querySelector=selector=>{assert.equal(selector,'[data-service="civitai"]');return {
    scrollIntoView(){scrolled=true;},querySelector(){return {focus(){focused=true;}};}};};
browser.openSettings();
assert.equal(host.tab,'Settings');assert.equal(focused,true);assert.equal(scrolled,true);
assert.equal(browser.returnToBrowser,true);
browser.download={status:'running',phase:'Downloading',bytes:4096,total:8192};
const progress=browser.progress();
assert.equal(progress.children[1].value,4096);
assert.equal(progress.children[1].max,8192);
browser.download.total=0;browser.updateProgress();
assert.equal(progress.children[1].value,undefined,'Unknown totals must remain indeterminate');
browser.download.status='paused';browser.updateProgress();
assert.equal(progress.hidden,false,'Navigation must retain interrupted download status');
browser.download.status='completed';host.tab='Create image';browser.updateProgress();
assert.equal(progress.hidden,true,'Completed downloads must not advertise a different checkpoint on Create image');
host.tab='Integrations';browser.updateProgress();
assert.equal(progress.hidden,false,'Completed downloads remain available in Integrations');
browser.download.status='running';host.tab='Create image';browser.updateProgress();
assert.equal(progress.hidden,false,'Active downloads keep their progress controls');
console.log('Civitai filters, stale-result protection, mature preview clearing, shortcuts and Settings deep link passed.');
