// Pure presentation policy. A file on disk is not a resident model.
export const FIRST_USE_MESSAGE = "The model is downloading on first use. This may take some time but only happens once per model.";

export function utilization(used, total) {
    return Number.isFinite(used) && Number.isFinite(total) && total > 0
        ? Math.min(1, Math.max(0, used / total)) : null;
}

export function loadedState(status) {
    if(Array.isArray(status?.model_residency)){
        const rows=status.model_residency;
        const loaded=rows.filter(r=>r.state==='loaded');
        const offloaded=rows.filter(r=>r.state==='offloaded');
        const unknown=rows.filter(r=>r.state==='unknown');
        const describe=items=>items.map(r=>r.name+(r.device?' ('+r.device+')':'')).join(', ');
        if(loaded.length||status.helper_loaded)return {state:'loaded',label:loaded.length?describe(loaded)+' · models loaded':'Description model loaded'};
        if(unknown.length)return {state:'unknown',label:describe(unknown)+' · model residency unknown'};
        if(offloaded.length)return {state:'offloaded',label:describe(offloaded)+' · models offloaded to RAM'};
        return {state:'empty',label:'No models loaded'};
    }
    if (!status || !Number.isFinite(status.loaded_models)) return {state:"unknown", label:"Model state unavailable"};
    const loaded = status.loaded_models > 0 || status.helper_loaded === true;
    return {state:loaded?"loaded":"empty", label:loaded?"Models loaded":"No models loaded"};
}

export function activityState(status) {
    if (!status) return {busy:false, label:"Status unavailable", unknown:true};
    const manual = status.resource_download?.status === "running";
    const download = (manual?status.resource_download:status.download) || {};
    const preparing=status.workflow_activity?.find(r=>r.dependency);
    if(preparing?.dependency){
        const d=preparing.dependency;
        return {busy:true,label:d.phase==='downloading'?'Downloading required models':'Preparing required models',
            detail:d.phase==='downloading'?FIRST_USE_MESSAGE:d.name||d.phase,
            fraction:utilization(d.bytes,d.total)};
    }
    if (["running", "downloading", "verifying"].includes(download.status))
        return {busy:true, label:download.status==="verifying"?"Verifying model files":"Downloading model", detail:manual?"Downloading the selected resource.":FIRST_USE_MESSAGE,
            fraction:utilization(download.bytes ?? download.downloaded ?? download.completed_bytes, download.total ?? download.total_bytes)};
    if (status.resource_cleanup?.status === "releasing") return {busy:true, label:"Unloading models"};
    if (status.running || status.model_residency?.some(r=>['loaded','unknown'].includes(r.state)&&r.name!=='ComfyUI') || status.description_helper?.running) return {busy:true, label:status.description_helper?.running?status.description_helper.phase:"Workflow running"};
    if (download.status === "failed") return {busy:false, label:download.error || "Model download failed", error:true};
    if (download.status === "paused") return {busy:false, label:"Model download paused"};
    return {busy:false, label:"Ready"};
}
