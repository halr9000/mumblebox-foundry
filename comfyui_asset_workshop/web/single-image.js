import {app} from "../../../scripts/app.js";
import {api} from "../../../scripts/api.js";
import {request, PREFIX, connectVisibleClient} from "./job-client.js";
import {openImageEditor} from "./image-editor.js?v=20261023-cutout";
import {downloadProgress} from "./creator.js";
import {CivitaiBrowser} from "./civitai-browser.js";
import {renderMeshPipeline} from "./mesh-pipeline.js";
import {modelUsageRows} from "./model-usage.js";

const names = {source:"Source image",design:"Chosen design",mesh_input:"Image for the mesh",
    reference_front:"Front reference",reference_back:"Back reference",reference_left:"Left reference",reference_right:"Right reference"};
const refs = Object.keys(names).filter(k=>k.startsWith("reference_"));
const active = job=>job && ["running","queued"].includes(job.state);
const delay = ms=>new Promise(resolve=>setTimeout(resolve,ms));
const clone = value=>JSON.parse(JSON.stringify(value));
const brandLogo = new URL("./assets/mumblebox-star.png",import.meta.url).href;
const modelUses = {sdxl_base:"Flexible styles and a mature LoRA library.",sdxl_juggernaut:"Photographic rendering with SDXL LoRAs.",
    qwen21:"Detailed descriptions and multiple references.",qwen2511:"Instruction-based edits to an existing image.",
    klein4:"Fast image creation and editing.",klein4_base:"More sampling control than the four-step version.",
    klein_distilled:"Larger four-step model; uses more memory.",klein_base:"Larger model with adjustable sampling.",
    klein_kv:"Reference editing with cached image features.",flux3_base:"Full descriptions with adjustable sampling.",
    flux3_distilled:"Create or edit with a full image description."};
function el(tag, attrs={}, ...children) {
    const node=document.createElement(tag);
    for(const [key,value] of Object.entries(attrs)) {
        if(key.startsWith("on")) node.addEventListener(key.slice(2),value);
        else if(key in node) node[key]=value;
        else node.setAttribute(key,value);
    }
    node.append(...children.flat().filter(c=>c!==null && c!==undefined));
    return node;
}
async function legacy(path,body,method) {
    const response=await api.fetchApi("/asset-workshop"+path,{method:method||(body===undefined?"GET":"POST"),
        ...(body===undefined?{}:{headers:{"Content-Type":"application/json"},body:JSON.stringify(body)})});
    const data=await response.json();
    if(!response.ok) throw Error(data.error || response.statusText);
    return data;
}
function styles() {
    if(document.getElementById("mumblebox-single-styles"))return;
    document.head.append(el("link",{id:"mumblebox-single-styles",rel:"stylesheet",href:new URL("./creator.css",import.meta.url).href}));
}

function controlStyles() {
    if(!document.getElementById("mumblebox-control-styles"))document.head.append(el("link",{
        id:"mumblebox-control-styles",rel:"stylesheet",href:new URL("./single-image.css",import.meta.url).href}));
    if(!document.getElementById("mumblebox-civitai-styles"))document.head.append(el("link",{
        id:"mumblebox-civitai-styles",rel:"stylesheet",href:new URL("./civitai-browser.css",import.meta.url).href}));
}

