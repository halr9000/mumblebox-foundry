// Node sampling may restart at zero within one stage. Only saved stages count
// as complete, and the display never moves backwards within an operation.
export function overallProgress(progress, sample=0, previous=0, finished=false) {
    if (!progress?.total) return null;
    if (finished) return 1;
    const done=progress.completed.length;
    const active=progress.stages.includes(progress.current)&&!progress.completed.includes(progress.current);
    return Math.min(.99,Math.max(previous,(done+(active?Math.min(.9,Math.max(0,sample)*.9):0))/progress.total));
}
