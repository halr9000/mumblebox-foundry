import {api} from "../../../scripts/api.js";

const PREFIX="/asset-workshop/v2/civitai";
const NSFW_KEY="mumblebox-civitai-nsfw";
const live=status=>["running","pausing","cancelling"].includes(status);
const size=value=>value>=1024**3?`${(value/1024**3).toFixed(2)} GB`:value>=1024**2?`${(value/1024**2).toFixed(1)} MB`:`${Math.max(0,Math.round(value/1024))} KB`;
function el(tag,attrs={},...children){
    const node=document.createElement(tag);
    for(const [key,value] of Object.entries(attrs)){
        if(key.startsWith("on"))node.addEventListener(key.slice(2),value);
        else if(key in node)node[key]=value;
        else node.setAttribute(key,value);
    }
    node.append(...children.flat().filter(value=>value!==null&&value!==undefined));return node;
}
const link=(label,url)=>el("a",{href:url,target:"_blank",rel:"noopener noreferrer"},label);
async function request(path,body,signal){
    const response=await api.fetchApi(PREFIX+path,{method:body===undefined?"GET":"POST",signal,
        ...(body===undefined?{}:{headers:{"Content-Type":"application/json"},body:JSON.stringify(body)})});
    const data=await response.json();
    if(!response.ok)throw Object.assign(Error(data.error||"The Civitai request could not finish."),data,{status:response.status});
    return data;
}

export class BrowserState {
    constructor(){
        this.profile="";this.kind="LORA";this.query="";this.sort="Highest Rated";this.period="AllTime";
        this.nsfw=false;try{this.nsfw=localStorage.getItem(NSFW_KEY)==="true";}catch{}
        this.items=[];this.cursor=null;this.selected=null;this.version=null;this.file=null;
        this.loading=false;this.error=null;this.sequence=0;this.initialized=false;
    }
    reset(){this.sequence++;this.items=[];this.cursor=null;this.selected=null;this.version=null;this.file=null;this.error=null;}
    changeNsfw(value){this.nsfw=!!value;this.reset();try{localStorage.setItem(NSFW_KEY,String(this.nsfw));}catch{}}
    accept(sequence,result,append){
        if(sequence!==this.sequence)return false;
        const prior=append?this.items:[],ids=new Set(prior.map(item=>item.id));
        this.items=[...prior,...result.items.filter(item=>!ids.has(item.id))];this.cursor=result.next_cursor;
        return true;
    }
}

