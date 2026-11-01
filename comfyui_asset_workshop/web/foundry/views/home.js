import {el,button,hint} from "../dom.js";
import {showWorkflow,savedWizardState} from "../graph-adapter.js";

const planned=[
["repair","Refine and Repair an Existing Mesh","Supply an existing mesh and a matching image for refinement and new output versions."],
["video","Start with a Video","Use a recorded subject as the starting point for a 3D asset."],
["turntable","PC-Controlled Turntable and Camera Capture","Capture a subject with a compatible ComXim Bluetooth turntable and connected camera."],
["figure","Action Figure Mode","Use identity references and figure presets to create a personalized figure, with optional base choices."]
];
const artwork=(id,alt)=>el("img",{src:new URL("../../assets/foundry/"+id+".png",import.meta.url).href,alt,loading:"lazy",decoding:"async",width:512,height:512});

export function home(shell) {
    const saved = savedWizardState(shell.node);
    const card = el("article",{class:"workflow-card"},
        el("div",{class:"art workflow-art"},artwork("image-to-3d","Reference image becoming a sculpted 3D figure")),
        el("div",{class:"card-body"},el("span",{class:"eyebrow"},"IMAGE TO 3D  /  01"),
            el("h3",{},"Create a 3D Asset from an Image"),
            el("p",{},"Upload one or more reference images, or use a connected webcam to photograph an object, drawing or printed picture. Create textured 3D assets with detailed and reduced triangle meshes, optional quad retopology, and exports for game development, editing and printing."),
            hint("The current workflow creates four views from your image, builds the mesh, refines its geometry and prepares the final textures and exports."),
            el("div",{class:"formats"},["GLB","FBX","OBJ","BLEND","STL","PNG","ZIP"].map(x=>el("span",{class:"badge"},x))),
            el("div",{class:"actions"},button("Open Wizard",()=>shell.openWizard(),{class:"primary"}),
                button("View Workflow",()=>showWorkflow(shell.node)),
                saved?button("Resume previous asset",()=>shell.openWizard({resume:true}),{title:saved.draft?.name||"Resume saved work"}):null),
            hint("Choose your export versions and formats before finishing.")));
    const imageCard=el('article',{class:'planned-workflow'},artwork('text','Develop images from a description'),el('div',{},el('span',{class:'badge'},'Available'),
        el('h3',{},'Create Images and 3D Assets from a Text Prompt'),hint('Describe an asset to create matching front and back references, or make a standalone image. Edit the result and optionally continue into 3D.'),
        button('Create Images',()=>{delete shell.imageOrigin;shell.openImages('Create Images');},{class:'primary'})));
    return el("div",{},card,el("div",{class:"future-workflows"},imageCard,...planned.map(([id,name,description])=>el("article",{class:"planned-workflow"},artwork(id,name),el("div",{},el("span",{class:"badge"},"Coming soon"),el("h3",{},name),hint(description))))));
}