export class SingleImageControls {
    constructor(node) {
        styles();
        controlStyles();
        this.node=node;
        this.tab="Create image";this.project=null;this.job=null;this.busy=false;this.notice="";this.offset=0;this.undo=[];
        this.civitai=new CivitaiBrowser(this);
        this.root=el("section",{class:"aw aw-single-controls","aria-label":"Mumblebox single-image controls"});
        node.root.replaceChildren(this.root);
        this.disconnect=connectVisibleClient(()=>this.root.isConnected&&!document.hidden,error=>this.status(error.message,true),async stage=>{
            this.project=await request(`/projects/${stage.project_id}`);
            this.job=await request(`/projects/${stage.project_id}/jobs/${stage.job_id}`);this.render();
        },graph=>this.showStageGraph(graph));
        this.onProgress=event=>{
            if(!active(this.job)||!this.job.prompt_ids?.includes(event.detail?.prompt_id)) return;
            this.nativeProgress=event.detail;this.updateProgress();
        };
        api.addEventListener("progress",this.onProgress);
        this.timer=setInterval(()=>this.poll().catch(error=>this.status(error.message,true)),1800);
        this.ready=this.initialize();
    }
    dispose() {
        this.civitai.dispose();
        clearInterval(this.timer);this.disconnect();api.removeEventListener("progress",this.onProgress);
        this.viewerInteractionCleanup?.();this.viewer?.remove();this.viewerResize?.disconnect();this.root.remove();
        if(app.mumbleboxSingle===this)app.mumbleboxSingle=null;
    }
    async showStageGraph(graph) {
        const previous=this.node,position=[...previous.pos],size=[...previous.size];
        const scale=app.canvas.ds.scale,offset=[...app.canvas.ds.offset];
        this.transferring=true;
        try {
            await app.loadApiJson(graph,app.extensionManager.workflow.activeWorkflow);
            const controller=LiteGraph.createNode(previous.type);
            controller.properties=clone(previous.properties);controller.pos=position;controller.size=size;
            controller.singleControls=this;this.node=controller;
            const nodes=[...app.graph._nodes];
            const left=Math.min(0,...nodes.map(node=>node.pos[0])),top=Math.min(0,...nodes.map(node=>node.pos[1]));
            for(const node of nodes) {node.pos[0]+=position[0]+size[0]+80-left;node.pos[1]+=position[1]-top;}
            app.graph.add(controller);controller.render();
            app.canvas.ds.scale=scale;app.canvas.ds.offset=offset;
            app.graph.setDirtyCanvas(true,true);
        } finally {this.transferring=false;}
    }
    async initialize() {
        try {
            [this.capabilities,this.presets,this.loraList]=await Promise.all([request("/capabilities"),request("/presets"),request("/loras")]);
            this.project=await request("/projects",{});
            this.render();await this.poll();
        } catch(error) {this.root.replaceChildren(el("div",{class:"content"},el("h2",{},"Mumblebox"),el("p",{class:"error"},error.message),
            this.button("Retry connection",()=>this.initialize())));}
    }
    path(suffix="") {return `/projects/${this.project.id}${suffix}`;}
    url(record,download=false) {return `${PREFIX}${this.path(`/artifacts/${record.id}`)}${download?"?download=1":""}`;}
    fileURL(file) {return `/asset-workshop/file/${this.project.id}?path=${encodeURIComponent(file)}`;}
    current(role) {const slot=this.project.images[role];return slot.revisions.find(r=>r.id===slot.current);}
    status(message,error=false) {
        this.notice=error?message:"";this.hasError=error;
        if(this.noticeNode){this.noticeNode.textContent=this.notice;this.noticeNode.hidden=!error;}
    }
    async action(callback) {
        this.busy=true;
        try {await callback();} catch(error) {this.status(error.message,true);if(error.status===409) await this.refresh();}
        finally {this.busy=false;this.render();}
    }
    button(label,callback,reason="",className="") {
        const button=el("button",{type:"button",class:className,disabled:!!reason,title:reason,onclick:()=>this.action(callback)},label);
        return button;
    }
    link(label,url) {return el("a",{href:url,class:"download",download:""},label);}
    hint(text) {return el("p",{class:"hint"},text);}
    help(label,text) {return el("details",{class:"help-panel"},el("summary",{},label),...text.split(/\n+/).map(line=>this.hint(line)));}
    blocked() {return this.helperBusy?"Wait for the description assistant or stop it first.":active(this.job)?"Wait for the current job or stop it first.":"";}
    imageBlocked() {
        const profiles=this.capabilities.profiles,sdxl=profiles[this.project.profile].lora.architecture==="sdxl";
        const mismatch=this.project.loras.find(l=>l.enabled!==false&&(Number(l.strength)!==0||sdxl&&Number(l.strength_clip??l.strength)!==0)&&
            !this.loraMatches(l.name));
        return this.blocked()||(mismatch?`A saved LoRA does not match this model. Choose a compatible Style / LoRA or None.`:"");
    }
    loraMatches(name,profile=this.project.profile) {
        const local=(this.loraList.items||[]).find(item=>item.name===name);
        if(local)return local.profiles.includes(profile);
        // A local but unidentified file must never inherit a download's identity.
        if((this.loraList.files||[]).includes(name))return false;
        return (this.loraList.downloadable||[]).some(item=>item.name===name&&item.profiles?.includes(profile));
    }
    loraOptions() {
        const options=Object.fromEntries((this.loraList.items||[]).filter(item=>this.loraMatches(item.name)).map(item=>[item.name,item.name]));
        for(const item of this.loraList.downloadable||[])if(this.loraMatches(item.name)&&!(item.name in options))
                options[item.name]=`${item.name} — optional first-use download`;
        return options;
    }
    async selectImageProfile(profile) {
        await this.loraQueue?.catch(()=>{});
        this.loraSearch="";
        const loras=this.project.loras.map(item=>({...item,profile:this.loraMatches(item.name,profile)?profile:item.profile,
            enabled:item.enabled!==false&&this.loraMatches(item.name,profile)}));
        const disabled=this.project.loras.filter((item,i)=>item.enabled!==false&&!loras[i].enabled).length;
        await this.save({profile,loras});
        if(disabled)this.status(`${disabled} LoRA${disabled===1?" was":"s were"} turned off because ${disabled===1?"it does":"they do"} not match the selected model.`);
    }
    setLoraEnabled(name,enabled) {
        const projectId=this.project.id,profile=this.project.profile;
        const pending=(this.loraQueue||Promise.resolve()).catch(()=>{}).then(async()=>{
            await this.saveQueue;
            if(this.project.id!==projectId||this.project.profile!==profile)throw Error("The model or job changed. Select the LoRA again.");
            if(enabled&&!this.loraMatches(name))throw Error("Choose a LoRA compatible with the selected image model.");
            const values=clone(this.project.loras),existing=values.find(item=>item.name===name);
            if(existing){existing.enabled=enabled;if(enabled)existing.profile=profile;}
            else if(enabled)values.push({name,profile,strength:1,strength_clip:1,enabled:true,
                trigger:(this.loraList.downloadable||[]).find(item=>item.name===name)?.trigger||""});
            await this.save({loras:values});
        });
        this.loraQueue=pending;return pending;
    }
    loadLocalLoras() {return request("/loras");}
    loraHelp(name) {
        const source=(this.civitai.installed||[]).find(item=>item.kind==="LORA"&&item.relative_path?.replaceAll("\\","/")===name.replaceAll("\\","/"));
        const download=(this.loraList.downloadable||[]).find(item=>item.name===name);
        const notes=typeof source?.notes==="string"?source.notes.trim().slice(0,12000):"";
        const triggers=(Array.isArray(source?.triggers)?source.triggers:download?.trigger?[download.trigger]:[])
            .filter(value=>typeof value==="string"&&value.trim()).slice(0,20).map(value=>value.slice(0,200));
        return {title:source?.model_name||name.split(/[\\/]/).pop(),notes,triggers,
            creator:source?.creator,baseModel:source?.base_model,license:source?.license,
            sourceURL:source?.source_url,licenseURL:source?.license_url,guide:source?.guide,
            permissions:source?.permissions};
    }
    loraHelpControl(label,info) {
        const id=`lora-guide-${crypto.randomUUID()}`;
        let pinned=false,timer;
        const tip=el("div",{id,popover:"auto",class:"lora-tooltip",role:"tooltip",tabIndex:0},el("strong",{},info.title||label));
        if(info.creator||info.baseModel)tip.append(el("p",{class:"lora-provenance"},[info.creator?`By ${info.creator}`:"",info.baseModel].filter(Boolean).join(" · ")));
        tip.append(el("p",{},info.notes||"No author description has been saved for this file."));
        const details=el("dl",{class:"lora-guide-details"});
        if(info.triggers.length)details.append(el("dt",{},"Trigger words"),el("dd",{},info.triggers.join(", ")));
        for(const [title,text] of Object.entries(info.guide||{}).slice(0,12))if(typeof text==="string")details.append(el("dt",{},title),el("dd",{},text));
        if(info.license)details.append(el("dt",{},"License"),el("dd",{},info.license));
        for(const [label,value] of modelUsageRows(info.permissions))details.append(el("dt",{},label),el("dd",{},value));
        if(details.children.length)tip.append(details);
        const links=el("div",{class:"row"});
        for(const [title,url] of [["Author’s page",info.sourceURL],["License & usage",info.licenseURL]]) {
            if(typeof url==="string"&&/^https:\/\//i.test(url))links.append(el("a",{href:url,target:"_blank",rel:"noopener noreferrer"},title));
        }
        if(links.children.length)tip.append(links);
        const close=()=>{clearTimeout(timer);pinned=false;if(tip.matches(":popover-open"))tip.hidePopover();};
        const open=()=>{
            clearTimeout(timer);if(!tip.isConnected)return;
            if(!tip.matches(":popover-open"))tip.showPopover();
            const rect=button.getBoundingClientRect(),width=Math.min(320,innerWidth-24);
            tip.style.width=`${width}px`;tip.style.maxHeight=`${Math.max(100,Math.min(300,innerHeight-24))}px`;
            const height=tip.getBoundingClientRect().height,below=innerHeight-rect.bottom-12;
            tip.style.left=`${Math.max(12,Math.min(rect.right-width,innerWidth-width-12))}px`;
            tip.style.top=`${Math.max(12,Math.min(below>=height?rect.bottom+5:rect.top-height-5,innerHeight-height-12))}px`;
        };
        const leave=()=>{clearTimeout(timer);timer=setTimeout(()=>{
            if(!pinned&&document.activeElement!==button&&!tip.contains(document.activeElement)&&!tip.matches(":hover"))close();
        },160);};
        const button=el("button",{type:"button",class:"lora-info","aria-label":`About ${label}`,"aria-controls":id,"aria-expanded":"false",
            onpointerenter:event=>{if(event.pointerType==="mouse")open();},onpointerleave:leave,onfocus:open,onblur:leave,
            onclick:event=>{event.stopPropagation();if(pinned)close();else{pinned=true;open();}}},"?");
        tip.addEventListener("pointerenter",()=>clearTimeout(timer));tip.addEventListener("pointerleave",leave);
        tip.addEventListener("focusin",()=>clearTimeout(timer));tip.addEventListener("focusout",leave);
        tip.addEventListener("toggle",()=>{
            const shown=tip.matches(":popover-open");button.setAttribute("aria-expanded",String(shown));
            if(shown)button.setAttribute("aria-describedby",id);else{button.removeAttribute("aria-describedby");pinned=false;}
        });
        return el("span",{class:"lora-info-wrap"},button,tip);
    }
    async resetModelDefaults() {
        const settings={steps:null,cfg:null};
        if(this.capabilities.profiles[this.project.profile].lora.architecture==="sdxl")Object.assign(settings,{
            sdxl_sampler:"dpmpp_2m",sdxl_scheduler:"karras",sdxl_source_mode:"reference",sdxl_reference_strength:.8,
            sdxl_img2img_denoise:.65,sdxl_edit_denoise:.85});
        await this.save({settings});
    }
    input(label,value,onchange,attrs={}) {
        const field=el("input",{value:value??"",disabled:!!this.blocked(),"data-control":label,...attrs});
        field.onchange=()=>{if(!field.checkValidity()){field.reportValidity();return;}this.action(()=>onchange(field.value));};
        return el("label",{class:"field"},el("span",{},label),field);
    }
    text(label,value,onchange,hideLabel=false) {
        return el("label",{class:"field"},el("span",{class:hideLabel?"visually-hidden":""},label),el("textarea",{value:value||"",disabled:!!this.blocked(),"data-control":label,onchange:event=>this.action(()=>onchange(event.target.value))}));
    }
    select(label,values,value,onchange) {
        return el("label",{class:"field"},el("span",{},label),el("select",{disabled:!!this.blocked(),"data-control":label,onchange:event=>this.action(()=>onchange(event.target.value))},
            Object.entries(values).map(([key,text])=>el("option",{value:key,selected:key===String(value)},text))));
    }
    check(label,checked,onchange,hint="") {
        return el("label",{class:"check toggle",title:hint},el("input",{type:"checkbox",role:"switch",checked,disabled:!!this.blocked(),"data-control":label,
            onchange:event=>this.action(()=>onchange(event.target.checked))}),el("span",{class:"toggle-track","aria-hidden":"true"}),el("span",{},label));
    }
    grid(columns,...children) {return el("div",{class:`control-grid columns-${columns}`},...children);}
    panel(title,description,...children) {
        return el("section",{class:"control-panel","aria-label":title},el("header",{class:"panel-heading"},el("h3",{},title),description?this.hint(description):null),...children);
    }
    disclosure(title,...children) {return el("details",{class:"control-disclosure"},el("summary",{},title),el("div",{class:"disclosure-body"},...children));}
    range(label,value,onchange,{min=0,max=1,step=.1,defaultValue=0,resetValue=defaultValue,help="",unit=""}={}) {
        const key=`range-${label}`,number=el("input",{type:"number",min,max,step,value,"aria-label":`${label} value`,
            "data-control":`${key}-value`,disabled:!!this.blocked()});
        const slider=el("input",{type:"range",min,max,step,value,"aria-label":label,"data-control":key,disabled:!!this.blocked()});
        const sync=()=>{number.value=slider.value;slider.style.setProperty("--fill",`${(Number(slider.value)-min)/(max-min)*100}%`);};
        slider.oninput=sync;sync();
        const commit=field=>{if(!field.checkValidity()){field.reportValidity();return;}this.action(()=>onchange(Number(field.value)));};
        slider.onchange=()=>commit(slider);number.onchange=()=>commit(number);
        const reset=this.button("Reset",()=>onchange(resetValue),this.blocked(),"control-reset");
        reset.title=`Reset ${label.toLowerCase()} to ${defaultValue}${unit}`;reset.setAttribute("aria-label",reset.title);
        return el("div",{class:"range-control"},el("div",{class:"range-title"},el("span",{},label),
            el("span",{class:"range-default"},`Default ${defaultValue}${unit}`),
            help?el("details",{class:"control-help"},el("summary",{"aria-label":`Help for ${label}`},"?"),el("p",{},help,` Default: ${defaultValue}${unit}.`)):null),
            el("div",{class:"range-values"},slider,number,reset));
    }
    numericSetting(label,value,onchange,{min,max,step,defaultValue,help}) {
        const input=this.input(label,value,v=>onchange(Number(v)),{type:"number",min,max,step,required:true,"aria-label":`${label} value`});
        input.classList.add("numeric-setting");
        const explanation=el("details",{class:"control-help"},el("summary",{"aria-label":`Help for ${label}`},"?"),el("p",{},help));
        input.firstElementChild.append(explanation);
        return el("div",{class:"numeric-setting-group"},input,el("span",{class:"setting-default"},`Default ${defaultValue}`));
    }
    lastImageSeed() {
        const records=Object.values(this.project.images).flatMap(slot=>slot.revisions).filter(r=>Number.isSafeInteger(r.recipe?.seed)&&r.recipe.seed>=0);
        return records.sort((a,b)=>(b.created||0)-(a.created||0))[0]?.recipe.seed;
    }
    randomSeed() {return crypto.getRandomValues(new Uint32Array(1))[0];}
    async setSeedMode(mode) {
        const current=this.project.settings.requested_seed;
        await this.save({settings:{requested_seed:mode==="randomize"?-1:current>=0?current:this.lastImageSeed()??this.randomSeed(),seed_mode:mode}});
    }
    async shuffleSeed() {
        await this.save({settings:{requested_seed:this.randomSeed(),seed_mode:"fixed"}});
        this.status("A new seed is ready to reuse. No image was generated.");
    }
    async reuseLastSeed() {
        const seed=this.lastImageSeed();if(seed===undefined)return;
        await this.save({settings:{requested_seed:seed,seed_mode:"fixed"}});
    }
    async copySeed() {
        const seed=this.project.settings.requested_seed>=0?this.project.settings.requested_seed:this.lastImageSeed();
        if(seed===undefined)return;
        await navigator.clipboard.writeText(String(seed));this.status(`Seed ${seed} copied.`);
    }
    seedControls() {
        const seed=this.project.settings.requested_seed,last=this.lastImageSeed();
        const reuse=this.button("Reuse seed",()=>this.setSeedMode("fixed"),this.blocked(),seed>=0?"selected":"");
        const random=this.button("Random each time",()=>this.setSeedMode("randomize"),this.blocked(),seed<0?"selected":"");
        for(const [button,on] of [[random,seed<0],[reuse,seed>=0]])button.setAttribute("aria-pressed",String(on));
        const input=seed>=0?this.input("Seed to reuse",seed,v=>this.save({settings:{requested_seed:Number(v),seed_mode:"fixed"}}),
            {type:"number",min:0,max:Number.MAX_SAFE_INTEGER,step:1,required:true}):null;
        input?.classList.add("seed-value");
        return el("section",{class:"seed-panel","aria-label":"Image seed"},el("div",{class:"seed-line"},el("h4",{},"Seed"),
            el("div",{class:"segmented",role:"group","aria-label":"Image seed behavior"},random,reuse),input,
            this.button("Shuffle",()=>this.shuffleSeed(),this.blocked(),"quiet"),
            seed>=0?this.button("Copy seed",()=>this.copySeed(),"","quiet"):null),
            last===undefined?null:el("div",{class:"seed-last"},el("span",{},"Last used: ",el("strong",{},String(last))),
                this.button("Reuse last",()=>this.reuseLastSeed(),this.blocked(),"text-button"),
                this.button("Copy last",async()=>{await navigator.clipboard.writeText(String(last));this.status(`Seed ${last} copied.`);},"","text-button")),
            this.help("How seeds work","Random chooses a new seed for each image. Reuse keeps the same number; the model, prompt and settings also affect the result. Shuffle chooses a new number to reuse without generating an image."));
    }
    async refresh() {if(this.project)this.project=await request(this.path());}
    async save(changes,expected=null) {
        const projectId=this.project.id;
        const pending=(this.saveQueue||Promise.resolve()).catch(()=>{}).then(async()=>{
            const result=await request(`/projects/${projectId}`,{expected_revision:expected??this.project.revision,changes},"PATCH");
            if(this.project.id===projectId)this.project=result;
        });
        this.saveQueue=pending;await pending;
    }
    async setting(key,value) {await this.save({settings:{[key]:value}});}
    async post(suffix,body={}) {
        await this.saveQueue;
        const result=await request(this.path(suffix),{expected_revision:this.project.revision,...body});
        this.project=result.project || result;return result;
    }
    async start(kind,payload={}) {
        await this.saveQueue;await this.refresh();this.nativeProgress=null;
        const stages=["texture_mesh","prepare_variant","prepare_material_guide","apply_materials"].includes(kind)?[]:kind==="build_geometry"?["image","mesh"]:kind==="build_mesh_package"?["image","mesh"]:kind==="prepare_foreground"?["prepare"]:kind==="finish_mesh"?[]:["image"];
        for(const stage of stages) if(!await this.downloadModels(stage,kind))
            throw Error("Required model files are missing. Follow the download setup, then retry this action. No generation was started.");
        this.job=await request(this.path("/jobs"),{expected_revision:this.project.revision,kind,request_key:crypto.randomUUID(),payload});
        this.status("Job started. Its native graph appears in this Desktop before execution.");this.render();
        if(this.root&&this.progressNode)this.root.scrollTop=this.progressNode.offsetTop-60;
        return this.job;
    }
    async waitJob(job) {
        while(true) {
            const latest=await request(this.path(`/jobs/${job.id}`));this.job=latest;
            this.updateProgress();
            if(!active(latest)) {
                await this.refresh();
                if(latest.state!=="completed"&&latest.state!=="awaiting_review") throw Error(latest.error?.message||latest.cleanup_error||`Job ${latest.state}.`);
                return latest;
            }
            await delay(800);
        }
    }
    async poll() {
        if(!this.root.isConnected) return;
        this.resources=await legacy("/status");this.updateResources();
        await this.civitai.poll();
        if(this.project&&!active(this.job)&&!this.busy&&!this.root.querySelector("input:focus,textarea:focus,select:focus")) {
            const projectId=this.project.id;
            const latest=await request(`/projects/${projectId}`);
            if(this.project?.id!==projectId)return;
            const running=latest.jobs.find(j=>active(j));
            if(running) {
                const job=await request(`/projects/${projectId}/jobs/${running.id}`);
                if(this.project?.id!==projectId)return;
                this.job=job;
            }
            if(latest.revision>this.project.revision){this.project=latest;this.render();}
        }
        if(this.job&&active(this.job)) {
            const previous=this.job,projectId=this.project.id;
            const next=await request(`/projects/${projectId}/jobs/${previous.id}`);
            if(this.project?.id!==projectId||this.job?.id!==previous.id)return;
            this.job=next;
            this.updateProgress();
            if(!active(this.job)) {
                await this.refresh();
                this.status(this.job.error?.message||this.job.cleanup_error||"Saved results are ready to review.",this.job.state==="failed");
                if(["create_image","three_quarter"].includes(this.job.kind)&&this.job.state==="completed") this.tab="Approve image";
                this.render();
            } else if(previous.phase!==this.job.phase) this.nativeProgress=null;
        }
    }
    updateResources() {
        if(!this.resourceNode||!this.resources) return;
        const s=this.resources,gb=n=>(n/1024**3).toFixed(1);
        this.resourceNode.textContent=`CPU ${Math.round(s.cpu_percent)}% · RAM ${gb(s.ram_used)} / ${gb(s.ram_total)} GB · VRAM ${gb(s.vram_used)} / ${gb(s.vram_total)} GB`;
        const progress=downloadProgress(s.download);
        const complete=s.description_helper?.running?"The description model is ready. The assistant is continuing.":
            "Model files are ready. Retry the original action when you are ready.";
        if(s.download?.status==="complete"&&["running","failed","paused"].includes(this.lastDownloadStatus))this.status(complete);
        this.lastDownloadStatus=s.download?.status;
        if(this.downloadNode) this.downloadNode.textContent=progress?.message||s.download?.error||
            (s.download?.status==="complete"?complete:s.description_helper?.running?s.description_helper.phase:"No model download running.");
        if(this.downloadMeter) {this.downloadMeter.hidden=!progress;if(progress?.progress?.max){this.downloadMeter.max=progress.progress.max;this.downloadMeter.value=progress.progress.value;}else this.downloadMeter.removeAttribute("value");}
        if(this.inlineDownloadNode) {
            this.inlineDownloadNode.hidden=!progress;
            if(progress) {
                this.inlineDownloadText.textContent=progress.message;
                if(progress.progress?.max){this.inlineDownloadMeter.max=progress.progress.max;this.inlineDownloadMeter.value=progress.progress.value;}
                else this.inlineDownloadMeter.removeAttribute("value");
            }
        }
        this.updateDownloadRecovery();
        this.updateDescriptionStatus();
        this.updateWorkingIndicator();
        if(this.helperBusy) this.updateProgress();
    }
    openModelConnection() {
        this.tab="Settings";this.render();
        const field=this.root.querySelector('[aria-label="Hugging Face token"]');
        field?.scrollIntoView({block:"center"});field?.focus();
    }
    async retryDownload() {
        const retry=this.resources?.download?.request;
        if(!retry||retry.asset_id!==this.project.id) throw Error("Return to the job whose download stopped before retrying it.");
        if(retry.kind==="description") {
            if(!["describe","enhance"].includes(retry.action)) throw Error("Return to Create image and retry the description assistant.");
            return this.describe(retry.action);
        }
        await legacy(`/assets/${retry.asset_id}/download`,{retry:true,accept_licenses:true});
        this.status("Retrying the original model download. Completed files are reused and partial files resume when supported. Retry generation after the download finishes.");
        await this.poll();
    }
    updateDownloadRecovery() {
        if(!this.downloadRecoveryNode) return;
        const download=this.resources?.download;
        const key=JSON.stringify([download?.status,download?.error,download?.source,download?.recovery,download?.request,this.project.id,this.blocked()]);
        if(this.downloadRecoveryKey===key)return;
        this.downloadRecoveryKey=key;this.downloadRecoveryNode.replaceChildren();
        this.downloadRecoveryNode.hidden=!["failed","paused"].includes(download?.status);
        if(this.downloadRecoveryNode.hidden)return;
        const access=download.recovery?.kind==="access",source=download.recovery||download.source;
        const link=(label,url)=>el("a",{href:url,target:"_blank",rel:"noopener noreferrer"},label);
        this.downloadRecoveryNode.append(el("h3",{},access?"Hugging Face access is needed":"Model download stopped"),
            this.hint(download.error||"The download was paused. Downloaded files are retained."));
        if(access)this.downloadRecoveryNode.append(el("ol",{},
            el("li",{},"Open the model page below. Sign in, then request access or accept its terms. Some repositories require the author's approval."),
            el("li",{},"Connect a Hugging Face read token for that same account. An existing token must also have permission to read this repository."),
            el("li",{},"After access is approved and the token is connected, retry. Generation will not restart automatically.")));
        if(source?.repo_url)this.downloadRecoveryNode.append(el("div",{class:"row"},
            link(`Open Hugging Face model page — ${source.model}`,source.repo_url),
            ...(source.license_url?[link("Read this model's license",source.license_url)]:[])));
        const retry=download.request;
        const retryReason=this.blocked()||(!retry||retry.asset_id!==this.project.id?"Return to the original job to retry its download.":
            retry.kind==="description"&&!["describe","enhance"].includes(retry.action)?"Retry the original description action from Create image.":"");
        this.downloadRecoveryNode.append(el("div",{class:"row"},
            el("button",{disabled:!!this.blocked(),title:this.blocked(),onclick:()=>this.openModelConnection()},"Connect Hugging Face"),
            this.button(retry?.kind==="description"?"Retry description assistant":"Retry download",()=>this.retryDownload(),retryReason)));
        if(access){
            this.downloadRecoveryNode.style.scrollMarginTop=`${this.root.querySelector(".brand").getBoundingClientRect().height}px`;
            this.downloadRecoveryNode.scrollIntoView({block:"start"});
        }
    }
    updateProgress() {
        this.updateWorkingIndicator();
        if(!this.progressNode) return;
        this.progressNode.hidden=!this.job&&!this.helperBusy;
        const helperPhase=this.resources?.description_helper?.phase;
        this.phaseNode.textContent=this.helperBusy?(helperPhase&&helperPhase!=="idle"?helperPhase:"Preparing description assistant"):
            this.job?`${this.job.phase}${this.job.error?"\n"+this.job.error.message:""}`:"";
        if(this.nativeProgress?.max) {this.meter.max=this.nativeProgress.max;this.meter.value=this.nativeProgress.value;}
        else this.meter.removeAttribute("value");
        this.meter.hidden=!active(this.job)&&!this.helperBusy;
    }
    render() {
        if(!this.project||!this.root.isConnected) return;
        const scroll=this.root.scrollTop,focused=this.root.contains(document.activeElement)?document.activeElement:null;
        const focusKey=focused?.dataset?.control,selection=focused&&["textarea","input"].includes(focused.localName)&&focused.type!=="number"?{start:focused.selectionStart,end:focused.selectionEnd}:null;
        const expanded=new Set([...this.root.querySelectorAll("details[open]")]
            .map(detail=>detail.dataset.disclosure||detail.querySelector(":scope > summary")?.textContent));
        this.viewerInteractionCleanup?.();this.viewer?.remove();this.viewer=null;this.viewerResize?.disconnect();
        this.root.replaceChildren();
        this.root.append(el("header",{class:"brand"},el("span",{class:"brand-mark","aria-hidden":"true"},
            el("img",{src:brandLogo,alt:"",width:40,height:40})),
            el("div",{},el("h2",{},"Mumblebox"),el("p",{class:"muted"},"3D game & print asset studio"))));
        this.resourceNode=el("span");
        const navigation=el("div",{class:"control-navigation"});this.root.append(navigation);
        this.workingNode=el("span",{class:"working-indicator","aria-hidden":"true"},this.activityIcon());
        this.workingLabel=el("span",{class:"working-label",role:"status","aria-live":"polite",hidden:true});
        navigation.append(el("div",{class:"stats"},this.resourceNode,this.workingLabel,this.button("Free RAM & VRAM",async()=>{const result=await request("/release",{});this.status(`Model release: ${result.status||"completed"}.`);},this.blocked(),"unload-models")));
        this.root.querySelector(".unload-models").title="Unload Comfy models to release their RAM and VRAM. This does not close other programs or stop another workflow.";
        const tabs=["Create image","Approve image","Mesh & agent package","History","Integrations","Settings"];
        const labels=["Create image","Prepare for 3D","Mesh & export","History","Integrations","Settings"];
        navigation.append(el("nav",{class:"tabs","aria-label":"Mumblebox steps"},this.workingNode,tabs.map((name,index)=>el("button",{
            ...(this.tab===name?{"aria-current":"step"}:{}),onclick:()=>{this.tab=name;this.render();this.root.scrollTop=0;if(name==="History")this.loadHistory();}},index<3?`${index+1}. ${labels[index]}`:name))));
        this.phaseNode=el("div");this.meter=el("progress");
        this.progressNode=el("section",{class:"job-progress","aria-live":"polite"},this.phaseNode,this.meter,
            el("div",{class:"row"},this.button(this.helperBusy?"Stop description assistant":"Stop this job",async()=>{
                if(this.helperBusy) await request(this.path("/describe/cancel"),{});
                else this.job=await request(this.path(`/jobs/${this.job.id}/cancel`),{});
            },active(this.job)||this.helperBusy?"":"No active job."),
            this.button("Retry unfinished stages",()=>this.start(this.job.kind,{resume_job_id:this.job.id}),this.job&&["failed","cancelled","interrupted"].includes(this.job.state)?"":"Retry is available after an interrupted or failed job.")));
        this.noticeNode=el("p",{class:"action-error",role:"alert",hidden:!this.hasError},this.hasError?this.notice:"");
        this.downloadRecoveryNode=el("section",{class:"content help-panel",role:"alert","aria-label":"Model download recovery",hidden:true});
        this.downloadRecoveryKey=null;
        this.inlineDownloadText=el("div");this.inlineDownloadMeter=el("progress");
        this.inlineDownloadNode=el("section",{class:"job-progress download-progress",hidden:true,"aria-label":"Model download progress","aria-live":"polite"},this.inlineDownloadText,this.inlineDownloadMeter);
        this.root.append(this.progressNode,this.inlineDownloadNode,this.civitai.progress(),this.noticeNode,this.downloadRecoveryNode);
        const content=el("main",{class:"content"});this.root.append(content);
        if(this.tab==="Create image") this.renderCreate(content);
        else if(this.tab==="Approve image") this.renderApprove(content);
        else if(this.tab==="Mesh & agent package") this.renderMesh(content);
        else if(this.tab==="Settings") this.renderSettings(content);
        else if(this.tab==="Integrations") this.civitai.render(content);
        else {this.historyNode=content;content.append(this.hint("Loading saved jobs…"));queueMicrotask(()=>this.loadHistory());}
        for(const detail of this.root.querySelectorAll("details"))
            if(expanded.has(detail.dataset.disclosure||detail.querySelector(":scope > summary")?.textContent))detail.open=true;
        this.updateProgress();this.updateResources();
        this.root.scrollTop=scroll;
        if(focusKey) {
            const next=[...this.root.querySelectorAll("[data-control]")].find(field=>field.dataset.control===focusKey);
            next?.focus({preventScroll:true});
            if(selection&&selection.start!==null&&next?.setSelectionRange)next.setSelectionRange(selection.start,selection.end);
        }
    }
    modelGuide() {
        return el("details",{class:"help-panel model-guide"},el("summary",{},"What model should I use?"),
            this.hint("Choose a model above. Open a row here to compare its capabilities."),
            el("div",{class:"model-guide-list"},Object.entries(this.capabilities.profiles).map(([key,info])=>
                el("details",{class:"model-choice",name:`model-help-${this.project.id}`},
                    el("summary",{},el("strong",{},info.label),el("span",{},modelUses[key]||info.help.purpose.split(". ")[0]+".")),
                    el("div",{class:"model-choice-detail"},this.hint(info.help.purpose),
                        el("ul",{},el("li",{},el("strong",{},"Starting image: "),info.source_required?"Required":"Optional"),
                            el("li",{},el("strong",{},"References: "),`Up to ${info.max_references}`)),
                        el("a",{href:info.license.url,target:"_blank",rel:"noopener noreferrer"},info.license.label))))));
    }
    modelControls(content) {
        const profiles=this.capabilities.profiles,info=profiles[this.project.profile],settings=this.project.settings;
        const controls=this.panel("Image model settings",null,
            el("div",{class:"sampling-controls"},
                this.numericSetting("Steps",settings.steps??info.defaults.steps,v=>this.setting("steps",v),{min:1,max:150,step:1,defaultValue:info.defaults.steps,help:info.help.steps}),
                this.numericSetting("CFG / guidance",settings.cfg??info.defaults.cfg,v=>this.setting("cfg",v),{min:.1,max:30,step:.1,defaultValue:info.defaults.cfg,help:info.help.cfg}),
                this.select("Image size",Object.fromEntries([...new Set([512,768,1024,1536,2048,settings.resolution])].sort((a,b)=>a-b).map(n=>[n,`${n} px`])),settings.resolution,v=>this.setting("resolution",Number(v)))),
            this.hint("Larger images use more memory. More steps or guidance do not always improve results."),this.seedControls());
        controls.classList.add("image-settings");
        const heading=controls.querySelector(".panel-heading");heading.classList.add("settings-heading");
        heading.append(el("span",{class:"hint"},info.label),this.button("Reset model defaults",()=>this.resetModelDefaults(),this.blocked(),"quiet"));
        content.append(controls);
        const sdxl=info.lora.architecture==="sdxl";
        if(sdxl)content.append(this.disclosure("SDXL references, sampling & editing",
            this.text("Negative prompt — optional",settings.sdxl_negative_prompt||"",value=>this.setting("sdxl_negative_prompt",value)),
            this.hint("These exclusions discourage collages and repeated objects. Add specific unwanted details here. Reset model defaults keeps this text."),
            this.grid(2,
                this.select("Sampler",{dpmpp_2m:"DPM++ 2M — default",dpmpp_2m_sde:"DPM++ 2M SDE",euler:"Euler",euler_ancestral:"Euler ancestral",heun:"Heun"},settings.sdxl_sampler||"dpmpp_2m",value=>this.setting("sdxl_sampler",value)),
                this.select("Noise schedule",{karras:"Karras — default",normal:"Normal",exponential:"Exponential",simple:"Simple"},settings.sdxl_scheduler||"karras",value=>this.setting("sdxl_scheduler",value))),
            this.select("Use reference images to…",{reference:"Guide appearance with IP-Adapter Plus",img2img:"Rework the first source image"},settings.sdxl_source_mode||"reference",value=>this.setting("sdxl_source_mode",value)),
            this.grid(3,
                this.range("Reference influence",settings.sdxl_reference_strength??.8,v=>this.setting("sdxl_reference_strength",v),{min:-1,max:5,step:.05,defaultValue:.8,help:"Lower values give the description more freedom; higher values pull toward the references. Zero disables visual conditioning."}),
                this.range("Image-to-image change strength",settings.sdxl_img2img_denoise??.65,v=>this.setting("sdxl_img2img_denoise",v),{min:0,max:1,step:.05,defaultValue:.65,help:"Controls how much to redraw when reworking the first source. Higher values allow more change."}),
                this.range("Masked edit change strength",settings.sdxl_edit_denoise??.85,v=>this.setting("sdxl_edit_denoise",v),{min:0,max:1,step:.05,defaultValue:.85,help:"Controls redraw inside the mask. The edited result is composited over the original to preserve the area outside your selection."})),
            this.hint("Preparing a 3D input and generating agent references always use appearance conditioning so the composition can change. SDXL references do not reliably interpret separate instructions for each picture.")));
    }
    loraControls() {
        const sdxl=this.capabilities.profiles[this.project.profile].lora.architecture==="sdxl",options=this.loraOptions();
        const enabled=this.project.loras.map((lora,index)=>({lora,index})).filter(({lora})=>lora.enabled!==false&&this.loraMatches(lora.name));
        const update=async(index,changes)=>{const values=clone(this.project.loras);Object.assign(values[index],changes);await this.save({loras:values});};
        const display=name=>name.split(/[\\/]/).pop().replace(/\.(safetensors|ckpt|pt)$/i,"");
        const selector=el("details",{class:"model-field lora-stack","data-disclosure":"style-loras"},
            el("summary",{},"Style / LoRAs ",el("span",{class:"lora-count"},enabled.length?`${enabled.length} active`:"Optional")));
        const body=el("div",{class:"lora-body"},el("div",{class:"lora-heading"},el("span",{},"Compatible with this model"),
            this.button("Refresh",async()=>{this.loraList=await request("/loras/refresh",{});await this.civitai.loadInstalled();},this.blocked(),"text-button")));
        selector.append(body);
        const list=el("div",{class:"lora-picker",role:"group","aria-label":"Compatible LoRAs",tabIndex:0,
            onscroll:()=>{for(const tip of list.querySelectorAll(":popover-open"))tip.hidePopover();}});
        const filter=()=>{const query=(this.loraSearch||"").toLowerCase();for(const row of list.children)row.hidden=!row.dataset.name.toLowerCase().includes(query);};
        if(Object.keys(options).length>5)body.append(el("input",{type:"search",class:"lora-search",placeholder:"Search compatible LoRAs…",
            "aria-label":"Search compatible LoRAs","data-control":"LoRA search",value:this.loraSearch||"",oninput:event=>{this.loraSearch=event.target.value;filter();}}));
        for(const [name,label] of Object.entries(options)) {
            const help=this.loraHelp(name);
            list.append(el("div",{class:"lora-choice-row","data-name":name},this.loraHelpControl(display(name),help),el("label",{class:"lora-choice",title:label},
                el("input",{type:"checkbox",checked:enabled.some(item=>item.lora.name===name),disabled:!!this.blocked(),"data-control":`LoRA ${name}`,
                    onchange:event=>this.action(()=>this.setLoraEnabled(name,event.target.checked))}),el("span",{},display(name)),
                label.includes("first-use download")?el("small",{},"Download"):null)));
        }
        if(Object.keys(options).length){body.append(list);filter();}
        else body.append(this.hint("No compatible LoRAs installed for this model."));
        if(enabled.length)body.append(el("div",{class:"lora-selected-heading"},`${enabled.length} selected`));
        for(const [position,{lora,index}] of enabled.entries()) {
            const remove=this.button("×",()=>this.setLoraEnabled(lora.name,false),this.blocked(),"lora-remove");
            remove.setAttribute("aria-label",`Remove ${display(lora.name)}`);remove.title=`Remove ${display(lora.name)}`;
            const row=el("div",{class:"lora-selected"},el("div",{class:"lora-selected-title"},el("strong",{title:lora.name},display(lora.name)),remove));
            const strength=this.range(`LoRA ${position+1} strength`,lora.strength,v=>update(index,{strength:v}),{min:-2,max:2,step:.05,defaultValue:1});
            strength.querySelector('.range-title>span').textContent="Strength";row.append(strength);
            const trigger=this.input(`LoRA ${position+1} trigger words`,lora.trigger,v=>update(index,{trigger:v}));trigger.firstElementChild.textContent="Trigger words";
            const extras=[trigger];
            if(sdxl)extras.push(this.numericSetting(`LoRA ${position+1} text strength`,lora.strength_clip??lora.strength,v=>update(index,{strength_clip:v}),
                {min:-2,max:2,step:.05,defaultValue:1,help:"Changes matching text encoder layers when the file includes them."}));
            const detail=this.disclosure(`LoRA ${position+1} options`,...extras);detail.classList.add("lora-settings");row.append(detail);body.append(row);
        }
        if(this.project.loras.some(lora=>lora.enabled!==false&&!this.loraMatches(lora.name)))body.append(el("div",{class:"lora-mismatch",role:"alert"},
            "A saved LoRA does not match this model. ",this.button("Turn it off",()=>this.save({loras:this.project.loras.map(l=>({...l,enabled:l.enabled!==false&&this.loraMatches(l.name)}))}),this.blocked(),"text-button")));
        if(this.loraList.unidentified)body.append(this.hint(`${this.loraList.unidentified} unidentified file${this.loraList.unidentified===1?" is":"s are"} hidden until model compatibility can be verified.`));
        return {selector,detail:null};
    }
    renderCreate(content) {
        const sources=this.project.sources.filter(s=>s.enabled!==false&&!s.cleared),profile=this.capabilities.profiles[this.project.profile];
        const imageReason=this.generatingImage?"Starting image generation…":this.imageBlocked()||(profile.source_required&&!sources.length?"Upload at least one reference for Qwen Edit 2511.":
            !this.project.prompt.trim()&&!sources.length?"Write a description or upload a reference image first.":"");
        content.append(el("div",{class:"step-heading"},el("div",{},el("h3",{},"Start with an idea or an image"),
            this.hint("Describe your asset, add optional references, then generate one image."))));
        const newJob=this.button("Start Over",async()=>{this.project=await request("/projects",{});this.job=null;this.notice="";this.descriptionMessage=null;},this.blocked(),"quiet start-over");
        newJob.title=this.blocked()||"Start a fresh asset. Your current job remains in History.";
        const category=this.select("Asset type",{props:"Prop",characters:"Character",creatures:"Creature",vehicles:"Vehicle",environment:"Environment piece"},this.project.category,v=>this.save({category:v}));
        const assetHelp=el("details",{class:"help-panel asset-help"},el("summary",{},"What asset type should I choose?"),
            el("ul",{},...[ ["Prop","tools, furniture and manufactured objects"],["Character","clothed people or humanoids"],
                ["Creature","animals and nonhuman anatomy"],["Vehicle","ships, cars and moving machines"],
                ["Environment piece","buildings, terrain, plants or scenery"] ].map(([name,description])=>el("li",{},el("strong",{},name+": "),description))),
            this.hint("Guides instructions for anatomy, parts and structure."));
        const model=el("div",{class:"model-field"},
            this.select("Image model",Object.fromEntries(Object.entries(this.capabilities.profiles).map(([k,v])=>[k,v.label])),this.project.profile,profile=>this.selectImageProfile(profile)),
            el("div",{class:"model-note"},el("span",{},modelUses[this.project.profile]||""),
                el("a",{class:"model-license",href:profile.license.url,target:"_blank",rel:"noopener noreferrer"},"License & usage")),this.modelGuide());
        const loras=this.loraControls();
        const metadata=el("section",{class:"control-panel asset-setup","aria-label":"Your asset"},
            el("div",{class:"identity-row"},this.input("Job name",this.project.name,v=>this.save({name:v})),newJob),
            el("div",{class:"identity-row asset-type-row"},category),assetHelp,
            el("div",{class:"model-pair"},model,loras.selector),
            el("div",{class:"model-browser-action"},this.button("Browse for more Model Checkpoints and Loras",()=>this.civitai.open(),"","text-button")));
        content.append(metadata);
        const installedModels=this.civitai.installed.filter(item=>item.kind==="Checkpoint"&&(item.profile===this.project.profile||item.family==="sdxl"&&this.project.profile.startsWith("sdxl")));
        if(installedModels.length||this.project.settings.image_checkpoint)model.append(this.select("Model weights",{"":"Official weights",...Object.fromEntries(installedModels.map(item=>[item.file_id,`${item.model_name} · ${item.version_name}`]))},this.project.settings.image_checkpoint||"",value=>this.setting("image_checkpoint",value)));
        this.descriptionStatusNodes=[];
        const enhance=this.button("Enhance description",()=>this.describe("enhance"),this.blocked()||(!this.project.prompt.trim()?"Write a description first.":""));
        enhance.title="Replace this text using the selected model's guidance. Undo restores your description.";
        const descriptionTools=el("div",{class:"row description-tools"},enhance);
        const undo=this.descriptionUndo;
        if(undo?.projectId===this.project.id&&undo.enhanced===this.project.prompt)
            descriptionTools.append(this.button("Undo",async()=>{await this.save({prompt:undo.previous});this.descriptionUndo=null;this.descriptionMessage=null;},this.blocked(),"quiet"));
        const describe=this.button("Auto Describe my image",()=>this.describe("describe"),this.blocked()||(!this.current("source")?"Upload a source image first.":""));
        describe.title="Describe the latest upload directly in the description box. Undo is available. The local assistant may need a first-use download.";
        const referenceArea=el("div",{class:"reference-input"},el("h4",{},profile.source_required?"Reference images — required":"Reference images — optional"),
            this.hint(profile.source_required?"This editing model needs at least one starting picture.":"Text alone is enough. Add pictures to guide shape, detail or style."),
            el("div",{class:"row upload-actions"},this.button("Upload references",()=>this.upload("source",true),this.blocked()),describe,
                this.project.sources.some(s=>!s.cleared)?this.button("Clear all images",()=>this.confirmClear(),this.blocked(),"quiet danger"):null),
            this.descriptionStatus("describe"));
        const cards=el("div",{class:"cards source-cards"});
        for(const source of this.project.sources) {
            if(source.cleared)continue;
            const card=this.imageCard("source",source);card.classList.add("source-card");
            card.append(this.check("Use as reference",source.enabled!==false,enabled=>this.save({source_selection:this.project.sources.filter(r=>!r.cleared&&(r.id===source.id?enabled:r.enabled!==false)).map(r=>r.id)})),
                this.input("What should this reference contribute?",source.instructions||"",value=>this.save({source_details:{[source.id]:{instructions:value}}})));
            cards.append(card);
        }
        if(!cards.childNodes.length)referenceArea.append(el("div",{class:"upload-placeholder"},this.hint("Use photos or artwork to guide the result. A ready-to-use image can also go straight to Prepare for 3D.")));
        const cleared=this.project.sources.filter(source=>source.cleared);
        if(cleared.length)referenceArea.append(this.disclosure("Previously cleared references",this.hint("Restore a reference only if you want to use it again."),
            ...cleared.map((source,index)=>this.button(`Restore reference ${index+1}`,()=>this.save({source_selection:[...sources.map(r=>r.id),source.id]}),this.blocked()))));
        const description=this.text("Object description",this.project.prompt,v=>this.save({prompt:v}),true);
        description.querySelector("textarea").addEventListener("input",event=>{
            const empty=!event.target.value.trim();
            enhance.disabled=!!this.blocked()||empty;
            const reason=this.generatingImage?"Starting image generation…":this.imageBlocked()||
                (profile.source_required&&!sources.length?"Upload at least one reference for Qwen Edit 2511.":
                empty&&!sources.length?"Write a description or upload a reference image first.":"");
            for(const button of this.root.querySelectorAll(".generate-image")) {
                button.disabled=!!reason;button.title=reason;
                button.parentElement.querySelector(".action-copy .hint").textContent=reason||"Creates one image to review before making a mesh.";
            }
        });
        content.append(this.panel("Describe the object to create a starting image, or upload images to use as reference.",null,el("div",{class:"starting-grid"},el("div",{class:"description-input"},
            description,descriptionTools,
            this.descriptionStatus("enhance")),referenceArea),cards.childNodes.length?cards:null));
        content.append(this.generateAction(imageReason,true),
            this.disclosure("Unseen details & instructions for the agent",this.text("Specific details for unseen sides / agent instructions",this.project.design_notes,v=>this.save({design_notes:v})),
                this.hint("These notes guide the design references and agent handoff. Pixal3D sees only the approved image, so details written only here may not appear in the mesh.")));
        this.modelControls(content);
        content.append(this.generateAction(imageReason));
        const design=this.current("design");
        if(design)content.append(this.panel("Your generated image","Edit this image, prepare a clearer 3D input, or use it directly if it already shows the whole object.",
            this.imageCard("design",design),el("div",{class:"row"},this.button("Prepare image for 3D",()=>{this.tab="Approve image";return this.start("three_quarter");},this.imageBlocked(),"primary"),
                this.button("Use this image directly",()=>this.adopt("design",design),this.blocked()))));
        else {const saved=this.savedImages("design");if(saved)content.append(saved);}
    }
    activityIcon() {
        return el("span",{class:"activity-star","aria-hidden":"true"},el("img",{src:brandLogo,alt:"",width:20,height:20}));
    }
    updateWorkingIndicator() {
        if(!this.workingNode)return;
        const downloading=this.resources?.download?.status==="running"||["running","queued","pausing","cancelling"].includes(this.civitai?.download?.status);
        const phase=this.job?.phase||"",kind=this.job?.kind||"";
        const stage=/reference|image|three.quarter/i.test(phase)?"Rendering image":/export|package|archive/i.test(phase)?"Exporting assets":
            /finish|decimat|simplif/i.test(phase)||kind==="finish_mesh"?"Finishing mesh":/mesh|structure|shape|texture/i.test(phase)||kind==="build_mesh_package"?"Rendering mesh":"Rendering image";
        const label=this.helperBusy?(downloading?"Downloading assistant…":this.descriptionAction==="describe"?"Describing image…":"Enhancing description…"):
            downloading?"Downloading asset…":active(this.job)?`${stage}…`:this.generatingImage?"Preparing image…":"";
        this.workingNode.dataset.busy=String(!!label);
        if(this.workingLabel){this.workingLabel.hidden=!label;this.workingLabel.textContent=label;}
        this.workingNode.title=this.job?.phase||this.resources?.description_helper?.phase||label;
    }
    generateAction(reason,advanced=false) {
        const running=this.generatingImage||active(this.job)&&this.job.kind==="create_image";
        const button=this.button("Generate image",()=>this.generateImage(),reason,"primary generate-image");
        if(running){button.prepend(this.activityIcon());button.disabled=true;button.setAttribute("aria-busy","true");}
        return el("div",{class:"action-bar"},button,el("div",{class:"action-copy"},this.hint(reason||"Creates one image to review before making a mesh."),
            advanced?el("a",{href:"#",onclick:event=>{event.preventDefault();const target=this.root.querySelector('.image-settings');target?.scrollIntoView({block:"start"});target?.querySelector('input')?.focus({preventScroll:true});}},"See advanced settings below."):null));
    }
    async generateImage() {
        if(this.generatingImage||this.blocked())return;
        this.generatingImage=true;
        this.updateWorkingIndicator();
        for(const button of this.root.querySelectorAll('.generate-image')) {button.disabled=true;button.setAttribute("aria-busy","true");button.prepend(this.activityIcon());}
        try {await this.start("create_image");}
        finally {this.generatingImage=false;this.updateWorkingIndicator();}
    }
    descriptionStatus(action) {
        const node=el("div",{class:"description-status",role:"status","aria-live":"polite",hidden:true});
        this.descriptionStatusNodes.push({node,action});return node;
    }
    updateDescriptionStatus() {
        for(const {node,action} of this.descriptionStatusNodes||[]) {
            const current=this.descriptionAction===action,working=current&&this.helperBusy,message=current?this.descriptionMessage:null;
            node.hidden=!working&&!message;if(node.hidden)continue;
            node.classList.toggle("error",!!message?.error);node.setAttribute("aria-busy",String(!!working));
            if(!working){node.replaceChildren(message.text);continue;}
            const download=this.resources?.download,helper=this.resources?.description_helper;
            const progress=download?.request?.kind==="description"&&download.status==="running"?downloadProgress(download):null;
            const text=progress?`Downloading description assistant · ${progress.message}`:
                helper?.phase&&helper.phase!=="idle"?helper.phase:action==="enhance"?"Enhancing your description…":"Describing your image…";
            if(!node.querySelector('.activity-star'))node.replaceChildren(this.activityIcon(),el("span",{class:"description-phase"}));
            node.querySelector('.description-phase').textContent=text;
            let meter=node.querySelector('progress');
            if(progress?.progress?.max){
                if(!meter){meter=el("progress",{"aria-label":"Description assistant download"});node.append(meter);}
                meter.max=progress.progress.max;meter.value=progress.progress.value;
            }else meter?.remove();
        }
    }
    async describe(action) {
        if(this.helperBusy)return;
        this.helperBusy=true;this.descriptionAction=action;this.descriptionMessage=null;this.render();this.updateDescriptionStatus();
        try {
            await this.saveQueue;
            const previous=this.project.prompt,projectId=this.project.id;
            const result=await request(this.path("/describe"),{expected_revision:this.project.revision,action});
            if(this.project.id!==projectId)throw Error("The current job changed. Its description was not replaced.");
            await this.save({prompt:result.text},result.input_revision);
            this.descriptionUndo={projectId,previous,enhanced:result.text};
            this.descriptionMessage={text:"Description updated. Undo is available."};
        }
        catch(error) {
            if(error.message.includes("Description assistant stopped")) {this.descriptionMessage={text:"Stopped. Your description was not changed."};return;}
            this.descriptionMessage={text:error.message,error:true};
            throw error;
        }
        finally {this.helperBusy=false;this.render();this.updateDescriptionStatus();}
    }
    async upload(role,multiple=false) {
        const picker=el("input",{type:"file",accept:"image/png,image/jpeg,image/webp",multiple});
        picker.onchange=()=>this.action(async()=>{
            for(const file of picker.files) {
                const data=new FormData();data.append("image",file);data.append("role",role);data.append("expected_revision",this.project.revision);
                const response=await api.fetchApi(PREFIX+this.path("/images"),{method:"POST",body:data});const result=await response.json();
                if(!response.ok) throw Error(result.error);
                this.project=result.project;
            }
            this.status("Source files saved at full resolution. Select their role, edit them, or use a suitable image directly.");
        });picker.click();
    }
    async adopt(role,record) {
        await this.post("/images/adopt",{source_role:role,revision_id:record.id,role:"mesh_input"});
        this.tab="Approve image";this.status("This exact image is selected for the mesh. Inspect and approve it below; no new image was generated.");
    }
    savedImages(role) {
        const revisions=this.project.images[role].revisions.filter(r=>!r.recipe?.edit||r.edit_accepted);
        if(this.current(role)||!revisions.length)return null;
        return el("details",{class:"help-panel"},el("summary",{},`Restore saved ${names[role].toLowerCase()}`),
            this.hint("The original files are still saved. Restoring an image does not approve it or run generation."),
            this.select("Saved image to restore",{"":"Choose a saved image…",...Object.fromEntries(revisions.map(r=>[r.id,
                `${new Date((r.created||0)*1000).toLocaleString()} · seed ${r.recipe?.seed??"uploaded"}`]))},"",
                revision_id=>revision_id?this.post("/images/select",{role,revision_id}):undefined));
    }
    savedEdits(role,record) {
        const previews=this.project.images[role].revisions.filter(r=>r.recipe?.edit?.source?.id===record.id&&!r.edit_accepted);
        if(!previews.length)return null;
        return el("details",{class:"help-panel"},el("summary",{},"Review saved edit previews"),
            this.hint("These previews have not replaced your image. Compare a preview before choosing Keep this edit."),
            previews.map(r=>el("article",{class:"saved-edit"},el("img",{src:this.url(r),alt:"Saved edit preview"}),
                el("div",{class:"row"},this.link("Download edit preview",this.url(r,true)),
                    this.button("Keep this edit",()=>this.post("/edits/accept",{role,revision_id:r.id}),this.blocked(),"primary")))));
    }
    imageCard(role,record) {
        const image=el("img",{src:this.url(record),alt:names[role]});
        const card=el("article",{class:"card"},el("div",{class:"inline-heading"},el("h4",{},names[role]),el("span",{class:"review-badge"},(record.review?.decision||"unreviewed").replaceAll("_"," "))),image,
            this.hint(`Review: ${record.review?.decision||"unreviewed"}${record.review?.reviewer?" by "+record.review.reviewer:""} · Seed used: ${record.recipe?.seed??"uploaded"}`),
            el("div",{class:"row"},this.link("Download image",this.url(record,true)),
                this.button("Edit image",()=>this.edit(role,record),this.blocked()),
                this.button("Clear this image",()=>this.post("/images/clear",{role,revision_id:record.id}),this.blocked(),"quiet danger")));
        if(role==="source") card.append(this.button("Prepare this image for 3D",()=>this.adopt(role,record),this.blocked()));
        const alternatives=this.project.images[role].revisions.filter(r=>!r.recipe?.edit||r.edit_accepted);
        if(role!=="source"&&alternatives.length>1)card.append(this.select("Saved image revision",Object.fromEntries(alternatives.map(r=>[r.id,
            `${new Date((r.created||0)*1000).toLocaleString()} · seed ${r.recipe?.seed??"uploaded"} · ${r.review?.decision||"unreviewed"}`])),record.id,
            revision_id=>this.post("/images/select",{role,revision_id})));
        const savedEdits=this.savedEdits(role,record);if(savedEdits)card.append(savedEdits);
        if(role.startsWith("reference_")) card.append(this.button("Regenerate",()=>this.start("reference_view",{role}),this.imageBlocked()));
        if(role==="mesh_input"||role.startsWith("reference_")) {
            const notes=el("textarea",{value:record.review?.notes||"",placeholder:"Known differences or details for the agent"});
            card.append(el("label",{class:"field review-notes"},el("span",{},"Differences or instructions for the agent"),notes),el("div",{class:"row"},this.button(role==="mesh_input"?"Approve this image":"Approve reference",()=>this.review(role,record,"approved",notes.value),this.blocked(),"primary"),
                this.button("Approve with notes",()=>this.review(role,record,"approved_with_notes",notes.value),this.blocked()||(!notes.value.trim()?"Enter the differences or instructions before approving with notes.":"")),
                this.button("Reject",()=>this.review(role,record,"rejected",notes.value),this.blocked())));
            notes.oninput=()=>{const button=card.querySelectorAll("button");const match=[...button].find(b=>b.textContent==="Approve with notes");if(match)match.disabled=!!this.blocked()||!notes.value.trim();};
        }
        return card;
    }
    async review(role,record,decision,notes) {
        await this.post("/reviews",{role,revision_id:record.id,sha256:record.sha256,decision,notes,reviewer:"user"});
        if(role==="mesh_input"&&["approved","approved_with_notes"].includes(decision))await this.cutout();
    }
    renderApprove(content) {
        const image=this.current("mesh_input"),design=this.current("design");
        content.append(el("div",{class:"step-heading"},el("div",{},el("h3",{},"Prepare and approve the image for 3D"),
            this.hint("A three-quarter view shows the front, a side and the object's depth. Preparation creates a new image in that view; skip it if your image is already suitable."))));
        content.append(this.panel("Choose your mesh input","Pixal3D receives exactly the image you approve here. It does not receive your text prompt or the other reference images.",
            el("div",{class:"row"},this.button("Prepare image for 3D",()=>this.start("three_quarter"),this.imageBlocked()||(!this.project.prompt.trim()&&!this.project.sources.some(s=>s.enabled&&!s.cleared)?"Write a description or upload a source image first.":""),image?"":"primary"),
                this.button("Upload image for the mesh",()=>this.upload("mesh_input"),this.blocked())),
            this.hint("Keep the whole object in frame. Check proportions, thin parts and any missing features before approval.")));
        if(design&&!image)content.append(this.panel("Use your current design",null,this.imageCard("design",design),
            this.button("Use this design directly for the mesh",()=>this.adopt("design",design),this.blocked(),"primary")));
        if(image)content.append(this.imageCard("mesh_input",image));
        else {content.append(el("div",{class:"empty"},"No mesh input selected. Prepare a view, upload a suitable image, or choose your existing design."));const saved=this.savedImages("mesh_input");if(saved)content.append(saved);}
    }
    async edit(role,record) {
        if(this.project.images[role].current!==record.id) await this.post("/images/select",{role,revision_id:record.id});
        await openImageEditor({element:el,sourceURL:this.url(record),title:names[role],model:this.capabilities.profiles[this.project.profile].label,
            download:()=>this.link("Download original",this.url(record,true)),progress:()=>({message:this.job?.phase,progress:this.nativeProgress}),
            stop:()=>request(this.path(`/jobs/${this.job.id}/cancel`),{}),
            generate:async selection=>{
                await this.refresh();
                if(selection.random) await this.setting("requested_seed",-1);
                const data=new FormData();for(const [key,value] of Object.entries({expected_revision:this.project.revision,role,revision_id:record.id,
                    prompt:selection.prompt,feather:selection.feather,replace_detail:selection.replaceDetail}))data.append(key,value);
                data.append("mask",selection.mask);
                const response=await api.fetchApi(PREFIX+this.path("/edits"),{method:"POST",body:data});const edit=await response.json();
                if(!response.ok)throw Error(edit.error);
                const job=await this.start("edit_image",{role,edit:edit.id});const completed=await this.waitJob(job);
                const id=completed.stages[0].result.revision,revision=this.project.images[role].revisions.find(r=>r.id===id);
                return {...revision,url:this.url(revision),download:this.link("Download edit preview",this.url(revision,true))};
            },accept:async revision=>{await this.refresh();await this.post("/edits/accept",{role,revision_id:revision.id});this.render();}});
    }
    async cutout() {
        const image=this.current("mesh_input");
        await openImageEditor({element:el,sourceURL:this.url(image),initialMaskURL:image.foreground?this.fileURL(image.foreground.mask_file):null,
            prepareMask:image.foreground?null:async()=>{
                await this.waitJob(await this.start("prepare_foreground",{role:"mesh_input"}));
                return this.fileURL(this.current("mesh_input").foreground.mask_file);
            },title:"Image for the mesh",model:"Foreground mask",mode:"foreground",
            keepLabel:"Keep Cutout and Continue to Create Mesh",
            download:()=>this.link("Download original",this.url(image,true)),progress:()=>({message:this.job?.phase,progress:this.nativeProgress}),
            stop:async()=>{if(active(this.job))await request(this.path(`/jobs/${this.job.id}/cancel`),{});},
            generate:async selection=>{
                const data=new FormData();data.append("slot","mesh_input");data.append("revision",image.id);data.append("feather",selection.feather);data.append("mask",selection.mask);
                const response=await api.fetchApi(`/asset-workshop/assets/${this.project.id}/foreground`,{method:"POST",body:data});const result=await response.json();
                if(!response.ok)throw Error(result.error);
                return {...result,url:this.fileURL(result.cutout_file),download:this.link("Download cutout",this.fileURL(result.cutout_file)+"&download=1")};
            },accept:async candidate=>{
                await legacy(`/assets/${this.project.id}/foreground/accept`,{slot:"mesh_input",candidate:candidate.id});
                await this.refresh();this.tab="Mesh & agent package";this.root.scrollTop=0;this.render();
            }});
    }
    renderMesh(content) {return renderMeshPipeline(this,content,el);}
    renderLegacyMesh(content) {
        const approved=this.current("mesh_input")&&this.project.images.mesh_input.approved===this.current("mesh_input").id;
        content.append(el("div",{class:"step-heading"},el("div",{},el("h3",{},"Build, inspect and export"),
            this.hint("Build a mesh from your prepared image, inspect it, then download it or open it in Blender."))));
        content.append(this.panel("Build your asset","The mesh is reconstructed from your prepared image. Four additional pictures show the intended design; they are not measured views and do not enter reconstruction.",
            el("div",{class:"action-bar"},this.button("Generate mesh & reference images",()=>this.start("build_mesh_package"),this.imageBlocked()||(!approved?"Approve one image on step 2 first.":""),"primary"),
                this.hint(approved?"Creates the mesh and four design reference pictures.":"First choose and approve your mesh input in Prepare for 3D."))));
        const master=[...this.project.artifacts].reverse().find(a=>a.kind==="master"&&!a.stale);
        const mesh=[...this.project.artifacts].reverse().find(a=>a.kind==="mesh"&&a.export_kind==="master"&&!a.stale);
        const game=[...this.project.artifacts].reverse().find(a=>a.kind==="mesh"&&a.export_kind==="game"&&!a.stale&&a.master===mesh?.master);
        if(mesh) {
            const viewer=el("div",{class:"viewer",role:"application",tabIndex:0,"aria-label":"Exported mesh preview"});
            const downloads=el("div",{class:"output-actions"},el("div",{class:"row"},this.link("Download mesh (.glb)",this.url(mesh,true)),this.button("Reset view",()=>this.viewer?.fitToViewer(),"","quiet")));
            if(mesh.print?.file)downloads.append(el("div",{class:"row"},this.link("Download geometry (.stl, millimeters)",this.fileURL(mesh.print.file)+"&download=1")),
                this.hint("STL is geometry only. Check wall thickness and supports before printing."));
            if(game)downloads.append(el("div",{class:"row"},this.link("Download game version (.glb)",this.url(game,true))));
            content.append(this.panel("Your exported mesh",`${mesh.triangles?.toLocaleString()||"Recorded"} triangles · Measured XYZ: ${(mesh.dimensions_meters||[]).map(n=>n.toFixed(3)).join(" × ")} meters.`,viewer,
                this.hint("Drag to rotate; scroll to zoom. Inspect all sides before using the mesh."),downloads));
            requestAnimationFrame(()=>this.mountViewer(viewer,mesh).catch(error=>viewer.replaceChildren(this.hint(error.message))));
        } else content.append(el("div",{class:"empty"},master?"Reconstruction is saved. Finish it on the GPU below to create downloadable files.":"No mesh exported yet. Approve an image, then generate the mesh above."));
        if(master)content.append(this.disclosure("Finish or optimize the saved reconstruction",
            this.hint("Uses the current GPU finishing settings from Settings. It does not repeat image generation or Pixal3D reconstruction."),el("div",{class:"row"},
                this.button(mesh?"Apply finishing settings to saved mesh":"Finish saved mesh on GPU",()=>this.start("finish_mesh",{master_id:master.id}),this.blocked()),
                ...(mesh?[this.button("Create lighter game version",()=>this.start("finish_mesh",{master_id:mesh.master,export_kind:"game"}),this.blocked())]:[])),
            this.hint("The game version uses the game triangle and texture targets. Collision and LODs still need checking in the game editor.")));
        const cards=el("div",{class:"cards"});
        for(const role of refs) {const image=this.current(role);cards.append(image?this.imageCard(role,image):el("article",{class:"card"},el("h4",{},names[role]),this.hint("No current reference."),this.savedImages(role),this.button("Generate reference",()=>this.start("reference_view",{role}),this.imageBlocked()||(!approved?"Approve the mesh image first.":""))));}
        const reviewed=refs.filter(role=>this.current(role)&&this.project.images[role].approved===this.current(role).id).length;
        content.append(this.disclosure(`Reference pictures · ${reviewed} of 4 reviewed`,this.hint("Optional design references. Their review status is saved with the export."),cards));
        content.append(this.panel("Export asset","Download the mesh, source image, available references and settings together, or open the mesh in Blender.",
            this.disclosure("Export notes (optional)",this.text("Notes for you, a collaborator or a coding agent",this.project.target.user_instructions,value=>this.save({target:{user_instructions:value}}))),
            el("div",{class:"action-bar"},this.button("Download asset (.zip)",()=>this.exportAsset(mesh,game),this.blocked()||(!mesh?"Finish a mesh first.":""),"primary"),
                this.button("Open in Blender",async()=>{await this.saveQueue;await request(this.path("/blender"),{expected_revision:this.project.revision,artifact_id:mesh.id});},this.blocked()||(!mesh?"Finish a mesh first.":"")))));
        for(const artifact of this.project.artifacts.filter(a=>a.kind==="package"&&!a.stale))content.append(el("div",{class:"row"},this.link("Download saved ZIP",this.url(artifact,true))));
    }
    async exportAsset(mesh,game) {
        await this.saveQueue;
        const artifact=await request(this.path("/packages"),{expected_revision:this.project.revision,artifact_ids:[mesh.id,...(game?[game.id]:[])],audience:"asset"});
        await this.refresh();
        const download=this.link("Download asset (.zip)",this.url(artifact,true));download.hidden=true;
        document.body.append(download);download.click();download.remove();
    }
    async mountViewer(container,mesh) {
        if(!container.isConnected)return;
        const factory=window.comfyAPI?.createLoad3d?.createLoad3d;if(!factory)throw Error("The native Comfy 3D viewer has not loaded. The mesh download remains available.");
        const preview=await legacy(`/assets/${this.project.id}/preview`,{export:mesh.id});
        if(!container.isConnected)return;
        const viewer=factory(container);this.viewer=viewer;this.guardViewerDrag(viewer);
        this.viewerResize=new ResizeObserver(()=>viewer.handleResize());this.viewerResize.observe(container);
        container.addEventListener("pointerenter",()=>viewer.updateStatusMouseOnViewer(true));container.addEventListener("pointerleave",()=>viewer.updateStatusMouseOnViewer(false));
        await viewer.loadModel(preview.url);viewer.handleResize();viewer.fitToViewer();viewer.forceRender();
    }
    guardViewerDrag(viewer) {
        this.viewerInteractionCleanup?.();
        const controls=viewer.controlsManager?.controls;
        if(!controls?.domElement)return;
        controls.autoRotate=false;controls.enableDamping=false;
        const surface=controls.domElement;
        const release=event=>{
            if(controls._pointers?.includes(event.pointerId))controls._onPointerUp(event);
        };
        const guard=event=>{
            if(event.pointerType!=="touch"&&event.buttons===0){release(event);event.stopImmediatePropagation();}
        };
        const blur=()=>{for(const pointerId of [...(controls._pointers||[])])release(new PointerEvent("pointerup",{pointerId}));};
        surface.addEventListener("pointermove",guard,true);
        window.addEventListener("pointerup",release,true);window.addEventListener("pointercancel",release,true);window.addEventListener("blur",blur);
        this.viewerInteractionCleanup=()=>{
            surface.removeEventListener("pointermove",guard,true);
            window.removeEventListener("pointerup",release,true);window.removeEventListener("pointercancel",release,true);window.removeEventListener("blur",blur);
        };
        blur();
    }
    confirmClear() {
        this.confirm("Clear all images?","This removes the current images and approval from this job. Saved revisions and earlier files remain in its History. Existing mesh results become out of date.","Clear all images",()=>this.post("/images/clear"));
    }
    confirm(title,text,label,action,phrase="") {
        const input=phrase?el("input",{type:"text",autocomplete:"off","aria-label":`Type ${phrase} to confirm`}):null;
        const proceed=el("button",{disabled:!!phrase,onclick:()=>{if(phrase&&input.value!==phrase)return;dialog.close();this.action(action);}},label);
        if(input)input.oninput=()=>{proceed.disabled=input.value!==phrase;};
        const dialog=el("dialog",{class:"aw"},el("h3",{},title),el("p",{},text),
            phrase?el("label",{},`Type ${phrase} to confirm`,input):null,
            el("div",{class:"row"},el("button",{onclick:()=>dialog.close()},"Cancel"),proceed));
        document.body.append(dialog);dialog.addEventListener("close",()=>dialog.remove());dialog.showModal();
    }
    renderSettings(content) {
        const p=this.project,s=p.settings;
        content.append(el("div",{class:"step-heading"},el("div",{},el("h3",{},"Settings"),this.hint("Changes apply to future attempts. Saved images and meshes stay as they are until you explicitly generate or finish again."))));
        const choices=Object.fromEntries(Object.entries(this.presets.presets).map(([id,v])=>[id,v.label]));
        if(!this.pendingPreset||!(this.pendingPreset in choices))this.pendingPreset=p.memory_preset_id in choices?p.memory_preset_id:"standard_16gb";
        const selected=this.presets.presets[this.pendingPreset];
        const presetLabels={resolution:"Generated image size",shape_resolution:"Shape resolution",master_texture:"Master texture size",master_faces:"Master triangle target",game_texture:"Game texture size",game_faces:"Game triangle target",normal_resolution:"Normal map size",ao_resolution:"Ambient-occlusion map size",extra_vram_headroom_gb:"Extra VRAM headroom (GB)",min_ram_free_gb:"Minimum free system RAM (GB)",min_vram_free_gb:"Minimum free VRAM (GB)",cache_device:"Reference cache location",tiled_vae:"Tiled image decoding",release_between_stages:"Unload models between stages",remesh:"Remesh before finishing",uv_method:"GPU UV method",helper_precision:"Description assistant precision",image_precision:"Image weight precision",cache_precision:"Reference cache precision"};
        const preview=this.grid(3,el("div",{},el("strong",{},"Starting image model"),this.hint(this.capabilities.profiles[selected.profile].label)),
            ...Object.entries(selected.settings).map(([key,value])=>el("div",{},el("strong",{},presetLabels[key]||key),this.hint(typeof value==="boolean"?(value?"On":"Off"):value==="cpu"?"System RAM":value==="pec"?"PEC — GPU":String(value)))));
        const presetDetails=el("details",{class:"help-panel preset-preview",open:this.pendingPreset!==p.memory_preset_id},el("summary",{},"Review preset changes"),preview,...Object.values(selected.explanations).map(text=>this.hint(text)));
        content.append(this.panel("Memory preset","Preview a preset before applying it. Models unload between heavy stages; that safeguard stays enabled.",
            this.grid(2,this.select("Preset to preview",choices,this.pendingPreset,async id=>{this.pendingPreset=id;}),
                el("div",{},this.hint(`Current: ${this.presets.presets[p.memory_preset_id]?.label||p.memory_preset_id}`),this.hint(p.preset_overrides.length?"Custom overrides: "+p.preset_overrides.map(key=>({profile:"Image model",requested_seed:"Image seed",seed_mode:"Seed behavior",steps:"Image steps",cfg:"Image guidance",cache_limit_gb:"CPU cache limit",mesh_fov:"Manual camera FOV",mesh_fov_mode:"Camera estimation",smoothing:"Surface smoothing",crease_angle:"Hard-edge angle",bake_normal:"Normal map",bake_ao:"Ambient occlusion",asset_height:"Default height",sdxl_negative_prompt:"SDXL exclusions",sdxl_sampler:"SDXL sampler",sdxl_scheduler:"SDXL schedule",sdxl_source_mode:"SDXL source mode",sdxl_reference_strength:"Reference influence",sdxl_img2img_denoise:"Image change strength",sdxl_edit_denoise:"Masked edit strength",...presetLabels}[key]||key.replaceAll("_"," "))).join(", "):"No preset overrides."))),
            presetDetails,this.hint(selected.validation.message),el("div",{class:"row"},this.button("Apply preset",()=>this.save({memory_preset_id:this.pendingPreset}),this.blocked(),"primary"),
                this.button("Reset current preset",()=>this.save({memory_preset_id:p.memory_preset_id}),this.blocked()||(!(p.memory_preset_id in choices)?"Choose a preset first.":""),"quiet"))));
        const memory=this.grid(3);
        for(const [key,label,min,max] of [["extra_vram_headroom_gb","Extra VRAM headroom (GB)",0,12],["min_ram_free_gb","Free system RAM reserve (GB)",1,128],["min_vram_free_gb","Free VRAM reserve (GB)",0,24],["cache_limit_gb","CPU feature cache limit (GB)",1,500]])
            memory.append(this.input(label,s[key],value=>this.setting(key,Number(value)),{type:"number",min,max,step:.5}));
        memory.append(this.select("Image feature cache",{cpu:"System RAM",gpu:"GPU VRAM",auto:"Automatic",off:"Off"},s.cache_device,v=>this.setting("cache_device",v)),
            this.select("Description assistant precision",{q8:"Q8 — more memory",q4:"Q4 — smaller"},s.helper_precision,v=>this.setting("helper_precision",v)));
        content.append(this.disclosure("Memory & cache controls",memory,this.check("Tiled image decoding",s.tiled_vae,v=>this.setting("tiled_vae",v)),
            this.hint("Reserves encourage offloading; they are not hard memory limits. CPU caching uses system RAM to save repeated encoding. Tiled decoding lowers peak VAE memory and may take longer.")));
        content.append(this.panel("Reconstruction & camera","These settings affect the next Pixal3D reconstruction. GPU finishing below can be rerun separately on a saved reconstruction.",
            this.grid(2,this.select("Shape resolution",Object.fromEntries([...new Set([1024,1536,2048,s.shape_resolution])].sort((a,b)=>a-b).map(n=>[n,`${n}`])),s.shape_resolution,v=>this.setting("shape_resolution",Number(v))),
                this.input("Mesh seed (-1 = random)",s.mesh_requested_seed,v=>this.setting("mesh_requested_seed",Number(v)),{type:"number",min:-1,max:9007199254740976,step:1})),
            this.grid(2,this.select("Source camera FOV",{auto:"Estimate with MoGe-2",manual:"Use manual estimate"},s.mesh_fov_mode,v=>this.setting("mesh_fov_mode",v)),
                s.mesh_fov_mode==="manual"?this.range("Manual horizontal FOV",s.mesh_fov,v=>this.setting("mesh_fov",v),{min:1,max:170,step:.01,defaultValue:49.13,unit:"°",help:"An estimate of the source camera's horizontal field of view, not a measured camera. A wrong estimate can distort proportions."}):this.hint("MoGe-2 estimates horizontal FOV from the prepared image. It is an estimate, not a measured camera.")),
            this.hint("Higher shape resolution can preserve small features and uses more memory. It cannot recover details that the image does not show.")));
        const stages=el("div");
        for(const [stage,label,steps,cfg] of [["structure","Structure",12,7.5],["shape","Shape",20,7.5],["refine","Refinement",12,7.5],["material","Material",12,1]])
            stages.append(el("h4",{},label),this.grid(2,
                this.range(`${label} steps`,s[`mesh_${stage}_steps`],v=>this.setting(`mesh_${stage}_steps`,v),{min:1,max:150,step:1,defaultValue:steps,help:"More sampling iterations take longer. This controls only this reconstruction stage."}),
                this.range(`${label} guidance`,s[`mesh_${stage}_cfg`],v=>this.setting(`mesh_${stage}_cfg`,v),{min:0,max:30,step:.1,defaultValue:cfg,help:"Higher guidance increases conditioning strength in this stage and can exaggerate or distort features."})));
        content.append(this.disclosure("Reconstruction sampling — four stages",stages));
        const textures=["master_texture","game_texture","normal_resolution","ao_resolution"],textureLabels=["Master texture size","Game texture size","Normal map size","Ambient-occlusion map size"];
        const exportFields=this.grid(2);
        for(const [key,label,min] of [["master_faces","Master triangle target",0],["game_faces","Game triangle target",100]])
            exportFields.append(this.input(label,s[key],v=>this.setting(key,Number(v)),{type:"number",min,max:50000000,step:1}));
        const maps=this.grid(2,...textures.map((key,i)=>this.select(textureLabels[i],Object.fromEntries([...new Set([512,1024,2048,4096,8192,s[key]])].sort((a,b)=>a-b).map(n=>[n,`${n} px`])),s[key],v=>this.setting(key,Number(v)))));
        content.append(this.panel("GPU finishing & exports","PEC finishes UVs on the GPU. Apply these settings to a saved reconstruction from Mesh & export without repeating image generation or Pixal3D.",
            exportFields,this.hint("More triangles keep fine parts but produce larger files. Master target 0 keeps the available faces. Triangle targets do not lower earlier reconstruction memory."),maps,
            this.grid(2,this.range("Surface smoothing",s.smoothing,v=>this.setting("smoothing",v),{min:0,max:20,step:1,defaultValue:0,help:"Smoothing modifies geometry and can soften small details or openings. Zero skips it."}),
                this.range("Hard-edge angle",s.crease_angle,v=>this.setting("crease_angle",v),{min:0,max:180,step:1,defaultValue:45,unit:"°",help:"Used when remeshing to preserve sharp edges. This is a geometry control, not a texture detail control."})),
            this.grid(3,this.check("Remesh before finishing",s.remesh,v=>this.setting("remesh",v)),this.check("Bake normal map",s.bake_normal,v=>this.setting("bake_normal",v)),this.check("Bake ambient occlusion",s.bake_ao,v=>this.setting("bake_ao",v))),
            this.hint("Remeshing changes geometry and can affect thin parts. Texture and map sizes change surface detail and baking memory, not the underlying shape. This workflow has no CPU finishing fallback.")));
        const dimensions=this.grid(3);
        for(const axis of ["width","height","depth"])dimensions.append(this.input(`Requested ${axis} (meters)`,p.target.requested_dimensions_m[axis],value=>{
            const values={...this.project.target.requested_dimensions_m};if(value.trim())values[axis]=Number(value);else delete values[axis];return this.save({target:{requested_dimensions_m:values}});
        },{type:"number",min:.000001,step:"any"}));
        content.append(this.panel("Target & dimensions","Requested sizes and measured mesh sizes are recorded separately in the exported package.",
            this.grid(2,this.select("Intended use",{game:"Game starting asset",print:"3D print starting asset",both:"Game and print"},p.target.intended_use,v=>this.save({target:{intended_use:v}})),
                this.input("Default asset height (meters)",s.asset_height,v=>this.setting("asset_height",Number(v)),{type:"number",min:.001,max:100000,step:"any"})),dimensions,
            this.hint("Height can uniformly scale the mesh. Width and depth are instructions for the receiving agent. Collision, LODs, print wall thickness and supports still need checking.")));
        this.downloadNode=el("p",{class:"hint"});this.downloadMeter=el("progress",{"aria-label":"Model download progress"});
        const token=el("input",{type:"password",autocomplete:"off",placeholder:"Paste a read token here","aria-label":"Hugging Face token","data-control":"Hugging Face token"});
        const connect=this.panel("Local models & Hugging Face","Public models usually need no token. Gated models require access approval on their Hugging Face page and a read token from that same account.",
            el("div",{class:"connection-state"},`Hugging Face: ${this.resources?.hugging_face?.connected?"Connected":"Not connected"}. A token does not accept a model's license for you.`),
            el("label",{class:"field"},el("span",{},"Hugging Face read token"),token),
            el("div",{class:"row"},this.button("Save token",async()=>{try{await legacy("/hugging-face",{action:"connect",token:token.value});this.status("Hugging Face token saved privately.");}finally{token.value="";}},this.blocked()),
                this.button("Test connection",async()=>{const status=await legacy("/hugging-face",{action:"test"});this.status(status.connected?`Connected to Hugging Face${status.account?" as "+status.account:""}. Your token is stored privately.`:status.error||status.message||"Save a read token, then test again.",!status.connected);},this.blocked(),"quiet"),
                this.button("Disconnect",()=>legacy("/hugging-face",{action:"disconnect"}),this.blocked(),"quiet")),
            el("a",{href:"https://huggingface.co/settings/tokens",target:"_blank",rel:"noopener noreferrer",class:"text-link"},"Create or manage a Hugging Face read token"),
            this.hint("If a download asks for access: open its model page, sign in and accept or request access. Then save a token allowed to read that repository and retry. Browser sign-in does not connect this downloader."),
            el("div",{class:"row"},this.button("Check / download image models",()=>this.downloadModels("image"),this.blocked()),this.button("Check / download mesh models",()=>this.downloadModels("mesh"),this.blocked()),
                this.button("Pause download",()=>legacy("/download/pause",{}),"","quiet")),this.downloadNode,this.downloadMeter,
            el("p",{class:"path"},`Models: ${this.resources?.models_directory||"this Comfy installation"}\nLibrary: ${this.resources?.root||"loading"}`));
        content.append(connect);
        this.civitai.renderSettings(content);
    }
    async downloadModels(stage,action="generate") {
        const status=await legacy(`/assets/${this.project.id}/models?stage=${encodeURIComponent(stage)}&action=${encodeURIComponent(action)}`);
        if(!status.missing.length){this.status("The selected model files are available locally.");return true;}
        const projectId=this.project.id;
        const dialog=el("dialog",{class:"aw","aria-label":"Required model downloads"},el("h3",{},"Download the required model files"),
            this.hint("These files are missing from this Comfy installation. Review their licenses before downloading. If a repository asks for access, accept or request it on Hugging Face and connect a read token for that same account. Public repositories usually need no token."),
            el("ul",{},status.missing.map(model=>el("li",{},`${model.name} · ${(model.size/1024**3).toFixed(2)} GB `,
                el("a",{href:model.repo_url||`https://huggingface.co/${model.repo}`,target:"_blank",rel:"noopener noreferrer"},"Open model page")," · ",
                el("a",{href:model.license_url,target:"_blank",rel:"noopener noreferrer"},"Read license")))),
            this.hint("Click Download after reviewing the licenses. This does not accept gated terms on Hugging Face or start generation."));
        const close=()=>dialog.close();
        dialog.append(el("div",{class:"row"},el("button",{onclick:close},"Cancel"),
            el("button",{onclick:()=>{close();this.openModelConnection();}},"Connect Hugging Face"),
            this.button("Download these files",async()=>{
                if(this.project.id!==projectId)throw Error("The current job changed. Open its model setup again.");
                await legacy(`/assets/${projectId}/download`,{stage,action,accept_licenses:true});
                close();this.status("Downloading to this Comfy installation. Progress and verification appear below. Retry the original action when the download finishes.");
                await this.poll();
                this.root.scrollTop=this.inlineDownloadNode.offsetTop-60;
            },this.blocked(),"primary")));
        document.body.append(dialog);dialog.addEventListener("close",()=>dialog.remove());dialog.showModal();
        return false;
    }
    async loadHistory() {
        try {
            const data=await request(`/projects?offset=${this.offset}&limit=12`);if(this.tab!=="History"||!this.historyNode?.isConnected)return;
            this.historyNode.replaceChildren(el("h3",{},"History"),this.hint("Open a saved job to review or continue it. Reuse parameters creates a separate job and keeps the original. Opening the workflow starts clean; saved jobs stay here."),
                el("div",{class:"history-actions"},this.button("Clear history",async()=>{
                    const all=await legacy("/assets");this.confirm("Clear all history?",`Move all ${all.length} saved jobs and their files to the local trash? They disappear from History. Undo is available here after this action.`,"Clear all history",async()=>{
                        const result=await legacy("/history/clear",{assets:all.map(a=>a.id)});this.undo=result.deleted.map(r=>r.token);this.project=await request("/projects",{});this.job=null;await this.loadHistory();},"DELETE HISTORY");
                },this.blocked(),"quiet danger"),this.button("Undo last deletion",async()=>{for(const token of this.undo)await legacy(`/trash/${token}/restore`,{});this.undo=[];await this.loadHistory();},this.blocked()||(!this.undo.length?"No deletion to undo in this session.":""),"quiet")));
            const cards=el("div",{class:"cards"});this.historyNode.append(cards);
            for(const entry of data.entries) {
                const image=entry.thumbnail?el("figure",{},el("img",{src:`/asset-workshop/file/${entry.id}?path=${encodeURIComponent(entry.thumbnail)}`,alt:entry.name}),
                    this.link("Download image",`/asset-workshop/file/${entry.id}?path=${encodeURIComponent(entry.thumbnail)}&download=1`)):null;
                const include=el("input",{type:"checkbox"});
                cards.append(el("article",{class:"card history-card"},el("h4",{},entry.name),el("div",{class:"history-meta"},entry.updated?new Date(entry.updated*1000).toLocaleString():"Saved job"),image,el("p",{class:"history-prompt"},entry.prompt),el("label",{class:"check"},include,"Also reuse saved images (review required)"),
                    el("div",{class:"row"},this.button("Open saved job",async()=>{this.project=await request(`/projects/${entry.id}`);this.job=null;
                        this.tab=this.project.artifacts.some(a=>a.kind==="mesh"&&!a.stale)?"Mesh & agent package":this.current("mesh_input")?"Approve image":"Create image";
                        this.root.scrollTop=0;this.status("Saved job opened. Its original files and settings are available.");},this.blocked()),
                        this.button("Reuse parameters",async()=>{this.project=await request(`/projects/${entry.id}/reuse`,{include_images:include.checked});this.job=null;this.tab="Create image";},this.blocked()),
                        this.button("Delete",()=>this.confirm(`Delete ${entry.name}?`,"Move this job and its files to the local trash? Undo will be available here.","Delete",async()=>{
                            const result=await legacy(`/assets/${entry.id}`,undefined,"DELETE");this.undo=[result.token];if(this.project.id===entry.id)this.project=await request("/projects",{});await this.loadHistory();}),this.blocked(),"quiet danger"))));
            }
            this.historyNode.append(el("div",{class:"row"},this.button("Previous",async()=>{this.offset=Math.max(0,this.offset-12);await this.loadHistory();},this.offset===0?"First page.":""),
                this.hint(`${Math.min(data.offset+1,data.total)}–${Math.min(data.offset+data.limit,data.total)} of ${data.total}`),
                this.button("Next",async()=>{this.offset+=12;await this.loadHistory();},data.offset+data.limit>=data.total?"Last page.":"")));
        } catch(error){this.status(error.message,true);}
    }
}

export function renderSingleControls(node) {
    clearInterval(node.timer);node.title="Mumblebox — image to mesh & agent package";
    node.size=[Math.max(node.size[0],1060),Math.max(node.size[1],900)];
    node.root.style.padding="0";node.root.style.overflow="hidden";
    if(!node.singleControls)node.singleControls=new SingleImageControls(node);
    else if(node.singleControls.root.parentNode!==node.root)node.root.replaceChildren(node.singleControls.root);
    app.mumbleboxSingle=node.singleControls;
}
