(()=>{
const C=window.SetCalc,$=s=>document.querySelector(s);
const COL={XLB:'#d6a24a',XLC:'#e0457b',XLE:'#7fb04a',XLF:'#a78bfa',XLI:'#f59e0b',XLK:'#c6e84b',XLP:'#4f8fd6',XLRE:'#8b93e8',XLU:'#b5703b',XLV:'#2dd4bf',XLY:'#ef4444',
 ICON:'#e0457b',IEEX:'#facc15',IFNC:'#a78bfa',IMAT:'#d6a24a',IMOB:'#8b93e8',INDX:'#f59e0b',UTIL:'#4f8fd6',SPY:'#f4f1ea',IBOV:'#f4f1ea'};
const PERS=['1D','5D','10D','MTD','1M','QTD','3M','6M','YTD','1Y','3Y','5Y','10Y'],ROLLS=['1M','3M','6M','12M'],HORS=['1Y','3Y','5Y','10Y'];
const S={tab:'us',mode:'acc',per:'YTD',rel:false,roll:'3M',hor:'5Y',off:new Set(),hl:null,hover:null,lang:'pt'};
let D=null,L=I18N.pt;
const tr=(k,o={})=>(L[k]??I18N.pt[k]??k).replace(/\{(\w+)\}/g,(_,x)=>o[x]??'');
const p2=x=>String(x).padStart(2,'0');
// horário/data em Brasília (America/Sao_Paulo) de um ISO UTC
const hm=iso=>new Intl.DateTimeFormat('pt-BR',{timeZone:'America/Sao_Paulo',hour:'2-digit',minute:'2-digit',hour12:false}).format(new Date(iso));
const dBRT=iso=>new Intl.DateTimeFormat('en-CA',{timeZone:'America/Sao_Paulo',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(iso));
const fd=(ms,y=true)=>{const d=new Date(ms),dd=d.getUTCDate(),mm=d.getUTCMonth(),yy=d.getUTCFullYear();
 return S.lang==='en'?L.mes[mm]+' '+dd+(y?', '+yy:''):p2(dd)+'/'+p2(mm+1)+(y?'/'+yy:'')};
const pct=v=>v==null?'—':(v>0?'+':v<0?'−':'')+Math.abs(v*100).toFixed(Math.abs(v)<.1?2:1).replace('.',L.dec)+'%';

function compute(){
 const X=D[S.tab],bm=X.bench,keys=S.rel?X.order:[...X.order,bm];let src,i0,k=0,weekly;
 if(S.mode==='acc'){weekly=C.WEEKLY_PERS.includes(S.per);src=weekly?X.W:X.D;i0=C.windowStart(src.t,S.per)}
 else{weekly=S.hor!=='1Y';src=weekly?X.W:X.D;k=weekly?C.KW[S.roll]:C.KD[S.roll];const t=src.t;i0=Math.max(0,C.lastLE(t,C.minus(t[t.length-1],C.MON[S.hor])))}
 const r=C.compute(src,{keys,bm,i0,mode:S.mode,rel:S.rel,k}),n=r.t.length,end={};
 for(const kk of keys)end[kk]=r.s[kk][n-1];
 return{t:r.t,s:r.s,late:r.late,keys,bm,end,weekly,k,base:src.t[i0]};
}

// ---------- gráfico (canvas) ----------
const cv=$('#chart'),cx=cv.getContext('2d');let cur=null,prev=null,anim=0,cw=0,ch=0;
const mob=()=>innerWidth<700;
function size(){const r=cv.getBoundingClientRect(),dp=devicePixelRatio||1;cw=r.width;ch=r.height;cv.width=cw*dp;cv.height=ch*dp;cx.setTransform(dp,0,0,dp,0,0)}
function niceTicks(a,b,m=6){const sp=(b-a)||.01,st0=sp/m,mag=10**Math.floor(Math.log10(st0)),st=[1,2,2.5,5,10].map(x=>x*mag).find(x=>x>=st0);const o=[];for(let v=Math.ceil(a/st)*st;v<=b+1e-12;v+=st)o.push(+v.toFixed(10));return o}
function range(st){let lo=0,hi=0;for(const k of st.keys){if(S.off.has(k))continue;for(const v of st.s[k])if(v!=null){if(v<lo)lo=v;if(v>hi)hi=v}}const pad=(hi-lo)*.06||.01;return[lo-pad,hi+pad]}
function resample(a,m){if(a.length===m)return a;const o=new Array(m);for(let j=0;j<m;j++){const f=m===1?0:j/(m-1)*(a.length-1),i=Math.floor(f),w=f-i,x=a[i],y=a[Math.min(i+1,a.length-1)];o[j]=x==null||y==null?(x??y):x+(y-x)*w}return o}
const ease=x=>x<.5?4*x*x*x:1-(-2*x+2)**3/2;
function frame(p){ // p em [0,1]: interpola de prev para cur
 const st=cur,m=st.t.length,e=ease(p);let s=st.s,yr=st.yr;
 if(prev&&p<1){s={};for(const k of st.keys){const tg=st.s[k],pv=prev.s[k]?resample(prev.s[k],m):null;s[k]=tg.map((v,j)=>v==null?null:(pv&&pv[j]!=null?pv[j]+(v-pv[j])*e:v))}
  yr=[prev.yr[0]+(st.yr[0]-prev.yr[0])*e,prev.yr[1]+(st.yr[1]-prev.yr[1])*e]}
 draw(st,s,yr,p);
}
function xLabel(ms,u){const d=new Date(ms);return u==='y'?String(d.getUTCFullYear()):u==='m'?L.mes[d.getUTCMonth()]+'/'+String(d.getUTCFullYear()).slice(2):fd(ms,false)}
function draw(st,s,yr,p){
 const W=cw,H=ch,mr=mob()?52:98,ml=8,mt=12,mb=26,pw=W-ml-mr,ph=H-mt-mb,m=st.t.length;
 const X=j=>ml+(m===1?pw:j/(m-1)*pw),Y=v=>mt+(yr[1]-v)/(yr[1]-yr[0])*ph;
 cx.clearRect(0,0,W,H);cx.font='10.5px ui-monospace,Menlo,Consolas,monospace';
 for(const v of niceTicks(yr[0],yr[1],mob()?5:7)){const y=Y(v);cx.strokeStyle=v===0?'rgba(244,241,234,.35)':'rgba(255,255,255,.06)';cx.setLineDash(v===0?[3,4]:[]);cx.beginPath();cx.moveTo(ml,y);cx.lineTo(ml+pw,y);cx.stroke();cx.setLineDash([]);cx.fillStyle='#5f5f68';cx.textAlign='left';cx.fillText(pct(v).replace(/[.,]0%$/,'%'),ml+2,y-4)}
 // eixo x: marcas em fronteiras de calendário (dia, mês ou ano), sem rótulos repetidos
 cx.fillStyle='#8a8a93';let lastR=-1e9;
 for(const{j,u}of C.timeTicks(st.t,mob()?4:7)){const lab=xLabel(st.t[j],u),w=cx.measureText(lab).width,x=Math.min(Math.max(X(j),ml+w/2),ml+pw-w/2);
  if(x-w/2<lastR+10)continue;cx.textAlign='center';cx.fillText(lab,x,H-8);lastR=x+w/2;
  cx.strokeStyle='rgba(255,255,255,.08)';cx.beginPath();cx.moveTo(X(j),mt+ph);cx.lineTo(X(j),mt+ph+4);cx.stroke()}
 const hl=S.hl,order=[...st.keys].sort((a,b)=>(a===hl)-(b===hl));
 for(const k of order){if(S.off.has(k))continue;const a=s[k],isB=k===st.bm;cx.beginPath();let on=false;
  for(let j=0;j<m;j++){const v=a[j];if(v==null){on=false;continue}const x=X(j),y=Y(v);on?cx.lineTo(x,y):cx.moveTo(x,y);on=true}
  cx.strokeStyle=COL[k];cx.globalAlpha=hl&&hl!==k?.12:isB?.85:(S.mode==='rot'&&!hl?.75:.95);cx.lineWidth=hl===k?2.6:isB?1.6:1.4;cx.setLineDash(isB?[5,4]:[]);cx.lineJoin='round';cx.stroke();cx.setLineDash([]);cx.globalAlpha=1}
 // etiquetas no fim de cada linha, com anti-colisão
 const tags=st.keys.filter(k=>!S.off.has(k)&&s[k][m-1]!=null).map(k=>({k,v:s[k][m-1],y:Y(s[k][m-1])})).sort((a,b)=>a.y-b.y);
 const hh=15;for(let i=1;i<tags.length;i++)if(tags[i].y-tags[i-1].y<hh)tags[i].y=tags[i-1].y+hh;
 const over=tags.length?tags[tags.length-1].y-(mt+ph):0;if(over>0)for(const t of tags)t.y-=over;for(let i=tags.length-2;i>=0;i--)if(tags[i+1].y-tags[i].y<hh)tags[i].y=tags[i+1].y-hh;
 cx.font='600 10px ui-monospace,Menlo,Consolas,monospace';
 for(const t of tags){const txt=mob()?t.k:t.k+' '+pct(t.v),w=cx.measureText(txt).width+8,x=ml+pw+4;cx.globalAlpha=hl&&hl!==t.k?.3:1;cx.fillStyle=COL[t.k];cx.fillRect(x,t.y-hh/2+1,w,hh-2);cx.fillStyle='#050506';cx.textAlign='left';cx.fillText(txt,x+4,t.y+3.5);cx.globalAlpha=1}
 if(S.hover!=null&&p>=1){const j=S.hover,x=X(j);cx.strokeStyle='rgba(244,241,234,.35)';cx.beginPath();cx.moveTo(x,mt);cx.lineTo(x,mt+ph);cx.stroke();
  for(const k of st.keys){if(S.off.has(k))continue;const v=st.s[k][j];if(v==null)continue;cx.fillStyle=COL[k];cx.globalAlpha=hl&&hl!==k?.3:1;cx.beginPath();cx.arc(x,Y(v),hl===k?4:2.6,0,7);cx.fill();cx.globalAlpha=1}}
 cur.geo={X,Y,ml,pw,m,yr};
}
function animate(){cancelAnimationFrame(anim);if(!prev){frame(1);return}const t0=performance.now(),dur=520*(window.__slow||1);const f=now=>{const p=Math.min(1,(now-t0)/dur);frame(p);if(p<1)anim=requestAnimationFrame(f);else prev=null};anim=requestAnimationFrame(f)}

// ---------- ranking (também é a legenda) ----------
const rk=$('#rank');let rows={},RH=36;
function rank(st){
 const keys=[...st.keys].sort((a,b)=>(st.end[b]??-9)-(st.end[a]??-9)),vals=keys.map(k=>st.end[k]).filter(v=>v!=null);
 const lo=Math.min(0,...vals),hi=Math.max(0,...vals),sp=(hi-lo)||1,z=-lo/sp*100;
 for(const k in rows)if(!st.keys.includes(k)){rows[k].remove();delete rows[k]}
 keys.forEach((k,i)=>{let r=rows[k];
  if(!r){r=rows[k]=document.createElement('div');r.className='rr';r.innerHTML=`<div class="tk"><i style="background:${COL[k]}"></i>${k}<span class="nm">${L.names[k]}</span></div><div class="tr"><div class="bar" style="background:${COL[k]}"></div></div><div class="v" style="background:${COL[k]}"></div>`;
   r.style.transform=`translateY(${i*RH}px)`;
   r.onclick=()=>{clearTimeout(r._t);r._t=setTimeout(()=>{S.off.has(k)?S.off.delete(k):S.off.add(k);refresh(false)},220)};
   r.ondblclick=()=>{clearTimeout(r._t);const others=cur.keys.filter(x=>x!==k),isol=others.every(x=>S.off.has(x));S.off=isol?new Set():new Set(others);refresh(false)};
   r.onmouseenter=()=>{S.hl=k;paintHl()};r.onmouseleave=()=>{S.hl=null;paintHl()};rk.appendChild(r)}
  const v=st.end[k];r.classList.toggle('off',S.off.has(k));r.classList.toggle('bm',k===st.bm);
  r.style.transform=`translateY(${i*RH}px)`;r.querySelector('.tr').style.setProperty('--z',z+'%');
  const b=r.querySelector('.bar'),x=v==null?z:(v-lo)/sp*100;b.style.left=Math.min(z,x)+'%';b.style.width=Math.abs(x-z)+'%';
  r.querySelector('.v').textContent=pct(v)+(st.late[k]?'*':'');
 });
 rk.style.height=keys.length*RH+'px';rk.style.setProperty('--rh',RH+'px');
}
// ---------- encaixe na viewport (desktop) ----------
// No desktop (grade em 2 colunas) a altura do gráfico e das linhas do ranking sai do espaço que sobra
// abaixo do topo da grade, para gráfico (com eixo x) e ranking caberem sem rolar. Na Rotação o
// heatmap entra junto só se ainda sobrar >= FULL px para o gráfico; senão ele fica abaixo da dobra.
const FULL=380,bot=e=>e.getBoundingClientRect().bottom,lastVis=el=>[...el.children].filter(e=>e.getClientRects().length).pop();
function fit(){
 let h=null;RH=36;
 if(innerWidth>1000){
  const g=$('.grid'),card=$('.chartcard'),rc=$('.rankcard'),hb=$('#heatBox'),px=(e,p)=>parseFloat(getComputedStyle(e)[p])||0;
  const avail=innerHeight-(g.getBoundingClientRect().top+px(g,'paddingTop'))-14;
  const ct=card.getBoundingClientRect().top,cvh=cv.getBoundingClientRect().height,le=lastVis(card);
  const content=bot(le)+px(le,'marginBottom')+px(card,'paddingBottom')-ct;
  const heatH=hb.hidden?0:bot(hb)-bot($('#cwrap'));
  const chrome=content-cvh-heatH;
  h=avail-chrome;if(heatH&&h-heatH>=FULL)h-=heatH;
  h=Math.round(Math.max(300,Math.min(620,h)));
  const rl=lastVis(rc),rch=bot(rl)+px(rl,'marginBottom')+px(rc,'paddingBottom')-rc.getBoundingClientRect().top-rk.getBoundingClientRect().height;
  const n=cur?cur.keys.length:12,target=Math.max(avail,chrome+h+heatH);
  RH=Math.max(26,Math.min(36,Math.floor((target-rch)/n)));
 }
 if(h==null)cv.style.removeProperty('--ch');else cv.style.setProperty('--ch',h+'px');
 size();
}
function paintHl(){for(const k in rows)rows[k].classList.toggle('hl',S.hl===k);if(cur){frame(1);if(S.hover!=null)tip()}}

// ---------- heatmap de liderança (Rotação) ----------
const hv=$('#heat'),hx=hv.getContext('2d');
function heat(st){
 const keys=st.keys.filter(k=>k!==st.bm),m=st.t.length,W=hv.getBoundingClientRect().width,rh=mob()?13:15,lw=46,H=keys.length*rh+18,dp=devicePixelRatio||1;
 hv.style.height=H+'px';hv.width=W*dp;hv.height=H*dp;hx.setTransform(dp,0,0,dp,0,0);hx.clearRect(0,0,W,H);
 const cols=Math.min(m,Math.floor((W-lw)/3)),cwid=(W-lw)/cols,ord=[...keys].sort((a,b)=>(st.end[b]??-9)-(st.end[a]??-9));
 hx.font='600 10px ui-monospace,Menlo,Consolas,monospace';hx.textAlign='left';
 ord.forEach((k,r)=>{hx.fillStyle=COL[k];hx.fillText(k,0,r*rh+rh-4)});
 for(let c=0;c<cols;c++){const j=Math.round(c/(cols-1||1)*(m-1));const vs=keys.map(k=>[k,st.s[k][j]]).filter(x=>x[1]!=null).sort((a,b)=>b[1]-a[1]);const n=vs.length;
  vs.forEach(([k],pos)=>{const r=ord.indexOf(k),f=n>1?pos/(n-1):0;hx.fillStyle=f<.5?`rgba(45,212,191,${(.5-f)*1.9+.04})`:`rgba(248,113,113,${(f-.5)*1.9+.04})`;hx.fillRect(lw+c*cwid,r*rh+1,Math.ceil(cwid),rh-2)})}
 hx.fillStyle='#8a8a93';hx.font='10px ui-monospace,Menlo,Consolas,monospace';hx.textAlign='left';hx.fillText(fd(st.t[0]),lw,H-3);hx.textAlign='right';hx.fillText(fd(st.t[m-1]),W,H-3);
}

// ---------- tooltip ----------
const tp=$('#tip');
function tip(){const st=cur,j=S.hover;if(j==null){tp.hidden=true;return}
 const ks=st.keys.filter(k=>!S.off.has(k)&&st.s[k][j]!=null).sort((a,b)=>st.s[b][j]-st.s[a][j]);
 tp.innerHTML=`<div class="d">${fd(st.t[j])}${st.weekly?' <span class="ill">'+tr('wk_tip')+'</span>':''}</div>`+ks.map(k=>`<div class="r${k===S.hl?' h':''}${k===st.bm?' bm':''}"><span><i style="background:${COL[k]}"></i>${k}</span><b>${pct(st.s[k][j])}</b></div>`).join('');
 tp.hidden=false;const x=st.geo.X(j),w=tp.offsetWidth;tp.style.left=(x+16+w>cw-10?x-16-w:x+16)+'px';}
cv.addEventListener('pointermove',e=>{if(!cur?.geo)return;const r=cv.getBoundingClientRect(),g=cur.geo,mx=e.clientX-r.left,my=e.clientY-r.top;
 const j=Math.max(0,Math.min(g.m-1,Math.round((mx-g.ml)/g.pw*(g.m-1))));S.hover=j;
 let best=null,bd=18;for(const k of cur.keys){if(S.off.has(k))continue;const v=cur.s[k][j];if(v==null)continue;const d=Math.abs(g.Y(v)-my);if(d<bd){bd=d;best=k}}
 S.hl=best;for(const k in rows)rows[k].classList.toggle('hl',S.hl===k);frame(1);tip()});
cv.addEventListener('pointerleave',()=>{S.hover=null;S.hl=null;tp.hidden=true;paintHl()});

// ---------- idioma ----------
function applyLang(){L=I18N[S.lang];document.documentElement.lang=L.html;document.title=L.title;
 document.querySelectorAll('[data-i]').forEach(e=>{const v=L.ui[e.dataset.i];if(v!=null)e.innerHTML=v});
 document.querySelectorAll('#lang button').forEach(b=>b.classList.toggle('on',b.dataset.l===S.lang));
 try{localStorage.setItem('setores_lang',S.lang)}catch(_){}
 const u=new URL(location.href);S.lang==='en'?u.searchParams.set('lang','en'):u.searchParams.delete('lang');history.replaceState(null,'',u)}
function readLang(){const q=new URLSearchParams(location.search).get('lang');if(q==='en'||q==='pt')return q;try{const v=localStorage.getItem('setores_lang');if(v==='en'||v==='pt')return v}catch(_){}
 return'pt'}
document.querySelectorAll('#lang button').forEach(b=>b.onclick=()=>{if(S.lang===b.dataset.l)return;S.lang=b.dataset.l;applyLang();if(D){rows={};rk.innerHTML='';pillsAll();header();refresh(false)}});

// ---------- UI ----------
function pills(el,list,key){el.innerHTML=list.map(v=>`<button data-v="${v}" class="${S[key]===v?'on':''}">${L.per[v]}</button>`).join('');el.onclick=e=>{const b=e.target.closest('button');if(!b)return;S[key]=b.dataset.v;el.querySelectorAll('button').forEach(x=>x.classList.toggle('on',x===b));refresh(true)}}
function pillsAll(){pills($('#per'),PERS,'per');pills($('#roll'),ROLLS,'roll');pills($('#hor'),HORS,'hor')}
function seg(el,key,cb){el.onclick=e=>{const b=e.target.closest('button');if(!b||S[key]===b.dataset.v)return;S[key]=b.dataset.v;el.querySelectorAll('button').forEach(x=>x.classList.toggle('on',x===b));cb&&cb();refresh(true)}}
function header(){const en=S.lang==='en';
 const stale=['us','br'].filter(k=>D[k].stale).map(k=>tr('stale',{t:tr('tab_'+k)}));
 const part=k=>D[k].intraday?' <span class="part">'+tr('partial')+'</span>':'';
 const intra=['us','br'].filter(k=>D[k].intraday&&D[k].as_of_ts).map(k=>tr('intra',{t:tr('tab_'+k),h:hm(D[k].as_of_ts)}));
 const g=D.generated_at,upd=g?(dBRT(g)===dBRT(new Date().toISOString())?tr('upd_at',{h:hm(g)}):tr('upd_on',{d:fd(Date.parse(dBRT(g))),h:hm(g)})):'';
 const notes=intra.concat(stale);
 $('#status').innerHTML=tr('status',{us:fd(Date.parse(D.us.last))+part('us'),br:fd(Date.parse(D.br.last))+part('br'),upd})+(notes.length?'<br><span class="warn">'+notes.join(' · ')+'</span>':'');
 $('#srcs').textContent=tr('srcs',{us:en?D.us.src_en||D.us.src:D.us.src,br:en?D.br.src_en||D.br.src:D.br.src})}
function refresh(tween){
 const X=D[S.tab],bm=X.bench;
 $('#rel').setAttribute('aria-pressed',S.rel);$('#relL').textContent='/'+bm;
 $('#accCtl').hidden=S.mode!=='acc';$('#rotCtl').hidden=S.mode!=='rot';$('#heatBox').hidden=S.mode!=='rot';
 if(tween&&cur)prev={s:cur.s,yr:cur.yr};else prev=null;
 cur=compute();cur.yr=range(cur);S.hover=null;tp.hidden=true;
 const lbl=S.mode==='acc'?L.per[S.per]:L.per[S.roll],n=cur.t.length;
 $('#cTitle').textContent=(S.mode==='acc'?tr('acc_t')+' · '+lbl:tr('rot_t',{r:lbl})+' · '+tr('hor_t',{h:L.per[S.hor]}));
 $('#cSub').textContent=S.rel?tr('rel_s',{b:bm}):tr(S.mode==='acc'?'abs_s':'rot_s');
 $('#cDates').textContent=(S.mode==='acc'?tr('base',{d:fd(cur.base)}):'')+fd(cur.t[n-1])+(D[S.tab].intraday&&cur.t[n-1]===Date.parse(D[S.tab].last)?' · '+tr('partial_at',{h:hm(D[S.tab].as_of_ts)}):'');
 $('#rTitle').textContent=S.mode==='acc'?tr('rank_acc',{p:lbl}):tr('rank_rot',{r:lbl});$('#rSub').textContent=S.rel?'/'+bm:tr('rsub_'+S.tab);
 const notes=Object.entries(cur.late).map(([k,ms])=>'<b>*</b> '+tr('since',{t:k,d:fd(ms)}));
 $('#notes').innerHTML=[cur.weekly?tr('weekly'):tr('daily'),...(D[S.tab].intraday?[tr('last_partial')]:[]),...notes].join(' · ');
 if(S.mode==='rot'){leader(cur);heat(cur)}else $('#leader').innerHTML='';
 fit();rank(cur);animate();
}
function leader(st){const keys=st.keys.filter(k=>k!==st.bm),m=st.t.length,top=j=>keys.filter(k=>st.s[k][j]!=null).sort((a,b)=>st.s[b][j]-st.s[a][j])[0];
 const L0=top(m-1);if(!L0){$('#leader').innerHTML='';return}let n=0;for(let j=m-1;j>=0&&top(j)===L0;j--)n++;
 $('#leader').innerHTML=tr('leader',{t:L0,n:L.names[L0],r:L.per[S.roll],k:n,u:st.weekly?(n===1?L.one_wk:L.wk):(n===1?L.one_dd:L.dd),s:n===1?'':(st.weekly?L.seq_f:L.seq_m)})+(n===m?tr('whole'):'')}
function start(data){D=data;for(const k of['us','br']){D[k].D=C.dec(D[k].d);D[k].W=C.dec(D[k].w)}
 seg($('#tab'),'tab',()=>{S.off.clear();rows={};rk.innerHTML='';prev=null});seg($('#mode'),'mode');
 $('#rel').onclick=()=>{S.rel=!S.rel;refresh(true)};$('#all').onclick=()=>{S.off.clear();refresh(false)};
 pillsAll();header();size();refresh(false);
 addEventListener('resize',()=>{if(cur){if(S.mode==='rot')heat(cur);fit();rank(cur);frame(1)}else size()});
 // ganchos para testes/screenshots
 window.__S=S;window.__g=()=>cur;window.__set=(o,tw=true)=>{Object.assign(S,o);document.querySelectorAll('#tab button').forEach(b=>b.classList.toggle('on',b.dataset.v===S.tab));document.querySelectorAll('#mode button').forEach(b=>b.classList.toggle('on',b.dataset.v===S.mode));
  for(const id of['per','roll','hor'])document.querySelectorAll('#'+id+' button').forEach(b=>b.classList.toggle('on',b.dataset.v===S[id]));refresh(tw)};
 document.body.classList.add('ready')}
S.lang=readLang();applyLang();$('#status').textContent=tr('loading');
fetch('data/setores.json',{cache:'no-cache'}).then(r=>{if(!r.ok)throw new Error(r.status);return r.json()}).then(start)
 .catch(e=>{console.error(e);$('#status').innerHTML='<span class="warn">'+tr('load_err')+'</span>'});
})();
