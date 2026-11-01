// Session policy is separate from DOM rendering and durable backend run files.
export const hasWork = state => !!(state?.runId || state?.draft?.references?.length || state?.draft?.name);
export function initialState(saved, resume=false) {
    if (resume && hasWork(saved)) return structuredClone(saved);
    return {page:1,runId:null,draft:{name:"",category:"characters",turnaround_model:"qwen21",
        references:[],profile:"default",overrides:{}}};
}
export function retainSession(recent, state) {
    if (!hasWork(state)) return recent || [];
    const copy=structuredClone(state);
    copy.sessionId??=copy.runId||crypto.randomUUID();
    return [copy,...(recent||[]).filter(s=>copy.runId?s.runId!==copy.runId:s.sessionId!==copy.sessionId)].slice(0,12);
}

// Older durable runs omit settings introduced in later interface versions.
export function copyRunConfiguration(defaults,run) {
    const draft=structuredClone(defaults);
    for(const field of ['name','references','category','turnaround_model','profile','overrides','selection']) {
        if(run[field]!==undefined)draft[field]=structuredClone(run[field]);
    }
    return draft;
}