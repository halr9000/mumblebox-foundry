const PREFIX = "/mumblebox-foundry/v1";
export async function request(path, data, options = {}) {
    const response = await fetch(path.startsWith("/") ? path : PREFIX + "/" + path, {
        method: data === undefined ? "GET" : "POST",
        ...options,
        headers: {"Content-Type":"application/json", ...(options.headers || {})},
        ...(data === undefined ? {} : {body:JSON.stringify(data)}),
    });
    let result;
    try { result = await response.json(); }
    catch { throw Error("The Foundry service is unavailable. Check that the installed extension is loaded."); }
    if (!response.ok) throw Error(result.error || result.message || "The request could not finish.");
    return result;
}
export const fileUrl = (id, file) => PREFIX + "/library/" + encodeURIComponent(id) + "/files/" + encodeURIComponent(file);
export function pollResources(onStatus, onError) {
    let disposed = false, timer, controller;
    const run = async () => {
        controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 8000);
        try {
            const data = await request("/asset-workshop/status", undefined, {signal:controller.signal});
            if (!disposed) onStatus(data);
        } catch (error) { if (!disposed) onError(error); }
        finally { clearTimeout(timeout); if (!disposed) timer = setTimeout(run, 3000); }
    };
    run();
    return () => { disposed = true; clearTimeout(timer); controller?.abort(); };
}
