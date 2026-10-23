// Three-step interface over the existing, validated native Comfy stage graphs.
const editorURL = new URL("./image-editor.js", import.meta.url);
editorURL.search = new URL(import.meta.url).search;
const {openImageEditor} = await import(editorURL);
export function downloadProgress(download) {
    if(download?.status!=="running") return null;
    const size=bytes=>bytes>=1e9?`${(bytes/1e9).toFixed(2)} GB`:`${(bytes/1e6).toFixed(1)} MB`;
    const total=download.total || 0, bytes=Math.min(total,download.bytes || 0);
    const verifying=download.phase==="verifying SHA-256";
    const installing=download.phase==="installing";
    let message=`${verifying?"Verifying downloaded file":installing?"Installing downloaded files":download.phase==="connecting"?"Connecting to download":"Downloading"}: ${download.name || "required models"}`;
    if(total) message+=` · ${size(bytes)} of ${size(total)}${verifying?"":` · ${Math.floor(100*bytes/total)}%`}`;
    const overall=(download.completed_bytes || 0)+bytes;
    if(download.file_count>1) message+=`\nAll required files: ${size(overall)} of ${size(download.batch_total)} · File ${download.file_index} of ${download.file_count}`;
    return {message,progress:verifying||installing?null:{value:download.batch_total?overall:bytes,max:download.batch_total || total}};
}
export function createInterface(Base, { app, api, request, element: el, defaultAsset, PREFIX, TYPE, profileLabels }) {
    const hints = {
        qwen21: "General image creation and editing with reference images. Useful for combining your descriptions and object details.",
        qwen2511: "Edits existing images and follows detailed visual references. Requires at least one image; supports three reference inputs.",
        klein_base: "Full FLUX.2 Klein 9B model. More control over steps and guidance for detailed image creation and editing.",
        klein_distilled: "Faster FLUX.2 Klein 9B generation. Designed for a short sampling run with CFG 1.",
        klein_kv: "FLUX.2 Klein 9B variant optimized for reference-image editing. Keep the same references while trying changes.",
        klein4: "Smaller FLUX.2 Klein model for image creation and reference editing. Uses compressed weights and a smaller encoder, with four steps and CFG 1. An 8 GB hardware pass is still needed.",
        klein4_base: "Full Klein 4B variant. Supports the separate RefControl depth adapter; uses more sampling steps than the distilled four-step model.",
        flux3_base: "Full FLUX 3 Image Klein model for image creation and reference-guided editing. Allows longer sampling runs.",
        flux3_distilled: "Faster FLUX 3 Image Klein variant for image creation and editing, using its distilled sampling settings.",
    };
    const defaults = {qwen21:[25,1], qwen2511:[40,4], klein_base:[20,5], klein_distilled:[4,1],
        klein_kv:[4,1], klein4:[4,1], klein4_base:[20,5], flux3_base:[50,3.5], flux3_distilled:[16,1]};
    const categories={props:"Props",characters:"Characters",creatures:"Creatures",vehicles:"Vehicles",environment:"Environment pieces"};
    const labels = {image:"Creating an image", foreground:"Removing the background", draft:"Building the draft shape", guide:"Rendering camera guides", mesh:"Building the 3D shape and materials",
        master:"Finishing the high-quality asset", game:"Preparing the game version"};
    const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
    const active = () => app.graph._nodes.find(n => n.type === TYPE);
    const operation = () => app.mumbleboxOperation;
    app.mumbleboxSessionId ??= crypto.randomUUID();
    const terminal = new Set(["failed", "cancelled", "interrupted"]);
    const memoryKeys=["extra_vram_headroom_gb","min_ram_free_gb","cache_device","tiled_vae",
        "image_precision","cache_precision","helper_precision","release_between_stages"];
    if (!app.mumbleboxProgressInstalled) {
        api.addEventListener("execution_start", event => {
            const op=operation();
            if(op) {op.executingPromptId=event.detail?.prompt_id;op.executingNode=null;}
        });
        api.addEventListener("executing", event => {
            const op=operation();
            if(!op?.jobId || !op.promptId || op.executingPromptId!==op.promptId ||
                op.executingNode===event.detail) return;
            op.executingNode=event.detail;
            op.progress=null;
            active()?.updateProgress();
        });
        api.addEventListener("progress", event => {
            const op=operation();
            if (!op?.jobId) return;
            const detail=event.detail || {};
            if (op.promptId && detail.prompt_id && op.promptId !== detail.prompt_id) return;
            op.progress={value:detail.value,max:detail.max};
            active()?.updateProgress();
        });
        app.mumbleboxProgressInstalled=true;
    }
    function stylesheet() {
        const id = "mumblebox-creator-style";
        const old = document.getElementById(id);
        const url = new URL("./creator.css", import.meta.url);
        url.search = new URL(import.meta.url).search;
        const href = url.href;
        if (old?.href === href) return;
        old?.remove();
        document.head.append(el("link", {id, rel:"stylesheet", href}));
    }
    function settings(asset) {
        asset.category ??= "props";
        asset.settings ??= {};
        const fallback={...defaultAsset().settings,helper_precision:"q8",include_design:true,
            draft_backend:"pixal_multiview",draft_appearance:"geometry",draft_seed:0};
        asset.settings.memory_overrides ??= asset.id ? memoryKeys.filter(key=>key in asset.settings) : [];
        asset.settings.requested_seed ??= asset.settings.seed_mode==="fixed" ? asset.settings.seed : -1;
        for(const [key,value] of Object.entries(fallback)) if(!(key in asset.settings)) asset.settings[key]=value;
        asset.initial ??= {revisions:[], current:null, approved:null};
        asset.design ??= {revisions:[], current:null, approved:null};
        asset.references ??= [];
        asset.loras ??= [];
        return asset;
    }
    return class Creator extends Base {
        constructor() {
            super();
            this.properties.sessionId=app.mumbleboxSessionId;
            const configure=this.onConfigure;
            this.onConfigure=(...args)=>{
                if(this.properties.asset_workshop_mode==="single_image_agent") {
                    configure?.apply(this,args);
                    return;
                }
                if(this.properties.sessionId!==app.mumbleboxSessionId && !operation()) {
                    this.properties.asset=defaultAsset();
                    this.properties.tab="Design";
                    this.properties.advanced=false;
                    delete this.properties.pendingSettings;
                    this.lastJob=null;
                    this.suggestion=null;
                    this.message="Start a new job below, or use History to reuse saved parameters.";
                    queueMicrotask(()=>this.resetStageGraph().catch(error=>this.status(error.message,true)));
                }
                this.properties.sessionId=app.mumbleboxSessionId;
                configure?.apply(this,args);
            };
            this.size = [1060, 900];
            this.message = "";
            this.render();
            const cleanup = this.onRemoved;
            this.onRemoved = (...args) => {
                this.viewer?.remove();
                this.viewer = null;
                this.viewerResize?.disconnect();
                cleanup?.apply(this,args);
            };
        }
        get asset() { return settings(this.properties.asset); }
        changed() {
            this.editVersion=(this.editVersion || 0)+1;
            super.changed();
        }
        mergeResults(saved) {
            const draft=this.asset;
            if(draft.id!==saved.id) return;
            const designChanged=draft.design.current!==saved.design.current;
            const merged={...saved};
            for(const key of ["name","prompt","profile","category","settings","loras","references"])
                merged[key]=draft[key];
            if(saved.settings.mesh_seed!==undefined) merged.settings.mesh_seed=saved.settings.mesh_seed;
            merged.views=saved.views.map(view=>{
                const local=draft.views.find(v=>v.id===view.id);
                if(!local) return view;
                const result={...view};
                for(const key of ["azimuth","elevation","fov","name"])
                    result[key]=local[key];
                if(!designChanged) result.correction=local.correction;
                if(!designChanged && local.current===view.current) result.enabled=local.enabled;
                return result;
            });
            this.properties.asset=merged;
        }
        status(text, error = false) {
            this.message = text;
            this.messageError = error;
            if (this.notice) {
                this.notice.textContent = text;
                this.notice.classList.toggle("error", error);
            }
        }
        button(label, action, disabled = false, className = "") {
            const button = el("button", {type:"button", disabled, class:className}, label);
            if(disabled) button.title=operation() ? "Wait for the current operation to finish, or use Stop." : "Complete the required input shown in this section first.";
            button.addEventListener("click", async () => {
                if (button.disabled) return;
                button.disabled = true;
                try { await action(); }
                catch (error) { (active() || this).status(error.message, true); }
                finally { if (button.isConnected) button.disabled = disabled; }
            });
            return button;
        }
        unloadButton() {
            return this.button("Unload models",async()=>{
                if(operation() || this.server?.running || this.releasingModels)
                    throw Error("Available when generation finishes.");
                this.releasingModels=true;
                this.updateUnloadButtons();
                try {
                    this.status("Releasing models and temporary execution results. Checking memory…");
                    const result=await request("/release",{});
                    const after=result.resources.after,gb=value=>(value/1073741824).toFixed(1);
                    this.status(`Memory release checked. Comfy process: ${gb(after.process_rss)} GB RAM; GPU memory in use: ${gb(after.vram_used)} GB. Your saved work is unchanged.`);
                    await this.refreshStatus();
                } finally {
                    this.releasingModels=false;
                    this.updateUnloadButtons();
                }
            },false,"unload-models");
        }
        updateUnloadButtons() {
            const busy=!!operation() || this.server?.running || this.server?.description_helper?.running;
            const explanation="Free memory by unloading Comfy's idle models from VRAM and system RAM. Your images, settings and saved work stay intact. Models reload when you generate again.";
            for(const button of this.root.querySelectorAll(".unload-models")) {
                button.disabled=!this.server || busy || !!this.releasingModels;
                button.title=this.releasingModels?"Releasing idle models…":busy?
                    `Available when generation finishes. ${explanation}`:
                    !this.server?"Connecting to Comfy…":explanation;
            }
        }
        updateInputButtons() {
            const a=this.asset,busy=!!operation();
            const hasImage=!!a.initial.current || a.references.some(r=>r.enabled);
            const guards={
                "Generate image and go to Step 2":busy || (!a.prompt.trim() && !hasImage) || (a.profile==="qwen2511" && !hasImage),
                "Enhance description":busy || !a.prompt.trim(),
                "Auto Describe my image":busy || !a.initial.current,
            };
            for (const b of this.root.querySelectorAll("button")) {
                if (Object.hasOwn(guards,b.textContent)) {
                    b.disabled=guards[b.textContent];
                    b.title=busy?"Wait for the current operation, or use Stop.":!b.disabled?"":
                        b.textContent==="Auto Describe my image"?"Upload an initial image first.":
                        b.textContent==="Enhance description"?"Enter a description first.":
                        a.profile==="qwen2511"?"Qwen Edit needs an initial or reference image.":"Enter a description or add an image.";
                }
            }
            const explanation=this.root.querySelector("[data-description-prerequisites]");
            if(explanation) explanation.textContent=[
                !a.initial.current?"Auto Describe my image needs an uploaded initial image.":"",
                !a.prompt.trim()?"Enhance description needs some text in the description box.":"",
                a.profile==="qwen2511" && !hasImage?"Qwen Edit needs an initial or reference image before it can generate.":"",
            ].filter(Boolean).join(" ");
            for(const b of this.root.querySelectorAll("[data-correct-view]")) {
                const view=a.views.find(v=>v.id===b.dataset.correctView);
                const locked=view?.id!=="view_05" && !this.pairReady();
                b.disabled=busy || locked || !view?.current || !view.correction.trim();
                b.title=busy?"Wait for the current operation, or use Stop.":locked?"Approve the front and back first.":!view?.current?"Generate or upload this angle first.":
                    !view.correction.trim()?"Describe a change in the box above.":"";
            }
            this.updateMeshButtons();
        }
        primary(label, action, disabled = false) { return this.button(label,action,disabled,"primary"); }
        help(text, title="Help") {
            return el("details", {class:"help"}, el("summary", {"aria-label":title, title}, "?"), el("p",{},text));
        }
        section(title, description, ...children) {
            return el("section", {class:"section"}, title ? el("h3",{},title) : null,
                description ? el("p",{class:"hint"},description) : null, children);
        }
        field(label, object, key, type="text", extra={}) {
            const input = el("input", {type, ...extra, "aria-label":label,
                ...(type === "checkbox" ? {checked:!!object[key]} : {value:object[key] ?? ""}),
                oninput: e => {
                    object[key] = type === "checkbox" ? e.target.checked :
                        type === "number" ? (e.target.value === "" ? null : Number(e.target.value)) : e.target.value;
                    this.changed();
                    if (key === "enabled" || key === "include_design") this.updateMeshButtons();
                    if(key==="enabled" && this.asset.id && this.asset.views.includes(object))
                        this.persistSelection(object).catch(error=>this.status(`Could not save this image selection: ${error.message}`,true));
                }});
            return el("label",{class:type === "checkbox" ? "check" : ""},type === "checkbox" ? [input,label] : [label,input]);
        }
        select(values,current,change,label) {
            return el("select",{"aria-label":label || "Choose an option", onchange:e=>{
                change(e.target.value); this.changed();
            }}, Object.entries(values).map(([value,name])=>el("option",{value,selected:value===String(current)},name)));
        }
        fileURL(file,assetId=this.asset.id) { return `${PREFIX}/file/${assetId}?path=${encodeURIComponent(file)}`; }
        downloadImage(file,label="Image",assetId=this.asset.id) {
            const extension=file.split(".").at(-1);
            return el("a",{class:"download",href:this.fileURL(file,assetId),
                download:`${label.replace(/[<>:"/\\|?*]/g,"-")}.${extension}`,
                "aria-label":`Download image: ${label}`},"Download image");
        }
        revision(slot) { return slot?.revisions?.find(r=>r.id===slot.current); }
        preview(slot) {
            const revision = this.revision(slot);
            const slotId=slot.id || (slot===this.asset.initial?"initial":slot===this.asset.design?"design":null);
            return revision ? el("figure",{class:"image-preview"},
                el("img",{src:this.fileURL(revision.file),alt:slot.name || "Asset image"}),
                el("figcaption",{},this.downloadImage(revision.file,slot.name || this.asset.name),
                    slotId ? this.button("Edit image",()=>this.editImage(slotId),!!operation()) : null,
                    slotId ? this.button("Background removal",()=>this.editForeground(slotId),!!operation()) : null,
                    revision.foreground ? this.downloadImage(revision.foreground.cutout_file,"Transparent cutout") : null,
                    revision.recipe?.seed!=null ? el("span",{class:"hint"},`Seed used: ${revision.recipe.seed}`) : null)) :
                el("div",{class:"empty"}, "Your image will appear here.");
        }
        saveImage(slot) {
            const revision = this.revision(slot);
            return revision ? this.downloadImage(revision.file,`${this.asset.name}-${slot.name || "design"}`) :
                this.button("Download image",()=>{},true);
        }
        async persistSelection(view) {
            const assetId=this.asset.id,viewId=view.id,enabled=!!view.enabled;
            const save=async()=>{
                // Save only the selection; a completed generation may have
                // installed a newer image since this checkbox was clicked.
                const saved=await request(`/assets/${assetId}`,{view_selection:{[viewId]:enabled}},"PATCH");
                if(this.asset.id===assetId) {
                    for(const key of ["masters","exports","selected_master","selected_export"])
                        this.asset[key]=saved[key];
                    if(this.properties.tab==="Result") this.render();
                }
                this.historyLoaded=false;
            };
            this.saveChain=(this.saveChain || Promise.resolve()).catch(()=>{}).then(save);
            return this.saveChain;
        }
        async persist() {
            const save=async()=>{
                if(!this.asset.id) {
                    const created=await request("/assets",{name:this.asset.name});
                    this.properties.asset={...created,...this.asset,id:created.id};
                }
                const version=this.editVersion;
                const saved=await request(`/assets/${this.asset.id}`,JSON.parse(JSON.stringify(this.asset)),"PATCH");
                if(version===this.editVersion) this.properties.asset=saved;
                else this.mergeResults(saved);
                this.historyLoaded=false;
                if(this.graph) {
                    app.graph.extra.ds={scale:app.canvas.ds.scale,offset:[...app.canvas.ds.offset]};
                    await api.storeUserData("workflows/Mumblebox Creator.json",app.graph.serialize());
                }
                this.render();
                return this.asset;
            };
            this.saveChain=(this.saveChain || Promise.resolve()).catch(()=>{}).then(save);
            return this.saveChain;
        }
        setTab(tab) {
            this.properties.tab = tab;
            this.render(); this.root.scrollTop = 0; this.changed();
            this.root.querySelector(`#mumblebox-tab-${tab}`)?.focus({preventScroll:true});
        }
        async resetStageGraph() {
            if(!this.graph?.extra?.asset_workshop || operation()) return;
            const graph=this.graph, nodes=[...graph._nodes].filter(node=>node!==this);
            for(const node of nodes)
                for(let index=(node.inputs?.length || 0)-1;index>=0;index--)
                    if(node.inputs[index].link!=null) node.disconnectInput(index);
            // Comfy's dynamic-input handlers run on the next animation frame.
            await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
            if(this.graph!==graph) return;
            for(const node of nodes) if(node.graph===graph) graph.remove(node);
            delete graph.extra.asset_workshop;
            graph.setDirtyCanvas(true,true);
        }
        async refreshStatus() {
            if (!this.graph || document.hidden || this.refreshing) return;
            this.refreshing = true;
            try {
                const data = await request("/status");
                this.server = data;
                const gb = value => (value/1073741824).toFixed(1);
                const cleaning=data.resource_cleanup?.status==="releasing" || data.resource_cleanup?.pending_jobs>0;
                if (this.stats) this.stats.textContent = `CPU ${data.cpu_percent.toFixed(0)}%    ·    RAM ${gb(data.ram_used)} / ${gb(data.ram_total)} GB    ·    VRAM ${gb(data.vram_used)} / ${gb(data.vram_total)} GB    ·    ${data.running ? "Comfy is working" : cleaning ? "Releasing memory…" : data.resource_cleanup?.status==="failed" ? "Memory release needs attention" : "Ready"}`;
                this.updateProgress();
                if (!operation() && this.lastJob && this.asset.id && !data.running) {
                    const asset = await request(`/assets/${this.asset.id}`);
                    const job = asset.jobs.find(j=>j.id===this.lastJob);
                    if (job?.status === "complete" || terminal.has(job?.status)) {
                        this.mergeResults(asset); this.lastJob = null;
                        // A completed individual stage must not erase a later
                        // batch/persistence error that requires attention.
                        if(job.status!=="complete" || !this.messageError)
                            this.status(job.status==="complete" ? "Finished. Your result has been saved." : job.error || job.status, job.status!=="complete");
                        this.render();
                    }
                }
            } catch (error) {
                if (this.stats) this.stats.textContent = "Connection to Comfy is unavailable. Saved work is retained.";
            } finally { this.refreshing = false; }
        }
        updateProgress() {
            this.updateUnloadButtons();
            const op = operation(), download = this.server?.download;
            const transfer=downloadProgress(download);
            if (this.progressLabel) this.progressLabel.textContent = op?.message ||
                (this.lastJob ? "Comfy is processing your asset…" : "Ready to create your asset.");
            if(this.progressLabel && this.server?.description_helper?.running && !op?.reconnecting && !op?.stopRequested)
                this.progressLabel.textContent=this.server.description_helper.phase;
            if (this.progressBar) {
                if (transfer) {
                    if(transfer.progress?.max) {
                        this.progressBar.value=transfer.progress.value;
                        this.progressBar.max=transfer.progress.max;
                    } else this.progressBar.removeAttribute("value");
                    if(this.progressLabel) this.progressLabel.textContent=transfer.message;
                } else if (op?.progress?.max) {
                    this.progressBar.max=op.progress.max; this.progressBar.value=op.progress.value;
                } else this.progressBar.removeAttribute("value");
            }
        }
        async runOperation(kind, task) {
            if (operation()) throw Error("An operation is already running. Wait for it or use Stop.");
            this.server=await request("/status");
            if(operation()) throw Error("Another operation just started. Wait for it or use Stop.");
            if ((this.server?.interface_version || 0) < 10) throw Error("The surface-detail controls need a Comfy backend restart before generation. Your inputs are retained.");
            if (this.server?.running) throw Error("Comfy is already working. Wait for that job to finish.");
            const op = {kind, assetId:this.asset.id, cancelled:false, message:"Getting ready…", progress:null};
            app.mumbleboxOperation=op;
            try {
                this.render();
                await task(op);
            }
            catch (error) {
                (active() || this).status(op.cancelled
                    ? "Stop requested. Waiting for the current Comfy step to finish stopping."
                    : error.message, !op.cancelled);
            }
            finally {
                let recoveryError=null;
                try { if(op.cancelled) await (active() || this).waitForCancellation(op); }
                catch(error) {recoveryError=error;}
                if (app.mumbleboxOperation===op) app.mumbleboxOperation=null;
                const controller=active() || this;
                if(op.cancelled) {
                    controller.lastJob=null;
                    controller.status(recoveryError ? recoveryError.message : "Stopped. Completed work is saved and memory release has been checked.",!!recoveryError);
                }
                if(op.settingsDraft && controller.asset.id===op.assetId) {
                    // Apply only edits, retaining seeds and other values produced by this run.
                    for(const [key,value] of Object.entries(op.settingsDraft))
                        if(JSON.stringify(value)!==JSON.stringify(op.settingsOriginal[key]))
                            controller.asset.settings[key]=value;
                }
                delete controller.properties.pendingSettings;
                try { if(controller.asset.id) await controller.persist(); }
                catch(error) {controller.status(`Could not save the latest settings: ${error.message}`,true);}
                controller.render();
            }
        }
        async waitForCancellation(op) {
            if(!op.promptId) return;
            op.progress=null;
            for (;;) {
                op.message="Stopping… Waiting for the current Comfy step to release.";
                try {
                    const queue=await api.getQueue({throwOnError:true});
                    if(![...queue.Running,...queue.Pending].some(job=>job.id===op.promptId)) break;
                } catch {
                    op.message="Stop requested. Reconnecting to confirm that Comfy has stopped.";
                }
                this.updateProgress();
                await sleep(1000);
            }
            for (;;) {
                op.message="Stopped generation. Releasing models and checking memory…";
                this.updateProgress();
                let state;
                try { state=await request("/status"); }
                catch(error) {
                    if(!error.connectionError) throw error;
                    await sleep(1000);continue;
                }
                this.server=state;
                if(state.resource_cleanup?.status==="failed") throw Error(state.resource_cleanup.error);
                if(!state.resource_cleanup?.pending_jobs && state.resource_cleanup?.status!=="releasing") return;
                await sleep(1000);
            }
        }
        async stop() {
            const op=operation();
            if(op?.stopRequested) return;
            if(op) op.stopRequested=true;
            for (;;) {
                try {
                    if (this.server?.download?.status==="running") await request("/download/pause",{});
                    if (this.asset.id) await request(`/assets/${this.asset.id}/cancel`,{});
                    if(op) op.cancelled=true;
                    this.status("Stopping this asset’s operation. Completed images and files are saved.");
                    return;
                } catch(error) {
                    if(!error.connectionError) {
                        if(op) op.stopRequested=false;
                        throw error;
                    }
                    if(op) op.message="Stop requested. Reconnecting to Comfy to confirm it…";
                    this.status("Stop requested. Waiting for Comfy to reconnect; the job may still be running.");
                    this.updateProgress();
                    await sleep(3000);
                }
            }
        }
        async readWhileWorking(path, op) {
            // A lost reply does not mean the running job stopped. Retry reads only;
            // never submit another generation to recover an uncertain connection.
            for (;;) {
                if(op?.cancelled) throw Error("Stopped. Completed work is saved.");
                try {
                    const result=await request(path);
                    if(op?.reconnecting) {
                        op.reconnecting=false;
                        if(!op.stopRequested) op.message=op.connectedMessage;
                        this.updateProgress();
                    }
                    return result;
                } catch(error) {
                    if(!error.connectionError) throw error;
                    if(op && !op.reconnecting) op.connectedMessage=op.message;
                    if(op) {
                        op.reconnecting=true;
                        if(!op.stopRequested) op.message="Reconnecting to Comfy… Your existing job may still be running.";
                    }
                    this.updateProgress();
                    await sleep(3000);
                }
            }
        }
        nextSeed(force=false, slot=null) {
            const s=this.asset.settings;
            const requested=Number(s.requested_seed);
            if(!Number.isSafeInteger(requested) || requested < -1)
                throw Error("Seed must be -1 for random, or a whole number of zero or greater.");
            s.seed=force || requested===-1 ? crypto.getRandomValues(new Uint32Array(1))[0] : requested;
            if (slot && slot!=="design") this.asset.views.find(v=>v.id===slot).seed=s.seed;
            this.changed();
        }
        async ensureModels(stage, op=operation(), slot="design", action="generate") {
            await this.persist();
            if(op) op.assetId=this.asset.id;
            const needed=await request(`/assets/${this.asset.id}/models?stage=${stage}&camera=0&slot=${encodeURIComponent(slot)}&action=${action}`);
            if (!needed.missing.length) return;
            const stageMessage=op?.message;
            if (op) op.message="Downloading the models needed for this step…";
            this.status("Downloading required models for first use. Existing files will be reused.");
            await request(`/assets/${this.asset.id}/download`,{stage,slot,action,camera:false,accept_licenses:true});
            for (;;) {
                if (op?.cancelled) throw Error("Stopped. Downloaded files are kept for the next attempt.");
                await sleep(1200);
                const state=await this.readWhileWorking("/status",op); this.server=state; this.updateProgress();
                if (["failed","paused"].includes(state.download.status)) throw Error(state.download.error || "Download paused.");
                if (state.download.status==="complete") break;
            }
            if(op) op.message=stageMessage;
            this.updateProgress();
        }
        async stage(stage,slot="design",action="generate",run=true,edit=null) {
            const pending=operation();
            if(pending) {pending.progress=null;this.updateProgress();}
            const route=this.asset.settings.angle_route || "references";
            if(stage==="image" && action==="generate" && !["design","initial","view_01","view_05"].includes(slot) && route!=="references") {
                const kind=route==="qwen_anyangle"?"color":"depth";
                if(!this.guideFor(slot)?.files?.[kind]) throw Error(`Render this angle’s ${kind} camera guide first. AnyAngle requires a draft with color.`);
            }
            await this.ensureModels(stage,operation(),slot,action);
            if (operation()?.cancelled) throw Error("Stopped before starting the next stage.");
            const controller=await super.stage(stage,slot,action,run,edit);
            controller.message="";
            controller.server=this.server;
            controller.size=[1060,900];
            controller.pos=[110,110];
            app.canvas.ds.scale=.82; app.canvas.ds.offset=[0,30];
            app.graph.extra.ds={scale:.82,offset:[0,30]};
            const op=operation();
            if (op) {
                op.jobId=controller.lastJob; op.assetId=controller.asset.id; op.stage=stage; op.progress=null;
                const saved=await controller.readWhileWorking(`/assets/${controller.asset.id}`,op);
                op.promptId=saved.jobs.find(j=>j.id===op.jobId)?.prompt_id;
            }
            controller.render();
            await api.storeUserData("workflows/Mumblebox Creator.json",app.graph.serialize());
            return controller;
        }
        async waitForJob(op) {
            for (;;) {
                if (op.cancelled) throw Error("Stopped. Completed work is saved.");
                await sleep(1500);
                const asset=await this.readWhileWorking(`/assets/${this.asset.id}`,op);
                const job=asset.jobs.find(j=>j.id===this.lastJob);
                if (terminal.has(job?.status) || job?.status==="complete") {
                    const state=await this.readWhileWorking("/status",op);
                    this.server=state;
                    if (state.running) continue;
                    if(state.resource_cleanup?.pending_jobs || state.resource_cleanup?.status==="releasing") {
                        op.message="Saved this stage. Releasing models and checking memory before continuing…";
                        op.progress=null;this.updateProgress();continue;
                    }
                    // Retain completed output even if its later memory release failed.
                    this.mergeResults(asset); this.lastJob=null; this.changed(); this.render();
                    if(state.resource_cleanup?.status==="failed") throw Error(state.resource_cleanup.error);
                    if (terminal.has(job?.status)) throw Error(job.error || `The operation was ${job.status}. Your earlier results are saved.`);
                    return job;
                }
            }
        }
        async generateImage(slot="design",action="generate",force=false) {
            return this.runOperation("image",async op=>{
                this.nextSeed(force,slot);
                const name=slot==="design" ? "your image" : this.asset.views.find(v=>v.id===slot).name;
                op.message=`Creating ${name}…`;
                let controller=await this.stage("image",slot,action);
                await controller.waitForJob(op);
                if(slot==="design") {
                    controller.setTab("Views");
                    controller.status("The front is ready. Creating the back from this front and your description…");
                    controller=await controller.generateBack(op);
                    controller.status("Front and back are ready. Check both images, correct anything needed, then approve the pair.");
                } else controller.status(`${name} is ready. Review it below.`);
            });
        }
        async generateBack(op) {
            if(!this.asset.design.current) throw Error("Create or upload the front first.");
            if(op.cancelled) throw Error("Stopped. Your completed front is saved.");
            const back=this.asset.views.find(v=>v.id==="view_05");
            back.azimuth=180;back.elevation=0;
            this.nextSeed(false,"view_05");
            op.message="Creating the back using your front image and description…";
            const controller=await this.stage("image","view_05");
            await controller.waitForJob(op);
            return controller;
        }
        pairReady() {
            const a=this.asset,back=a.views.find(v=>v.id==="view_05"),pair=a.pair_approval;
            return !!(pair?.front && pair?.back && pair.front===a.design.current && pair.back===back?.current
                && a.design.approved===pair.front && back.approved===pair.back && !a.design.stale && !back.stale);
        }
        async approvePair() {
            await this.persist();
            const saved=await request(`/assets/${this.asset.id}/approve-pair`,{});
            this.mergeResults(saved);this.changed();this.render();
            this.status("Front and back approved. Generate the remaining eight angles using both images.");
        }
        async editForeground(slotId) {
            if(operation()) throw Error("Wait for this operation or use Stop before editing the background.");
            await this.persist();
            const assetId=this.asset.id;
            const getSlot=controller=>slotId==="initial"?controller.asset.initial:slotId==="design"?controller.asset.design:controller.asset.views.find(v=>v.id===slotId);
            let controller=this, revision=controller.revision(getSlot(controller));
            if(!revision) throw Error("Choose an image before removing its background.");
            if(!revision.foreground) {
                await controller.runOperation("foreground",async op=>{
                    op.message="Finding the object and saving its editable cutout…";
                    controller=await controller.stage("foreground",slotId);
                    await controller.waitForJob(op);
                });
                controller=active();revision=controller.revision(getSlot(controller));
                if(!revision?.foreground) throw Error(controller.message || "Background removal stopped. Your original is unchanged.");
            }
            await openImageEditor({
                element:el,mode:"foreground",sourceURL:controller.fileURL(revision.file),
                initialMaskURL:controller.fileURL(revision.foreground.mask_file),
                title:getSlot(controller).name || (slotId==="initial"?"Initial image":"Starting image"),
                download:()=>{const link=controller.downloadImage(revision.file,"Original image",assetId);link.textContent="Download original";return link;},
                stop:()=>active().stop(),progress:()=>null,
                generate:async input=>{
                    const current=active();
                    if(current.asset.id!==assetId) throw Error("The active asset changed. Open background removal again.");
                    const data=new FormData();data.append("slot",slotId);data.append("revision",revision.id);
                    data.append("feather",String(input.feather));data.append("mask",input.mask,"foreground.png");
                    const response=await api.fetchApi(`${PREFIX}/assets/${assetId}/foreground`,{method:"POST",body:data});
                    const result=await response.json();
                    if(!response.ok) throw Error(result.error || "Could not save the cutout preview.");
                    const link=current.downloadImage(result.cutout_file,"Transparent cutout",assetId);link.textContent="Download cutout";
                    return {...result,url:current.fileURL(result.cutout_file),download:link};
                },
                accept:async candidate=>{
                    const current=active();
                    if(current.asset.id!==assetId) throw Error("The active asset changed. Open background removal again.");
                    const saved=await request(`/assets/${assetId}/foreground/accept`,{slot:slotId,candidate:candidate.id});
                    current.mergeResults(saved);current.changed();current.render();
                    current.status("Cutout saved for mesh preparation. The original image is unchanged. Existing meshes are marked for rebuilding.");
                },
            });
        }
        async editImage(slotId) {
            if(operation()) throw Error("Wait for this operation or use Stop before editing.");
            await this.persist();
            const slot=slotId==="initial"?this.asset.initial:slotId==="design"?this.asset.design:this.asset.views.find(v=>v.id===slotId);
            const revision=this.revision(slot), assetId=this.asset.id;
            if(!revision) throw Error("Choose an image before opening the editor.");
            await openImageEditor({
                element:el,sourceURL:this.fileURL(revision.file),title:slot.name || (slotId==="initial"?"Initial image":"Starting image"),
                model:profileLabels[this.asset.profile],
                download:()=>{const link=this.downloadImage(revision.file,"Original image",assetId);link.textContent="Download original";return link;},
                stop:()=>active().stop(),
                progress:()=>downloadProgress(active()?.server?.download) || operation(),
                generate:async input=>{
                    let preview;
                    const controller=active();
                    if(controller.asset.id!==assetId) throw Error("The active asset changed. Open its editor again.");
                    await controller.runOperation("image",async op=>{
                        controller.nextSeed(input.random);
                        if(slotId.startsWith("view_")) controller.asset.views.find(v=>v.id===slotId).seed=controller.asset.settings.seed;
                        await controller.persist();
                        const data=new FormData();
                        data.append("slot",slotId);data.append("revision",revision.id);
                        data.append("prompt",input.prompt);data.append("feather",String(input.feather));
                        data.append("replace_detail",String(input.replaceDetail));
                        data.append("mask",input.mask,"selection.png");
                        const response=await api.fetchApi(`${PREFIX}/assets/${assetId}/edits`,{method:"POST",body:data});
                        const edit=await response.json();
                        if(!response.ok) throw Error(edit.error || "Could not save the selection.");
                        op.message="Creating your selected-area edit preview…";
                        const current=await controller.stage("image",slotId,"edit",true,edit.id);
                        const job=await current.waitForJob(op);
                        const target=slotId==="initial"?current.asset.initial:slotId==="design"?current.asset.design:current.asset.views.find(v=>v.id===slotId);
                        const result=target.revisions.find(r=>r.id===job.result.revision);
                        const link=current.downloadImage(result.file,"Edit preview");link.textContent="Download preview";
                        preview={...result,url:current.fileURL(result.file),download:link};
                        current.status("Edit preview ready. The original remains in use until you keep the edit.");
                    });
                    if(!preview) throw Error(active()?.message || "The edit stopped. Your original and selection are retained.");
                    return preview;
                },
                accept:async candidate=>{
                    const current=active();
                    if(current.asset.id!==assetId) throw Error("The active asset changed. Open its editor again.");
                    const saved=await request(`/assets/${assetId}/edits/accept`,{slot:slotId,revision:candidate.id});
                    current.mergeResults(saved);current.changed();await current.persist();current.render();
                    current.status(slotId==="initial"
                        ? "Initial image updated. Use this image or generate a new design to continue. Earlier results remain in History."
                        : "Edit kept. This image will be used next; earlier files remain in History.");
                },
            });
        }
        async generateViews() {
            return this.runOperation("angles",async op=>{
                if(!this.pairReady()) throw Error("Review and approve the front and back first.");
                let controller=this;
                const pending=this.asset.views.filter(v=>!["view_01","view_05"].includes(v.id) && (!v.current || v.stale)).map(v=>v.id);
                if (!pending.length) {this.status("All included angles already have images. Regenerate an individual angle to change it."); return;}
                for (let i=0;i<pending.length;i++) {
                    if(op.cancelled) break;
                    const view=controller.asset.views.find(v=>v.id===pending[i]);
                    op.message=`Creating angle ${i+1} of ${pending.length}: ${view.name}`;
                    controller.nextSeed(false,view.id);
                    controller=await controller.stage("image",view.id);
                    await controller.waitForJob(op);
                }
                controller.status("Angles are ready. Review each image and uncheck any you do not want used in the mesh.");
            });
        }
        async generateDraft() {
            return this.runOperation("draft",async op=>{
                op.message="Building a rough shape from the front and back. Final mesh detail settings stay unchanged…";
                const controller=await this.stage("draft");
                await controller.waitForJob(op);
                controller.setTab("Views");
                controller.status("Draft saved. Rotate it and check its overall shape before approving it for camera guides.");
            });
        }
        async approveDraft(id) {
            await this.persist();
            const saved=await request(`/assets/${this.asset.id}/approve-draft`,{draft:id});
            this.mergeResults(saved);this.changed();this.render();
            this.status("Draft approved for camera guides. Its source images, masks and generation settings are saved with it.");
        }
        guideFor(slot) {
            const view=this.asset.views.find(v=>v.id===slot);
            return this.asset.guides?.filter(g=>g.slot===slot && g.draft===this.asset.selected_draft && !g.stale &&
                ["azimuth","elevation","fov"].every(key=>g.pose[key]===view[key])).at(-1);
        }
        async generateGuides(slot=null) {
            return this.runOperation("guides",async op=>{
                const pending=slot?[slot]:this.asset.views.filter(v=>!this.guideFor(v.id)).map(v=>v.id);
                let controller=this;
                for(let i=0;i<pending.length;i++) {
                    if(op.cancelled) break;
                    const view=controller.asset.views.find(v=>v.id===pending[i]);
                    op.message=`Rendering camera guides ${i+1} of ${pending.length}: ${view.name}`;
                    controller=await controller.stage("guide",view.id);
                    await controller.waitForJob(op);
                }
                controller.setTab("Views");
                controller.status("Camera guides saved. Expand Camera guide images to inspect the shape, depth and silhouette at each angle.");
            });
        }
        guidePreview(view,busy) {
            const guide=this.guideFor(view.id);
            const draft=this.asset.drafts?.find(d=>d.id===this.asset.selected_draft && d.approved && !d.stale);
            if(!draft) return null;
            const panel=el("details",{class:"advanced"},el("summary",{},`Camera guide images${guide?" — ready":""}`),
                el("p",{class:"hint"},"Rendered from your approved draft at this angle. These are shape guides, not newly generated pictures. Depth is brighter nearer the camera; white in the silhouette is the object."),
                this.button(guide?"Refresh guides for this angle":"Render guides for this angle",()=>this.generateGuides(view.id),busy,"quiet"));
            if(guide) {
                const maps=el("div",{class:"guide-maps"});
                for(const [kind,file] of Object.entries(guide.files)) {
                    const name={depth:"Depth",normal:"Surface normals",silhouette:"Silhouette",color:"Draft color"}[kind];
                    maps.append(el("figure",{},el("figcaption",{},name),
                        el("img",{src:this.fileURL(file.file),alt:`${view.name} ${name.toLowerCase()} guide`,loading:"lazy"}),
                        this.downloadImage(file.file,`${view.name} ${name}`)));
                }
                panel.append(maps,el("p",{class:"hint"},`${guide.pose.azimuth}° around · ${guide.pose.elevation}° elevation · ${guide.pose.fov}° field of view. The guide camera is known; an AI-generated result may still depart from it.`));
            }
            return panel;
        }
        meshReady() {
            const a=this.asset;
            if(a.settings.mesh_backend==="pixal_multiview" && !this.pairReady()) return false;
            return a.views.some(v=>v.enabled && v.current && !v.stale) || (!!a.design.current && a.settings.include_design);
        }
        updateMeshButtons() {
            for (const b of this.root.querySelectorAll("[data-mesh]")) b.disabled=!this.meshReady() || !!operation();
            for (const summary of this.root.querySelectorAll("[data-mesh-selection]")) summary.textContent=this.meshSelectionSummary();
        }
        meshSelectionSummary() {
            const count=this.asset.views.filter(v=>v.enabled && v.current && !v.stale).length;
            return `${count} angle ${count===1?"image is":"images are"} selected. Empty angles are skipped. With no angle images, the starting image can be used on its own.`;
        }
        meshButton() {
            const button=this.primary("Generate mesh",()=>this.generateMesh(),!this.meshReady() || !!operation());
            button.dataset.mesh="true";
            return button;
        }
        async generateMesh() {
            if(!this.meshReady()) throw Error("Choose at least one image to use in the mesh.");
            this.setTab("Result");
            return this.runOperation("mesh",async op=>{
                op.message=labels.mesh;
                let controller=await this.stage("mesh");
                const built=await controller.waitForJob(op);
                const master=built.result?.master || controller.asset.masters.at(-1)?.id;
                if(!master) throw Error("The mesh did not produce a saved master.");
                op.message=labels.master; op.progress=null;
                controller=await controller.stage("master",master);
                await controller.waitForJob(op);
                controller.properties.asset=await request(`/assets/${controller.asset.id}/approve-master`,{master});
                op.message=labels.game; op.progress=null;
                controller=await controller.stage("game");
                await controller.waitForJob(op);
                controller.status("Your 3D asset is ready. The high-quality master and game version are saved separately.");
            });
        }
        async finishMaster(master) {
            this.setTab("Result");
            return this.runOperation("mesh",async op=>{
                let controller=this;
                if(!controller.asset.exports.some(e=>e.kind==="master" && e.master===master && !e.stale)) {
                    op.message=labels.master;
                    controller=await controller.stage("master",master);
                    await controller.waitForJob(op);
                }
                controller.properties.asset=await request(`/assets/${controller.asset.id}/approve-master`,{master});
                op.message=labels.game; op.progress=null;
                controller=await controller.stage("game");
                await controller.waitForJob(op);
                controller.status("Finishing complete. Your master and game version are saved.");
            });
        }
        async uploadFiles(slot,files) {
            if (operation()) throw Error("Wait for the current operation before changing images.");
            if ((this.server?.interface_version || 0) < 2) throw Error("The Comfy backend needs to load the update before images can be added here.");
            await this.persist();
            for (const file of files) {
                const data=new FormData(); data.append("image",file); data.append("slot",slot);
                const response=await api.fetchApi(`${PREFIX}/assets/${this.asset.id}/upload`,{method:"POST",body:data});
                const result=await response.json(); if(!response.ok) throw Error(result.error);
            }
            await this.reload();
            this.status(slot==="references" ? "References added. Explain what you want from each image." : "Image loaded.");
        }
        upload(slot) {
            const picker=el("input",{type:"file",accept:"image/png,image/jpeg,image/webp",multiple:slot==="references"});
            picker.onchange=()=>this.uploadFiles(slot,picker.files).catch(e=>this.status(e.message,true));
            picker.click();
        }
        uploadArea() {
            const a=this.asset;
            const area=el("div",{class:"upload-area"},
                this.preview(a.initial),
                el("div",{},this.button("Upload initial image",()=>this.upload("initial"),!!operation()),
                    el("p",{class:"hint"},"Optional. Drop an image here, choose a file, or simply enter a description below."),
                    a.initial.current ? this.button("Remove initial image",async()=>{
                        a.initial.current=null; await this.persist(); this.render();
                    },!!operation(),"quiet") : null));
            area.addEventListener("dragover",e=>{e.preventDefault(); area.classList.add("drag");});
            area.addEventListener("dragleave",()=>area.classList.remove("drag"));
            area.addEventListener("drop",e=>{
                e.preventDefault(); area.classList.remove("drag");
                if(e.dataTransfer.files.length) this.uploadFiles("initial",[e.dataTransfer.files[0]]).catch(e=>this.status(e.message,true));
            });
            return area;
        }
        async useInitial() {
            const revision=this.revision(this.asset.initial);
            const response=await api.fetchApi(this.fileURL(revision.file));
            await this.uploadFiles("design",[new File([await response.blob()],"design.png",{type:"image/png"})]);
            await this.useDesign();
        }
        async useDesign() {
            return this.runOperation("image",async op=>{
                this.setTab("Views");
                const controller=await this.generateBack(op);
                controller.status("Front and back are ready. Review and approve the pair before generating the remaining angles.");
            });
        }
        async clearAngles(view=null) {
            for(const target of view?[view]:this.asset.views) {
                target.current=null;target.approved=null;target.enabled=false;target.stale=false;
            }
            await this.persist();
            this.render();
            this.status(view?`${view.name} cleared. Its saved revisions remain in History.`:
                "All angle images cleared. Your starting image and History are kept.");
        }
        confirmClearAngles() {
            const dialog=el("dialog",{},el("h3",{},"Clear all images?"),
                el("p",{},"Are you sure you want to clear all angle images? Your starting image and saved History will be kept."),
                el("div",{class:"row"},this.button("Cancel",()=>dialog.close()),
                    this.button("Clear all images",async()=>{await this.clearAngles();dialog.close();},!!operation(),"danger")));
            this.root.append(dialog);dialog.addEventListener("close",()=>dialog.remove());dialog.showModal();
        }
        async helper(action) {
            await this.runOperation("description",async op=>{
                await this.persist();
                op.assetId=this.asset.id;
                op.message=action==="describe" ? "Looking at your initial image…" : "Improving your object description…";
                this.render();
                const result=await request(`/assets/${this.asset.id}/describe`,{action});
                if(op.cancelled) return;
                this.suggestion=result.text;
                this.suggestionId=result.suggestion_id;
                this.suggestionContract=result.contract;
                this.status(action==="enhance" ?
                    "Review the suggested design, including any proposed back, side, top or underside details. It only replaces your text when you choose Use this description." :
                    "Review the description of the visible image. It only replaces your text when you choose Use this description.");
            });
        }
        async loadLoras() {
            this.loraCatalog=await request("/loras");
            this.render();
        }
        renderDesign(content) {
            const a=this.asset,s=a.settings,busy=!!operation();
            content.append(el("div",{class:"step-heading"},
                el("div",{},el("h3",{},"Step 1 — Design your asset"),
                    el("p",{class:"hint"},"Start with a description, an image, or both. Create an image you like, then continue to the next step.")),
                this.button("Start over",async()=>{
                    if(this.asset.id) await this.persist();
                    this.properties.asset=defaultAsset(); this.lastJob=null; this.suggestion=null;
                    await this.resetStageGraph();
                    this.status(""); this.setTab("Design");
                    await api.storeUserData("workflows/Mumblebox Creator.json",app.graph.serialize());
                },busy,"quiet")));
            content.append(this.section(null,null,this.field("Asset name",a,"name"),
                el("label",{},"Asset type",this.select(categories,a.category,value=>{
                    a.category=value;this.suggestion=null;this.render();this.changed();
                },"Asset type")),
                this.help("Props are individual objects such as tools or furniture. Characters are people and humanoid robots. Creatures are animals and non-humanoid beings. Vehicles include ships and major vehicle assemblies. Environment pieces are buildings, structural modules, trees or rocks. This choice helps preserve relevant details; it does not secretly change quality or sampling settings.","Which asset type should I choose?")));
            content.append(this.section("Upload initial image (optional)",
                "Upload a front image if you have one. Otherwise, describe the object below. We create the front first, then use it to create the back for your review. You do not need an image to begin.",
                this.uploadArea(),
                a.initial.current ? el("div",{class:"row"},this.button("Use this image → Next step",()=>this.useInitial(),busy),
                    el("span",{class:"hint"},"Already happy with this front? Use it unchanged and generate its back.")) : null));
            const description=el("textarea",{value:a.prompt,"aria-label":"Describe your asset",
                placeholder:"For example: A sci-fi cargo crate with a folding handle, recessed panels, worn turquoise paint and silver metal edges.",
                oninput:e=>{a.prompt=e.target.value; this.changed();}});
            const descriptionSection=this.section(null,null,
                el("h3",{},"Describe your asset",this.help("Describe the object, its shape, materials, colors and style. Mention details that should appear on the back or sides. If you uploaded an initial image, explain what to keep or change.","Description help")),
                el("p",{class:"hint"},"Describe what the image should look like, or describe the changes you want to make here."),
                description,
                el("div",{class:"row description-actions"},
                    el("span",{class:"action-help"},
                        this.button("Auto Describe my image",()=>this.helper("describe"),busy || !a.initial.current),
                        this.help("Describes the initial image you already uploaded and shows an editable suggestion. Upload an initial image to enable this action. The local assistant model downloads on first use.","Auto Describe my image help")),
                    el("span",{class:"action-help"},
                        this.button("Enhance description",()=>this.helper("enhance"),busy || !a.prompt.trim()),
                        this.help("Uses guidance for the selected image model and asset type. It keeps specified details and their assigned sides; any simple proposed hidden details need your review. With references, it explains the requested changes and what to preserve. This uses our local assistant, not the official PE/PUP checkpoint. Write a description to enable it. The assistant downloads on first use and unloads afterward.","Enhance description help")),
                    this.primary("Generate image and go to Step 2",()=>this.generateImage(),busy || (!a.prompt.trim() && !a.initial.current && !a.references.some(r=>r.enabled)))),
                el("p",{class:"hint prerequisites","data-description-prerequisites":""}));
            if(this.suggestion) descriptionSection.append(el("div",{class:"helper-result"},
                el("strong",{},"Suggested description"),
                el("p",{class:"hint"},`Prepared for ${profileLabels[this.suggestionContract?.profile] || a.profile} · ${categories[this.suggestionContract?.category] || a.category}. Review before using.`),
                el("textarea",{value:this.suggestion,"aria-label":"Suggested description",oninput:e=>this.suggestion=e.target.value}),
                el("div",{class:"row"},
                    this.primary("Use this description",()=>this.runOperation("description",async()=>{
                        const previous=this.asset.prompt;
                        await this.persist();
                        this.properties.asset=await request(`/assets/${this.asset.id}/descriptions/${this.suggestionId}/accept`,{text:this.suggestion});
                        this.previousPrompt=previous;this.suggestion=null;this.render();this.changed();
                        this.status("Description accepted. The original and suggested text are saved with this job.");
                    }),busy),
                    this.button("Keep my description",()=>{this.suggestion=null; this.render();}))));
            if(a.prompt_provenance) descriptionSection.append(el("p",{class:"hint"},
                a.prompt_provenance.profile!==a.profile || a.prompt_provenance.category!==a.category ?
                    "This description was enhanced for a different model or asset type. You can keep it, or Enhance again using your current choice." :
                    "This description was enhanced for the current model and asset type. Its original text is preserved."));
            if(this.previousPrompt!==undefined) descriptionSection.append(el("div",{class:"row"},this.button("Undo description change",()=>{
                a.prompt=this.previousPrompt; this.previousPrompt=undefined; this.render(); this.changed();
            },false,"quiet")));
            content.append(descriptionSection);
            content.append(el("p",{class:"hint"},"Generation creates the front first, then its back. Step 2 lets you review both before creating the remaining eight angles."));
            const refs=this.section("Add reference images (optional)",
                "These extra images show specific details you want to borrow — a face, a backpack, a logo, materials or a style. Explain what to use from each image.",
                this.button("Add reference images",()=>this.upload("references"),busy));
            for(const r of a.references) refs.append(el("div",{class:"reference"},
                el("figure",{class:"image-preview"},el("img",{src:this.fileURL(r.file),alt:r.role || "Reference image"}),
                    el("figcaption",{},this.downloadImage(r.file,r.role || "Reference image"))),
                el("div",{},this.field("Use this reference",r,"enabled","checkbox"),
                    this.field("What does this image show?",r,"role"),
                    el("textarea",{value:r.instructions,"aria-label":`Instructions for ${r.role || "reference"}`,
                        placeholder:"For example: Use this backpack on the character. Keep its shape and pockets.",
                        oninput:e=>{r.instructions=e.target.value; this.changed();}}),
                    el("div",{class:"row"},this.button("Remove",()=>{a.references=a.references.filter(x=>x!==r); this.render(); this.changed();},busy,"quiet")))));
            const model=this.select(profileLabels,a.profile,value=>{
                a.profile=value; [s.steps,s.cfg]=defaults[value];
                this.suggestion=null;
                if(!["qwen21","qwen2511","klein_kv","flux3_base"].includes(value)) s.camera_lora=false;
                s.image_precision="native";
                s.memory_overrides=s.memory_overrides.filter(key=>key!=="image_precision");
                this.memoryInfo=null;this.memoryInfoKey=null;this.render();
            },"Image model");
            const [steps,cfg]=defaults[a.profile] || [25,1];
            s.steps ??= steps; s.cfg ??= cfg;
            const advanced=el("details",{class:"advanced model-advanced",open:!!this.properties.advanced},
                el("summary",{},"Advanced — Image model and controls"));
            advanced.addEventListener("toggle",()=>{this.properties.advanced=advanced.open;});
            advanced.append(this.section(null,"Choosing an image model loads its recommended CFG and steps. You can adjust them here. These controls affect the next image you generate.",
                el("div",{class:"model-fields"},
                    el("label",{},el("span",{},"Image model",this.help(hints[a.profile],"About this image model")),model),
                    this.field("CFG",s,"cfg","number",{min:.1,max:30,step:.1,placeholder:String(cfg)}),
                    this.field("Steps",s,"steps","number",{min:1,max:150,step:1,placeholder:String(steps)})),
                el("div",{class:"seed-fields"},
                    this.field("Seed",s,"requested_seed","number",{min:-1,max:9007199254740991,step:1}),
                    el("p",{class:"hint"},"Use -1 for a new random seed each time. Enter a specific number to reuse that seed. The actual seed is shown with the finished image.")),
                el("p",{class:"hint",style:"margin-top:12px"},`Recommended defaults for this model: ${steps} steps · CFG ${cfg}. “Generate again” always uses a new random seed.`),
                this.modelLicense(a.profile),
                a.profile==="qwen2511" ? el("p",{class:"hint"},"Qwen Edit needs an initial image or a reference image before it can generate.") : null));
            const loras=this.section("LoRAs (optional)","Add a LoRA made for your selected image model. Strength controls how strongly it changes the result.");
            if(this.loraCatalog) loras.append(el("p",{class:"path"},this.loraCatalog.folders[0] || "No LoRA folder registered."));
            else loras.append(el("p",{class:"hint"},"LoRAs go in ComfyUI’s models/loras folder. Refresh the list to show the exact folder and installed files."));
            loras.append(el("div",{class:"row"},this.button("Refresh LoRA list",()=>this.loadLoras()),
                this.button("Open LoRA folder",()=>request("/open-folder",{kind:"loras"}))));
            for(const lora of a.loras) {
                const files=Object.fromEntries((this.loraCatalog?.files || []).map(f=>[f,f]));
                if(lora.name) files[lora.name]=lora.name;
                loras.append(el("div",{class:"lora"},
                    el("label",{},"LoRA",this.select({"":"Choose a LoRA",...files},lora.name,v=>{lora.name=v; lora.profile=a.profile;},"LoRA")),
                    this.field("Strength",lora,"strength","number",{min:-2,max:2,step:.05}),
                    this.button("Remove",()=>{a.loras=a.loras.filter(l=>l!==lora); this.render(); this.changed();},busy,"quiet"),
                    el("div",{class:"trigger"},this.field("Trigger words (if required by the LoRA)",lora,"trigger")),
                    lora.profile!==a.profile ? el("p",{class:"hint"},"This LoRA was selected for another model. Remove it or switch back before generating.") : null));
            }
            loras.append(el("div",{class:"row"},this.button("Add LoRA",async()=>{
                if(!this.loraCatalog) this.loraCatalog=await request("/loras");
                a.loras.push({name:"",profile:a.profile,strength:1,trigger:"",enabled:true}); this.render(); this.changed();
            },busy)));
            advanced.append(loras);
            content.append(refs,advanced);
            content.append(el("section",{class:"design-preview"},
                el("h3",{},"Your image"),el("div",{class:"image-stage"},this.preview(a.design)),
                el("div",{class:"row spread"},
                    this.primary("Use this image → Next step",()=>this.useDesign(),busy || !a.design.current),
                    el("div",{class:"row"},
                        this.button("Generate again",()=>this.generateImage("design","generate",true),busy || !a.design.current),
                        this.button("Clear image",async()=>{a.design.current=null; await this.persist(); this.render();},busy || !a.design.current,"quiet")))));
        }
        renderViews(content) {
            const a=this.asset,busy=!!operation(),ready=this.pairReady();
            const back=a.views.find(v=>v.id==="view_05");
            content.append(el("div",{class:"step-heading"},el("div",{},el("h3",{},"Step 2 — Review front and back, then create other angles"),
                el("p",{class:"hint"},"Check that the front and back show the same object. Correct either image if needed, then approve the pair. Below, choose whether to use these references directly or build a draft to guide the remaining angles."))));
            content.append(el("div",{class:"cards"},
                el("article",{class:"card"},
                    el("header",{},el("h3",{},"Front reference"),
                        this.field("Include in mesh",a.views.find(v=>v.id==="view_01"),"enabled","checkbox",{disabled:!ready || busy})),
                    this.preview(a.design),
                    el("p",{class:"hint"},ready?"This front is used to create the back. Replacing it clears the old back and other angles; saved files remain in History.":"Approving the pair includes this front and back in the mesh. You can change that selection afterward. Replacing the front clears dependent angles; saved files remain in History."),
                    el("div",{class:"row"},
                        this.button("Regenerate front and back",()=>this.generateImage("design","generate",true),busy || !a.design.current),
                        this.button("Back to design",()=>this.setTab("Design"),false,"quiet"))),
                this.viewCard(back,busy,true)));
            const approve=this.primary(ready?"Front and back approved":"Approve front and back",()=>this.approvePair(),
                busy || ready || !a.design.current || !back.current);
            if(ready) approve.title="These front and back images are already approved. Generate the remaining angles below.";
            if(!ready && !busy && (!a.design.current || !back.current)) approve.title="Create both the front and back images first.";
            content.append(el("div",{class:"row"},approve,
                el("p",{class:"hint",style:"margin:0"},ready?
                    "The approved pair is ready. The angle method below explains which images it uses.":
                    "Review both images before approval. The remaining angles stay locked until you approve this pair.")));
            this.renderDraft(content);
            this.renderAngleSettings(content,busy);
            this.renderMeshSettings(content,busy);
            content.append(el("div",{class:"row spread"},
                el("div",{class:"row"},this.primary("Generate remaining angles",()=>this.generateViews(),busy || !ready),
                    this.button("Clear all images",()=>this.confirmClearAngles(),busy || !a.views.some(v=>v.current),"quiet")),
                this.meshButton()),
                el("p",{class:"hint",style:"margin-top:12px","data-mesh-selection":""},this.meshSelectionSummary()));
            if(!ready) content.append(el("p",{class:"hint"},"Approve the front and back above to unlock generation of the remaining eight angles."));
            const cards=el("div",{class:"cards"});
            for(const view of a.views.filter(v=>!["view_01","view_05"].includes(v.id))) cards.append(this.viewCard(view,busy,false));
            content.append(cards,el("div",{class:"row spread"},
                el("p",{class:"hint"},"Review each angle. Only checked, current images will be used in the mesh."),
                this.meshButton()));
        }
        modelLicense(profile,route="references") {
            const four=["klein4","klein4_base"].includes(profile),permissive=four || profile==="qwen2511";
            const info=profile==="qwen21" ? {
                text:"Qwen 2.1’s standard license allows research and evaluation. Commercial use requires separate permission from Qwen; contact model-business@notice.qwencloud.com. AnyAngle’s Apache license does not replace the base-model terms.",
                url:"https://huggingface.co/Qwen/Qwen-Image-2.1/blob/main/LICENSE"
            } : profile==="qwen2511" ? {
                text:"Qwen Edit 2511 uses Apache 2.0, which permits commercial use under its terms. Added LoRAs and reference images have their own terms.",
                url:"https://huggingface.co/Qwen/Qwen-Image-Edit-2511"
            } : four ? {
                text:"Klein 4B uses Apache 2.0, which permits commercial use under its terms. The matching RefControl adapter is Apache 2.0. Depth here is rendered from your mesh; no separate AI depth estimator is used.",
                url:"https://huggingface.co/black-forest-labs/FLUX.2-klein-base-4B"
            } : profile.startsWith("flux3") ? {
                text:"FLUX Kommunity allows qualifying users with combined annualized revenue below US$5 million to run the model to generate commercial outputs, subject to the full terms. Other commercial uses need BFL permission. Review/disclosure and redistribution conditions also apply.",
                url:"https://huggingface.co/black-forest-labs/flux-3-image-klein/blob/main/LICENSE.md"
            } : {
                text:"Klein 9B’s standard weights license restricts commercial operation. It separately permits commercial use of outputs, subject to its terms. Output permission does not authorize every commercial use of the model itself; consult BFL for a commercial deployment license.",
                url:"https://huggingface.co/black-forest-labs/FLUX.2-klein-base-9B/blob/main/LICENSE.md"
            };
            const adapter=route==="qwen_anyangle"?"https://huggingface.co/lilylilith/QI_2.1_AnyAngle":
                route==="klein_depth"?`https://huggingface.co/thedeoxen/refcontrol-FLUX.2-klein-${four?"4B":"9B"}-reference-depth-lora`:null;
            return el("details",{class:"license-info"},
                el("summary",{},`${permissive?"Commercial use allowed":"Commercial use has conditions"} — license details`),
                el("p",{class:"hint"},info.text),el("a",{href:info.url,target:"_blank",rel:"noopener noreferrer"},"Read the model license"),
                adapter?el("p",{},el("a",{href:adapter,target:"_blank",rel:"noopener noreferrer"},"Read the camera adapter’s guidance and terms")):null);
        }
        renderAngleSettings(content,busy) {
            const a=this.asset,s=a.settings,route=s.angle_route || "references";
            const selected=s.angle_profile && s.angle_profile!=="same"?s.angle_profile:a.profile;
            const choices={references:"Approved front and back — no mesh guide",klein_depth:"Depth guide — Klein Base",
                qwen_anyangle:"Color guide — Qwen 2.1 AnyAngle",qwen_edit_depth:"Depth editing — Qwen Edit 2511 (experimental)"};
            const recommendations={klein_depth:[20,5],qwen_anyangle:[25,3],qwen_edit_depth:[40,4]};
            const [steps,cfg]=recommendations[route] || defaults[selected];
            const changeRoute=value=>{
                s.angle_route=value;s.angle_steps=null;s.angle_cfg=null;s.guide_strength=1;s.angle_camera_lora=false;
                if(value==="klein_depth" && !["klein4_base","klein_base"].includes(selected)) s.angle_profile="klein4_base";
                if(value==="qwen_anyangle") s.angle_profile="qwen21";
                if(value==="qwen_edit_depth") s.angle_profile="qwen2511";
                this.render();this.changed();
            };
            const hints={references:"Uses your approved front, back and description. It asks for a new camera in words; the result may miss the angle.",
                klein_depth:"Uses the draft’s depth image first and the nearest approved front or back image second, with the matching RefControl adapter. Rear angles use the back; side-on angles use the front. " +
                    (selected==="klein_base"?"The 9B adapter uses its trained trigger only: appearance comes from your approved image, whose design was made with your description. Extra pose text can compete with the depth camera. ":"Your description supplies the side details. ") +
                    "Review each result: depth guides can still carry rough-shape mistakes.",
                qwen_anyangle:"Uses your original front image first and a color render of the draft second, with AnyAngle. Build a draft with color and render its guides first. This follows the published two-image recipe; the back informs the draft and description.",
                qwen_edit_depth:"Experimental: asks Qwen Edit 2511 to turn the draft’s depth image into the object shown in your front reference. This has no trained camera adapter and needs comparison before recommendation."};
            const section=el("details",{class:"advanced",open:!!this.properties.angleSettings},el("summary",{},"Angle generation settings"));
            section.addEventListener("toggle",()=>{this.properties.angleSettings=section.open;});
            section.append(el("label",{},"Angle method",this.select(choices,route,changeRoute,"Angle method")),
                el("p",{class:"hint"},hints[route]),
                el("label",{},"Model for other angles",this.select({same:"Same model as the design",...profileLabels},s.angle_profile || "same",v=>{
                    s.angle_profile=v;s.angle_steps=null;s.angle_cfg=null;s.angle_camera_lora=false;
                    this.render();this.changed();
                },"Model for other angles")),
                el("p",{class:"hint"},"These controls affect the remaining angles. Your original design and front/back model settings stay unchanged. Only LoRAs labeled for this angle model are used."),
                el("div",{class:"model-fields"},
                    this.field("Angle steps",s,"angle_steps","number",{min:1,max:150,placeholder:String(steps)}),
                    this.field("Angle CFG",s,"angle_cfg","number",{min:.1,max:30,step:.1,placeholder:String(cfg)})),
                el("p",{class:"hint"},`Blank values use this method’s defaults: ${steps} steps, CFG ${cfg}. The Seed control in Step 1 also applies to angle attempts; each result records its actual seed.`));
            if(["klein_depth","qwen_anyangle"].includes(route)) section.append(
                this.field("Guide adapter strength",s,"guide_strength","number",{min:0,max:2,step:.05}),
                el("p",{class:"hint"},"Default 1 follows the adapter example. Raising it is not guaranteed to improve accuracy. Required model and adapter files download locally on first use."));
            if(route==="references") {
                const supported=["qwen21","qwen2511","klein_kv","flux3_base"].includes(selected);
                section.append(this.field("Use optional camera LoRA",s,"angle_camera_lora","checkbox",{disabled:busy || !supported}),
                    el("p",{class:"hint"},supported?"Optional camera presets can help, but results are not always consistent. Leave off to use words and references alone.":"No matching camera-preset LoRA is configured for this variant. Reference-based generation remains available."));
            }
            section.append(this.button("Reset angle defaults",()=>{s.angle_steps=null;s.angle_cfg=null;s.guide_strength=1;this.changed();this.render();},busy,"quiet"),
                this.modelLicense(selected,route),
                el("p",{class:"hint"},"A guide fixes the requested camera, not the AI result. Review each generated image before including it in the mesh."));
            content.append(section);
        }
        viewCard(view,busy,anchor=false) {
                const locked=!anchor && !this.pairReady();
                const correct=this.button("Apply change",()=>this.generateImage(view.id,"correct"),busy || locked || !view.current || !view.correction.trim());
                correct.dataset.correctView=view.id;
                return el("article",{class:"card"},
                el("header",{},el("h3",{},anchor?"Back reference":view.name),this.field("Include in mesh",view,"enabled","checkbox")),
                this.preview(view),
                view.current && view.stale ? el("p",{class:"hint"},"This image is out of date and will not be used in the mesh. Regenerate it to match the current design.") : null,
                el("textarea",{value:view.correction,"aria-label":`Change ${view.name}`,
                    placeholder:"Describe a change to this image, or leave blank to try this angle again.",
                    oninput:e=>{view.correction=e.target.value; this.changed();}}),
                el("div",{class:"row"},
                    this.button(anchor?(view.current?"Regenerate back":"Generate back"):(view.current ? "Regenerate" : "Generate angle"),
                        ()=>this.generateImage(view.id,"generate"),busy || locked || !this.asset.design.current),
                    this.button("Clear this image",()=>this.clearAngles(view),busy || !view.current,"quiet"),
                    correct),
                el("p",{class:"hint"},"To apply a change, generate or upload this angle first, then describe the change above."),
                this.guidePreview(view,busy),
                el("details",{class:"advanced"},el("summary",{},"Angle settings & upload"),
                    el("div",{class:"fields"},this.field("Around object °",view,"azimuth","number",{step:1,disabled:anchor}),
                        this.field("Above / below °",view,"elevation","number",{min:-90,max:90,step:1,disabled:anchor}),
                        this.field("Field of view °",view,"fov","number",{min:2,max:169,step:1})),
                    el("p",{class:"hint"},"Generated camera angles are estimates. Check the image before including it."),
                    el("div",{class:"row"},this.button("Upload this angle",()=>this.upload(view.id),busy || (!anchor && locked)))));
        }
        renderProgress() {
            this.progressLabel=el("strong",{},operation()?.message || "Working…");
            this.progressBar=el("progress",{"aria-label":"Current operation progress"});
            return el("div",{class:"progress-area"},this.progressLabel,this.progressBar,
                el("p",{class:"hint"},"Progress shows the current stage. Completed results are saved as each stage finishes."),
                this.button("Stop",()=>this.stop(),false,"quiet"));
        }
        renderMeshSettings(content,busy) {
            const s=this.asset.settings,defaults=this.server?.mesh_defaults;
            if(!defaults) return;
            for(const [key,value] of Object.entries(defaults)) s[key]??=value;
            const numeric=(label,key,min,max,step=1)=>this.field(label,s,key,"number",{min,max,step,disabled:busy});
            const section=el("details",{class:"advanced","data-mesh-controls":""},el("summary",{},"Advanced — Mesh quality and export"),
                el("p",{class:"hint"},"These are the existing workflow defaults. Change them for the next final mesh; they do not change your images or the cheaper draft. More steps take longer, and higher guidance is not automatically more accurate."),
                el("label",{},"3D model",this.select({pixal_multiview:"Pixal3D — multiple images",pixal_single:"Pixal3D — single image",trellis2:"TRELLIS.2 — single image"},s.mesh_backend,v=>{s.mesh_backend=v;this.changed();this.render();},"Mesh model")),
                el("p",{class:"hint"},"Pixal3D multiple-image mode uses checked current images. Both single-image modes use the starting image, or the first checked image when it is unavailable. Ten checked images do not become ten inputs in a single-image mode."),
                el("div",{class:"fields"},numeric("Final shape resolution","shape_resolution",1024,2048,128),numeric("Mesh seed (-1 = random)","mesh_requested_seed",-1,2**53-16)),
                el("p",{class:"hint"},`Shape resolution controls the reconstruction grid, not the exported triangle count. Higher values can retain smaller features and use more memory. Mesh seed is independent of the image seed; -1 chooses a new seed for each mesh.${s.mesh_seed!==undefined?` Last mesh seed: ${s.mesh_seed}.`:""}`));
            for(const [key,label,help] of [
                ["structure","Overall structure","Establishes occupied space and the broad silhouette."],
                ["shape","Base shape","Builds the geometry before high-resolution refinement."],
                ["refine","Fine shape detail","Refines the geometry at the final shape resolution."],
                ["material","Surface color and materials","Generates surface information before texture baking. This does not set texture size."]]) {
                section.append(el("h4",{},label),el("div",{class:"fields"},numeric(`${label} steps`,`mesh_${key}_steps`,1,150),numeric(`${label} guidance (CFG)`,`mesh_${key}_cfg`,0,30,.1)),el("p",{class:"hint"},help));
            }
            if(s.mesh_backend==="pixal_single") section.append(el("label",{},"Source perspective",this.select({manual:"Manual field of view",auto:"Estimate field of view — MoGe-2"},s.mesh_fov_mode,v=>{s.mesh_fov_mode=v;this.changed();this.render();},"Source perspective")),
                s.mesh_fov_mode==="manual"?numeric("Source camera field of view °","mesh_fov",1,170,.01):null,
                el("p",{class:"hint"},"Horizontal field of view describes lens perspective: smaller values mean flatter perspective. Auto retains a mesh-guided image's requested perspective; otherwise it estimates from the prepared image using MoGe-2, downloaded locally on first use (1.31 GB, MIT license). It does not measure the object's turnaround angle. Use manual to override the perspective if the shape looks distorted."));
            else section.append(el("p",{class:"hint"},s.mesh_backend==="pixal_multiview"?"Camera field of view is stored separately on each angle card. Mesh-guided images retain their recorded camera and full frame; requested AI angles are still estimates.":"TRELLIS.2's single-image conditioning has no camera field-of-view control."));
            section.append(el("p",{class:"hint"},"This installed native upsample node exposes resolution, but no token-budget control. No hidden token limit or automatic resolution reduction is applied here."),
                this.button("Reset reconstruction defaults",()=>{Object.assign(s,defaults,{shape_resolution:1536});this.changed();this.render();},busy,"quiet"),
                el("h4",{},"Saved versions"),el("div",{class:"fields"},numeric("Master triangles (0 = retain)","master_faces",0,50000000,10000),numeric("Game triangles","game_faces",100,50000000,100),numeric("Asset height (meters)","asset_height",.001,100000,.001)),
                el("p",{class:"hint"},"The raw master is preserved before finishing. Lower triangle targets make lighter exports but can lose thin parts. Height sets export scale; printable STL uses millimeters."),
                el("div",{class:"fields"},numeric("Master texture pixels","master_texture",64,8192,64),numeric("Game texture pixels","game_texture",64,8192,64),numeric("Normal map pixels","normal_resolution",64,8192,64)),
                this.field("Transfer surface detail (normal map)",s,"bake_normal","checkbox",{disabled:busy}),
                el("p",{class:"hint"},"Default: on. Transfers fine shading detail from the raw mesh to the export. Turn it off if it carries unwanted bumps; this keeps the geometry and color, but loses some fine shading detail. Larger maps cost memory and disk space."),
                el("div",{class:"fields"},this.field("Remesh before reduction",s,"remesh","checkbox",{disabled:busy}),numeric("Smoothing iterations","smoothing",0,20),numeric("Hard-edge angle °","crease_angle",0,180)),
                el("p",{class:"hint"},"Remeshing can clean rough surfaces but change thin features or holes. Smoothing softens geometry. Lower hard-edge angles preserve more sharp shading edges."),
                el("div",{class:"fields"},this.field("Bake ambient occlusion",s,"bake_ao","checkbox",{disabled:busy}),numeric("Ambient occlusion pixels","ao_resolution",64,8192,64)),
                el("label",{},"Texture unwrap method",this.select({adaptive:"Adaptive — CPU",pec:"Parallel edge collapse — GPU"},s.uv_method,v=>{s.uv_method=v;this.changed();},"Texture unwrap method")),
                el("p",{class:"hint"},"Unwrapping lays out the surface for textures. The GPU method uses additional VRAM. Ambient occlusion stores contact shading in a separate map."));
            for(const select of section.querySelectorAll("select")) select.disabled=busy;
            content.append(section);
        }
        renderDraft(content) {
            const a=this.asset,busy=!!operation();
            const choice=(items,value,change)=>{const input=this.select(items,value,change);input.disabled=busy;return input;};
            const draft=a.drafts?.find(d=>d.id===a.selected_draft) || a.drafts?.at(-1);
            const section=el("section",{class:"output"},el("h3",{},"Draft shape for camera guides"),
                el("p",{class:"hint"},"Build a rough 3D shape from your approved references. Check it before using it to guide other angles: a wrong shape can carry its mistakes into those images."),
                el("details",{class:"advanced"},el("summary",{},"Draft settings"),
                    el("div",{class:"fields"},
                        el("label",{},"Draft model",choice({pixal_multiview:"Pixal3D — front and back",pixal_single:"Pixal3D — front only",trellis2:"TRELLIS.2 — front only"},a.settings.draft_backend,value=>{a.settings.draft_backend=value;this.changed();})),
                        el("label",{},"Draft appearance",choice({geometry:"Shape only — for depth guides",color:"Color — for appearance guides"},a.settings.draft_appearance,value=>{a.settings.draft_appearance=value;this.changed();})),
                        this.field("Draft seed",a.settings,"draft_seed","number",{min:0,max:2**53-1,step:1,disabled:busy})),
                    el("p",{class:"hint"},"Uses the 512-resolution shape stage without high-resolution refinement or UV baking. Shape-only skips the material model. Color takes longer and supplies approximate vertex colors. These settings do not lower your final mesh quality.")),
                el("div",{class:"row"},this.primary(draft?"Rebuild draft":"Build draft shape",()=>this.generateDraft(),busy || !this.pairReady())));
            if(draft) {
                const viewer=el("div",{class:"viewer","aria-label":"Interactive draft shape preview"});
                section.append(el("p",{class:"hint"},`${draft.triangles.toLocaleString()} triangles · ${draft.appearance==="color"?"Approximate color":"Shape only"}${draft.stale?" · Source references changed — rebuild before using guides":""}`),viewer,
                    el("p",{class:"hint"},"Drag to rotate · Scroll to zoom. Check thickness, openings and missing parts. You can correct the reference images above and rebuild."),
                    el("div",{class:"row"},this.button("Reset view",()=>this.viewer?.fitToViewer(),false,"quiet"),
                        this.primary(draft.approved?"Draft approved":"Use this draft for camera guides",()=>this.approveDraft(draft.id),busy || draft.stale || draft.approved),
                        el("a",{class:"download",href:this.fileURL(draft.file),download:`${a.name}-draft.glb`},"Save draft GLB")));
                if(draft.approved && !draft.stale) {
                    const count=a.views.filter(v=>this.guideFor(v.id)).length;
                    section.append(el("div",{class:"row"},this.primary("Render camera guides",()=>this.generateGuides(),busy || count===a.views.length),
                        el("span",{class:"hint"},`${count} of ${a.views.length} angles have current guides.`)),
                        el("p",{class:"hint"},"Guides use the saved draft. They do not rebuild it or load an image model. Review individual guides in the angle cards below."),
                        this.guidePreview(a.views.find(v=>v.id==="view_01"),busy));
                }
                requestAnimationFrame(()=>this.mountViewer(viewer,draft,"draft"));
            }
            content.append(section);
        }
        async mountViewer(container,output,kind="export") {
            try {
                if(!container.isConnected) return;
                const factory=window.comfyAPI?.createLoad3d?.createLoad3d;
                if(!factory) throw Error("The Comfy 3D viewer has not loaded yet. Reopen this tab after the 3D nodes finish loading.");
                const viewer=factory(container);
                this.viewer=viewer;
                container.addEventListener("pointerenter",()=>viewer.updateStatusMouseOnViewer(true));
                container.addEventListener("pointerleave",()=>viewer.updateStatusMouseOnViewer(false));
                viewer.updateStatusMouseOnViewer(container.matches(":hover"));
                viewer.setLightIntensity(3);
                this.viewerResize=new ResizeObserver(()=>viewer.handleResize());
                this.viewerResize.observe(container);
                const preview=await request(`/assets/${this.asset.id}/preview`,{[kind]:output.id});
                await viewer.loadModel(preview.url);
                if(!container.isConnected) {viewer.remove(); return;}
                if(!viewer.getCurrentModel()) throw Error("The 3D file could not be loaded. You can still save it below.");
                viewer.handleResize(); viewer.fitToViewer(); viewer.forceRender();
            } catch(error) {container.replaceChildren(el("div",{class:"empty"},error.message));}
        }
        renderResult(content) {
            content.append(el("div",{class:"step-heading"},el("div",{},el("h3",{},"Step 3 — Your 3D asset"),
                el("p",{class:"hint"},"The shape, textures and game version are created in order. You can inspect and save the finished asset here."))));
            const outputs=this.asset.exports || [];
            const latest=outputs.find(e=>e.id===this.asset.selected_export) || outputs.filter(e=>!e.stale).at(-1);
            const unfinished=this.asset.masters.find(m=>m.id===this.asset.selected_master) || this.asset.masters.filter(m=>!m.stale).at(-1);
            if(!operation() && unfinished && !outputs.some(e=>e.kind==="game" && e.master===unfinished.id && !e.stale))
                content.append(el("div",{class:"progress-area"},el("p",{},"A saved 3D mesh is available. Continue texturing and export without rebuilding its shape."),
                    this.primary("Continue finishing saved mesh",()=>this.finishMaster(unfinished.id))));
            if(latest) {
                const viewer=el("div",{class:"viewer","aria-label":"Interactive 3D asset preview"});
                content.append(viewer,el("p",{class:"hint",style:"margin-top:10px"},"Drag to rotate · Scroll to zoom"),
                    el("div",{class:"row"},this.button("Reset view",()=>this.viewer?.fitToViewer(),false,"quiet")));
                requestAnimationFrame(()=>this.mountViewer(viewer,latest));
                for(const kind of ["master","game"]) {
                    const output=[...outputs].reverse().find(e=>e.kind===kind && (!latest?.master || e.master===latest.master));
                    if(!output) continue;
                    content.append(el("div",{class:"output"},
                        el("h3",{},kind==="master" ? "High-quality master" : "Game version"),
                        el("p",{class:"hint"},`${(output.triangles || 0).toLocaleString()} triangles${output.stale ? " · Built from earlier settings" : ""}`),
                        el("div",{class:"row"},el("a",{class:"download",href:this.fileURL(output.file),download:`${this.asset.name}-${kind}.glb`},"Save textured GLB"),
                            this.button("Preview",async()=>{
                                const preview=await request(`/assets/${this.asset.id}/preview`,{export:output.id});
                                await this.viewer?.loadModel(preview.url);
                                this.viewer?.fitToViewer();
                            },false,"quiet")),
                        el("p",{class:"path",style:"margin-top:10px"},output.file)));
                    if(output.print) {
                        const p=output.print;
                        content.append(el("div",{class:"output"},
                            el("h3",{},"3D printing"),
                            el("a",{class:"download",href:this.fileURL(p.file),download:`${this.asset.name}-print-mm.stl`},"Save STL — millimeters"),
                            el("p",{class:"hint"},`Shape only; textures are not included. Size: ${p.dimensions_mm.map(v=>v.toFixed(1)).join(" × ")} mm. Z-up.`),
                            el("p",{class:"hint"},`Closed surface: ${p.watertight?"yes":"no"} · Consistent face direction: ${p.winding_consistent?"yes":"no"} · Separate pieces: ${p.components} · Degenerate faces: ${p.degenerate_faces}.`),
                            el("p",{class:"hint"},"Review this mesh in your slicer before printing. Wall thickness, self-intersections, supports and printer tolerances have not been checked.")));
                    }
                }
                content.append(el("p",{class:"hint"},"Your original mesh data, master and game files are stored separately. Saving the game version does not replace the master."),
                    this.button("Open asset folder",()=>request("/open-folder",{kind:"asset",asset:this.asset.id}),false,"quiet"));
            } else if(!operation()) content.append(el("div",{class:"empty"},"Your finished 3D asset will appear here."),
                this.button("Go to Step 2",()=>this.setTab("Views")));
        }
        editableSettings() {
            const op=operation();
            if(!op) return this.asset.settings;
            op.settingsOriginal ??= JSON.parse(JSON.stringify(this.asset.settings));
            op.settingsDraft ??= JSON.parse(JSON.stringify(op.settingsOriginal));
            return op.settingsDraft;
        }
        async saveSettings() {
            const op=operation();
            if(op?.settingsDraft) {
                this.properties.pendingSettings={asset:this.asset.id,
                    original:op.settingsOriginal,values:op.settingsDraft};
                await api.storeUserData("workflows/Mumblebox Creator.json",app.graph.serialize());
                this.status("Settings saved for the next run. The current run keeps the settings it started with.");
            } else {
                await this.persist();this.status("Settings saved. They apply to your next generation.");
            }
        }
        async loadMemoryInfo() {
            if(this.memoryLoading) return;
            const key=`${this.asset.id || ""}:${this.asset.profile}`;
            this.memoryLoading=true;
            try {
                const path=this.asset.id?`/assets/${this.asset.id}/memory`:"/memory";
                const data=await request(`${path}?profile=${encodeURIComponent(this.asset.profile)}`);
                if(key!==`${this.asset.id || ""}:${this.asset.profile}`) return;
                this.memoryInfo=data;this.memoryInfoKey=key;this.memoryError="";
                const s=this.editableSettings();
                for(const [field,value] of Object.entries(data.values))
                    if(!s.memory_overrides.includes(field)) s[field]=value;
            } catch(error) {
                this.memoryError=error.status===404?
                    "Hardware recommendations will be available after the repaired backend is activated. Your settings remain editable.":error.message;
                this.memoryInfoKey=key;
            } finally {this.memoryLoading=false;this.render();}
        }
        memoryControl(label,key,explanation,choices=null,extra={}) {
            const s=this.editableSettings();
            const badge=el("span",{class:"setting-origin"},s.memory_overrides.includes(key)?"Saved override":"Automatically selected");
            const mark=()=>{
                if(!s.memory_overrides.includes(key)) s.memory_overrides.push(key);
                badge.textContent="Changed by you";this.changed();
            };
            const control=choices ? el("label",{},label,this.select(choices,s[key],v=>{s[key]=v;mark();},label)) :
                this.field(label,s,key,typeof s[key]==="boolean"?"checkbox":"number",extra);
            if(!choices) control.addEventListener("input",mark);
            return el("div",{class:"setting"},control,badge,el("p",{class:"hint"},explanation));
        }
        renderResources(content) {
            const a=this.asset,s=this.editableSettings(),busy=!!operation();
            content.append(el("div",{class:"step-heading"},el("div",{},el("h3",{},"Settings"),
                el("p",{class:"hint"},busy?"You can change and save settings while work runs. Your changes apply after this run finishes.":"New assets use recommended memory defaults for your hardware. Existing assets keep their saved choices. Change any setting, or restore recommendations below.")),
                this.primary("Save settings",()=>this.saveSettings())));
            content.append(el("div",{class:"row"},this.unloadButton(),
                el("p",{class:"hint",style:"margin:0"},"Free VRAM and system RAM used by idle Comfy models. Models reload when needed.")));
            if(this.memoryInfoKey!==`${a.id || ""}:${a.profile}` && !this.memoryLoading) {
                this.memoryLoading=true;
                queueMicrotask(()=>{this.memoryLoading=false;this.loadMemoryInfo();});
            }
            const info=this.memoryInfo,hw=info?.hardware || this.server?.hardware;
            const hardware=hw?el("div",{class:"hardware"},
                el("strong",{},hw.name),el("p",{class:"hint"},`${hw.vram_total_gb.toFixed(1)} GB VRAM · ${hw.ram_total_gb.toFixed(1)} GB system RAM`),
                el("p",{class:"hint"},`Comfy mode: ${hw.comfy_mode}. The launcher's ${hw.startup_reserve_gb.toFixed(1)} GB VRAM reserve is read-only here; the extra headroom below is added for sampling.`)):
                el("p",{class:"hint"},"Reading the hardware selected by Comfy…");
            content.append(this.section("Memory","These controls manage memory use without reducing your mesh or texture detail. Smaller GPUs may need slower CPU offloading. The recommendations are starting settings, not a guarantee that every model fits.",
                hardware,this.memoryError?el("p",{class:"hint"},this.memoryError):null,
                ...(info?.warnings || []).map(w=>el("p",{class:"memory-warning"},w)),
                el("div",{class:"settings-grid"},
                    this.memoryControl("Extra VRAM headroom (GB)","extra_vram_headroom_gb","More headroom encourages Comfy to keep more model weights in system RAM. This can reduce GPU pressure but slow sampling. It is not a hard VRAM limit.",null,{min:0,max:12,step:.25}),
                    this.memoryControl("Keep system RAM free (GB)","min_ram_free_gb","Before starting a stage, pause if less than this much RAM is available. Lowering it allows work to start with less room left for Windows.",null,{min:1,max:60,step:1}),
                    el("div",{class:"hint"},"Automatic memory release is always on. After each stage, including failure or cancellation, unload models and clear temporary execution results. Check memory before continuing. Saved images and meshes stay intact; the next model may take time to reload."),
                    this.memoryControl("Decode images in tiles","tiled_vae","Decode smaller image sections to reduce peak VRAM. It can take longer than decoding the full image at once."),
                    this.memoryControl("Qwen 2.1 reference cache","cache_device","Only used by Qwen 2.1. System RAM saves VRAM; VRAM may be faster; recomputing avoids keeping a cache.",{cpu:"Use system RAM",auto:"Automatic",gpu:"Use VRAM",off:"Recompute instead"}),
                    this.memoryControl("Description assistant","helper_precision","Q8 keeps more precision. Q4 needs less memory. The selected assistant downloads on first use.",{q8:"Q8 — higher precision",q4:"Q4 — less memory"})),
                el("details",{class:"advanced"},el("summary",{},"Advanced memory precision"),
                    el("div",{class:"settings-grid"},
                        this.memoryControl("Image model precision","image_precision","Native uses this model's configured format. BF16 requires larger weights and more memory; it is offered only where this workflow has a supported model file.",
                            info?.bf16_supported?{native:"Native model format",bf16:"BF16 — more memory"}:{native:"Native model format"}),
                        this.memoryControl("Qwen 2.1 cache precision","cache_precision","Preserve precision for quality. INT8 and INT4 reduce cache memory but can change the result. Other image models do not use this setting.",
                            {default:"Preserve precision",int8:"INT8 — smaller cache",int4:"INT4 — smallest cache"}))),
                el("div",{class:"row"},
                    this.button("Restore recommended memory settings",async()=>{
                        if(!this.memoryInfo) await this.loadMemoryInfo();
                        if(!this.memoryInfo) throw Error(this.memoryError || "Hardware recommendations are not available yet.");
                        Object.assign(this.editableSettings(),this.memoryInfo.values,{memory_overrides:[]});
                        this.changed();this.render();this.status("Recommended memory settings selected. Save settings to keep them. Quality settings were not changed.");
                    },false,"quiet"),
                    this.button("Refresh hardware information",()=>this.loadMemoryInfo(),false,"quiet")),
                busy?el("p",{class:"hint"},"Releasing models and downloading new ones waits until the current operation finishes. Settings remain editable."):null));
            const connection=this.server?.hugging_face;
            const tokenInput=el("input",{type:"password",autocomplete:"off",spellcheck:false,
                placeholder:"Paste your Hugging Face access token", "aria-label":"Hugging Face access token",
                style:"width:min(100%,520px)"});
            const connectionText=el("p",{class:"hint",role:"status"},
                connection?.connected?`Connected as ${connection.account}. Token saved in your operating system's credential vault.`:
                    "Optional. Public models can download without an account. Connect for models that require access.");
            const connect=async action=>{
                const body={action};
                if(action==="connect") {body.token=tokenInput.value;tokenInput.value="";}
                connectionText.textContent=action==="disconnect"?"Removing this installation's connection…":"Checking Hugging Face…";
                try {
                    const result=await request("/hugging-face",body);
                    this.server.hugging_face=result;
                    this.render();
                    this.status(action==="test"?`Hugging Face connection verified for ${result.account}.`:
                        action==="disconnect"?"Hugging Face disconnected from this Comfy installation. Downloaded models are kept.":
                        `Connected to Hugging Face as ${result.account}.`);
                } catch(error) {
                    connectionText.textContent=error.message;throw error;
                } finally {delete body.token;}
            };
            content.append(this.section("Hugging Face connection",
                "Use your own account to download models into this Comfy installation. Your token is never saved in workflows, asset parameters or History.",
                connectionText,connection?.error?el("p",{class:"memory-warning"},connection.error):null,
                el("label",{},"Access token",tokenInput),
                el("div",{class:"row",style:"margin-top:12px"},
                    this.button("Connect Hugging Face",()=>connect("connect"),this.server?.download?.status==="running"),
                    this.button("Test connection",()=>connect("test"),!connection?.connected),
                    this.button("Disconnect",()=>connect("disconnect"),!connection?.connected || this.server?.download?.status==="running")),
                el("p",{class:"hint"},"Create a fine-grained token with permission to read public gated repositories. Some models also require you to accept their license on Hugging Face.",
                    " ",el("a",{href:"https://huggingface.co/settings/tokens",target:"_blank",rel:"noopener noreferrer"},"Create or manage your tokens")),
                el("p",{class:"hint"},"Disconnect removes this installation's saved token. It does not revoke the token on Hugging Face or delete model files.")));
            content.append(this.section("Models & downloads","Required models download automatically the first time you use them. You can also download them here in advance.",
                el("p",{class:"hint"},`Download folder: ${this.server?.models_directory || "This Comfy installation's models folder"}`),
                el("div",{class:"row"},
                    this.button("Download selected image model",()=>this.runOperation("download",async()=>{
                        await this.ensureModels("image");
                        this.status("The selected image model files are ready. Existing files were reused where available.");
                    }),busy),
                    this.button("Download selected 3D models",()=>this.runOperation("download",async()=>{
                        await this.ensureModels("mesh");
                        this.status("The selected 3D model files are ready. Existing files were reused where available.");
                    }),busy)),
                el("label",{style:"margin-top:16px"},"3D model",
                    this.select({pixal_multiview:"Pixal3D — multiple images",pixal_single:"Pixal3D — single image",trellis2:"TRELLIS.2 — single image"},
                        s.mesh_backend,v=>s.mesh_backend=v,"3D model")),
                el("p",{class:"hint",style:"margin-top:10px"},"Multiple-image mode uses the checked angle images. With only the starting image, Pixal3D automatically uses its single-image model."),
                this.field("Allow starting image when no angles are selected",s,"include_design","checkbox")));
            content.append(this.section("Quality","Your current quality settings are preserved. Higher detail and larger textures use more memory and take longer.",
                el("div",{class:"fields"},this.field("3D detail",s,"shape_resolution","number",{min:1024,max:2048,step:128}),
                    this.field("Image size",s,"resolution","number",{min:256,max:2048,step:32}),
                    this.field("Asset height (meters)",s,"asset_height","number",{min:.001,step:.001})),
                el("p",{class:"hint settings-explanation"},"3D detail controls the reconstruction grid: higher values can capture smaller features but require more memory. Image size controls the generated reference images. Asset height sets the scale of exported files."),
                el("div",{class:"fields"},this.field("Master triangles",s,"master_faces","number",{min:0,step:10000}),
                    this.field("Game triangles",s,"game_faces","number",{min:100,step:100}),
                    this.field("Hard-edge angle °",s,"crease_angle","number",{min:0,max:180})),
                el("p",{class:"hint settings-explanation"},"Triangle targets control exported mesh complexity. A master target of 0 keeps the available geometry. Lower game targets make lighter assets but can lose detail. Lower hard-edge angles preserve more sharp shading edges; 180° smooths them."),
                el("div",{class:"fields"},this.field("Master texture",s,"master_texture","number",{min:64,max:8192,step:64}),
                    this.field("Game texture",s,"game_texture","number",{min:64,max:8192,step:64}),
                    this.field("Normal map",s,"normal_resolution","number",{min:64,max:8192,step:64})),
                this.field("Transfer surface detail (normal map)",s,"bake_normal","checkbox"),
                el("p",{class:"hint settings-explanation"},"Default: on. Transfers fine shading detail from the raw mesh to the export. Turn it off if it carries unwanted bumps; this keeps the geometry and color, but loses some fine shading detail. Texture and normal-map values are pixel sizes. Larger maps cost memory and disk space."),
                el("details",{class:"advanced"},el("summary",{},"Surface & texture options"),
                    this.field("Bake ambient occlusion",s,"bake_ao","checkbox"),
                    this.field("Ambient occlusion map",s,"ao_resolution","number",{min:64,max:8192,step:64}),
                    this.field("Remesh (can change thin details)",s,"remesh","checkbox"),
                    this.field("Smoothing iterations",s,"smoothing","number",{min:0,max:20}),
                    el("label",{},"UV unwrap",this.select({adaptive:"Adaptive — CPU",pec:"Parallel edge collapse — GPU"},s.uv_method,v=>s.uv_method=v,"UV unwrap")),
                    el("p",{class:"hint settings-explanation"},"Ambient occlusion adds contact shading to a separate texture; its size controls detail. New assets start with remeshing enabled to clean the surface before triangle reduction. It can alter thin parts or small openings; turn it off when those details need preserving. Existing assets keep their saved choice. Smoothing softens uneven geometry. UV unwrap lays out the surface for textures; the GPU option needs additional VRAM."))));
            content.append(this.section("Files & cleanup","Images, master files and game exports stay in your asset folder. Only this workflow’s completed temporary files are eligible for cleanup.",
                el("p",{class:"path"},this.server?.root || "Comfy output / AssetWorkshop"),
                this.field("Temporary cache limit (GB)",s,"cache_limit_gb","number",{min:1,max:500}),
                el("p",{class:"hint"},"A stage will not start if this workflow's temporary files already exceed this limit. Completed job caches are removed automatically. Images, models and exports are retained."),
                el("div",{class:"row"},this.button("Open library folder",()=>request("/open-folder",{kind:"library"})),
                    this.button("Clean completed temporary files",async()=>{
                        await this.persist();const result=await request(`/assets/${a.id}/cleanup`,{});
                        this.status(`Removed ${result.removed} completed temporary folders. Saved work is retained.`);
                    },busy)),
                el("details",{class:"advanced"},el("summary",{},"Change library location"),
                    el("p",{class:"hint"},"This selects a library. It does not move or delete existing assets."),
                    this.field("Library folder",this.properties,"libraryPath"),
                    this.button("Use this library",async()=>{
                        if(this.asset.id) await this.persist();
                        await request("/root",{root:this.properties.libraryPath});
                        this.properties.asset=defaultAsset();
                        this.lastJob=null;this.suggestion=null;this.previousPrompt=undefined;
                        this.historyLoaded=false;this.historyAssets=[];this.historyPage=null;
                        this.historyAssetId=null;this.historyError="";
                        this.lastDeleted=null;this.deletedHistory=null;
                        await this.resetStageGraph();
                        await this.refreshStatus();
                        this.status("Library changed. Open History to reuse a saved job.");
                        this.setTab("Design");
                    },busy || this.historyBusy))));
            content.append(el("div",{class:"row"},this.primary("Save settings",()=>this.saveSettings())));
            if(a.jobs.length) content.append(el("details",{class:"advanced"},el("summary",{},"Recent operations"),
                ...a.jobs.slice(-8).reverse().map(job=>el("p",{class:"hint"},`${labels[job.stage] || job.stage}: ${job.status}${job.error ? ` — ${job.error}` : ""}`))));
        }
        async openLibrary() {
            this.setTab("History");
            await this.loadHistory();
        }
        async loadHistory(assetId=this.historyAssetId || this.asset.id,offset=0) {
            this.historyBusy=true; this.historyError=""; this.render();
            try {
                this.historyAssets=await request("/assets");
                this.historyAssetId=this.historyAssets.some(a=>a.id===assetId)?assetId:this.historyAssets[0]?.id;
                this.historyPage=this.historyAssetId ?
                    await request(`/assets/${this.historyAssetId}/history?offset=${offset}&limit=12`) : null;
                this.historyLoaded=true;
            } catch(error) {this.historyError=error.message;this.historyLoaded=true;}
            finally {this.historyBusy=false;this.render();}
        }
        async openAsset(assetId,job=null) {
            if(operation()) throw Error("Finish or stop the current operation before reusing saved parameters.");
            if(this.asset.id) await this.persist();
            const asset=job ? await request(`/assets/${assetId}/restore`,{job}) : await request(`/assets/${assetId}`);
            this.properties.asset=asset; this.lastJob=null; this.suggestion=null; this.memoryInfo=null;
            await this.resetStageGraph();
            this.status("Saved description, model settings, seed and associated images loaded. Nothing generates automatically.");
            this.setTab("Design");
            await this.persist();
        }
        confirmDelete(asset) {
            const dialog=el("dialog",{},el("h3",{},`Delete ${asset.name}?`),
                el("p",{},"This removes the asset and all its versions from History. Its images, parameters and mesh files move together to the library’s trash folder. Models are kept."),
                el("div",{class:"row"},
                    this.button("Cancel",()=>dialog.close(),false,"quiet"),
                    this.button("Delete asset",async()=>{
                        if(operation()) throw Error("Finish or stop the current operation before deleting assets.");
                        this.lastDeleted=await request(`/assets/${asset.id}`,null,"DELETE");
                        if(this.asset.id===asset.id) {
                            this.properties.asset=defaultAsset();this.lastJob=null;this.suggestion=null;
                            await api.storeUserData("workflows/Mumblebox Creator.json",app.graph.serialize());
                        }
                        dialog.close(); await this.loadHistory(null);
                        this.status(`${asset.name} moved to trash. Use Undo deletion to put it back.`);
                    },!!operation(),"danger")));
            this.root.append(dialog);dialog.addEventListener("close",()=>dialog.remove());dialog.showModal();
        }
        confirmClearHistory() {
            const ids=(this.historyAssets || []).map(a=>a.id);
            const dialog=el("dialog",{},el("h3",{},"Clear all history?"),
                el("p",{},"Are you sure you want to clear all history? This deletes every saved job in History, including its stored images, meshes and generation parameters."),
                el("p",{class:"hint"},"Deleted jobs are moved to local trash. You can undo this deletion here."),
                el("div",{class:"row"},this.button("Cancel",()=>dialog.close()),
                    this.button("Delete all history",async()=>{
                        const result=await request("/history/clear",{assets:ids});
                        this.deletedHistory=result.deleted;
                        this.lastDeleted=null;
                        this.properties.asset=defaultAsset();this.lastJob=null;this.suggestion=null;
                        dialog.close();
                        await api.storeUserData("workflows/Mumblebox Creator.json",app.graph.serialize());
                        await this.loadHistory(null);
                        this.status("History cleared. Use Undo clear history to restore the deleted jobs.");
                    },!!operation(),"danger")));
            this.root.append(dialog);dialog.addEventListener("close",()=>dialog.remove());dialog.showModal();
        }
        renderHistory(content) {
            content.append(el("div",{class:"step-heading"},
                el("div",{},el("h3",{},"History"),
                    el("p",{class:"hint"},"Reuse a job’s description, model settings, seed and associated images in Step 1. Nothing generates automatically.")),
                el("div",{class:"row"},this.button("Refresh History",()=>this.loadHistory(),!!this.historyBusy,"quiet"),
                    this.button("Clear history",()=>this.confirmClearHistory(),!!operation() || !!this.historyBusy || !this.historyAssets?.length,"danger"))));
            if(this.deletedHistory?.length) content.append(el("div",{class:"row"},
                this.button("Undo clear history",async()=>{
                    while(this.deletedHistory.length) {
                        await request(`/trash/${this.deletedHistory[0].token}/restore`,{});
                        this.deletedHistory.shift();
                    }
                    await this.loadHistory();
                    this.status("Deleted jobs restored to History.");
                },!!operation(),"quiet")));
            if(this.lastDeleted) content.append(el("div",{class:"row"},
                el("span",{},`${this.lastDeleted.name} was moved to trash.`),
                this.button("Undo deletion",async()=>{
                    await request(`/trash/${this.lastDeleted.token}/restore`,{});
                    this.lastDeleted=null;await this.loadHistory();
                    this.status("Deleted job restored to History.");
                },!!operation(),"quiet")));
            if(!this.historyLoaded && !this.historyBusy) {
                this.historyBusy=true;
                queueMicrotask(()=>this.loadHistory());
            }
            if(this.historyBusy) content.append(el("p",{class:"hint"},"Loading saved assets…"));
            if(this.historyError) content.append(el("p",{class:"error"},this.historyError));
            const assets=this.historyAssets || [];
            if(!assets.length && !this.historyBusy) content.append(el("p",{class:"empty"},"No saved assets yet. Create or upload an image in Step 1 to start your history."));
            const list=el("div",{class:"history-list"});
            for(const asset of assets) list.append(el("article",{class:"history-asset"},
                asset.thumbnail ? el("figure",{class:"image-preview"},
                    el("img",{src:this.fileURL(asset.thumbnail,asset.id),alt:asset.name,loading:"lazy"}),
                    el("figcaption",{},this.downloadImage(asset.thumbnail,asset.name,asset.id))) : el("div",{class:"empty"},"No image"),
                el("div",{},el("h4",{},asset.name),
                    el("p",{class:"hint"},`${new Date(asset.updated*1000).toLocaleString()} · ${profileLabels[asset.profile] || asset.profile}`),
                    el("p",{class:"history-description"},asset.prompt || "No description saved."),
                    asset.seed!=null?el("p",{class:"hint"},`Seed used: ${asset.seed}`):null,
                    el("div",{class:"row"},
                        this.button("Reuse parameters",()=>this.openAsset(asset.id),!!operation()),
                        this.button("Show generations",()=>this.loadHistory(asset.id),!!this.historyBusy,"quiet"),
                        this.button("Delete asset",()=>this.confirmDelete(asset),!!operation(),"quiet")),
                    el("a",{class:"text-link",href:this.fileURL("asset.json",asset.id),download:`${asset.name}-parameters.json`},"Download asset parameters"))));
            content.append(list);
            const page=this.historyPage, selected=assets.find(a=>a.id===this.historyAssetId);
            if(!page || !selected) return;
            content.append(el("section",{class:"section"},el("h3",{},`${selected.name} — saved generations`),
                el("p",{class:"hint"},"Each completed generation keeps the inputs that produced it. Restore a generation to reuse its description, actual seed and parameters.")));
            for(const entry of page.entries) content.append(el("article",{class:"history-generation"},
                entry.thumbnail?el("figure",{class:"image-preview"},el("img",{src:this.fileURL(entry.thumbnail,selected.id),alt:`${selected.name} ${entry.slot || "generation"}`,loading:"lazy"}),
                    el("figcaption",{},this.downloadImage(entry.thumbnail,`${selected.name}-${entry.slot || "generation"}`,selected.id))):null,
                el("div",{},el("h4",{},`${entry.image_edit?"Selected-area edit":labels[entry.stage] || entry.stage} · ${new Date(entry.created*1000).toLocaleString()}`),
                    el("p",{class:"hint"},`${profileLabels[entry.profile] || entry.profile} · Seed used: ${entry.seed}`),
                    el("p",{class:"history-description"},entry.prompt),
                    el("details",{},el("summary",{},"View saved parameters"),el("pre",{},JSON.stringify(entry.parameters,null,2))),
                    el("div",{class:"row"},
                        this.button("Reuse parameters",()=>this.openAsset(selected.id,entry.id),!!operation() || !entry.can_restore),
                        entry.parameters_file?el("a",{class:"download",href:this.fileURL(entry.parameters_file,selected.id),download:`${selected.name}-${entry.id}-parameters.json`},"Download parameters"):null),
                    !entry.can_restore?el("p",{class:"hint"},"The input record for this older generation is missing. Its saved image is still available."):null)));
            if(!page.entries.length) content.append(el("p",{class:"hint"},"This asset has no completed generations yet."));
            if(page.total>page.limit) {
                const previous=this.button("Previous generations",()=>this.loadHistory(selected.id,Math.max(0,page.offset-page.limit)),page.offset===0 || this.historyBusy,"quiet");
                const next=this.button("More generations",()=>this.loadHistory(selected.id,page.offset+page.limit),page.offset+page.limit>=page.total || this.historyBusy,"quiet");
                previous.title=page.offset===0?"You are on the first page.":"";
                next.title=page.offset+page.limit>=page.total?"You are on the last page.":"";
                content.append(el("div",{class:"row spread"},previous,
                    el("span",{class:"hint"},`${page.total} saved generations`),next));
            } else content.append(el("p",{class:"hint"},`Showing all ${page.total} saved generations.`));
        }
        render() {
            stylesheet();
            const a=this.asset;
            if(!operation() && this.properties.pendingSettings && this.properties.pendingSettings.asset===a.id) {
                const pending=this.properties.pendingSettings;
                for(const [key,value] of Object.entries(pending.values))
                    if(JSON.stringify(value)!==JSON.stringify(pending.original[key])) a.settings[key]=value;
                delete this.properties.pendingSettings;
            }
            if(["Mesh","Export"].includes(this.properties.tab)) this.properties.tab="Result";
            if(this.properties.tab==="Resources") this.properties.tab="Settings";
            this.viewer?.remove(); this.viewer=null; this.viewerResize?.disconnect();
            this.progressBar=null; this.progressLabel=null;
            const scroll=this.root.scrollTop;
            const focusedTab=this.root.contains(document.activeElement) && document.activeElement?.getAttribute("role")==="tab"
                ? document.activeElement.id : null;
            this.root.replaceChildren();
            this.stats=el("span",{"aria-live":"off"},"Connecting to local resource status…");
            const resourceBar=el("div",{class:"stats"},this.stats,this.unloadButton());
            this.notice=el("div",{class:`status${this.messageError?" error":""}`,role:"status"},this.message || "");
            const tabs=[["Design","1","Design your asset"],["Views","2","Other angles"],["Result","3","Your 3D asset"],["History","","History"],["Settings","","Settings"]];
            const nav=el("nav",{class:"tabs",role:"tablist","aria-label":"Asset creation steps"});
            for(const [key,num,label] of tabs) nav.append(el("button",{
                type:"button",role:"tab",id:`mumblebox-tab-${key}`,"aria-selected":this.properties.tab===key,
                "aria-controls":"mumblebox-tab-panel",tabIndex:this.properties.tab===key?0:-1,
                onclick:()=>this.setTab(key),onkeydown:e=>{
                    if(!["ArrowLeft","ArrowRight","Home","End"].includes(e.key))return;
                    e.preventDefault(); const i=tabs.findIndex(t=>t[0]===key);
                    const next=e.key==="Home"?0:e.key==="End"?tabs.length-1:(i+(e.key==="ArrowRight"?1:tabs.length-1))%tabs.length;
                    this.setTab(tabs[next][0]);this.root.querySelector(`#mumblebox-tab-${tabs[next][0]}`).focus();
                }},num?el("span",{class:"tab-number"},num+" "):null,label));
            this.root.append(resourceBar,el("header",{class:"brand"},
                el("div",{},el("h2",{},"Mumblebox Creator"),el("p",{class:"hint"},"Turn images and ideas into 3D assets."),
                    el("span",{class:"publisher"},"By Mumblepress"))),nav,this.notice);
            const content=el("main",{class:"content",id:"mumblebox-tab-panel",role:"tabpanel","aria-labelledby":`mumblebox-tab-${this.properties.tab}`});
            this.root.append(content);
            if(operation() || this.lastJob) content.append(this.renderProgress());
            this.root.oninput=()=>this.updateInputButtons();
            const renderers={Design:"renderDesign",Views:"renderViews",Result:"renderResult",History:"renderHistory",Settings:"renderResources"};
            this[renderers[this.properties.tab] || "renderDesign"](content);
            if(operation() && this.properties.tab!=="Settings")
                for(const input of content.querySelectorAll("input,textarea,select")) {
                    input.disabled=true;
                    input.title="These inputs are in use. Wait for the current operation or use Stop before changing them.";
                }
            content.append(el("footer",{},el("span",{class:"hint"},a.id ? `${a.name} · Saved locally` : "Start with an image or a description"),
                this.button("Return to top",()=>this.root.scrollTo({top:0,behavior:"instant"}),false,"quiet")));
            this.root.scrollTop=scroll;
            this.refreshStatus(); this.updateProgress(); this.updateInputButtons();
            if(focusedTab) this.root.querySelector(`#${focusedTab}`)?.focus({preventScroll:true});
        }
    };
}
