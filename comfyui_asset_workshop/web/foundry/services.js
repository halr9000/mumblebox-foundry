const PREFIX = "/mumblebox-foundry/v1";
export async function request(path, data, options = {}) {
    let response;
    try { response = await fetch(path.startsWith("/") ? path : PREFIX + "/" + path, {
        method: data === undefined ? "GET" : "POST",
        ...options,
        headers: {"Content-Type":"application/json", ...(options.headers || {})},
        ...(data === undefined ? {} : {body:JSON.stringify(data)}),
    }); } catch (cause) {
        const error=new Error("Foundry has lost its connection to the local service. Restart Foundry in Pinokio if it has stopped; this page reconnects automatically.",{cause});
        error.code="FOUNDRY_OFFLINE";throw error;
    }
    let result;
    try { result = await response.json(); }
    catch { throw Error("The Foundry service is unavailable. Check that the installed extension is loaded."); }
    if (!response.ok) throw Error(result.error || result.message || "The request could not finish.");
    return result;
}
export const fileUrl = (id, file) => PREFIX + "/library/" + encodeURIComponent(id) + "/files/" + encodeURIComponent(file);
export function pollResources(onStatus, onError) {
    let disposed = false, timer, controller, failures=0;
    const run = async () => {
        if(disposed)return;
        controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 8000);
        let delay=1000;
        try {
            const data = await request("/asset-workshop/status", undefined, {signal:controller.signal});
            failures=0;
            if (!disposed) onStatus(data);
        } catch (error) { delay=Math.min(10000,1000*2**++failures);if (!disposed) onError(error); }
        finally { clearTimeout(timeout); if (!disposed) timer = setTimeout(run, delay); }
    };
    run();
    return () => { disposed = true; clearTimeout(timer); controller?.abort(); };
}
