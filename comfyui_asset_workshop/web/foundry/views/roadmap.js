import {el,button,link} from "../dom.js";
import {roadmap} from "../roadmap-data.js";

export function render() {
    const sections = roadmap.map(group => el("section", {
        class: "roadmap-section", "aria-label": group.title,
    },
        el("header", {class: "roadmap-section-head"},
            el("h3", {}, group.title),
            el("span", {class: "roadmap-count"}, String(group.items.length))),
        el("p", {class: "muted roadmap-summary"}, group.summary),
        el("ul", {class: "roadmap-items"}, group.items.map(item => el("li", {},
            el("div", {class: "roadmap-item-head"},
                el("h4", {}, item.title),
                el("span", {class: "roadmap-state", "data-state": item.status || "Planned"}, item.status || "Planned")),
            el("p", {}, item.description),
            item.source ? link(item.sourceLabel || "Source", item.source) : null,
        ))),
    ));
    const count = el("span", {class: "muted", role: "status", "aria-live": "polite"});
    const filters = el("div", {class: "roadmap-filters", role: "group", "aria-label": "Filter roadmap by type"});
    const choices = [{id: "all", title: "All"}, ...roadmap];
    function select(id) {
        sections.forEach((section, index) => { section.hidden = id !== "all" && roadmap[index].id !== id; });
        [...filters.children].forEach((control, index) => control.setAttribute("aria-pressed", String(choices[index].id === id)));
        const shown = roadmap.filter(group => id === "all" || group.id === id);
        count.textContent = `${shown.reduce((sum, group) => sum + group.items.length, 0)} items`;
    }
    for (const choice of choices) filters.append(button(choice.title, () => select(choice.id), {"aria-pressed": "false"}));
    select("all");
    return el("div", {class: "roadmap"},
        el("header", {class: "roadmap-head"},
            el("div", {}, el("h2", {}, "Roadmap"), el("p", {class: "muted"}, "Planned improvements and research for the Foundry. Scope and order may change as we learn.")), count),
        filters,
        el("div", {class: "roadmap-sections"}, sections),
    );
}
