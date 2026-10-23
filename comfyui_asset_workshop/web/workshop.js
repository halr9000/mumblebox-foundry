// All stage graphs are loaded into the existing Comfy canvas before submission.
const { app } = await import(`${location.origin}/scripts/app.js`);
const { api } = await import(`${location.origin}/scripts/api.js`);
const TYPE = "AssetWorkshop/Controls";
const PREFIX = "/asset-workshop";
const interfaceURL = new URL("./creator.js", import.meta.url);
interfaceURL.search = new URL(import.meta.url).search;
const { createInterface } = await import(interfaceURL);
const singleURL = new URL("./single-image.js", import.meta.url);
singleURL.search = new URL(import.meta.url).search;
const {renderSingleControls} = await import(singleURL);
// Comfy's reactive property wrappers cannot be passed to structuredClone.
const copySettings = value => JSON.parse(JSON.stringify(value));
const profileLabels = {
    qwen21: "Qwen Image 2.1 7B",
    qwen2511: "Qwen Image Edit 2511",
    klein_base: "FLUX.2 Klein 9B — base",
    klein_distilled: "FLUX.2 Klein 9B — distilled",
    klein_kv: "FLUX.2 Klein 9B — KV",
    klein4: "FLUX.2 Klein 4B — lighter model",
    klein4_base: "FLUX.2 Klein 4B — base for depth guidance",
    flux3_base: "FLUX 3 Image Klein — base",
    flux3_distilled: "FLUX 3 Image Klein — distilled",
};

function element(tag, attrs = {}, ...children) {
    const result = document.createElement(tag);
    for (const [key, value] of Object.entries(attrs)) {
        if (key.startsWith("on")) result.addEventListener(key.slice(2), value);
        else if (key === "class") result.className = value;
        else if (key in result) result[key] = value;
        else result.setAttribute(key, value);
    }
    for (const child of children.flat()) {
        if (child != null) result.append(child instanceof Node ? child : document.createTextNode(String(child)));
    }
    return result;
}

