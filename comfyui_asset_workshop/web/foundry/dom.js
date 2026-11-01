export function el(tag, attrs = {}, ...children) {
    const node = document.createElement(tag);
    for (const [key, value] of Object.entries(attrs)) {
        if (value === undefined || value === null) continue;
        if (key.startsWith("on")) node.addEventListener(key.slice(2), value);
        else if (key === "class") node.className = value;
        else if (key in node) node[key] = value;
        else node.setAttribute(key, value);
    }
    node.append(...children.flat().filter(value => value !== null && value !== undefined));
    return node;
}
export const button = (label, action, attrs = {}) => el("button", {type:"button", onclick:action, ...attrs}, label);
export const link = (label, href) => el("a", {href, target:"_blank", rel:"noopener noreferrer"}, label);
export const hint = text => el("p", {class:"muted"}, text);
export const field = (label, control, description) => el("label", {class:"field"}, el("span", {}, label), control, description ? hint(description) : null);
export const bytes = value => Number.isFinite(value) ? (value / 1024 ** 3).toFixed(1) + " GB" : "Unavailable";

const paths = {
    cube:"M12 3 3 8v9l9 5 9-5V8l-9-5ZM3 8l9 5 9-5M12 13v9",
    arrow:"M4 12h16m-6-6 6 6-6 6",
    gear:"M10 2h4l.5 3 1.5.8 2.8-1.1 2 3.4-2.3 2 .1 1.9 2.4 2-2 3.5-2.9-1-1.6.9-.5 3.1h-4l-.5-3.1-1.6-.9-2.9 1-2-3.5 2.4-2 .1-1.9-2.3-2 2-3.4 2.8 1.1L9.5 5 10 2ZM12 8.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7Z",
    image:"M3 3h18v18H3zM3 17l6-6 5 5 3-3 4 4M16 7h.01",
    history:"M3 10a9 9 0 1 1 1 7M3 3v7h7M12 7v5l3 2",
    download:"M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5",
    sun:"M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8ZM12 1v3m0 16v3M1 12h3m16 0h3M4 4l2 2m12 12 2 2M4 20l2-2M18 6l2-2",
    contrast:"M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Z",
};
export function icon(name, size=24) {
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    for (const [k,v] of Object.entries({viewBox:"0 0 24 24",width:size,height:size,fill:"none",stroke:"currentColor","stroke-width":1.5,"stroke-linecap":"round","stroke-linejoin":"round","aria-hidden":"true"})) svg.setAttribute(k,v);
    const path = document.createElementNS(svg.namespaceURI, "path");
    path.setAttribute("d", paths[name] || paths.cube); svg.append(path);
    if(name==="contrast") {
        const half=document.createElementNS(svg.namespaceURI,"path");
        half.setAttribute("d","M12 3a9 9 0 0 1 0 18Z");half.setAttribute("fill","currentColor");svg.append(half);
    }
    return svg;
}
