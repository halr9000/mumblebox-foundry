import {el,button,hint,field} from '../dom.js';
import {request} from '../services.js';
import {dialog} from '../dialogs.js';

export async function gallery(shell){
    const state=shell.imageGalleryState??={search:'',category:'',kind:'all',sort:'newest',cursor:''};
    let disposed=false,sequence=0;const selected=new Set(),body=el('div',{}),more=el('div',{}),message=hint('');
    const cap=await request('images/capabilities');
    const open=id=>{shell.openImageId=id;return shell.openImages('Create Images');};
    async function remove(ids){
        const files=el('input',{type:'checkbox'}),detail=hint('Saved files stay on disk unless you select the separate file deletion option.');
        dialog(shell,ids?'Remove selected images?':'Purge Image Gallery?',el('div',{},detail,
            el('label',{class:'gallery-actions'},files,'Also delete this creation’s saved image files. Copies already used by the 3D workflow are preserved.')),[
            {label:'Cancel',run:close=>close()},
            {label:'Review removal',run:async close=>{
                const review=await request('images/removal-preview',{ids,delete_files:files.checked});close();
                dialog(shell,'Confirm image removal',el('div',{},hint(review.entry_count+' creations · '+review.image_count+' image revisions.'),
                    hint(review.delete_files?'These image files will also be deleted.':'Only the Gallery entries will be removed.')),[
                    {label:'Cancel',run:done=>done()},
                    {label:review.delete_files?'Delete entries and files':'Remove entries',run:async done=>{await request('images/remove',{token:review.token});done();selected.clear();state.cursor='';await load();}}
                ]);
            }}]);
    }
    async function detail(id){
        const record=await request('images/'+id),sides=record.config.paired?['front','back']:['single'];
        const choices=sides.map(side=>{const revision=record.revisions.find(r=>r.id===record.accepted[side]);
            return el('figure',{class:'creator-frame'},el('figcaption',{},side),el('img',{src:revision.url,alt:record.config.name+' '+side}),
                el('small',{},revision.size.join(' × ')+' px'));
        });
        dialog(shell,record.config.name,el('div',{},el('div',{class:'creator-pair','data-paired':String(record.config.paired)},...choices),
            hint(record.config.category+' · '+new Date(record.created*1000).toLocaleString()),
            el('details',{},el('summary',{},'Revisions and generation details'),...record.revisions.map(revision=>el('div',{class:'gallery-actions'},
                el('a',{href:revision.url,target:'_blank',rel:'noopener noreferrer'},revision.side+' · '+new Date(revision.created*1000).toLocaleString()),
                el('span',{class:'badge'},record.accepted[revision.side]===revision.id?'Current':'Retained revision'),
                record.accepted[revision.side]!==revision.id?button('Restore revision',async()=>{await request('images/'+id+'/accept',{revision_id:revision.id,expected:record.accepted[revision.side]});await detail(id);}):null)),
                el('pre',{},JSON.stringify({model:record.config.model,settings:record.config.settings,loras:record.config.loras},null,2)))),[
            {label:'Edit / Continue',primary:true,run:async close=>{close();await open(id);}},
            {label:'Reuse settings',run:async close=>{const copy=await request('images/'+id+'/reuse',{});close();await open(copy.id);}},
            {label:'Close',run:close=>close()}]);
    }
    function card(item){
        const thumbs=Object.entries(item.accepted).map(([side,id])=>el('img',{src:'/mumblebox-foundry/v1/images/'+item.id+'/files/'+id,alt:item.name+' '+side,loading:'lazy'}));
        return el('article',{class:'image-gallery-card'},el('div',{class:'pair-thumbnails'},...thumbs),el('div',{class:'card-copy'},
            el('div',{class:'gallery-actions'},el('input',{type:'checkbox','aria-label':'Select '+item.name,checked:selected.has(item.id),onchange:e=>e.target.checked?selected.add(item.id):selected.delete(item.id)}),el('h3',{},item.name)),
            hint((item.paired?'Front / Back pair':'Single image')+' · '+item.category),
            el('div',{class:'actions'},button('View / Edit',()=>detail(item.id).catch(e=>shell.message(e.message,true))),
                el('a',{href:'/mumblebox-foundry/v1/images/'+item.id+'/package',download:''},'Download Images'),
                button('Delete',()=>remove([item.id]).catch(e=>shell.message(e.message,true)),{class:'danger'}))));
    }
    async function load(append=false){
        const current=++sequence;message.textContent='Loading images…';
        try{
            const result=await request('images?'+new URLSearchParams({...state,limit:24}));if(disposed||current!==sequence)return;
            if(!append)body.replaceChildren();body.append(...result.items.map(card));
            message.textContent=body.childElementCount?body.childElementCount+' creations shown.':'No saved creations match these filters.';
            more.replaceChildren(result.next_cursor?button('Load more',()=>{state.cursor=result.next_cursor;load(true);}):'');
        }catch(error){message.textContent=error.message;}
    }
    const filter=(key,label,choices)=>field(label,el('select',{onchange:e=>{state[key]=e.target.value;state.cursor='';load();}},
        ...choices.map(([value,name])=>el('option',{value,selected:state[key]===value},name))));
    const search=el('input',{value:state.search,placeholder:'Search image names','aria-label':'Search image names',onchange:e=>{state.search=e.target.value;state.cursor='';load();}});
    const host=el('section',{},el('div',{class:'gallery-actions'},button('Create images',()=>shell.openImages('Create Images'),{class:'primary'}),button('Refresh',()=>{state.cursor='';load();}),
        button('Remove selected',()=>{if(!selected.size){message.textContent='Select at least one creation.';return;}remove([...selected]);}),button('Purge Gallery',()=>remove(null),{class:'danger'})),
        el('div',{class:'gallery-filters'},field('Search',search),filter('category','Category',[['','All categories'],...cap.categories.map(c=>[c.id,c.name])]),
            filter('kind','Image set',[['all','All'],['pair','Front / Back pairs'],['single','Single images']]),filter('sort','Order',[['newest','Newest first'],['oldest','Oldest first']])),message,body,more);
    body.className='image-gallery-grid';state.cursor='';await load();
    return {element:host,dispose(){disposed=true;sequence++;shell.imageGalleryScroll=shell.content.scrollTop;}};
}
