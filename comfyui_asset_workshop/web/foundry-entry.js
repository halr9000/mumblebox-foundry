import {app} from "/scripts/app.js";
import {FoundryShell} from "./foundry/shell.js";
import {NODE_TYPE,installReturnControl,showInterface} from "./foundry/graph-adapter.js";

function registerNode() {
    if(LiteGraph.registered_node_types[NODE_TYPE])return;
    class InterfaceNode extends LiteGraph.LGraphNode {
        constructor() {
            super("Mumblebox 3D Asset Foundry");
            this.isVirtualNode=true;
            this.serialize_widgets=false;
            const host=document.createElement("div");
            host.style.cssText="width:100%;height:100%;min-height:820px;overflow:hidden";
            this.addDOMWidget("foundry","MUMBLEBOX_FOUNDRY",host,{
                serialize:false,hideOnZoom:false,getMinHeight:()=>820,getHeight:()=>900});
            this.shell=new FoundryShell(host,this);
            this.size=[1280,960];this.color="#3d7257";this.bgcolor="#1f2d26";
            const originalRemoved=this.onRemoved;
            this.onRemoved=()=>{this.shell.dispose();this.removeReturn?.();originalRemoved?.call(this);};
        }
    }
    LiteGraph.registerNodeType(NODE_TYPE,InterfaceNode);
}
app.registerExtension({
    name:"MumbleboxFoundry.Interface.v1",
    async registerCustomNodes(){registerNode();},
    async setup(){registerNode();},
    async afterConfigureGraph(){
        const marker=app.graph.extra?.mumblebox_foundry;
        const node=marker&&app.graph.getNodeById(marker.interface_node_id);
        if(!node||node.type!==NODE_TYPE)return;
        node.removeReturn?.();node.removeReturn=installReturnControl(node);
        if(marker.landing_view==="gui")requestAnimationFrame(()=>showInterface(node));
    },
});
registerNode();

export function addInterface() {
    const existing=app.graph._nodes.find(n=>n.type===NODE_TYPE);
    if(existing){showInterface(existing);return existing.id;}
    const node=LiteGraph.createNode(NODE_TYPE);
    node.pos=[-1520,80];node.size=[1280,960];
    app.graph.add(node);
    const group=new LiteGraph.LGraphGroup("MUMBLEBOX — WORKFLOW INTERFACE");
    group.configure({title:"MUMBLEBOX — WORKFLOW INTERFACE",bounding:[-1560,10,1360,1080],color:"#3d7257",font_size:24,flags:{}});
    app.graph.add(group);group.recomputeInsideNodes?.();
    app.graph.extra??={};
    app.graph.extra.mumblebox_foundry={schema:1,interface_node_id:node.id,workflow_id:"image-to-3d/v1",reference_node_id:app.graph._nodes.find(n=>n.type==="LoadImage" && /approved/i.test(n.title))?.id,landing_view:"gui"};
    node.removeReturn=installReturnControl(node);showInterface(node);
    app.canvas.setDirty(true,true);
    return node.id;
}