async function request(path, body, method = body ? "POST" : "GET") {
    // Preparation and the assistant can legitimately take minutes. Short requests
    // still need a bounded failure so a lost connection cannot freeze the controls.
    const longRequest=/\/(prepare|describe|release)$/.test(path);
    let response, data;
    try { response = await api.fetchApi(PREFIX + path, {
        method,
        ...(!longRequest ? {signal:AbortSignal.timeout(30000)} : {}),
        ...(body ? { headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : {}),
    });
        data = await response.json();
    } catch(error) {
        const failure = Error(error.name==="TimeoutError" || error.name==="AbortError"?
            "Comfy did not respond within 30 seconds. Your inputs are retained. Check its connection before retrying.":
            `Could not reach Comfy: ${error.message}. Your inputs are retained.`);
        failure.connectionError = error.name !== "SyntaxError";
        throw failure;
    }
    if (response.status === 404) {
        const error = Error("Restart Comfy when ready to activate the saved Asset Workshop extension.");
        error.status = 404;
        throw error;
    }
    if (!response.ok) {
        const error=Error(data.error || response.statusText);
        error.status=response.status;
        throw error;
    }
    return data;
}

function defaultAsset() {
    const labels = ["Front", "Front right", "Right", "Rear right", "Back",
        "Rear left", "Left", "Front left", "Upper front", "Lower rear"];
    return {
        name: "Untitled asset", tags: [], prompt: "", profile: "qwen21", category:"props", references: [], loras: [],
        design: { revisions: [], current: null, approved: null },
        views: labels.map((name, i) => ({
            id: `view_${String(i + 1).padStart(2, "0")}`, name, enabled: true,
            azimuth: i < 8 ? i * 45 : i === 8 ? 0 : 180,
            elevation: i < 8 ? 0 : i === 8 ? 60 : -30, fov: 20,
            camera_source: "generated_estimate", correction: "", revisions: [], current: null, approved: null,
        })),
        settings: { resolution: 1024, seed: 0, requested_seed: -1, steps: null, cfg: null, camera_lora: false,
            shape_resolution: 1536, mesh_backend: "pixal_multiview", master_faces: 700000,
            game_faces: 100000, master_texture: 4096, game_texture: 2048,
            normal_resolution: 2048, ao_resolution: 1024, bake_ao: true, bake_normal: true, crease_angle: 45, remesh: true,
            smoothing: 0, tiled_vae: true, cache_device: "cpu", cache_precision: "default",
            extra_vram_headroom_gb: 0, image_precision: "native", cache_limit_gb: 20, min_ram_free_gb: 8,
            min_vram_free_gb: 1.5, uv_method: "pec", asset_height: 1,
            memory_overrides:[],release_between_stages:true,
            angle_profile:"same",angle_route:"references",angle_steps:null,angle_cfg:null,guide_strength:1,angle_camera_lora:false },
        masters: [], exports: [], jobs: [],
    };
}

function addStyles() {
    if (document.getElementById("asset-workshop-style")) return;
    document.head.append(element("style", { id: "asset-workshop-style" }, `
      .aw { color:#e8eef1;background:#172024;font:14px/1.45 system-ui;padding:16px;box-sizing:border-box;
        width:100%;height:100%;overflow:auto;user-select:text;pointer-events:auto;border-radius:8px; }
      .aw * { box-sizing:border-box } .aw h2 {margin:0 0 5px;font-size:21px;color:#7ee3ce}
      .aw h3 {margin:14px 0 8px;font-size:16px} .aw p {margin:8px 0}
      .aw input,.aw select,.aw textarea {background:#10181c;color:#f4f7f9;border:1px solid #56707a;
        border-radius:4px;padding:7px;font:inherit;max-width:100%}
      .aw input[type=number] {width:105px} .aw textarea {width:100%;min-height:72px;resize:vertical}
      .aw input[type=checkbox] {accent-color:#7ee3ce} .aw label {display:flex;gap:8px;align-items:center;margin:6px 0}
      .aw button {border:1px solid #558378;background:#254a42;color:#f4fffb;padding:8px 11px;
        border-radius:5px;cursor:pointer;font:inherit}
      .aw button:disabled {opacity:.45;cursor:default} .aw button.selected {background:#357664}
      .aw .row {display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:8px 0}
      .aw .muted {color:#adc1c8;font-size:12px} .aw .status {padding:9px;border-left:3px solid #7ee3ce;
        background:#223238;white-space:pre-wrap;margin:10px 0}
      .aw .stats {position:sticky;top:-16px;z-index:5;background:#10181c;padding:8px;font-size:13px}
      .aw .cards {display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
      .aw .card {padding:12px;border:1px solid #48616a;border-radius:6px;background:#1d2a30}
      .aw .card img {display:block;width:100%;height:210px;object-fit:contain;background:#10181c;border-radius:4px}
      .aw .empty {height:110px;display:grid;place-items:center;color:#8da7b0;background:#10181c}
      .aw .approved {border-color:#7ee3ce} .aw a {color:#95dfed} .aw details {margin:10px 0}
      .aw pre {white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px}
    `));
}

class LegacyWorkshop extends LiteGraph.LGraphNode {
    constructor() {
        super("Mumblebox Creator");
        this.isVirtualNode = true;
        this.properties = { asset: defaultAsset(), tab: "Design" };
        this.size = [1060, 900];
        this.message = "Describe the asset or load an image, then choose a stage action. Nothing runs automatically.";
        this.root = element("div", { class: "aw" });
        for (const event of ["pointerdown", "pointerup", "wheel", "keydown"]) {
            this.root.addEventListener(event, ev => ev.stopPropagation());
        }
        this.addDOMWidget("workshop", "ASSET_WORKSHOP", this.root, {
            serialize: false, hideOnZoom: false, getMinHeight: () => 820,
            getHeight: () => 850,
        });
        const removeWidget = this.onRemoved;
        const configureWidget = this.onConfigure;
        this.onRemoved = (...args) => {
            clearInterval(this.timer);
            this.root.remove();
            removeWidget?.apply(this, args);
        };
        this.onConfigure = (...args) => {
            configureWidget?.apply(this, args);
            this.render();
            this.refreshStatus();
        };
        this.timer = setInterval(() => this.refreshStatus(), 3000);
        addStyles();
        this.render();
        this.refreshStatus();
    }
    get asset() { return this.properties.asset; }
    changed() {
        this.graph?.setDirtyCanvas(true, true);
    }
    moveItem(collection, item, delta) {
        const index = collection.indexOf(item);
        const target = index + delta;
        if (index < 0 || target < 0 || target >= collection.length) return;
        collection.splice(index, 1);
        collection.splice(target, 0, item);
        this.changed();
        this.render();
    }
    status(text) {
        this.message = text;
        if (this.notice) this.notice.textContent = text;
    }
    button(label, action, disabled = false) {
        return element("button", { disabled, onclick: async () => {
            if (this.busy) return;
            this.busy = true;
            try { await action(); } catch (error) { this.status(error.message); }
            finally { this.busy = false; }
        } }, label);
    }
    select(values, current, change) {
        return element("select", { onchange: e => { change(e.target.value); this.changed(); } },
            Object.entries(values).map(([value, label]) => element("option", { value, selected: value === current }, label)));
    }
    field(label, object, key, type = "text", extra = {}) {
        const input = element("input", { type, ...extra,
            ...(type === "checkbox" ? { checked: !!object[key] } : { value: object[key] ?? "" }),
            onchange: e => {
                object[key] = type === "checkbox" ? e.target.checked : type === "number" ?
                    (e.target.value === "" ? null : Number(e.target.value)) : e.target.value;
                this.changed();
            } });
        return element("label", {}, label, input);
    }
    preview(slot) {
        const revision = slot.revisions?.find(r => r.id === slot.current);
        if (!revision || !this.asset.id) return element("div", { class: "empty" }, "No image yet");
        return element("img", {
            src: `${PREFIX}/file/${this.asset.id}?path=${encodeURIComponent(revision.file)}&v=${revision.id}`,
            alt: slot.name || "Approved design",
        });
    }
    async persist() {
        if (!this.asset.id) {
            const local = copySettings(this.asset);
            const created = await request("/assets", { name: local.name });
            this.properties.asset = { ...created, ...local, id: created.id };
        }
        this.properties.asset = await request(`/assets/${this.asset.id}`, this.asset, "PATCH");
        this.changed();
        return this.asset;
    }
    async reload() {
        if (this.asset.id) this.properties.asset = await request(`/assets/${this.asset.id}`);
        this.changed();
        this.render();
    }
    async refreshStatus() {
        if (!this.graph || document.hidden) return;
        try {
            const data = await request("/status");
            this.server = data;
            if (this.stats) {
                const gb = value => (value / 1073741824).toFixed(1);
                this.stats.textContent = `CPU ${data.cpu_percent.toFixed(0)}% · RAM ${gb(data.ram_used)} / ${gb(data.ram_total)} GB · ` +
                    `VRAM ${gb(data.vram_used)} / ${gb(data.vram_total)} GB · Disk ${gb(data.disk_free)} GB free · ${data.running ? "Comfy job running" : "Idle"} · ` +
                    (data.download?.status === "running" ? `${data.download.phase} ${gb(data.download.bytes || 0)} / ${gb(data.download.total || 0)} GB` :
                        data.download?.status === "failed" ? `Download failed: ${data.download.error}` : "No active download");
            }
            if (this.asset.id && this.lastJob && !data.running && !this.busy) {
                const updated = await request(`/assets/${this.asset.id}`);
                const job = updated.jobs.find(j => j.id === this.lastJob);
                if (job && ["complete", "failed", "cancelled", "interrupted"].includes(job.status)) {
                    this.properties.asset = updated;
                    this.lastJob = null;
                    this.status(job.status === "complete" ? "Stage finished and saved. Review it before continuing." : `${job.status}: ${job.error || "You can resume this stage."}`);
                    this.render();
                }
            }
        } catch (error) {
            if (this.stats) this.stats.textContent = error.status === 404 ?
                "Asset Workshop backend awaiting activation · restart Comfy when ready" :
                "Resource status unavailable · current queue status unknown";
        }
    }
    async stage(stage, slot = "design", action = "generate", run = true, edit = null) {
        await this.persist();
        this.status("Checking selected inputs, models and available memory…");
        const prepared = await request(`/assets/${this.asset.id}/prepare`, { stage, slot, action, ...(edit?{edit}:{}) });
        const properties = copySettings(this.properties);
        const position = [...this.pos];
        // The native graph is visible before an execution request is made.
        await app.reloadNodeDefs();
        // Reuse the active workflow tab instead of opening a tab for every stage.
        await app.loadApiJson(prepared.prompt, app.extensionManager?.workflow?.activeWorkflow || "Mumblebox Creator");
        const controller = LiteGraph.createNode(TYPE);
        controller.properties = properties;
        controller.pos = position;
        controller.lastJob = prepared.job.id;
        controller.message = prepared.summary + "\n" + prepared.bindings.join("\n");
        app.graph.add(controller);
        controller.render();
        for (const node of app.graph._nodes) {
            if (node !== controller) {
                node.pos[0] += 1150;
                node.pos[1] += 40;
            }
        }
        app.graph.extra.asset_workshop = { schema: 1, asset: this.asset.id, stage, job: prepared.job.id, automatic_mesh: false };
        app.canvas.ds.scale = .85;
        app.canvas.ds.offset = [20, 60];
        app.graph.setDirtyCanvas(true, true);
        await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
        await api.storeUserData("workflows/Mumblebox Creator.json", app.graph.serialize());
        await request(`/assets/${this.asset.id}/cleanup-previews`, {});
        if (run) {
            // Queue through the visible native frontend, preserving Comfy's preview events.
            try {
                const result = await api.queuePrompt(0, { output: prepared.prompt, workflow: app.graph.serialize() });
                try {
                    await request(`/assets/${this.asset.id}/queued`, { job: prepared.job.id, prompt_id: result.prompt_id });
                } catch(error) {
                    // Native on_prompt already records ownership. If the
                    // redundant acknowledgement loses its reply, confirm that
                    // exact job instead of stopping a healthy batch or requeueing.
                    const saved=await request(`/assets/${this.asset.id}`);
                    if(saved.jobs.find(job=>job.id===prepared.job.id)?.prompt_id!==result.prompt_id) throw error;
                }
                controller.status(prepared.summary + "\nRunning only this stage. Mesh generation always needs its own action.");
            } catch (error) {
                controller.status(`This stage was not confirmed queued: ${error.message}. Check the Comfy queue before retrying.`);
                throw error;
            }
        } else {
            controller.status(prepared.summary + "\nGraph ready. The normal Run button executes only this displayed stage.");
        }
        return controller;
    }
    async generateViews() {
        if (app.assetWorkshopSequence) throw Error("A view sequence is already active.");
        const sequence = { cancelled: false };
        app.assetWorkshopSequence = sequence;
        let controller = this;
        try {
            await controller.persist();
            const pending = controller.asset.views.filter(v => v.enabled && !v.current).map(v => v.id);
            if (!pending.length) { controller.status("All enabled cards have images. Use a card's Generate or Correct action to revise it."); return; }
            for (let index = 0; index < pending.length; index++) {
                if (sequence.cancelled) break;
                controller = await controller.stage("image", pending[index]);
                const jobId = controller.lastJob;
                controller.status(`Generating view ${index + 1} of ${pending.length}. Each result is saved; none is accepted automatically.`);
                while (!sequence.cancelled) {
                    await new Promise(resolve => setTimeout(resolve, 2000));
                    const asset = await request(`/assets/${controller.asset.id}`);
                    const job = asset.jobs.find(j => j.id === jobId);
                    if (job?.status === "complete") {
                        const state = await request("/status");
                        if (state.running) continue;
                        controller.properties.asset = asset;
                        controller.render();
                        break;
                    }
                    if (job && ["failed", "cancelled", "interrupted"].includes(job.status)) {
                        throw Error(`Stopped at ${pending[index]}: ${job.error || job.status}. Earlier views are saved.`);
                    }
                }
            }
            controller.status(sequence.cancelled ? "View sequence stopped. Earlier saved views remain available." :
                "View generation finished. Review and accept the images before making a mesh.");
        } finally {
            app.assetWorkshopSequence = null;
        }
    }
    async accept(slot, revision) {
        await this.persist();
        await request(`/assets/${this.asset.id}/approve`, { slot, revision });
        await this.reload();
    }
    renderDesign(content) {
        const asset = this.asset;
        content.append(
            this.button("Start over", async () => {
                if (this.asset.id) await this.persist();
                this.properties.asset = defaultAsset();
                this.properties.tab = "Design";
                this.lastJob = null;
                this.message = "Start here: describe the object below, or load an image to begin.";
                this.render();
                this.root.scrollTop = 0;
                this.changed();
            }),
            this.field("Asset name", asset, "name"),
            this.field("Tags (comma separated)", asset, "tags"),
            element("label", {}, "Image model", this.select(profileLabels, asset.profile, value => { asset.profile = value; this.render(); })),
            element("textarea", { placeholder: "Describe the object, its hidden details, materials and intended style…",
                value: asset.prompt, oninput: e => { asset.prompt = e.target.value; this.changed(); } }),
            element("p", { class: "muted" }, "References have stable IDs. Explain what each supplies. The selected model's actual input limit is checked before generation."),
            element("div", { class: "row" },
                this.button("Add reference images", () => this.upload("references")),
                this.button("Use my image as the design", () => this.upload("design")),
                this.button("Save asset", async () => { await this.persist(); this.status("Asset settings saved."); })),
        );
        const activeReferences = asset.references.filter(r => r.enabled);
        const limit = this.server?.profiles?.[asset.profile]?.references;
        content.append(element("p", { class: "muted" },
            `${activeReferences.length} active ingredient references${limit ? ` / ${limit} recipe slots` : ""}. Views also reserve an image slot for the approved design; correction reserves one more for the edit source.`));
        if (activeReferences.length) content.append(element("details", {},
            element("summary", {}, "Reference order sent to the model"),
            element("pre", {}, activeReferences.map((r, i) =>
                `${asset.profile === "qwen21" ? `<image${i + 1}>` : asset.profile.startsWith("flux3") ? `<ref_image_${i}>` : asset.profile.startsWith("qwen") ? `Picture ${i + 1}` : `Figure ${i + 1}`} = ${r.id}: ${r.role}. ${r.instructions}`).join("\n"))));
        for (const reference of asset.references) {
            const row = element("div", { class: "card" },
                this.field("Use", reference, "enabled", "checkbox"),
                element("strong", {}, reference.id),
                this.field("Role", reference, "role"),
                this.field("Instructions", reference, "instructions"),
                element("div", { class: "row" },
                    this.button("Move reference up", () => this.moveItem(asset.references, reference, -1)),
                    this.button("Move reference down", () => this.moveItem(asset.references, reference, 1))),
                this.button("Remove reference from this asset", () => {
                    asset.references = asset.references.filter(r => r.id !== reference.id); this.render(); this.changed();
                }));
            if (asset.id) row.prepend(element("img", { src: `${PREFIX}/file/${asset.id}?path=${encodeURIComponent(reference.file)}`, alt: reference.role }));
            content.append(row);
        }
        content.append(element("h3", {}, "Compatible LoRAs"));
        for (const lora of asset.loras) {
            content.append(element("div", { class: "card" },
                this.field("Use", lora, "enabled", "checkbox"),
                this.field("LoRA filename", lora, "name"),
                element("label", {}, "Family", this.select(profileLabels, lora.profile, v => lora.profile = v)),
                this.field("Strength", lora, "strength", "number", { step: .05, min: -2, max: 2 }),
                this.field("Trigger / instructions", lora, "trigger"),
                this.button("Move LoRA up", () => this.moveItem(asset.loras, lora, -1)),
                this.button("Move LoRA down", () => this.moveItem(asset.loras, lora, 1)),
                this.button("Remove LoRA", () => { asset.loras = asset.loras.filter(l => l !== lora); this.render(); })));
        }
        content.append(this.button("Add LoRA", () => {
            asset.loras.push({ name: "", profile: asset.profile, strength: 1, trigger: "", enabled: true });
            this.render(); this.changed();
        }), element("p", { class: "muted" }, "LoRAs must match the selected architecture. Ordered top to bottom. Camera LoRA is controlled under Views."),
        element("div", { class: "row" },
            this.button("Generate design", () => this.stage("image")),
            this.button("Show design graph only", () => this.stage("image", "design", "generate", false)),
            this.button("Download missing models", () => this.downloadModels())),
        element("h3", {}, "Design candidate"), this.preview(asset.design),
        this.revisionControls("design", asset.design));
    }
    revisionControls(id, slot) {
        const options = Object.fromEntries((slot.revisions || []).map(r => [r.id, `${new Date(r.created * 1000).toLocaleString()}${r.id === slot.approved ? " · accepted" : ""}`]));
        return element("div", { class: "row" },
            this.select(options, slot.current, v => { slot.current = v; this.render(); }),
            this.button("Accept this revision", () => this.accept(id, slot.current), !slot.current),
            this.button("Revert to accepted", async () => {
                if (slot.approved) await this.accept(id, slot.approved);
            }, !slot.approved));
    }
    renderViews(content) {
        const asset = this.asset;
        content.append(element("p", {}, "Review every included view. Correcting one card preserves the other cards. Camera angles from generated pictures are estimates."),
            this.field("Use compatible camera LoRA", asset.settings, "camera_lora", "checkbox"),
            element("div", { class: "row" },
                this.button("Generate missing views — sequentially", () => this.generateViews()),
                this.button("Adapt angles to selected camera LoRA", async () => {
                    await this.persist();
                    this.properties.asset = await request(`/assets/${asset.id}/camera-preset`, {});
                    this.render();
                }),
                this.button("Download camera LoRA", () => this.downloadModels(true)),
                this.button("Add view", () => {
                    const id = `view_${crypto.randomUUID().slice(0, 8)}`;
                    asset.views.push({ id, name: "Extra view", azimuth: 0, elevation: 0, fov: 20,
                        camera_source: "generated_estimate", enabled: true, correction: "", revisions: [], current: null, approved: null });
                    this.render(); this.changed();
                }),
                this.button("Review coverage", async () => {
                    await this.persist();
                    const review = await request(`/assets/${asset.id}/review`);
                    this.status(review.messages.join("\n"));
                })));
        const cards = element("div", { class: "cards" });
        for (const view of asset.views) {
            cards.append(element("div", { class: `card ${view.approved === view.current && view.approved ? "approved" : ""}` },
                this.field("Include in mesh", view, "enabled", "checkbox"),
                this.field("View name", view, "name"),
                this.preview(view),
                element("div", { class: "row" },
                    this.field("Orbit °", view, "azimuth", "number", { step: 1 }),
                    this.field("Elevation °", view, "elevation", "number", { min: -90, max: 90 }),
                    this.field("FOV °", view, "fov", "number", { min: 2, max: 169 })),
                element("p", { class: "muted" }, `Camera source: ${view.camera_source}. ${view.stale ? "Inputs changed; review needed." : ""}`),
                element("textarea", { placeholder: "Change only this view…", value: view.correction,
                    oninput: e => { view.correction = e.target.value; this.changed(); } }),
                this.field("Seed (blank uses asset seed)", view, "seed", "number", { min: 0, step: 1 }),
                element("div", { class: "row" },
                    this.button("Generate view", () => this.stage("image", view.id)),
                    this.button("Correct this view", () => this.stage("image", view.id, "correct"), !view.current),
                    this.button("Show view graph", () => this.stage("image", view.id, "generate", false)),
                    this.button("Load own view", () => this.upload(view.id))),
                this.revisionControls(view.id, view)));
        }
        content.append(cards);
    }
    renderMesh(content) {
        const asset = this.asset;
        content.append(element("label", {}, "Reconstruction",
            this.select({ pixal_multiview: "Pixal3D — all accepted enabled views",
                pixal_single: "Pixal3D — accepted design only", trellis2: "TRELLIS.2 — accepted design only" },
            asset.settings.mesh_backend, v => asset.settings.mesh_backend = v)),
        this.field("Shape resolution", asset.settings, "shape_resolution", "number", { min: 1024, max: 2048, step: 128 }),
        element("p", {}, `${asset.views.filter(v => v.enabled).length} views enabled. Multiview requires every enabled view accepted. Single-image routes use the accepted design explicitly.`),
        element("div", { class: "row" },
            this.button("Download missing 3D models", () => this.downloadModels(false, "mesh")),
            this.button("Prepare and preview images", () => this.stage("prepare")),
            this.button("Make mesh — save native master", () => this.stage("mesh")),
            this.button("Show mesh graph only", () => this.stage("mesh", "design", "generate", false))),
        element("h3", {}, "Saved native masters"));
        for (const master of [...asset.masters].reverse()) {
            content.append(element("div", { class: "card" },
                element("strong", {}, `${master.id}${master.stale ? " · older inputs" : ""}`),
                element("p", { class: "muted" }, "Raw geometry and native texture voxels are preserved. Finishing can resume without running the reconstruction model."),
                this.button("Build textured master", () => this.stage("master", master.id)),
                this.button(master.approved ? "Master accepted" : "Accept master for game export", async () => {
                    await request(`/assets/${asset.id}/approve-master`, { master: master.id }); await this.reload();
                })));
        }
    }
    renderExport(content) {
        const settings = this.asset.settings;
        content.append(element("p", {}, "Master and game files are saved separately. The raw mesh and texture voxels remain available for another export."),
            element("div", { class: "row" },
                this.button("Mechanical preset", () => { Object.assign(settings, { remesh: false, smoothing: 0, crease_angle: 45 }); this.render(); this.changed(); }),
                this.button("Organic shading preset", () => { Object.assign(settings, { remesh: false, smoothing: 0, crease_angle: 180 }); this.render(); this.changed(); })),
            element("div", { class: "row" },
                this.field("Master triangles", settings, "master_faces", "number", { min: 0, step: 10000 }),
                this.field("Game triangles", settings, "game_faces", "number", { min: 100, step: 100 })),
            element("div", { class: "row" },
                this.field("Master texture", settings, "master_texture", "number", { min: 64, max: 8192, step: 64 }),
                this.field("Game texture", settings, "game_texture", "number", { min: 64, max: 8192, step: 64 }),
                this.field("Normals", settings, "normal_resolution", "number", { min: 64, max: 8192, step: 64 }),
                this.field("AO", settings, "ao_resolution", "number", { min: 64, max: 8192, step: 64 })),
            this.field("Hard edge angle °", settings, "crease_angle", "number", { min: 0, max: 180 }),
            this.field("Bake separate ambient occlusion map", settings, "bake_ao", "checkbox"),
            this.field("Optional remesh (can alter thin details)", settings, "remesh", "checkbox"),
            this.field("Smoothing iterations (when remesh is enabled)", settings, "smoothing", "number", { min: 0, max: 20 }),
            element("label", {}, "UV unwrap", this.select({ adaptive: "Adaptive CPU", pec: "Parallel edge collapse GPU" },
                settings.uv_method, v => settings.uv_method = v)),
            this.field("Asset height in meters", settings, "asset_height", "number", { min: .001, step: .001 }),
            this.button("Make game export from accepted master", () => this.stage("game")));
        for (const output of [...this.asset.exports].reverse()) {
            content.append(element("div", { class: "card" },
                element("strong", {}, `${output.kind} · ${output.triangles.toLocaleString()} triangles${output.stale ? " · settings changed" : ""}`),
                element("p", {}, output.file),
                element("a", { href: `${PREFIX}/file/${this.asset.id}?path=${encodeURIComponent(output.file)}`, download: "" }, "Download GLB")));
        }
    }
    renderResources(content) {
        const settings = this.asset.settings;
        content.append(element("p", {}, `Library: ${this.server?.root || "Comfy output / AssetWorkshop"}`),
            this.button("Choose library path", async () => {
                const value = prompt("Absolute local library folder (existing files are not moved):", this.server?.root || "");
                if (value) { await request("/root", { root: value }); this.properties.asset = defaultAsset(); this.render(); }
            }),
            element("div", { class: "row" },
                this.field("Image size", settings, "resolution", "number", { min: 256, max: 2048, step: 32 }),
                this.field("Seed", settings, "seed", "number", { min: 0, step: 1 }),
                this.field("Steps (blank = model recipe)", settings, "steps", "number", { min: 1, max: 150 }),
                this.field("CFG (blank = model recipe)", settings, "cfg", "number", { min: 1, max: 15, step: .1 })),
            element("label", {}, "Image model precision", this.select({
                native: "Native recipe — INT8 / FP8", bf16: "BF16 model — available for Qwen 2.1 and FLUX 3"
            }, settings.image_precision || "native", v => settings.image_precision = v)),
            this.field("Tiled image VAE decode", settings, "tiled_vae", "checkbox"),
            element("label", {}, "Qwen 2.1 cache", this.select({ cpu: "CPU RAM", auto: "Automatic", gpu: "GPU VRAM", off: "Off (recompute)" },
                settings.cache_device, v => settings.cache_device = v)),
            element("label", {}, "Qwen 2.1 cache precision", this.select({ default: "Default — preserve precision", int8: "INT8", int4: "INT4" },
                settings.cache_precision, v => settings.cache_precision = v)),
            this.field("Extra VRAM headroom GB", settings, "extra_vram_headroom_gb", "number", { min: 0, max: 12, step: .5 }),
            element("p", { class: "muted" }, `Host reserve: ${this.server?.startup_vram_reserve_gb ?? "unknown"} GB. Extra headroom raises the diffusion sampler's memory estimate on the next stage, encouraging native model offload. It does not cap the process or change text-encoder/VAE memory. Host startup settings remain unchanged.`),
            this.field("Minimum free RAM before stage GB", settings, "min_ram_free_gb", "number", { min: 1, max: 60 }),
            this.field("Owned temporary-cache budget GB", settings, "cache_limit_gb", "number", { min: 1, max: 500 }),
            element("details", {},
                element("summary", {}, "Host startup headroom — requires launcher change and restart"),
                element("p", {}, `Active --vram-headroom: ${this.server?.startup_vram_headroom_gb ?? "unknown"} GB. Recorded request: ${this.server?.pending_vram_headroom_gb ?? "none"} GB.`),
                this.field("Requested startup headroom GB", this.properties, "startup_headroom_gb", "number", { min: 0, max: 12, step: .5 }),
                this.button("Record requested startup setting", async () => {
                    const result = await request("/startup-headroom", { gb: this.properties.startup_headroom_gb ?? 0 });
                    this.status(`${result.launch_argument}\n${result.instruction}`);
                }),
                element("p", { class: "muted" }, "This records a pending request. Apply the displayed argument in your launcher's settings before restarting. The workflow never edits the launcher or restarts Comfy automatically.")),
            element("div", { class: "row" },
                this.button("Save resource settings", async () => { await this.persist(); this.status("Settings saved for the next stage."); }),
                this.button("Release models (idle only)", async () => { await request("/release", {}); this.status("Idle Comfy model cache released."); }),
                this.button("Pause model download", async () => { await request("/download/pause", {}); this.status("Download will pause after its current chunk; resume keeps verified partial progress."); }),
                this.button("Clean completed job temporary files", async () => {
                    await this.persist(); const result = await request(`/assets/${this.asset.id}/cleanup`, {});
                    this.status(`Removed ${result.removed} owned temporary folders. Saved images, models and exports are retained.`);
                })),
            element("h3", {}, "Job history"),
            ...this.asset.jobs.slice(-12).reverse().map(job => element("div", { class: "row" },
                `${job.stage}: ${job.status}${job.error ? " — " + job.error : ""}`,
                this.button("Resume saved settings", async () => {
                    const result = await request(`/assets/${this.asset.id}/resume-info`, { job: job.id });
                    this.properties.asset = result.asset;
                    this.render();
                    this.status("Restored the saved stage settings. Starting its visible graph.");
                    return this.stage(result.stage, result.slot, result.action);
                }, !["failed", "cancelled", "interrupted"].includes(job.status)))));
    }
    async downloadModels(camera = false, stage = "image") {
        await this.persist();
        const needed = await request(`/assets/${this.asset.id}/models?camera=${camera ? "1" : "0"}&stage=${stage}`);
        if (!needed.missing.length) { this.status("Selected models are available."); return; }
        const names = needed.missing.map(m => `${m.name} — ${(m.size / 1073741824).toFixed(1)} GB\nLicense: ${m.license_url}`).join("\n");
        this.status(names);
        if (!confirm(`Download these model files? Review their licenses before accepting.\n\n${names}`)) return;
        await request(`/assets/${this.asset.id}/download`, { camera, stage, accept_licenses: true });
        this.status("Downloading verified files. Progress appears above. Generate after the download completes.");
    }
    upload(slot) {
        const picker = element("input", { type: "file", accept: "image/png,image/jpeg,image/webp", multiple: slot === "references" });
        picker.onchange = async () => {
            try {
                await this.persist();
                for (const file of picker.files) {
                    const data = new FormData();
                    data.append("image", file);
                    data.append("slot", slot);
                    const response = await api.fetchApi(`${PREFIX}/assets/${this.asset.id}/upload`, { method: "POST", body: data });
                    const result = await response.json();
                    if (!response.ok) throw Error(result.error);
                }
                await this.reload();
                this.status("Images saved in this asset. Describe each reference, or accept the loaded design/view.");
            } catch (error) { this.status(error.message); }
        };
        picker.click();
    }
    render() {
        // Older saved controls retain their values and gain only missing defaults.
        this.asset.settings = { ...defaultAsset().settings, ...this.asset.settings };
        this.asset.tags ??= [];
        if (this.properties.tab === "Resources") this.properties.tab = "Settings";
        this.root.replaceChildren();
        this.stats = element("div", { class: "stats" }, "Connecting to local resource status…");
        this.notice = element("div", { class: "status" }, this.message);
        this.root.append(this.stats, element("h2", {}, "Mumblebox Creator"),
            element("p", { class: "muted" }, "Turn images and ideas into 3D assets. · By Mumblepress"),
            element("div", { class: "row" },
                this.button("Open saved asset", async () => {
                    const assets = await request("/assets");
                    if (!assets.length) { this.status("No saved assets in this library yet."); return; }
                    const selected = prompt(assets.map((a, i) => `${i + 1}. ${a.name}`).join("\n"), "1");
                    const found = assets[Number(selected) - 1];
                    if (found) { this.properties.asset = await request(`/assets/${found.id}`); this.render(); }
                }),
                this.button("Save workflow", async () => {
                    await api.storeUserData("workflows/Asset Workshop.json", app.graph.serialize());
                    this.status("Workflow saved as Asset Workshop.");
                }),
                this.button("Cancel my current job", async () => {
                    if (app.assetWorkshopSequence) app.assetWorkshopSequence.cancelled = true;
                    if (!this.asset.id) return;
                    await request(`/assets/${this.asset.id}/cancel`, {});
                    this.status("Cancellation requested for this asset's job only.");
                })),
            element("div", { class: "row" }, ["Design", "Views", "Mesh", "Export", "Settings"].map(tab =>
                element("button", { class: this.properties.tab === tab ? "selected" : "", onclick: () => {
                    this.properties.tab = tab; this.render(); this.changed();
                } }, tab === "Design" ? "Design Asset" : tab))),
            this.notice);
        const content = element("div");
        this.root.append(content);
        const renderers = { Design: "renderDesign", Views: "renderViews", Mesh: "renderMesh", Export: "renderExport", Settings: "renderResources" };
        this[renderers[this.properties.tab] || "renderDesign"](content);
        this.refreshStatus();
    }
}

const LegacyCreator = createInterface(LegacyWorkshop, { app, api, request, element, defaultAsset, PREFIX, TYPE, profileLabels });
class Workshop extends LegacyCreator {
    constructor() {
        super();
        const removed=this.onRemoved;
        this.onRemoved=(...args)=>{
            if(!this.singleControls?.transferring)this.singleControls?.dispose();
            removed?.apply(this,args);
        };
    }
    render() {
        if(this.properties.asset_workshop_mode==="single_image_agent") return renderSingleControls(this);
        return super.render();
    }
    refreshStatus() {
        if(this.properties.asset_workshop_mode==="single_image_agent") return;
        return super.refreshStatus();
    }
}

if (!globalThis.__assetWorkshopRegistered) app.registerExtension({
    name: "AssetWorkshop.StagedWorkflow",
    registerCustomNodes() {
        if (!LiteGraph.registered_node_types[TYPE]) LiteGraph.registerNodeType(TYPE, Workshop);
    },
    setup() {
        if (!LiteGraph.registered_node_types[TYPE]) LiteGraph.registerNodeType(TYPE, Workshop);
    },
});
globalThis.__assetWorkshopRegistered = true;
// Also supports an explicit live preview while the backend extension awaits restart.
if (!LiteGraph.registered_node_types[TYPE]) LiteGraph.registerNodeType(TYPE, Workshop);
export { Workshop };
