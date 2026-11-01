import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';

const source=readFileSync(new URL('../web/single-image.js',import.meta.url),'utf8');
let editor,requestResult,legacyFails=false;
const Controls=vm.runInNewContext(source.slice(source.indexOf('class SingleImageControls'),source.indexOf('export function renderSingleControls'))+';SingleImageControls',{
    active:job=>job?.state==='running',el:()=>({}),
    openImageEditor:async options=>{editor=options;},
    legacy:async()=>{if(legacyFails)throw Error('Could not save');},
    request:async()=>requestResult,
    document:{body:{append:()=>{}}}
});
const image={id:'image1',sha256:'hash',foreground:{mask_file:'mask.png',cutout_file:'cutout.png'}};
function controls(){const c=Object.create(Controls.prototype);Object.assign(c,{
    project:{id:'job1',revision:1},root:{scrollTop:100},tab:'Approve image',
    current:()=>image,url:record=>`/artifact/${record.id}`,fileURL:file=>`/file/${file}`,post:async()=>{},refresh:async()=>{},render(){this.rendered=true;},link:()=>({})
});return c;}
{
    const c=controls();let saves=0,opens=0;c.post=async()=>{saves++;};c.cutout=async()=>{opens++;assert.equal(saves,1);};
    await c.review('mesh_input',image,'approved','');assert.equal(opens,1,'Approval must open background removal');
    saves=0;await c.review('mesh_input',image,'approved_with_notes','Thin edges');assert.equal(opens,2);
    await c.review('reference_front',image,'approved','');assert.equal(opens,2,'Reference reviews must not open the cutout editor');
}
{
    const c=controls();await c.cutout();assert.equal(editor.initialMaskURL,'/file/mask.png');
    assert.equal(editor.keepLabel,'Keep Cutout and Continue to Create Mesh');
    await editor.accept({id:'candidate1'});assert.equal(c.tab,'Mesh & agent package');assert.equal(c.root.scrollTop,0);
    c.tab='Approve image';legacyFails=true;
    await assert.rejects(()=>editor.accept({id:'candidate1'}),/Could not save/);
    assert.equal(c.tab,'Approve image','A failed save must keep the user in preparation');legacyFails=false;
}
{
    const c=controls();c.current=()=>({...image,foreground:null});let starts=0;
    c.start=async()=>{starts++;return {};};c.waitJob=async()=>{};
    await c.cutout();assert.equal(starts,0,'The editor must be opened before background detection begins');
    assert.equal(typeof editor.prepareMask,'function');
    c.current=()=>image;await editor.prepareMask();assert.equal(starts,1);
}
{
    const c=controls();let clicked=0,removed=0,refreshed=0;
    c.refresh=async()=>{refreshed++;};c.link=(label,url)=>({click(){assert.equal(url,'/artifact/package1');clicked++;},remove(){removed++;}});
    requestResult={id:'package1'};await c.exportAsset({id:'mesh1'},null);
    assert.equal(clicked,1);assert.equal(removed,1);assert.equal(refreshed,1);
}
console.log('Approval opens background removal; cutout save advances only on success; asset export starts the ZIP download.');
