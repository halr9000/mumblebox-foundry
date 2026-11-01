import {el,button,hint,field,link} from "../dom.js";
import {request} from "../services.js";
import {dialog} from "../dialogs.js";
import {modelUsageRows} from "../../model-usage.js";
import {activity} from "../activity.js";
import {activityState} from "../activity-state.js";
import {showCivitaiHelp} from "../connection-help.js";
const BASE="/asset-workshop/v2/civitai";
const NSFW_KEY="mumblebox-civitai-nsfw";
const profiles={"sdxl_base":"SDXL 1.0","klein4":"FLUX.2 Klein 4B","klein4_base":"FLUX.2 Klein 4B base",
    "klein_base":"FLUX.2 Klein 9B base","klein_distilled":"FLUX.2 Klein 9B","qwen21":"Qwen Image 2.1","qwen2511":"Qwen Image Edit 2511"};
const size=n=>n>=1024**3?(n/1024**3).toFixed(2)+" GB":(n/1024**2).toFixed(1)+" MB";
const select=(label,options)=>el("select",{"aria-label":label},Object.entries(options).map(([value,text])=>el("option",{value},text)));

export async function render(shell) {
    let disposed=false,sequence=0,controller,timer,cursor="",items=[];
    const profile=select("Image model family",profiles);
    const kind=select("Resource type",{LORA:"LoRAs",Checkpoint:"Checkpoints"});
    const query=el("input",{type:"search",placeholder:"Name or keyword","aria-label":"Search Civitai"});
    const sort=select("Sort by",{"Highest Rated":"Highest rated","Most Downloaded":"Most downloaded",Newest:"Newest"});
    let includeNsfw=false;
    try{includeNsfw=localStorage.getItem(NSFW_KEY)==="true";}catch{}
    const nsfw=el("input",{type:"checkbox",checked:includeNsfw,"aria-label":"Include NSFW resources"});
    const results=el("div",{class:"model-list"});
    const feedback=el("p",{class:"muted",role:"status"},"Choose a model family and search for compatible resources.");
    const status=el("div",{class:"note-panel"});
    const downloadActivity=activity();
    const installed=el("div",{class:"library-list"});
    const searchButton=button("Search",()=>search(false),{class:"primary"});
    const more=button("Load more",()=>search(true),{hidden:true});
    const root=el("div",{class:"civitai-browser"},
        el("div",{class:"page-head civitai-heading"},el("h2",{},"Civitai Model Browser"),
            button("Connection settings",()=>shell.settings({service:"civitai"}))),
        el("div",{class:"civitai-intro"},
            el("p",{class:"muted"},link("Civitai","https://civitai.com")," is an independent, third-party platform. Models and LoRAs belong to their creators and have individual licenses. Foundry browses and installs your selections."),
            hint("For initial image creation only. Turnarounds use Foundry’s built-in supported models.")),
        el("div",{class:"filters"},field("Model family",profile),field("Resource",kind),field("Search",query),field("Sort",sort),searchButton),
        el("div",{class:"civitai-options"},el("label",{class:"choice"},nsfw,"Include NSFW resources"),
            el("div",{class:"civitai-auth-help"},hint("Some downloads require a Civitai API key."),
                button("How to connect Civitai",()=>showCivitaiHelp(shell),{class:"text-link","aria-haspopup":"dialog"}))),
        feedback,results,more,status,el("h3",{style:"margin:26px 0 14px"},"Installed resources"),installed,
        hint("Downloads are placed in the correct ComfyUI model or LoRA folder. The upcoming image-creation workflow will use these resources; downloading them does not change the turnaround models."));
    query.addEventListener("keydown",e=>{if(e.key==="Enter"){e.preventDefault();search(false);}});
    for(const control of [profile,kind,sort,nsfw])control.addEventListener("change",()=>{
        if(control===nsfw){try{localStorage.setItem(NSFW_KEY,String(nsfw.checked));}catch{}}
        search(false);
    });

    async function search(append) {
        controller?.abort();controller=new AbortController();
        const current=++sequence;
        if(!append){cursor="";items=[];results.replaceChildren();more.hidden=true;}
        searchButton.disabled=true;more.disabled=true;feedback.textContent="Searching Civitai…";
        const params=new URLSearchParams({profile:profile.value,kind:kind.value,query:query.value,sort:sort.value,period:"AllTime",nsfw:String(nsfw.checked)});
        if(append&&cursor)params.set("cursor",cursor);
        try {
            const data=await request(BASE+"/search?"+params,undefined,{signal:controller.signal});
            if(disposed||current!==sequence)return;
            items=[...new Map((append?[...items,...data.items]:data.items).map(item=>[item.id,item])).values()];cursor=data.next_cursor;
            feedback.textContent=items.length?items.length+" resources shown. Review each version and its license before downloading.":"No matching resources. Try another name or model family.";
            results.replaceChildren(...items.map(model=>el("article",{class:"model-card resource-card"},preview(model),el("div",{class:"resource-card-body"},el("h3",{},model.name),
                hint((model.creator||"Creator not listed")+" · "+model.type),
                hint(model.description.slice(0,180)+(model.description.length>180?"…":"")),
                el("div",{class:"actions"},button("Download",()=>detail(model),{class:"primary"}),button("Details",()=>detail(model)),link("View on Civitai",model.source_url))))));
            more.hidden=!cursor;
        } catch(e){if(e.name!=="AbortError"&&!disposed&&current===sequence)feedback.textContent=e.message;}
        finally{if(current===sequence){searchButton.disabled=false;more.disabled=false;}}
    }
    function preview(model){
        const version=model.versions.find(v=>v.compatible)||model.versions[0],image=version?.images?.[0];
        return button(image?el("img",{src:image.url,alt:"Preview of "+model.name,loading:"lazy",decoding:"async",referrerPolicy:"no-referrer",
            onerror:e=>{e.target.replaceWith(el("span",{},"Preview unavailable"));}}):el("span",{},"No preview available"),
            ()=>detail(model),{class:"resource-preview","aria-label":"Open "+model.name});
    }
    async function detail(model) {
        try {
            const selectedProfile=profile.value,selectedKind=kind.value,current=sequence;
            const full=await request(BASE+"/model/"+model.id+"?"+new URLSearchParams({profile:selectedProfile,nsfw:String(nsfw.checked)}));
            if(disposed||current!==sequence)return;
            const versions=select("Resource version",Object.fromEntries(full.versions.map(v=>[v.id,v.name+" · "+v.base_model+(v.compatible?"":" · incompatible")])));
            const preferred=full.versions.find(v=>v.compatible&&v.files.some(f=>f.eligible));
            if(preferred)versions.value=String(preferred.id);
            const files=el("div",{});
            const redraw=()=>{
                const version=full.versions.find(v=>String(v.id)===versions.value);
                files.replaceChildren(el("div",{class:"resource-previews"},...(version?.images||[]).map(image=>
                    el("a",{href:image.url,target:"_blank",rel:"noopener noreferrer"},el("img",{src:image.url,alt:"Creator preview for "+version.name,
                        loading:"lazy",decoding:"async",referrerPolicy:"no-referrer"})))),
                    hint(version?.notes||"No version notes supplied."),
                    ...(version?.triggers?.length?[hint("Trigger words: "+version.triggers.join(", "))]:[]),
                    ...((version?.files)||[]).map(file=>el("div",{class:"settings-section"},
                        el("p",{class:"filename"},file.name),hint(size(file.size_bytes)+" · "+file.format),
                        hint(file.eligible?"Compatible file with a published checksum.":file.reason||"Not eligible for installation."),
                        button("Download",async event=>{
                            const control=event.currentTarget;control.disabled=true;
                            try {
                                await request(BASE+"/download",{model_id:full.id,version_id:version.id,file_id:file.id,profile:selectedProfile,kind:selectedKind});
                                shell.message("Downloading the selected resource. Progress appears below and in the header.");
                                await refreshStatus();
                            } catch(e){shell.message(e.message,true);}
                            finally{control.disabled=!file.eligible;}
                        },{disabled:!file.eligible,class:"primary"}))));
            };
            versions.addEventListener("change",redraw);redraw();
            dialog(shell,"Download · "+full.name,el("div",{},hint("Choose a version and file. The app installs it in the correct folder for initial image creation."),link("License and resource page",full.source_url),
                field("Version",versions),files,el("h3",{},"Author permissions"),
                el("dl",{},...modelUsageRows(full.permissions,true).flatMap(([key,value])=>[el("dt",{},key),el("dd",{},value)]))));
        } catch(e){shell.message(e.message,true);}
    }
    async function refreshStatus() {
        try{
            const [data,local]=await Promise.all([request(BASE+"/status"),request(BASE+"/installed")]);
            if(disposed)return;
            const d=data.download;
            downloadActivity.update({...activityState({download:d}),
                label:d.status==="running"?"Downloading "+(d.name||"resource"):d.status==="complete"?"Download complete":d.status==="idle"?"No download active":"Download "+d.status,
                detail:d.error||[d.total?size(d.bytes||0)+" / "+size(d.total):"",d.phase||""].filter(Boolean).join(" · ")});
            status.replaceChildren(el("div",{class:"connection-line"},el("strong",{},"Civitai"),
                el("span",{class:"badge"},data.connection.connected?"Connected":"Not connected"),
                !data.connection.connected?hint("Public browsing is available. Some downloads require a connection."):null),downloadActivity.element);
            const controls=el("div",{class:"actions"});
            if(d.status==="running")controls.append(button("Pause download",()=>control("pause")));
            if(["paused","failed"].includes(d.status))controls.append(button("Resume / retry",()=>control("retry")));
            if(["running","paused","failed"].includes(d.status))controls.append(button("Cancel download",()=>control("cancel")));
            status.append(controls);
            installed.replaceChildren(...local.items.map(item=>el("article",{class:"model-card"},el("strong",{},item.model_name||item.name||item.file_id),
                hint((item.base_model||item.profile||"")+" · "+(item.kind||"")+" · Initial image creation"),
                el("div",{class:"filename"},item.relative_path||item.name||""),el("span",{class:"badge"},"Installed"))));
            if(!local.items.length)installed.append(hint("No resources have been installed through this browser yet."));
        }catch(e){if(!disposed)status.replaceChildren(hint(e.message));}
        finally{clearTimeout(timer);if(!disposed)timer=setTimeout(refreshStatus,3000);}
    }
    async function control(action) {
        try{await request(BASE+"/download/control",{action});await refreshStatus();}
        catch(e){shell.message(e.message,true);}
    }
    await refreshStatus();
    search(false);
    return {element:root,dispose:()=>{disposed=true;controller?.abort();clearTimeout(timer);sequence++;}};
}
