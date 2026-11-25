'use strict';
/* VisitFallback cinematic UI. Presentation-only refactor: backend, oracle, and
   Relate/Cypher mutations stay in visitfallback/demo_service.py. */
const $ = id => document.getElementById(id);
const clean = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const clock = value => String(Math.floor(value/60)).padStart(2,'0')+':'+String(value%60).padStart(2,'0');
const sym = name => `<svg class="symbol" aria-hidden="true"><use href="#i-${name}"></use></svg>`;
let loading = false;
let lastSnapshot = null;
let firstRender = true;
function setErr(msg) {const e=$('error');e.hidden=!msg;e.textContent=msg||'';}
function updateProof(id,ok){const el=$(id);el.textContent=ok?'PASS':'FAIL';el.classList.toggle('failed',!ok);}
function effectiveCandidate(need){return need.candidate_name||need.offers.find(o=>o.state==='confirmed')?.person||null;}
function render(s) {
  if(!s || !Array.isArray(s.needs) || !s.proof || !s.cypher || !['A','B','C','D','E'].includes(s.phase))throw Error('Incomplete or unsupported Relate snapshot');
  lastSnapshot=s;
  const {phase,covered,needs,proof}=s;
  document.body.dataset.currentPhase=phase;
  document.body.dataset.coverage=covered?'covered':'not-covered';
  document.querySelectorAll('[data-phase]').forEach(button=>{
    let selected=button.dataset.phase===phase;
    button.classList.toggle('active',selected);
    button.setAttribute('aria-pressed',selected?'true':'false');
  });
  $('connection').innerHTML='<span class="green-dot"></span> Relate connected';
  $('verdict').textContent=covered?'PLAN COVERED':'PLAN NOT COVERED';
  $('phaseNote').textContent=({A:'Sofia covers all three steps.',B:'Sofia cancels.',C:'Return not confirmed.',D:'All three steps are covered.',E:'Celine is double-booked.'})[phase];
  $('count').textContent=s.covered_count+' / '+s.need_count;
  $('confirmation').textContent=s.confirmed_count+' / '+s.need_count;
  const special=phase==='E';
  $('decisionHook').textContent=special?'3 yes. Only 2 possible.':covered?'All steps covered.':'At least one step missing.';
  updateProof('relateProof',Boolean(proof.relate_read));
  updateProof('oracleProof',Boolean(proof.same_outcome));
  updateProof('expected',proof.expected===covered);
  $('cypher').textContent=s.cypher.read+'\n\n'+s.cypher.abilities+'\n\n'+s.cypher.busy;
  renderNeeds(needs);
  renderReason(s);
  renderTimeline(s);
  renderGraph(s);
  if(!firstRender) {
    $('decisionCard').classList.remove('just-updated');
    void $('decisionCard').offsetWidth;
    $('decisionCard').classList.add('just-updated');
  }
  firstRender=false;
  // Never silently show a green proof state on failed independent verification.
  if(!proof.relate_read||!proof.same_outcome||proof.expected!==covered){
    setErr('Verification failed: the connected graph, separate oracle, or expected outcome disagree.');
  }else setErr('');
}
function renderNeeds(needs){
  const names=['Outbound','Escort','Return'];
  $('needs').innerHTML=needs.map((n,i)=>{
    const candidate=effectiveCandidate(n);
    const initials=candidate?candidate.split(/\s+/).map(t=>t.slice(0,1)).slice(0,2).join('').toUpperCase():'?';
    const conflicts=n.conflicts||[];
    const status=n.individually_eligible?'Confirmed · available':conflicts.length?'Confirmed · conflict':'Not covered';
    const isReturn=n.slot.toLowerCase().includes('ret');
    const icon=i===1?'clinic':'car';
    return `<article class="need ${n.individually_eligible?'covered':'missing'}"><div class="need-head"><span class="need-number">0${i+1} / 03</span><span class="need-icon">${sym(icon)}</span></div><div class="need-slot">${clean(names[i]||n.slot)}</div><div class="need-times">${clock(n.start)}–${clock(n.end)} · ${clean(n.origin)} → ${clean(n.destination)}</div><div class="need-person"><span class="avatar">${clean(initials)}</span><span><strong>${clean(candidate||'Not assigned')}</strong><small>${clean(n.required)}</small></span></div><div class="need-verdict">${sym(n.individually_eligible?'check':'x')}${clean(status)}</div>${conflicts.length?`<div class="need-conflict">${conflicts.map(c=>`${clean(c.person)} busy ${clock(c.start)}–${clock(c.end)}`).join('; ')}</div>`:''}<details class="need-offer-details"><summary>Other offers</summary><div class="need-offers">${n.offers.map(o=>`<span class="offer ${clean(o.state)}">${clean(o.person)} · ${clean(o.state)}</span>`).join('')}</div></details></article>`;
  }).join('');
}
function renderReason(s){
 const {phase,covered,needs}=s;
 const conflicts=needs.flatMap(n=>(n.conflicts||[]).map(c=>({slot:n.slot,...c})));
 const missing=needs.filter(n=>!n.individually_eligible);
 const whyTitle=$('whyTitle');const reason=$('reason');const strip=$('conflictStrip');
 strip.hidden=conflicts.length===0;
 if(phase==='E'&&conflicts.length){
   whyTitle.textContent='3 confirmed. 1 conflict.';
   reason.textContent='Celine is double-booked during the return.';
   strip.querySelector('span').textContent=conflicts.map(c=>`${clean(c.person)} busy ${clock(c.start)}–${clock(c.end)} during ${clean(c.slot)}.`).join(' ');
 }else if(covered){
   whyTitle.textContent=phase==='A'?'All covered.':'3 confirmed. 3 executable.';
   reason.textContent='Every step has a compatible helper.';
 }else if(phase==='B'){
   whyTitle.textContent='One cancellation. No coverage.';
   reason.textContent='Offers are not confirmations.';
 }else if(phase==='C'){
   whyTitle.textContent='Return unconfirmed.';
   reason.textContent='Outbound and escort are covered. Return is not.';
 }else{
   whyTitle.textContent='One step cannot be completed.';
   reason.textContent=`${missing.map(n=>n.slot).join(', ')} need a compatible, confirmed helper.`;
 }
}
function renderTimeline(s){
 const conflict=s.needs.some(n=>n.conflicts?.length);
 const bar=$('busyBar');const marker=$('overlapMarker');const label=$('busyBarLabel');
 marker.hidden=!conflict;
 $('otherTime').textContent=conflict?'11:00–11:15':'12:00–12:30';
 label.textContent=conflict?'11:00–11:15':'12:00–12:30';
 $('timelineExplanation').textContent=conflict?'15 minutes overlap.':'No overlap.';
 $('timelineVerdict').innerHTML=conflict?`${sym('x')} <span>Conflict: 15-minute overlap</span>`:`${sym('check')} <span>No scheduling conflict</span>`;
}
function renderGraph(s){
 const palette={ok:'#65ead0',bad:'#ff819b',neutral:'#7eabc2'};
 const nodes=[];const paths=[];const ylist=[93,191,289];
 function node(x,y,w,h,title,detail,type='neutral'){
   let stroke=type==='bad'?palette.bad:type==='ok'?palette.ok:palette.neutral;
   let fill=type==='bad'?'#4a263c':type==='ok'?'#154444':'#17354a';
   nodes.push(`<g class="graph-node"><rect x="${x}" y="${y}" width="${w}" height="${h}" rx="12" fill="${fill}" stroke="${stroke}" stroke-opacity=".85" stroke-width="1.4"/><text x="${x+13}" y="${y+21}" fill="#f2fafd" font-size="14" font-weight="790">${clean(title)}</text><text x="${x+13}" y="${y+40}" fill="#a5c3cf" font-size="11">${clean(detail)}</text></g>`);
 }
 s.needs.forEach((n,i)=>{
  let y=ylist[i],ok=n.individually_eligible,possible=effectiveCandidate(n),bad=n.conflicts?.length>0;
  const state=ok?'ok':'bad';
  const selected=possible||(n.offers.find(o=>o.state==='proposed')?.person)||'Unassigned';
  const title=i===0?'OUTBOUND':i===1?'ESCORT':'RETURN';
  const status=ok?'VALID':bad?'CONFLICT':'MISSING';
  node(20,y-24,196,56,selected,ok?'Confirmed':bad?'Double-booked':'Not confirmed',state);
  node(326,y-24,178,56,title,clock(n.start)+'–'+clock(n.end),state);
  node(617,y-24,166,56,n.required,'Required','neutral');
  node(892,y-24,213,56,status,ok?'Covered':bad?'Double-booked':'Uncovered',state);
  const stroke=ok?palette.ok:palette.bad;
  paths.push(`<path class="graph-link ${ok?'line-ok':'line-bad'}" d="M216 ${y+4} C260 ${y+4} 282 ${y+4} 326 ${y+4}" fill="none" stroke="${stroke}" stroke-width="3"/><path class="graph-link" d="M504 ${y+4} H617" stroke="#5f91a9" stroke-width="2"/><path class="graph-link" d="M783 ${y+4} H892" stroke="${stroke}" stroke-width="2"/>`);
 });
 const hasConflict=s.needs.some(n=>n.conflicts?.length);
 $('graphHint').textContent=hasConflict?'BUSY_DURING · CONFLICT':'RELATE PATHS';
 const banner=hasConflict?`<g><rect x="752" y="320" width="361" height="39" rx="10" fill="#4a293e" stroke="#ff819b"/><text x="765" y="344" font-size="12" font-weight="800" fill="#ffd3db">CELINE → BUSY_DURING → 11:00–11:15</text><path d="M965 315 V289" stroke="#ff819b" stroke-dasharray="5 4" stroke-width="2"/></g>`:``;
 $('graph').innerHTML=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1140 ${hasConflict?375:344}" role="img" aria-label="Graph-derived helper, obligation and capability paths with eligibility results from Relate"><text x="20" y="26" class="column-label">PERSON / OFFER</text><text x="326" y="26" class="column-label">NEED</text><text x="617" y="26" class="column-label">CAPABILITY</text><text x="892" y="26" class="column-label">FEASIBILITY</text>${paths.join('')}${nodes.join('')}${banner}</svg>`;
}
async function fetchState(){
 try{
   const res=await fetch('/api/state',{cache:'no-store'});
   const value=await res.json();
   if(!res.ok)throw Error(value.error||'Relate request failed');
   render(value);
 }catch(error){
   setErr('Relate evaluation failed: '+error.message);
   $('connection').textContent='Relate unverified';
   document.body.dataset.coverage='error';
 }
}
async function changePhase(phase){
 if(loading)return;
 loading=true;
 document.querySelectorAll('[data-phase]').forEach(button=>button.disabled=true);
 try{
   const res=await fetch('/api/phase',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phase})});
   const value=await res.json();
   if(!res.ok)throw Error(value.error||'Relate mutation failed');
   render(value);
 }catch(error){setErr('Mutation or proof failed: '+error.message);}finally{
   loading=false;
   document.querySelectorAll('[data-phase]').forEach(button=>button.disabled=false);
 }
}
document.querySelectorAll('[data-phase]').forEach(b=>b.addEventListener('click',()=>changePhase(b.dataset.phase)));
$('demoJump').addEventListener('click',()=> $('experience').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'}));
$('evidenceJump').addEventListener('click',()=> $('evidence').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'}));
fetchState();
