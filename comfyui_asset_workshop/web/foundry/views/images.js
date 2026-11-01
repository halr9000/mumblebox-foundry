import {el,button,hint,icon} from "../dom.js";
import {render as gallery} from "./library.js";

export async function render(shell){
    let disposed=false,childDispose,sequence=0;
    const body=el("div",{});
    const tabs=el("div",{class:"image-tabs",role:"tablist","aria-label":"Images sections"});
    async function open(name){
        shell.imageSection=name;
        const current=++sequence;childDispose?.();childDispose=null;
        [...tabs.children].forEach(b=>{const selected=b.textContent===name;b.setAttribute("aria-selected",String(selected));b.tabIndex=selected?0:-1;});
        body.setAttribute("aria-label",name);
        if(name==="Create Images"){
            body.replaceChildren(el("section",{class:"image-creation-placeholder"},icon("image",54),
                el("span",{class:"badge"},"Coming soon"),el("h3",{},"A starting image for your next asset"),
                el("p",{},"This space will bring together image creation workflows and capture from a connected camera. Finished images will be available in Gallery."),
                hint("Image creation is not connected yet. The image-to-3D wizard already accepts uploaded reference images and photos from a connected camera."),
                button("Choose a workflow",()=>shell.open("Choose a Workflow"))));
            return;
        }
        body.replaceChildren(hint("Loading gallery…"));
        const view=await gallery(shell,"image");
        if(disposed||current!==sequence){view.dispose?.();return;}
        body.replaceChildren(view.element||view);childDispose=view.dispose;
    }
    for(const name of ["Create Images","Gallery"])tabs.append(button(name,()=>open(name),{role:"tab"}));
    tabs.addEventListener("keydown",e=>{
        if(!["ArrowLeft","ArrowRight","Home","End"].includes(e.key))return;
        e.preventDefault();const next=e.key==="Home"?0:e.key==="End"?1:[...tabs.children].findIndex(b=>b.getAttribute("aria-selected")==="true")===0?1:0;
        open(tabs.children[next].textContent);tabs.children[next].focus();
    });
    body.setAttribute("role","tabpanel");
    await open(shell.imageSection||"Create Images");
    return {element:el("div",{},el("div",{class:"page-head"},el("div",{},el("span",{class:"eyebrow"},"MUMBLEBOX / IMAGE WORKSPACE"),el("h2",{},"Images"),hint("Create, capture and keep your starting images in one place."))),tabs,body),
        dispose(){disposed=true;sequence++;childDispose?.();}};
}
