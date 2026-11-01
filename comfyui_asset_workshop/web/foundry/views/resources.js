import {el,button,hint} from "../dom.js";
import {request} from "../services.js";

const size=n=>n>=1024**3?(n/1024**3).toFixed(2)+" GB":(n/1024**2).toFixed(1)+" MB";

// Inline confirmation keeps Settings open and identifies the exact file.
export function resourceLists(shell) {
    let disposed=false;
    const lists=el("div",{class:"resource-lists"}),feedback=el("p",{role:"status",class:"muted"});
    const refresh=button("Refresh list",load);
    const root=el("section",{},el("div",{class:"section-heading"},el("h3",{},"Downloaded resources"),refresh),
        hint("Image models and LoRAs stored in this installation. Deleting a file frees disk space; a workflow may download it again when needed."),feedback,lists);
    async function load(){
        refresh.disabled=true;
        try {
            const data=await request("resources");if(disposed)return;
            feedback.textContent=data.truncated?"Showing the first 1,000 resources.":"";
            lists.replaceChildren(...[["image_model","Image models"],["lora","LoRAs"]].map(([kind,label])=>{
                const items=data.items.filter(i=>i.kind===kind);
                return el("section",{class:"resource-group"},el("h4",{},label),items.length?el("ul",{class:"resource-rows"},...items.map(item=>{
                    const details=el("div",{},el("strong",{},item.name),el("small",{class:"muted"},size(item.bytes)+(item.reason?" · "+item.reason:"")));
                    const row=el("li",{},details);
                    const remove=button("Delete",async()=>{
                        remove.disabled=true;
                        try{
                            const p=await request("resources/delete-preview",{id:item.id});
                            const confirmation=el("div",{class:"resource-confirm"},hint("Delete "+p.relative_path+" ("+size(p.bytes)+") from disk?"),
                                button("Cancel",()=>{confirmation.remove();remove.disabled=false;}),
                                button("Delete file",async()=>{
                                    try{await request("resources/delete",{token:p.token});shell.message(item.name+" deleted.");await load();}
                                    catch(e){await load();feedback.textContent=e.message;shell.message(e.message,true);}
                                },{class:"danger"}));
                            row.append(confirmation);
                        }catch(e){feedback.textContent=e.message;remove.disabled=!item.deletable;}
                    },{class:"danger",disabled:!item.deletable,title:item.reason||"Delete this downloaded file"});
                    row.append(remove);return row;
                })):hint("None found."));
            }));
        }catch(e){if(!disposed)feedback.textContent=e.message;}
        finally{refresh.disabled=false;}
    }
    load();return {element:root,dispose:()=>{disposed=true;}};
}
