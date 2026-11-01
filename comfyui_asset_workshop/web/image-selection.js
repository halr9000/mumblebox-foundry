// Bounded edge-following selection. Reduce the image once, not on pointer moves.
export function edgeField(data,width,height){
    const gray=new Float32Array(width*height),cost=new Float32Array(width*height);
    for(let i=0;i<gray.length;i++)gray[i]=(.2126*data[i*4]+.7152*data[i*4+1]+.0722*data[i*4+2])/255;
    for(let y=0;y<height;y++)for(let x=0;x<width;x++){
        const dx=gray[y*width+Math.min(width-1,x+1)]-gray[y*width+Math.max(0,x-1)];
        const dy=gray[Math.min(height-1,y+1)*width+x]-gray[Math.max(0,y-1)*width+x];
        cost[y*width+x]=1+18*(1-Math.min(1,Math.hypot(dx,dy)))**3;
    }
    return {cost,width,height};
}
export function magneticPath(field,start,end){
    const {width:w,height:h,cost}=field;
    if(w*h>65536)throw Error('Magnetic selection is limited to a 256-pixel guide.');
    const index=p=>Math.max(0,Math.min(h-1,Math.round(p[1])))*w+Math.max(0,Math.min(w-1,Math.round(p[0])));
    const first=index(start),last=index(end);if(first===last)return [end];
    const distances=new Float32Array(w*h).fill(Infinity),previous=new Int32Array(w*h).fill(-1),visited=new Uint8Array(w*h),heap=[];
    const heuristic=id=>Math.hypot(id%w-last%w,Math.floor(id/w)-Math.floor(last/w));
    function push(id,value){let i=heap.length;heap.push([id,value]);while(i){const p=(i-1)>>1;if(heap[p][1]<=value)break;heap[i]=heap[p];i=p;}heap[i]=[id,value];}
    function pop(){const top=heap[0],tail=heap.pop();if(heap.length){let i=0;while(i*2+1<heap.length){let j=i*2+1;if(j+1<heap.length&&heap[j+1][1]<heap[j][1])j++;if(heap[j][1]>=tail[1])break;heap[i]=heap[j];i=j;}heap[i]=tail;}return top[0];}
    distances[first]=0;push(first,heuristic(first));
    while(heap.length){const current=pop();if(visited[current])continue;if(current===last)break;visited[current]=1;
        const x=current%w,y=Math.floor(current/w);
        for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++){
            if(!(dx||dy)||x+dx<0||x+dx>=w||y+dy<0||y+dy>=h)continue;
            const next=(y+dy)*w+x+dx,nextCost=distances[current]+(cost[next]+cost[current])*.5*(dx&&dy?Math.SQRT2:1);
            if(nextCost<distances[next]){distances[next]=nextCost;previous[next]=current;push(next,nextCost+heuristic(next));}
        }
    }
    if(previous[last]<0)return [end];
    const points=[];for(let p=last;p!==first&&p>=0;p=previous[p])points.push([p%w,Math.floor(p/w)]);
    return points.reverse();
}
export function imageMagnet(source){
    const scale=Math.min(1,256/Math.max(source.naturalWidth,source.naturalHeight));
    const canvas=document.createElement('canvas');canvas.width=Math.max(1,Math.round(source.naturalWidth*scale));canvas.height=Math.max(1,Math.round(source.naturalHeight*scale));
    const ctx=canvas.getContext('2d',{willReadFrequently:true});ctx.drawImage(source,0,0,canvas.width,canvas.height);
    const field=edgeField(ctx.getImageData(0,0,canvas.width,canvas.height).data,canvas.width,canvas.height);
    return (start,end)=>magneticPath(field,start.map(n=>n*scale),end.map(n=>n*scale)).map(point=>point.map(n=>n/scale));
}
