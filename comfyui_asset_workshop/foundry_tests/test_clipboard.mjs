import test from "node:test";
import assert from "node:assert/strict";
import {installTextClipboard} from "../web/foundry/clipboard.js";

function fixture() {
    const document = new EventTarget();
    const text = {tagName: "P"}, input = {tagName: "TEXTAREA"}, outside = {tagName: "CANVAS"};
    const selection = {anchorNode: text, focusNode: text, isCollapsed: false, toString: () => "Copy these actual words"};
    const root = {ownerDocument: document, getRootNode: () => ({getSelection: () => selection}), contains: node => [text, input].includes(node)};
    const dispose = installTextClipboard(root);
    let graphCalls = 0;
    for (const type of ["copy", "cut", "paste"]) document.addEventListener(type, event => {
        graphCalls++;
        event.preventDefault();
        event.clipboardData.setData("text/html", "graph metadata");
    });
    function send(type, path) {
        const event = new Event(type, {cancelable: true});
        const data = new Map();
        Object.assign(event, {composedPath: () => path, clipboardData: {setData: (type, value) => data.set(type, value)}});
        document.dispatchEvent(event);
        return {event, data};
    }
    return {root, document, selection, text, input, outside, send, dispose, graphCalls: () => graphCalls};
}

test("copy rendered Foundry text as plain text, without graph metadata", () => {
    const f = fixture();
    const {event, data} = f.send("copy", [f.text, f.root]);
    assert.equal(data.get("text/plain"), "Copy these actual words");
    assert.equal(data.has("text/html"), false);
    assert.equal(event.defaultPrevented, true);
    assert.equal(f.graphCalls(), 0);
});

test("copy a Foundry selection even when the clipboard event targets the document", () => {
    const f = fixture();
    assert.equal(f.send("copy", [f.document]).data.get("text/plain"), "Copy these actual words");
    assert.equal(f.graphCalls(), 0);
});

for (const type of ["copy", "cut", "paste"]) test(`${type} in text fields keeps native browser editing`, () => {
    const f = fixture();
    const {event, data} = f.send(type, [f.input, f.root]);
    assert.equal(event.defaultPrevented, false);
    assert.equal(data.size, 0);
    assert.equal(f.graphCalls(), 0);
});

test("clipboard use outside Foundry still reaches ComfyUI graph handlers", () => {
    const f = fixture();
    f.selection.anchorNode = f.selection.focusNode = f.outside;
    assert.equal(f.send("copy", [f.outside]).data.get("text/html"), "graph metadata");
    f.send("paste", [f.outside]);
    assert.equal(f.graphCalls(), 2);
});

test("disposing the interface removes its document clipboard listeners", () => {
    const f = fixture();
    f.dispose();
    f.send("copy", [f.text, f.root]);
    assert.equal(f.graphCalls(), 1);
});
