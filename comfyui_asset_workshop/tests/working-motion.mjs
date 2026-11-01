import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createRequire} from 'node:module';
const {chromium}=createRequire(import.meta.url)('playwright');
const root=new URL('../web/',import.meta.url),css=readFileSync(new URL('single-image.css',root),'utf8');
const svg=readFileSync(new URL('assets/mumblebox-working.svg',root),'utf8');
const browser=await chromium.launch({headless:true,...(process.env.FOUNDRY_BROWSER_CHANNEL?{channel:process.env.FOUNDRY_BROWSER_CHANNEL}:{})});
try {
 const page=await browser.newPage();
 await page.setContent('<!doctype html><section class="aw-single-controls"><span class="activity-star"><img></span></section><div id="svg"></div>');
 await page.addStyleTag({content:css});
 const metrics=await page.evaluate(async svg=>{
   document.getElementById('svg').innerHTML=svg;
   const image=document.querySelector('.activity-star img'),animation=image.getAnimations()[0];
   animation.pause();
   const vector=document.querySelector('svg');vector.pauseAnimations();
   const native=vector.querySelector('animateTransform'),group=native.parentElement;
   const duration=animation.effect.getComputedTiming().duration/1000;
   const vectorDuration=parseFloat(native.getAttribute('dur'));
   const frame=()=>new Promise(resolve=>requestAnimationFrame(resolve));
   const angle=m=>Math.atan2(m.b,m.a)*180/Math.PI;
   const delta=(a,b)=>((b-a+540)%360)-180;
   const cssAngle=async t=>{animation.currentTime=t*1000;await frame();return angle(new DOMMatrix(getComputedStyle(image).transform));};
   const svgAngle=async t=>{vector.setCurrentTime(t);await frame();return angle(group.transform.animVal.getItem(0).matrix);};
   const analyze=async read=>{
     const velocity=async f=>{const t=duration*f;return delta(await read(t),await read(t+.01))/.01;};
     const early=await velocity(.02),middle=await velocity(.32),late=await velocity(.72);
     const rest=Math.abs(delta(await read(duration*.83),await read(duration*.94)));
     let total=0,previous=await read(0);
     for(let n=1;n<=90;n++){const current=await read(duration*.75*n/90);total+=delta(previous,current);previous=current;}
     return {early,middle,late,rest,turns:total/360};
   };
   return {duration,vectorDuration,css:await analyze(cssAngle),svg:await analyze(svgAngle)};
 },svg);
 assert.equal(metrics.duration,metrics.vectorDuration,'App and SVG must share one duration');
 for(const [name,m] of Object.entries({CSS:metrics.css,SVG:metrics.svg})){
   assert.ok(m.middle>m.early*1.5,name+' must accelerate naturally; '+JSON.stringify(m));
   assert.ok(m.middle>m.late*1.5,name+' must slow before resting; '+JSON.stringify(m));
   assert.ok(Math.abs(m.turns-3)<.01,name+' must make exactly three turns');
   assert.ok(m.rest<.01,name+' must remain still during its rest');
 }
 console.log('PASS: CSS and SVG accelerate, make three turns, decelerate and rest with matching duration.');
 console.log(JSON.stringify(metrics));
} finally {
 if(browser.isConnected())await Promise.race([new Promise(resolve=>browser.once('disconnected',resolve)),browser.close()]);
}
process.exit(0);
