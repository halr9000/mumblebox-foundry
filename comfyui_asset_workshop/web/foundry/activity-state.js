// Pure presentation policy. A file on disk is not a resident model.
export const FIRST_USE_MESSAGE = "The model is downloading on first use. This may take some time but only happens once per model.";

export function utilization(used, total) {
    return Number.isFinite(used) && Number.isFinite(total) && total > 0
        ? Math.min(1, Math.max(0, used / total)) : null;
}

export function loadedState(status) {
    if (!status || !Number.isFinite(status.loaded_models)) return {state:"unknown", label:"Model state unavailable"};
    const loaded = status.loaded_models > 0 || status.helper_loaded === true;
    return {state:loaded?"loaded":"empty", label:loaded?"Models loaded":"No models loaded"};
}

export function activityState(status) {
    if (!status) return {busy:false, label:"Status unavailable", unknown:true};
    const manual = status.resource_download?.status === "running";
    const download = (manual?status.resource_download:status.download) || {};
    if (["running", "downloading", "verifying"].includes(download.status))
        return {busy:true, label:download.status==="verifying"?"Verifying model files":"Downloading model", detail:manual?"Downloading the selected resource.":FIRST_USE_MESSAGE,
            fraction:utilization(download.bytes ?? download.downloaded ?? download.completed_bytes, download.total ?? download.total_bytes)};
    if (status.resource_cleanup?.status === "releasing") return {busy:true, label:"Unloading models"};
    if (status.running || status.description_helper?.running) return {busy:true, label:status.description_helper?.running?status.description_helper.phase:"Workflow running"};
    if (download.status === "failed") return {busy:false, label:download.error || "Model download failed", error:true};
    if (download.status === "paused") return {busy:false, label:"Model download paused"};
    return {busy:false, label:"Ready"};
}
