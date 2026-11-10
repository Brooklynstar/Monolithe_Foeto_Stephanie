// SPDX-License-Identifier: CC-BY-NC-SA-4.0
const assert=require('node:assert/strict'),fs=require('fs'),path=require('path'),http=require('http');
const {chromium}=require('playwright');
const cas=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),url=process.argv[3];
(async()=>{const b=await chromium.launch({headless:true,executablePath:process.env.MONOLITHE_CHROMIUM||(fs.existsSync('/usr/bin/chromium')?'/usr/bin/chromium':undefined)});try{
 const p=await b.newPage();const erreurs=[];p.on('pageerror',e=>erreurs.push(e.message));
 await p.goto(url+'/modules/macro_placenta');
 const resultats=await p.evaluate(cas=>cas.map(c=>PlacentaPercentiles.calculer(c.sa,c.masse,c.conditions)),cas);
 for(let i=0;i<cas.length;i++)assert.deepEqual(resultats[i],cas[i].attendu);
 await p.locator('#dossier').fill('TEST-PLACENTA');await p.locator('#operateur').fill('TEST');await p.waitForFunction(()=>dossier==='TEST-PLACENTA');
 await p.locator('#f_terme_sa').fill('28');await p.locator('#f_masse').fill('214');await p.locator('#conditions_masse').selectOption('fraiche_paree');
 await p.waitForFunction(()=>document.getElementById('resultatsPercentilesPlacenta').textContent.includes('P50'));
 assert.ok((await p.locator('#resultatsPercentilesPlacenta').textContent()).includes('P50'));
 const typographie=await p.locator('#resultatsPercentilesPlacenta table').evaluate(t=>({font:getComputedStyle(t).fontFamily,size:parseFloat(getComputedStyle(t).fontSize)}));
 assert.ok(typographie.font.startsWith('Cambria'));assert.ok(Math.abs(typographie.size-44/3)<.1);
 const [download]=await Promise.all([p.waitForEvent('download'),p.locator('#btnExport').click()]);
 const doc=JSON.parse(fs.readFileSync(await download.path(),'utf8'));
 assert.equal(doc.resultats_placentaires.position_percentile,'P50');assert.equal(doc.resultats_placentaires.percentile_exact,null);
 async function post(d){const r=await p.request.post(url+'/api/saisie',{data:d});assert.equal(r.status(),200,await r.text());}
 await post({module:'administratif',schema_version:'0.3.0',module_version:'2.1.0',dossier:doc.dossier,issue:{terme_sa:28}});
 const ancien=JSON.parse(JSON.stringify(doc));delete ancien.resultats_placentaires;delete ancien.conditions_masse;
 await post(ancien);
 for(const g of ['complet','synthese','placenta']){
  const r=await p.request.post(url+'/api/dossiers/'+doc.dossier+'/cr',{data:{gabarit:g}});assert.equal(r.status(),200,await r.text());
  const cr=await r.json();assert.ok(cr.texte.includes('P50'),g);
  assert.equal(cr.format,g==='synthese'?'texte':'html');
 }
 const stats=await(await p.request.get(url+'/api/dossiers/'+doc.dossier+'/percentiles-placenta')).json();
 assert.deepEqual(stats.resultats,doc.resultats_placentaires);
 assert.deepEqual(await(await p.request.get(url+'/api/saisie/'+doc.dossier+'/macro_placenta')).json(),ancien);
 await p.locator('#conditions_masse').selectOption('fixe');
 assert.ok(!(await p.locator('#resultatsPercentilesPlacenta').textContent()).includes('Position percentile'));
 await p.goto(url);await p.waitForFunction(()=>INDEX&&INDEX.dossiers.length);
 await p.locator('.cas[data-num="TEST-PLACENTA"]').click();await p.evaluate(()=>{ONGLET='m_macro_placenta';ouvrir('TEST-PLACENTA',true);});
 await p.locator('#percentilesPlacentaHub table').waitFor();assert.ok((await p.locator('#percentilesPlacentaHub').textContent()).includes('P50'));
 const root=path.resolve(__dirname,'..'),statique=http.createServer((req,res)=>{res.setHeader('Content-Type','text/html');res.end(fs.readFileSync(path.join(root,'hub/calculateur-unifie.html')));});
 await new Promise(resolve=>statique.listen(0,'127.0.0.1',resolve));
 try{
  const c=await b.newPage();await c.goto('http://127.0.0.1:'+statique.address().port);
  const out=await c.evaluate(cas=>cas.map(x=>PlacentaPercentiles.calculer(x.sa,x.masse,x.conditions)),cas);
  assert.deepEqual(out,resultats);
  await c.locator('#ga').selectOption('28');await c.locator('#in_placenta').fill('214');await c.locator('#placenta_conditions').selectOption('fraiche_paree');
  assert.ok((await c.locator('#resWrap').textContent()).includes('P50'));
 }finally{await new Promise(resolve=>statique.close(resolve));}
 for(const slug of ['autopsie','neuropath','macro_placenta','examen_clinique','biometrie_clinique','radio']){
  const diagnostic=await b.newPage();await diagnostic.goto(url+'/modules/'+slug+'?selftest=1');
  await diagnostic.waitForFunction(()=>[...document.querySelectorAll('pre')].some(e=>/OK : \d+\/\d+/.test(e.textContent)),undefined,{timeout:30000});
  const texte=(await diagnostic.locator('pre').allTextContents()).find(t=>/OK : \d+\/\d+/.test(t));
  const m=texte.match(/OK : (\d+)\/(\d+)/);assert.equal(m[1],m[2],slug+': '+texte);await diagnostic.close();
 }
 assert.deepEqual(erreurs,[]);console.log(`${cas.length} cas Python/JS/unifié, export, ancien dossier, 3 comptes rendus et Hub : OK`);
}finally{await b.close()}})().catch(e=>{console.error(e);process.exitCode=1});
