// SPDX-License-Identifier: CC-BY-NC-SA-4.0
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {chromium}=require('playwright');
(async()=>{
 const b=await chromium.launch({headless:true,executablePath:process.env.MONOLITHE_CHROMIUM || (fs.existsSync('/usr/bin/chromium') ? '/usr/bin/chromium' : undefined)});
 try{
  const p=await b.newPage({viewport:{width:1440,height:1000}}), url=process.argv[2];
  const erreurs=[];p.on('pageerror',e=>erreurs.push(e.message));
  await p.goto(url);
  await p.locator('.cas[data-num="DEMO_SLO_001"]').click();
  await p.locator('#ficheNum').filter({hasText:'DEMO_SLO_001'}).waitFor();
  assert.ok((await p.locator('[role="note"]').textContent()).includes('CAS ENTIÈREMENT FICTIF'));
  // L'onglet de saisie biométrique du Hub.
  await p.evaluate(()=>{ONGLET='m_biometrie_clinique';ouvrir('DEMO_SLO_001',true);});
  await p.locator('.bioExterne').waitFor();
  const t=p.locator('.bioExterne');
  assert.ok((await t.textContent()).includes('P50,00'));
  const style=await t.evaluate(t=>({font:getComputedStyle(t).fontFamily,size:getComputedStyle(t).fontSize}));
  assert.ok(style.font.startsWith('Cambria'));assert.ok(Math.abs(parseFloat(style.size)-44/3)<.1);
  // Une référence entièrement absente disparaît, tandis que Z=0 reste visible.
  const html=await p.evaluate(()=>rendreMesures({mesures:{a:0,b:null},ecarts_non_arrondis:{a:{GC:0}},percentiles:{a:{GC:50}}}));
  assert.ok(html.includes('Z-score GC'));assert.ok(html.includes('P50,00'));assert.ok(!html.includes('Percentile MA'));
  // Rendu du compte rendu dans le véritable conteneur du Hub.
  await p.evaluate(()=>{ONGLET='cr';ouvrir('DEMO_SLO_001',true);});
  await p.locator('#crGabarit option[value="complet"]').waitFor({state:'attached'});
  for(const g of ['complet','synthese']){
   await p.selectOption('#crGabarit',g);
   await p.getByRole('button',{name:'Produire un brouillon',exact:true}).click();
   await p.waitForFunction(g=>CR_AFFICHE.entete==='Brouillon — '+g, g);
   await p.locator('#crPre').waitFor();
   assert.ok((await p.locator('#crPre').textContent()).includes('sans permettre de l’affirmer'));
   if(g==='complet'){
    const table=p.locator('#crPre table').filter({has:p.locator('th', {hasText:'Percentile GC'})}).first();
    const stats=await table.evaluate(t=>{
     const rows=[...t.querySelectorAll('tr[data-mesure]')];
     return {font:getComputedStyle(t).fontFamily,size:getComputedStyle(t).fontSize,
      columns:[...t.querySelectorAll('th')].map((h,i)=>({text:h.textContent,
       hasValue:rows.some(r=>!['','—'].includes(r.cells[i].textContent.trim()))})),
      underline:[...t.querySelectorAll('td')].some(c=>getComputedStyle(c).textDecorationLine.includes('underline'))};
    });
    assert.ok(stats.font.startsWith('Cambria'));assert.ok(Math.abs(parseFloat(stats.size)-44/3)<.1);
    assert.ok(stats.columns.every(c=>c.hasValue));assert.equal(stats.underline,false);
    assert.ok(stats.columns.some(c=>c.text==='Z-score GC'));
    if(process.env.MONOLITHE_DEMO_CAPTURE){
     const preview=await b.newPage({viewport:{width:1100,height:850}});
     const report=await p.evaluate(()=>CR_AFFICHE.texte);
     await preview.setContent('<div style="white-space:pre-wrap">'+report+'</div>');
     await preview.locator('table').filter({has:preview.locator('th',{hasText:'Percentile GC'})}).first().screenshot({path:process.env.MONOLITHE_DEMO_CAPTURE.replace('.png','-table.png')});
     await preview.pdf({path:process.env.MONOLITHE_DEMO_CAPTURE.replace('.png','-rapport.pdf'),format:'A4'});
     await preview.close();
     await p.screenshot({path:process.env.MONOLITHE_DEMO_CAPTURE,fullPage:true});
     await p.pdf({path:process.env.MONOLITHE_DEMO_CAPTURE.replace('.png','.pdf'),format:'A4',landscape:true});
    }
   }
  }
  // Réouverture du module avec les données enregistrées, puis véritable téléchargement.
  await p.goto(url+'/modules/biometrie_clinique?dossier=DEMO_SLO_001&operateur=Codex');
  await p.waitForFunction(()=>document.getElementById('v_pc').value==='130');
  assert.equal(await p.locator('#v_dici').inputValue(),'');
  assert.ok((await p.locator('#z_pied').textContent()).includes('P50,00'));
  const [download]=await Promise.all([p.waitForEvent('download'),p.locator('#btnExport').click()]);
  const data=JSON.parse(fs.readFileSync(await download.path(),'utf8'));
  const exp=await (await p.request.get(url+'/demonstration/export.json')).json();
  const bio=exp.saisies.find(s=>s.module==='biometrie_clinique');
  for(const [cle,refs] of Object.entries(data.percentiles))for(const [src,v]of Object.entries(refs)){
   if(v!=null) assert.ok(Math.abs(v-bio.percentiles[cle][src])<2e-12);
  }
  assert.deepEqual(erreurs,[]);
  console.log('Hub, tableaux, complet, synthèse, saisie réouverte et export JSON : OK');
 }finally{await b.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
