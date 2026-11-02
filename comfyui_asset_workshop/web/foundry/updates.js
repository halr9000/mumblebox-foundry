import {el,button,link,hint} from "./dom.js";
import {request} from "./services.js";
import {dialog} from "./dialogs.js";

export class UpdateChecks {
    constructor(shell) {
        this.shell=shell;
        this.listeners=new Set();
        this.banner=el("aside",{class:"update-notice",hidden:true,"aria-label":"Foundry update"});
        shell.content.before(this.banner);
    }
    async startup() {
        if(this.shell.data?.preferences.auto_check_updates===false)return;
        try {await this.check(false);}catch(error){
            this.result={state:"unavailable",message:error.message};this.notify();
        }
    }
    async check(manual=true) {
        if(this.pending)return this.pending;
        this.pending=request("updates/check",{manual}).then(result=>{
            if(this.disposed)return result;
            this.result=result;this.refreshBanner();this.notify();return result;
        }).finally(()=>{this.pending=null;});
        return this.pending;
    }
    notify() {for(const listener of this.listeners)listener();}
    refreshBanner() {
        const result=this.result;
        const visible=result?.state==="available"&&result.latest!==this.dismissed;
        this.banner.hidden=!visible;
        if(!visible)return;
        this.banner.replaceChildren(el("strong",{},result.message),
            button("View update",()=>this.details(),{class:"text-link"}),
            button("Later",()=>{this.dismissed=result.latest;this.refreshBanner();},{class:"text-link"}));
    }
    details() {
        const result=this.result;if(!result?.release_url)return;
        const actions=el("div",{class:"actions"},link("Release notes on GitHub",result.release_url));
        if(result.download_url)actions.prepend(link("Download update",result.download_url));
        dialog(this.shell,"Foundry "+result.latest,el("div",{},
            hint("In Pinokio, choose Update in the left sidebar to install and restart Foundry. For standalone ComfyUI, download the archive and follow INSTALL.md. Saved assets, models and settings are preserved."),
            actions,el("pre",{class:"release-notes"},result.notes||"See GitHub for release notes.")));
    }
    settings() {
        const shell=this.shell;
        const automatic=el("input",{type:"checkbox",checked:shell.data?.preferences.auto_check_updates!==false});
        const status=el("p",{role:"status","aria-live":"polite",class:"muted"});
        const notes=el("div",{class:"actions"});
        const draw=()=>{
            const data=this.result;
            status.textContent=data?.message||"No update check has been made yet.";
            if(data?.checked_at)status.textContent+=" Last checked: "+new Date(data.checked_at*1000).toLocaleString()+".";
            notes.replaceChildren();
            if(data?.state==="available")notes.append(button("View update and download",()=>this.details()));
        };
        const check=button("Check for updates",async()=>{
            check.disabled=true;status.textContent="Checking GitHub releases…";
            try{await this.check(true);draw();}catch(error){status.textContent=error.message;}
            finally{check.disabled=false;}
        });
        automatic.addEventListener("change",async()=>{
            automatic.disabled=true;
            try{shell.data.preferences=await request("preferences",{auto_check_updates:automatic.checked},{method:"PATCH"});}
            catch(error){automatic.checked=!automatic.checked;status.textContent=error.message;}
            finally{automatic.disabled=false;}
        });
        const element=el("section",{class:"settings-section update-settings"},el("h3",{},"Updates"),
            hint("Installed version: "+shell.data.version),
            el("label",{class:"choice"},automatic,"Check for updates on startup"),
            hint("Checks published GitHub versions on startup, with a five-minute cache. Check for updates requests a fresh result. Source-code pushes appear here when published as a release. No images or project information are sent."),
            el("div",{class:"actions"},check),status,notes);
        this.listeners.add(draw);draw();
        request("updates/status").then(result=>{if(element.isConnected&&!this.pending){this.result=result;draw();}}).catch(error=>{if(element.isConnected)status.textContent=error.message;});
        return {element,dispose:()=>this.listeners.delete(draw)};
    }
    dispose() {this.disposed=true;this.listeners.clear();this.banner.remove();}
}
