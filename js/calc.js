// Cálculos puros da página (sem DOM): janelas, retornos acumulados/móveis e marcas do eixo x.
// Usado por js/app.js no navegador e por tests/calc.test.mjs no Node.
(function(root){
const DAY=864e5;
const MON={'1M':1,'3M':3,'6M':6,'1Y':12,'3Y':36,'5Y':60,'10Y':120};
const KD={'1M':21,'3M':63,'6M':126,'12M':252},KW={'1M':4,'3M':13,'6M':26,'12M':52};
const WEEKLY_PERS=['3Y','5Y','10Y'];
// {d0, gaps (dias entre datas), s} -> {t: datas em ms UTC, s}
function dec(e){const t=[Date.parse(e.d0+'T00:00:00Z')];for(const g of e.gaps)t.push(t[t.length-1]+g*DAY);return{t,s:e.s}}
// último índice com t[i] <= x (busca binária); -1 se nenhum
function lastLE(t,x){let lo=0,hi=t.length-1,r=-1;while(lo<=hi){const m=(lo+hi)>>1;if(t[m]<=x){r=m;lo=m+1}else hi=m-1}return r}
// volta mo meses no calendário, preservando o dia (limitado ao fim do mês)
function minus(ms,mo){const d=new Date(ms),day=d.getUTCDate();d.setUTCDate(1);d.setUTCMonth(d.getUTCMonth()-mo);const dim=new Date(Date.UTC(d.getUTCFullYear(),d.getUTCMonth()+1,0)).getUTCDate();d.setUTCDate(Math.min(day,dim));return+d}
// índice da base da janela: último fechamento antes do início
function windowStart(t,per){const n=t.length,T=t[n-1],d=new Date(T),y=d.getUTCFullYear(),m=d.getUTCMonth();let i;
 if(per==='1D')i=n-2;else if(per==='5D')i=n-6;else if(per==='10D')i=n-11;
 else if(per==='MTD')i=lastLE(t,Date.UTC(y,m,1)-1);
 else if(per==='QTD')i=lastLE(t,Date.UTC(y,Math.floor(m/3)*3,1)-1);
 else if(per==='YTD')i=lastLE(t,Date.UTC(y,0,1)-1);
 else i=lastLE(t,minus(T,MON[per]));
 return Math.max(i,0)}
// séries de uma aba: modo 'acc' (acumulado desde a base) ou 'rot' (retorno móvel de k pontos)
// rel=true divide cada setor pelo benchmark (o benchmark sai da lista). Retorna também a 1ª data válida quando > base.
function compute(src,o){const{keys,bm,i0,mode,rel,k}=o,N=src.t.length,n=N-i0,B=src.s[bm],out={},late={};
 for(const key of keys){const p=src.s[key];
  const raw=i=>{const v=p[i];if(v==null)return null;if(rel&&key!==bm){const b=B[i];return b?v/b:null}return v};
  const arr=new Array(n).fill(null);
  if(mode==='acc'){let base=null,bi=-1;for(let i=i0;i<N;i++){const v=raw(i);if(v!=null){base=v;bi=i;break}}
   if(base!=null)for(let i=bi;i<N;i++){const v=raw(i);arr[i-i0]=v==null?null:v/base-1}
   if(bi>i0)late[key]=src.t[bi];
  }else{let first=-1;for(let i=i0;i<N;i++){const a=raw(i),b=i-k>=0?raw(i-k):null;if(a!=null&&b!=null){arr[i-i0]=a/b-1;if(first<0)first=i}}
   if(first>i0)late[key]=src.t[first]}
  out[key]=arr}
 return{t:src.t.slice(i0),s:out,late}}
// marcas do eixo x em fronteiras de calendário: rótulos nunca se repetem (ex.: o ano aparece uma vez só)
function timeTicks(t,maxN){const m=t.length;if(m<2)return[{j:0,u:'d'}];const span=(t[m-1]-t[0])/DAY;
 if(span<100){const o=[],nt=Math.min(maxN,m);for(let q=0;q<nt;q++)o.push({j:Math.round(q/(nt-1)*(m-1)),u:'d'});return o.filter((x,i,a)=>!i||x.j!==a[i-1].j)}
 const yearly=span>=1200,key=ms=>{const d=new Date(ms);return yearly?d.getUTCFullYear():d.getUTCFullYear()*12+d.getUTCMonth()};
 const b=[];for(let j=1;j<m;j++)if(key(t[j])!==key(t[j-1]))b.push(j);
 const steps=yearly?[1,2,5,10]:[1,2,3,6,12];let st=steps[steps.length-1];
 for(const s of steps){const c=b.filter(j=>{const v=key(t[j]);return v%s===0}).length;if(c<=maxN){st=s;break}}
 return b.filter(j=>key(t[j])%st===0).map(j=>({j,u:yearly?'y':'m'}))}
const api={DAY,MON,KD,KW,WEEKLY_PERS,dec,lastLE,minus,windowStart,compute,timeTicks};
if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.SetCalc=api;
})(typeof window!=='undefined'?window:globalThis);
