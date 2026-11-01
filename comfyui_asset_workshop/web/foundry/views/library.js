import {el,button,hint,icon,link} from "../dom.js";
import {request,fileUrl} from "../services.js";
import {dialog} from "../dialogs.js";

const formatSize=n=>n>=1024**3?(n/1024**3).toFixed(2)+" GB":(n/1024**2).toFixed(1)+" MB";
const label = value => value.replaceAll("_", " ").replace(/\b\w/g, c => c.toUpperCase());
const number = value => Number.isInteger(value) ? value.toLocaleString() : Number(value).toLocaleString(undefined,{maximumFractionDigits:4});
const measure = value => Array.isArray(value) ? value.map(number).join(" × ") : typeof value === "boolean" ? (value ? "Yes" : "No") : typeof value === "number" ? number(value) : String(value);
function measurements(data) {
    return Object.entries(data).map(([section, values]) => {
        if (Array.isArray(values)) return el("section",{},el("h4",{},label(section)),
            el("ul",{},...values.map(v=>el("li",{},el("span",{class:"filename"},v.path)," — "+measure(v.dimensions)+" px; "+v.interpretation))));
        if (!values || typeof values !== "object") return el("dl",{},el("dt",{},label(section)),el("dd",{},measure(values)));
        return el("section",{},el("h4",{},label(section)),el("dl",{},...Object.entries(values).flatMap(([k,v])=>[el("dt",{},label(k)),el("dd",{},measure(v))])));
    });
}
async function details(shell,item) {
    const data=await request("library/"+item.id);
    const body=el("div",{},el("dl",{},el("dt",{},"Workflow"),el("dd",{},data.workflow),
        el("dt",{},"Created"),el("dd",{},new Date(data.created).toLocaleString()),el("dt",{},"Package"),el("dd",{},data.file_count+" cataloged files · "+formatSize(data.bytes))),
        ...data.variants.map(v=>el("section",{class:"settings-section"},el("h3",{},label(v.id)),hint(v.description||v.intended_use||""),
            ...measurements(v.measurements||{}),
            ...(v.validations||[]).map(check=>hint(check.name+" — "+check.status+". "+check.note)),
            ...(v.limitations||[]).map(hint))),
        el("h3",{},"Files"),el("div",{class:"file-list"},...data.catalog.files.map(f=>el("div",{},f.path+" · "+formatSize(f.bytes||0)))),
        ...data.warnings.map(text=>hint(text)));
    dialog(shell,data.name,body,[{label:"Close",run:close=>close()}]);
}
function confirmRemoval(shell,kind,ids) {
    const destructive=el("input",{type:"checkbox"});
    const first=el("div",{},el("p",{},ids?"Remove this entry from "+(kind==="mesh"?"History":"Image Gallery")+"?":"Purge all entries currently in "+(kind==="mesh"?"History":"Image Gallery")+"?"),
        hint("Saved files are kept unless you explicitly choose to delete them."),
        el("label",{class:"check-row"},destructive,el("span",{},"Also delete saved files")));
    dialog(shell,ids?"Remove entry":"Purge history",first,[
        {label:"Cancel",run:close=>close()},
        {label:"Review removal",primary:true,run:async close=>{
            const review=await request("library/removal-preview",{kind,ids,delete_files:destructive.checked});
            close();
            const explanation=el("div",{},el("p",{},review.count+" entr"+(review.count===1?"y":"ies")+" will be removed."),
                el("ul",{},...review.names.map(n=>el("li",{},n))),
                review.delete_files?el("div",{},el("strong",{},"These saved files will also be permanently deleted:"),
                    el("div",{class:"file-list"},...review.files.map(p=>el("div",{},p)))):
                    hint("Saved images, meshes and ZIP files will remain on disk."));
            dialog(shell,review.delete_files?"Confirm file deletion":"Confirm entry removal",explanation,[
                {label:"Cancel",run:c=>c()},
                {label:review.delete_files?"Delete files and entries":"Remove entries",primary:true,run:async c=>{
                    const result=await request("library/remove",{token:review.token});
                    if(!result.ok)throw Error(result.error+" "+(result.failures||[]).join(", "));
                    c();shell.message(result.removed_entries+" entr"+(result.removed_entries===1?"y":"ies")+" removed. "+(review.delete_files?"Selected files deleted.":"Saved files kept."));
                    if(kind==="mesh")await shell.open("History");
                    else await shell.openImages("Gallery");
                }}]);
        }}]);
}
export async function render(shell,kind) {
    let disposed=false,cursor="",items=[];
    const title=kind==="mesh"?"History":"Image Gallery";
    const intro=kind==="mesh"?"Completed mesh packages, their versions and recorded measurements.":"Final images from dedicated image-creation workflows. Turnarounds, masks and texture maps are not included.";
    const root=el("div",{});
    const list=el("div",{class:"library-list"});
    const purge=button("Purge History",()=>confirmRemoval(shell,kind,null),{class:"danger",disabled:true});
    const more=button("Load more",()=>load(true),{hidden:true});
    const refresh=button("Refresh",()=>load(false));
    root.append(el("div",{class:"page-head"},el("div",{},el("span",{class:"eyebrow"},kind==="mesh"?"ASSET LIBRARY":"IMAGE LIBRARY"),el("h2",{},title),hint(intro)),
        el("div",{class:"actions"},refresh,purge)),list,more);
    async function load(append) {
        refresh.disabled=true;more.disabled=true;
        try{
            if(!append) {
                const sync=await request("library/sync",{});
                if(sync.failed)shell.message(sync.failed+" history notification(s) need attention. Existing files are unchanged.",true);
            }
            const page=await request("library?"+new URLSearchParams({kind,cursor:append?cursor:"",limit:24}));
            if(disposed)return;
            items=append?[...items,...page.items]:page.items;cursor=page.next_cursor;
            purge.disabled=!items.length;more.hidden=!cursor;
            list.replaceChildren(...items.map(item=>{
                const thumb=el("div",{class:"thumbnail"},item.preview_id?el("img",{src:fileUrl(item.id,item.preview_id),alt:item.name}):icon(kind==="mesh"?"cube":"image",42));
                return el("article",{class:"library-card"},thumb,el("div",{},el("h3",{},item.name),
                    hint(new Date(item.created).toLocaleString()+" · "+item.workflow),
                    el("div",{class:"formats"},...item.formats.filter(Boolean).map(f=>el("span",{class:"badge"},f.toUpperCase()))),
                    hint(item.file_count+" files · "+formatSize(item.bytes)+" · "+item.variants.map(v=>v.id.replaceAll("_"," ")).join(", ")),
                    el("div",{class:"actions"},button("View Details",()=>details(shell,item).catch(e=>shell.message(e.message,true))),
                        button("Open Output Folder",async()=>{try{const result=await request("library/"+item.id+"/open-folder",{});shell.message(result.location);}catch(e){shell.message(e.message,true);}}),
                        el("a",{href:fileUrl(item.id,"archive"),download:"",class:"download-link"},"Download ZIP"),
                        button("Delete",()=>confirmRemoval(shell,kind,[item.id]),{class:"danger"}))));
            }));
            if(!items.length)list.append(el("div",{class:"empty"},icon(kind==="mesh"?"history":"image",42),
                el("h3",{},kind==="mesh"?"No mesh packages in History yet":"No image creations yet"),
                hint(kind==="mesh"?"Completed exports will appear here.":"This gallery will collect final images when the image-creation workflow is added.")));
        }catch(e){if(!disposed){shell.message(e.message,true);if(!items.length)list.replaceChildren(el("p",{},e.message));}}
        finally{refresh.disabled=false;more.disabled=false;}
    }
    await load(false);
    return {element:root,dispose:()=>{disposed=true;}};
}