export class CivitaiBrowser {
    constructor(host){this.host=host;this.state=new BrowserState();this.installed=[];this.connection={};this.download={status:"idle"};this.progressNodes=[];}
    dispose(){this.controller?.abort();clearTimeout(this.oauthTimer);}
    button(label,callback,disabled=false,className="quiet"){
        const button=el("button",{type:"button",class:className,disabled,onclick:async()=>{
            button.disabled=true;
            try{await callback();}catch(error){this.state.error=error;this.host.status(error.message,true);this.redraw();}
            finally{if(button.isConnected)button.disabled=disabled;}
        }},label);return button;
    }
    hint(text){return el("p",{class:"hint"},text);}
    field(label,options,value,change){
        return el("label",{class:"field"},el("span",{},label),el("select",{value,onchange:event=>change(event.target.value)},
            Object.entries(options).map(([key,label])=>el("option",{value:key,selected:String(key)===String(value)},label))));
    }
    async open(kind=this.state.kind){
        const changed=this.state.profile!==this.host.project.profile||kind!==this.state.kind;
        this.state.profile=this.host.project.profile;this.state.kind=kind;
        if(changed)this.state.reset();
        this.host.tab="Integrations";this.host.render();this.host.root.scrollTop=0;
        if(changed||!this.state.initialized)await this.search();
    }
    openSettings(){
        this.returnToBrowser=this.host.tab==="Integrations";this.host.tab="Settings";this.host.render();
        const section=this.host.root.querySelector('[data-service="civitai"]');
        section?.scrollIntoView({block:"start"});section?.querySelector("input")?.focus({preventScroll:true});
    }
    redraw(){if(this.content?.isConnected&&this.host.tab==="Integrations")this.render(this.content);}
    async search(append=false){
        this.controller?.abort();this.controller=new AbortController();
        const sequence=++this.state.sequence,s=this.state;
        if(!append){s.items=[];s.cursor=null;s.selected=null;s.version=null;s.file=null;}
        s.loading=true;s.error=null;s.initialized=true;this.redraw();
        const query=new URLSearchParams({profile:s.profile,kind:s.kind,query:s.query,sort:s.sort,period:s.period,nsfw:String(s.nsfw)});
        if(append&&s.cursor)query.set("cursor",String(s.cursor));
        try{const data=await request("/search?"+query,undefined,this.controller.signal);s.accept(sequence,data,append);}
        catch(error){if(error.name!=="AbortError"&&sequence===s.sequence)s.error=error;}
        finally{if(sequence===s.sequence){s.loading=false;this.redraw();}}
    }
    async change(key,value){this.state[key]=value;this.state.reset();await this.search();}
    async select(model){
        const sequence=++this.state.sequence;this.state.loading=true;this.state.error=null;this.redraw();
        try{
            const query=new URLSearchParams({profile:this.state.profile,nsfw:String(this.state.nsfw)});
            const result=await request(`/model/${model.id}?${query}`);
            if(sequence!==this.state.sequence)return;
            this.resultsScroll=this.host.root.scrollTop;this.chooseModel(result);
        }catch(error){if(sequence===this.state.sequence)this.state.error=error;}
        finally{if(sequence===this.state.sequence){this.state.loading=false;this.redraw();this.host.root.scrollTop=0;}}
    }
    chooseModel(model){
        this.state.selected=model;
        const requested=model.selected_version;
        this.chooseVersion(model.versions.find(v=>v.id===requested)||model.versions.find(v=>v.compatible)||model.versions[0]);
    }
    chooseVersion(version){this.state.version=version;this.state.file=version?.files.find(f=>f.eligible)||version?.files[0]||null;}
    async loadInstalled(){this.installed=(await request("/installed")).items;}
    needsProfileChange(item){return item.profile!==this.host.project.profile&&!(item.family==="sdxl"&&this.host.project.profile.startsWith("sdxl"));}
    applyLabel(item){
        const action=item.kind==="LORA"?"Add LoRA":"Use checkpoint";
        return this.needsProfileChange(item)?`${action} with ${this.host.capabilities.profiles[item.profile].label}`:action;
    }
    async apply(item){
        if(this.needsProfileChange(item))await this.host.save({profile:item.profile});
        this.host.project=await request("/apply",{project_id:this.host.project.id,expected_revision:this.host.project.revision,file_id:item.file_id,kind:item.kind});
        this.host.loraList=await this.host.loadLocalLoras();
        this.host.tab="Create image";this.host.status(item.kind==="LORA"?"LoRA added. Review its strength and trigger words before generating.":"Checkpoint selected for the next image.");
        this.host.render();
    }
    async poll(){
        if(this.polling)return;this.polling=true;
        try{
            const data=await request("/status"),previous=this.download.status;
            this.connection=data.connection;this.download=data.download;
            if(!this.loadedInstalled||this.download.status==="completed"&&previous!=="completed"){
                await this.loadInstalled();this.loadedInstalled=true;
                if(this.download.status==="completed"){this.host.loraList=await this.host.loadLocalLoras();this.redraw();}
            }
            this.updateProgress();
        }catch(error){this.backendError=error.message;}
        finally{this.polling=false;}
    }
    progress(){
        const root=el("section",{class:"civitai-transfer",hidden:this.download.status==="idle","aria-label":"Civitai download progress","aria-live":"polite"});
        this.progressNodes=this.progressNodes.filter(node=>node.isConnected);this.progressNodes.push(root);this.updateProgress();return root;
    }
    updateProgress(){
        const d=this.download;
        for(const node of this.progressNodes){
            node.hidden=!d.status||d.status==="idle";
            if(node.hidden)continue;
            const total=Number(d.total)||0,received=Number(d.bytes)||0;
            const meter=el("progress",{"aria-label":"Civitai file download"});
            if(total){meter.max=total;meter.value=Math.min(received,total);}
            const message=`${d.phase||d.status}${d.name?" · "+d.name:""}`;
            node.replaceChildren(el("div",{class:"transfer-heading"},el("strong",{},message),
                el("span",{},total?`${size(received)} / ${size(total)} · ${Math.min(100,Math.floor(received/total*100))}%`:`${size(received)} downloaded`)),meter);
            const actions=el("div",{class:"row"});
            if(live(d.status)){
                actions.append(this.button("Pause",async()=>{this.download=await request("/download/control",{action:"pause"});this.updateProgress();},d.status!=="running"),
                    this.button("Cancel download",async()=>{this.download=await request("/download/control",{action:"cancel"});this.updateProgress();},d.status!=="running"));
            }else if(["paused","failed","cancelled"].includes(d.status)){
                actions.append(this.button(d.status==="paused"?"Resume download":"Retry download",async()=>{this.download=await request("/download/control",{action:"retry"});this.updateProgress();}));
                if(d.status!=="cancelled")actions.append(this.button("Discard partial download",async()=>{this.download=await request("/download/control",{action:"cancel"});this.updateProgress();}));
            }
            if(d.error)actions.append(this.errorPanel(d.error));
            if(d.status==="completed"){
                const item=this.installed.find(item=>item.file_id===d.item?.file_id);
                if(item)actions.append(this.button(this.applyLabel(item),()=>this.apply(item),!!this.host.blocked(),"primary"));
            }
            node.append(actions);
        }
    }
    errorPanel(error){
        const box=el("div",{class:"civitai-error",role:"alert"},el("p",{},error.message||error.error||String(error)));
        if(error.kind==="authentication")box.append(this.button("Open Civitai Settings",()=>this.openSettings()));
        else if(error.kind==="access"&&this.state.selected)box.append(link("Review resource access on Civitai",this.state.selected.source_url),this.button("Civitai connection settings",()=>this.openSettings()));
        return box;
    }
    render(content){
        this.content=content;content.replaceChildren();const s=this.state;
        if(!s.profile)s.profile=this.host.project.profile;
        const toggle=el("input",{type:"checkbox",role:"switch",checked:s.nsfw,"aria-label":"Show NSFW content",onchange:async event=>{
            this.state.changeNsfw(event.target.checked);await this.search();
        }});
        content.append(el("section",{class:"civitai-browser-top"},
            el("label",{class:"toggle"},toggle,el("span",{class:"toggle-track","aria-hidden":"true"}),el("span",{},"Show NSFW content")),
            this.button("Civitai settings",()=>this.openSettings())));
        content.append(el("div",{class:"step-heading"},el("h3",{},"Civitai browser"),this.hint("Download optional LoRAs and checkpoints for the image workflows supported here. Downloads stay in this Comfy installation.")));
        if(!this.connection.connected)content.append(el("div",{class:"civitai-connection-hint"},this.hint("Public browsing is available. Some files require a Civitai connection or access approval."),this.button("Connect Civitai in Settings",()=>this.openSettings())));
        if(this.backendError&&!this.loadedInstalled)content.append(this.errorPanel({message:this.backendError}));
        const models=Object.fromEntries(Object.entries(this.host.capabilities.profiles).map(([key,value])=>[key,value.label]));
        const query=el("input",{type:"search",value:s.query,placeholder:"Search names, styles or creators","aria-label":"Search Civitai LoRAs and checkpoints",oninput:event=>{s.query=event.target.value;}});
        const form=el("form",{class:"civitai-search",onsubmit:event=>{event.preventDefault();this.search();}},query,this.button("Search",()=>this.search(),s.loading,"primary"));
        content.append(form,this.host.grid(2,
            this.field("Resource type",{LORA:"LoRAs",Checkpoint:"Checkpoints"},s.kind,value=>this.change("kind",value)),
            this.field("Compatible image model",models,s.profile,value=>this.change("profile",value))),
            this.host.grid(2,this.field("Sort by",{"Highest Rated":"Highest rated","Most Downloaded":"Most downloaded","Most Liked":"Most liked",Newest:"Newest"},s.sort,value=>this.change("sort",value)),
                this.field("Time period",{AllTime:"All time",Year:"Past year",Month:"Past month",Week:"Past week",Day:"Past day"},s.period,value=>this.change("period",value))));
        if(s.error)content.append(this.errorPanel(s.error));
        if(s.loading)content.append(el("p",{role:"status"},"Loading Civitai…"));
        const url=el("input",{type:"url",placeholder:"https://civitai.com/models/…","aria-label":"Civitai resource link"});
        content.append(this.host.disclosure("Open a Civitai link",this.hint("A pasted link goes through the same resource and compatibility checks."),
            el("div",{class:"civitai-search"},url,this.button("Open resource",async()=>{
                const sequence=++s.sequence;const model=await request("/resolve-url",{url:url.value,profile:s.profile,nsfw:s.nsfw});
                if(sequence===s.sequence){s.kind=model.type;this.chooseModel(model);this.redraw();}
            }))));
        if(s.selected)this.renderDetail(content);
        else{
            const cards=el("div",{class:"civitai-cards"});
            for(const model of s.items){
                const version=model.versions.find(v=>v.compatible)||model.versions[0],image=version?.images[0];
                const preview=image?el("img",{src:image.url,loading:"lazy",decoding:"async",alt:`Preview of ${model.name}`,referrerPolicy:"no-referrer"}):el("div",{class:"civitai-no-preview"},"No preview available");
                cards.append(el("article",{class:"civitai-card"},preview,el("div",{class:"civitai-card-body"},el("h4",{},model.name),
                    this.hint(`By ${model.creator||"creator"} · ${version?.base_model||"Base model unspecified"}`),
                    this.button("View versions & download",()=>this.select(model),s.loading),
                    version?.compatible?null:this.hint("Exact variant compatibility needs confirmation."))));
            }
            content.append(cards);
            if(!s.loading&&!s.items.length)content.append(el("div",{class:"empty"},"No matching resources yet. Try another search or supported model filter."));
            if(s.cursor)content.append(this.button("Load more",()=>this.search(true),s.loading));
        }
        this.renderInstalled(content);
        if(!s.initialized&&!s.loading)queueMicrotask(()=>{if(!s.initialized&&!s.loading&&this.content?.isConnected&&this.host.tab==="Integrations")this.search();});
    }
    renderDetail(content){
        const s=this.state,m=s.selected,v=s.version,f=s.file;
        const section=el("section",{class:"control-panel civitai-detail"},this.button("Back to results",()=>{s.selected=null;this.redraw();this.host.root.scrollTop=this.resultsScroll||0;}),
            el("h3",{},m.name),this.hint(`By ${m.creator||"creator"}`),link("Open resource on Civitai",m.source_url));
        if(!v){section.append(this.hint("No published versions are available."));content.append(section);return;}
        section.append(this.field("Version",Object.fromEntries(m.versions.map(v=>[v.id,`${v.name} · ${v.base_model}`])),v.id,value=>{this.chooseVersion(m.versions.find(v=>String(v.id)===value));this.redraw();}));
        const images=el("div",{class:"civitai-previews"},v.images.map(image=>el("img",{src:image.url,loading:"lazy",decoding:"async",alt:`Creator preview for ${v.name}`,referrerPolicy:"no-referrer"})));
        section.append(images,this.field("Weight file",Object.fromEntries(v.files.map(f=>[f.id,`${f.name} · ${size(f.size_bytes)}${f.eligible?"":" · unavailable"}`])),f?.id,value=>{s.file=v.files.find(f=>String(f.id)===value);this.redraw();}));
        if(f){
            section.append(this.hint(`${f.format||"Unspecified format"} · ${size(f.size_bytes)} · ${v.base_model}`));
            if(!f.eligible)section.append(el("p",{class:"error"},f.reason));
            const selection={model_id:m.id,version_id:v.id,file_id:f.id,profile:s.profile,kind:m.type};
            section.append(this.button("Download "+(m.type==="LORA"?"LoRA":"checkpoint"),async()=>{
                this.download=await request("/download",selection);this.updateProgress();
            },!f.eligible||live(this.download.status),"primary"));
            section.append(this.hint(`Destination: this Comfy installation’s models/${m.type==="LORA"?"loras":s.profile.startsWith("sdxl")?"checkpoints":"diffusion_models"}/Mumblebox folder. File names include version and file IDs to prevent collisions.`));
        }
        if(v.triggers.length)section.append(el("h4",{},"Creator trigger words"),el("p",{class:"civitai-trigger"},v.triggers.join(", ")));
        section.append(el("h4",{},"Creator’s usage notes"),el("p",{class:"civitai-notes"},v.notes||m.description||"No creator instructions were supplied."));
        section.append(el("h4",{},"Usage conditions"),this.hint("The creator’s permissions and the base model’s license apply separately. Read the linked resource page before commercial use."));
        const permissions=m.permissions||{};
        const commercial=Array.isArray(permissions.allowCommercialUse)?permissions.allowCommercialUse.join(", "):String(permissions.allowCommercialUse??"Not specified");
        section.append(el("dl",{class:"civitai-permissions"},el("dt",{},"Creator commercial-use flags"),el("dd",{},commercial),
            el("dt",{},"Credit required"),el("dd",{},permissions.allowNoCredit===true?"Creator allows use without credit":permissions.allowNoCredit===false?"Creator requires credit":"Not specified"),
            el("dt",{},"Derived models"),el("dd",{},permissions.allowDerivatives===true?"Allowed by creator":permissions.allowDerivatives===false?"Restricted by creator":"Not specified")));
        content.append(section);
    }
    renderInstalled(content){
        const rows=this.installed.filter(item=>item.profile===this.state.profile||item.family==="sdxl"&&this.state.profile.startsWith("sdxl"));
        content.append(this.host.disclosure(`Downloaded resources (${rows.length})`,
            rows.length?rows.map(item=>el("article",{class:"civitai-installed"},el("div",{},el("strong",{},item.model_name),
                this.hint(`${item.version_name} · ${item.base_model} · ${size(item.size_bytes)}`)),
                this.button(this.applyLabel(item),()=>this.apply(item),!!this.host.blocked()))):this.hint("Compatible downloads appear here after verification.")));
    }
    renderSettings(content){
        const connected=this.connection,token=el("input",{type:"password",autocomplete:"off","aria-label":"Civitai API key",placeholder:"Paste a Civitai API key"});
        const clientId=el("input",{value:connected.client_id||"","aria-label":"Mumblebox public Client ID",placeholder:"Public app identifier from Civitai registration"});
        const panel=this.host.panel("Civitai connection","Connect to browse and download resources available to your account. A connection does not purchase access or accept a creator’s conditions.",
            el("p",{class:"connection-state"},connected.connected?`Connected${connected.account?" as "+connected.account:""} · ${connected.method==="oauth"?"Connected app":"API key"}`:"Not connected · public browsing remains available"),
            connected.error?this.errorPanel({message:connected.error}):null,
            el("div",{class:"row"},this.button("Connect with Civitai",async()=>{const result=await request("/connection",{action:"begin"});this.connection.oauth=result;this.host.render();this.pollAuthorization();},!connected.client_id,"primary"),
                this.button("Test Civitai connection",async()=>{this.connection=await request("/connection",{action:"test"});this.host.status("Civitai connection verified.");this.host.render();},!connected.connected),
                this.button("Disconnect Civitai",async()=>{this.connection=await request("/connection",{action:"disconnect"});this.state.reset();this.state.initialized=false;this.host.status(this.connection.warning||"Civitai disconnected.");this.host.render();},!connected.connected)),
            this.hint(connected.client_id?"Connect provides Civitai’s authorization link and code. Mumblebox requests profile identity, model-download and preview-read permissions.":"Connected-app registration is the final setup step. A personal API key can also connect this installation."),
            el("label",{class:"field"},el("span",{},"Civitai API key — alternative connection"),token),
            this.hint("Open Civitai account settings, find API Keys, create a key and paste it above. The key is verified before it replaces an existing connection and is saved in the operating system’s credential vault."),
            el("div",{class:"row"},this.button("Save and verify Civitai key",async()=>{try{this.connection=await request("/connection",{action:"connect",token:token.value});this.host.status("Civitai key verified and saved securely.");this.host.render();}finally{token.value="";}},false,"primary"),
                link("Get or manage a Civitai API key","https://civitai.com/user/account")),
            this.host.disclosure("Connected-app setup",this.hint("Register Mumblebox as a public app with profile-read, model-read and media-read permissions. Enable device authorization. No client secret belongs here."),
                el("label",{class:"field"},el("span",{},"Mumblebox public Client ID"),clientId),
                this.button("Save public app identifier",async()=>{this.connection=await request("/connection",{action:"configure",client_id:clientId.value.trim()});this.host.status("Public app identifier saved. Connect with Civitai is ready to test.");this.host.render();})),
            this.button(this.returnToBrowser?"Return to Civitai browser":"Browse Civitai",()=>{this.host.tab="Integrations";this.host.render();this.host.root.scrollTop=0;}));
        panel.dataset.service="civitai";panel.style.scrollMarginTop="170px";
        const authorization=connected.oauth;
        if(authorization?.state==="pending")panel.append(el("section",{class:"civitai-authorization",role:"status"},
            el("strong",{},`Civitai authorization code: ${authorization.user_code}`),this.hint("Open the authorization page and approve the requested access. This page will detect the connection."),
            link("Open Civitai authorization",authorization.verification_uri),this.button("Cancel connection",async()=>{clearTimeout(this.oauthTimer);this.connection=await request("/connection",{action:"cancel"});this.host.render();})));
        content.append(panel);
    }
    async pollAuthorization(){
        clearTimeout(this.oauthTimer);
        try{
            this.connection=await request("/connection",{action:"poll"});
            if(this.connection.oauth?.state==="pending")this.oauthTimer=setTimeout(()=>this.pollAuthorization(),Math.max(5,this.connection.oauth.interval||5)*1000);
            else this.host.status(this.connection.connected?"Civitai connected securely.":"Authorization ended. Reconnect when ready.",!this.connection.connected);
            if(this.host.tab==="Settings")this.host.render();
        }catch(error){this.host.status(error.message,true);}
    }
}
