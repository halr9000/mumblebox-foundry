import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

export const PREFIX = "/asset-workshop/v2";

export async function request(path, body, method) {
    const response = await api.fetchApi(PREFIX + path, {
        method: method || (body === undefined ? "GET" : "POST"),
        ...(body === undefined ? {} : { headers: {"Content-Type": "application/json"}, body: JSON.stringify(body) }),
    });
    const result = await response.json();
    if (!response.ok) {
        const error = new Error(result.error || `Request failed (${response.status})`);
        error.status = response.status;
        throw error;
    }
    return result;
}

export function connectVisibleClient(isVisible, onError, onStage, showGraph) {
    let disposed = false;
    const stages = new Set();
    const heartbeat = async () => {
        if (disposed || !api.clientId) return;
        try { await request("/client", {client_id: api.clientId, visible: !!isVisible()}); }
        catch (error) { onError?.(error); }
    };
    const load = async event => {
        const stage = event.detail;
        if (disposed || !isVisible() || stage.client_id !== api.clientId || stages.has(stage.stage_id)) return;
        stages.add(stage.stage_id);
        try {
            await onStage?.(stage);
            await app.reloadNodeDefs();
            await showGraph(stage.graph);
            app.graph.setDirtyCanvas(true, true);
            await request(`/jobs/${stage.job_id}/visible`, {
                stage_id: stage.stage_id, graph_hash: stage.graph_hash, client_id: api.clientId,
            });
        } catch (error) { stages.delete(stage.stage_id); onError?.(error); }
    };
    api.addEventListener("mumblebox_stage", load);
    const timer = setInterval(heartbeat, 5000);
    heartbeat();
    return () => {
        disposed = true;
        clearInterval(timer);
        api.removeEventListener("mumblebox_stage", load);
        if (api.clientId) request("/client", {client_id: api.clientId, visible: false}).catch(() => {});
    };
}
