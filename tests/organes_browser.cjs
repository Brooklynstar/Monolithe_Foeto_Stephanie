// SPDX-License-Identifier: CC-BY-NC-SA-4.0
const assert=require('node:assert/strict'),fs=require('fs');
const {chromium}=require('playwright');
const entree=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),cas=entree.autopsie,url=process.argv[3];
function proche(a,b){if(b==null)assert.equal(a??null,null);else assert.ok(Math.abs(a-b)<Math.max(2e-12,Math.abs(b)*1e-12),`${a} / ${b}`);}
(async()=>{const b=await chromium.launch({headless:true,executablePath:process.env.MONOLITHE_CHROMIUM||(fs.existsSync('/usr/bin/chromium')?'/usr/bin/chromium':undefined)});try{
 const p=await b.newPage();const erreurs=[];p.on('pageerror',e=>erreurs.push(e.message));
 await p.goto(url+'/modules/autopsie');
 const resultats=await p.evaluate(cas=>cas.map(c=>{
  $('sa').value=String(c.sa);$('maroun').value=String(c.grade);
  return Object.fromEntries(Object.entries(c.masses).map(([id,v])=>[id,percentilesObjet(champDef(id),v)]));
 }),cas);
 for(let i=0;i<cas.length;i++)for(const[id,m]of Object.entries(resultats[i]))for(const src of ['gc','ma','mb']){
  proche(m.zscores_non_arrondis[src],cas[i].attendus[id]['z_brut_'+src]);
  proche(m.percentiles[src],cas[i].attendus[id]['percentile_'+src]);
 }
 await p.locator('#dossier').fill('TEST-ORGANES');await p.locator('#operateur').fill('TEST');
 await p.waitForFunction(()=>dossier==='TEST-ORGANES');
 await p.evaluate(c=>{$('sa').value='20';$('maroun').value='0';for(const[id,v]of Object.entries(c.masses)){const d=champDef(id);ecrire(d,d.t==='masse2'?{d:v/2,g:v/2}:v);}majTousZ();},cas.find(c=>c.sa===20&&c.grade===0));
 const [download]=await Promise.all([p.waitForEvent('download'),p.locator('#btnExport').click()]);
 const doc=JSON.parse(fs.readFileSync(await download.path(),'utf8'));
 assert.ok(doc.etapes.flatMap(e=>e.champs).filter(c=>c.percentiles).every(c=>Object.hasOwn(c,'zscores')));
 assert.ok((await p.locator('.resultatsMasses').first().textContent()).includes('Percentile'));
 const typographie=await p.locator('.resultatsMasses').first().evaluate(t=>({font:getComputedStyle(t).fontFamily,size:parseFloat(getComputedStyle(t).fontSize)}));
 assert.ok(typographie.font.startsWith('Cambria'));assert.ok(Math.abs(typographie.size-44/3)<.1);
 async function post(doc){const r=await p.request.post(url+'/api/saisie',{data:doc});assert.equal(r.status(),200,await r.text());}
 await post(doc);
 const sansAdmin=await(await p.request.get(url+'/api/dossiers/'+doc.dossier+'/percentiles-organes')).json();
 assert.ok(sansAdmin.autopsie.lignes.some(l=>l.percentile_gc!=null));
 await post({module:'administratif',schema_version:'0.3.0',module_version:'2.1.0',dossier:doc.dossier,issue:{terme_sa:20,sexe:'M'}});
 await post(doc);
 const n=await b.newPage();n.on('pageerror',e=>erreurs.push(e.message));await n.goto(url+'/modules/neuropath');
 const controlesNeuro=await n.evaluate(cas=>cas.map(c=>{
  $('sa').value=String(c.sa);const z=zsObjet(champDef(c.champ),c.valeur);
  return {z_brut:z.z_brut??null,percentile:z.percentile??null};
 }),entree.neuropath);
 for(let i=0;i<controlesNeuro.length;i++){proche(controlesNeuro[i].z_brut,entree.neuropath[i].z_brut);proche(controlesNeuro[i].percentile,entree.neuropath[i].percentile);}
 await n.locator('#dossier').fill(doc.dossier);await n.locator('#operateur').fill('TEST');await n.waitForFunction(()=>dossier==='TEST-ORGANES');
 const neuro=await n.evaluate(()=>{$('sa').value='20';for(const id of ['masse_enc','masse_cerv']){const c=champDef(id),r=refDe(c.ref,20);ecrire(c,r.m);}majTousZ();return collecter();});
 assert.ok(neuro.etapes.flatMap(e=>e.champs).filter(c=>['masse_enc','masse_cerv'].includes(c.id)).every(c=>c.zscore.percentile===50));
 // Ancien dossier : aucun Z exact/P dans son archive, recalcul au rendu.
 const ancien=JSON.parse(JSON.stringify(neuro));for(const c of ancien.etapes.flatMap(e=>e.champs))if(c.zscore){delete c.zscore.z_brut;delete c.zscore.percentile;}
 await post(ancien);
 for(const g of ['complet','synthese']){
  const r=await p.request.post(url+'/api/dossiers/'+doc.dossier+'/cr',{data:{gabarit:g}});assert.equal(r.status(),200,await r.text());
  const cr=await r.json();assert.ok(cr.texte.includes('P50,00'));assert.ok(cr.texte.includes('GC'));
 }
 const stats=await(await p.request.get(url+'/api/dossiers/'+doc.dossier+'/percentiles-organes')).json();
 assert.equal(stats.neuropath.lignes[0].percentile,50);assert.ok(stats.autopsie.html.includes('Cambria'));
 assert.deepEqual(await(await p.request.get(url+'/api/saisie/'+doc.dossier+'/neuropath')).json(),ancien);
 await p.goto(url);await p.waitForFunction(()=>INDEX&&INDEX.dossiers.length);
 await p.locator('.cas[data-num="TEST-ORGANES"]').click();await p.evaluate(()=>{ONGLET='m_autopsie';ouvrir('TEST-ORGANES',true);});
 await p.locator('#percentiles_autopsie table').waitFor();assert.ok((await p.locator('#percentiles_autopsie').textContent()).includes('Percentile'));
 // Même formule sur les tables propres au calculateur ; relever les différences préexistantes.
 const calc=await b.newPage();await calc.goto(url+'/modules/autopsie');
 // Le fichier unifié est servi par un petit serveur statique de test, sans greffe.
 const http=require('http'),path=require('path'),root=path.resolve(__dirname,'..');
 const statique=http.createServer((req,res)=>{res.setHeader('Content-Type','text/html');res.end(fs.readFileSync(path.join(root,'hub/calculateur-unifie.html')));});
 await new Promise(resolve=>statique.listen(0,'127.0.0.1',resolve));
 const differences=[];
 try{
  await calc.goto('http://127.0.0.1:'+statique.address().port);
  const zs=await calc.evaluate(cas=>cas.map(c=>{
   const out={};for(const[id,v]of Object.entries(c.masses)){
    const k=id.replace(/_masse$/,''),item=ITEMS.find(i=>i.id===k);if(!item)continue;
    const z=lookupZ(item,c.sa,v,c.grade<=1?'0-1':String(c.grade));out[id]={z,p:Object.fromEntries(Object.entries(z).map(([k,v])=>[k,percentileOrgane(item,v)]))};
   }return out;
  }),cas);
  for(let i=0;i<cas.length;i++)for(const[id,r]of Object.entries(zs[i]))for(const [src,k]of [['gc','gc'],['ma','mar'],['mb','mbo']]){
   const z=r.z[k];if(z==null)assert.equal(r.p[k],null);else assert.ok(r.p[k]>=0&&r.p[k]<=100);
   if(z!=null && Math.abs(z-(cas[i].attendus[id]['z_brut_'+src]??Infinity))<1e-10)proche(r.p[k],cas[i].attendus[id]['percentile_'+src]);
   if(z!=null && cas[i].attendus[id]['z_brut_'+src]!=null && Math.abs(z-cas[i].attendus[id]['z_brut_'+src])>1e-10)
    differences.push({sa:cas[i].sa,grade:cas[i].grade,organe:id,reference:src,z_autopsie:cas[i].attendus[id]['z_brut_'+src],z_unifie:z});
  }
  await calc.locator('#ga').selectOption('20');await calc.locator('#in_foie').fill('20');
  assert.ok((await calc.locator('#resWrap').textContent()).includes('P'));
 }finally{await new Promise(resolve=>statique.close(resolve));}
 if(process.env.MONOLITHE_COMPARAISON_ORGANES)fs.writeFileSync(process.env.MONOLITHE_COMPARAISON_ORGANES,JSON.stringify(differences,null,2));
 for(const slug of ['autopsie','neuropath','macro_placenta','examen_clinique','biometrie_clinique','radio']){
  const diagnostic=await b.newPage();await diagnostic.goto(url+'/modules/'+slug+'?selftest=1');
  await diagnostic.waitForFunction(()=>[...document.querySelectorAll('pre')].some(e=>/OK : \d+\/\d+/.test(e.textContent)),undefined,{timeout:30000});
  const texte=(await diagnostic.locator('pre').allTextContents()).find(t=>/OK : \d+\/\d+/.test(t));
  const m=texte.match(/OK : (\d+)\/(\d+)/);assert.equal(m[1],m[2],slug+': '+texte);await diagnostic.close();
 }
 assert.deepEqual(erreurs,[]);
 console.log(`${cas.length} cas autopsie et ${entree.neuropath.length} cas neuro Python/JS, exports, ancien dossier, CR et Hub OK ; ${differences.length} différences entre tables historiques autopsie/unifié.`);
}finally{await b.close()}})().catch(e=>{console.error(e);process.exitCode=1});
