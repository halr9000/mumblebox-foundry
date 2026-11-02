// ComfyUI's document-level clipboard handlers see a shadow host, not the
// input or selected text inside it, and otherwise copy/paste graph nodes.
export function installTextClipboard(root) {
    const document = root.ownerDocument;
    function handle(event) {
        const path = event.composedPath();
        const fromInterface = path.includes(root);
        const selection = root.getRootNode().getSelection?.() || document.getSelection();
        const selectedHere = selection && root.contains(selection.anchorNode) && root.contains(selection.focusNode);
        if (!fromInterface && !(event.type === "copy" && selectedHere)) return;

        // Stop graph handling while retaining the browser's native editing
        // behavior for inputs, textareas and contenteditable editors.
        event.stopImmediatePropagation();
        const editing = path.some(node => /^(INPUT|TEXTAREA|SELECT)$/.test(node.tagName) || node.isContentEditable);
        if (event.type === "copy" && !editing && selectedHere && !selection.isCollapsed && event.clipboardData) {
            event.clipboardData.setData("text/plain", selection.toString());
            event.preventDefault();
        }
    }
    const options = {capture: true};
    for (const type of ["copy", "cut", "paste"]) document.addEventListener(type, handle, options);
    return () => {
        for (const type of ["copy", "cut", "paste"]) document.removeEventListener(type, handle, options);
    };
}
