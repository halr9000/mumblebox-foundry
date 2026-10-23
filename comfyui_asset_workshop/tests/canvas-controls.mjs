import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const source=readFileSync(new URL('../web/single-image.js',import.meta.url),'utf8');
assert.ok(source.includes('export function renderSingleControls'), 'The canvas node must render the controls directly');
assert.ok(!source.includes('Open Mumblebox controls'), 'There must be no launcher');
assert.ok(!source.includes('aw-single-window'), 'There must be no floating controls layout');
const app={};let created=0;
const mount=vm.runInNewContext(source.slice(source.indexOf('export function renderSingleControls')).replace('export function','function')+';renderSingleControls',{
    app,clearInterval:()=>{},SingleImageControls:class {constructor(node){created++;this.node=node;this.root={};node.root.replaceChildren(this.root);}}
});
const node={size:[760,260],root:{replaceChildren(child){this.child=child;},style:{}}};
mount(node);mount(node);
assert.equal(created,1,'Rerendering must not create a second project or client');
assert.equal(node.root.child,node.singleControls.root,'Real controls must be mounted inside the canvas widget');
assert.equal(app.mumbleboxSingle,node.singleControls);
assert.ok(node.size[0]>=1060&&node.size[1]>=900,'The canvas node must fit the complete controls');

const Controls=vm.runInNewContext(source.slice(source.indexOf('class SingleImageControls'),source.indexOf('export function renderSingleControls'))+';SingleImageControls',{
    app,clone:value=>JSON.parse(JSON.stringify(value)),LiteGraph:{createNode:()=>({root:{},render(){this.singleControls.node=this;}})}
});
const c=Object.create(Controls.prototype),old={type:'AssetWorkshop/Controls',properties:{asset_workshop_mode:'single_image_agent'},pos:[30,40],size:[1060,900]};
c.node=old;c.project={id:'keep-this-project'};
app.canvas={ds:{scale:.8,offset:[10,20]}};
app.graph={_nodes:[],add(n){this._nodes.push(n);},setDirtyCanvas(){}};
app.extensionManager={workflow:{activeWorkflow:'current'}};
const graph={one:{class_type:'EmptyImage',inputs:{width:512,height:512,batch_size:1,color:0}}};
app.loadApiJson=async data=>{assert.equal(data,graph);assert.equal(c.transferring,true);app.graph._nodes=[{pos:[0,0]}];};
await c.showStageGraph(graph);
assert.equal(c.project.id,'keep-this-project','Loading a stage must retain the current project and approvals');
assert.equal(c.node.singleControls,c,'The stage must retain the same controls and client');
assert.equal(app.graph._nodes.length,2,'Processing nodes and controls must coexist');
assert.ok(app.graph._nodes[0].pos[0]>c.node.pos[0]+c.node.size[0],'Processing nodes must appear beside the controls');
assert.equal(c.transferring,false);
assert.equal(app.canvas.ds.scale,.8,'Loading a stage must preserve the view scale');
console.log('Canvas controls stay embedded and survive loading a processing graph beside them.');
