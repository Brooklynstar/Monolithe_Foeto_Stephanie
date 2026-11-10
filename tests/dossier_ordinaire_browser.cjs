// SPDX-License-Identifier: CC-BY-NC-SA-4.0
const assert=require('node:assert/strict'),fs=require('node:fs');
const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch({headless:true,executablePath:process.env.MONOLITHE_CHROMIUM || (fs.existsSync('/usr/bin/chromium')?'/usr/bin/chromium':undefined)});try{
 const url=process.argv[2], fichier=process.argv[3], context=await b.newContext(), p=await context.newPage();
 const errors=[];p.on('pageerror',e=>errors.push(e.message));
 await p.goto(url); await p.waitForFunction(()=>SERVI===true);
 assert.equal(await p.locator('.cas[data-num="DEMO_SLO_001"]').count(),0);
 await p.locator('#pickDepot').setInputFiles(fichier);

 await p.locator('.cas[data-num="DEMO_SLO_001"]').click();
 assert.ok((await p.locator('#liste').textContent()).includes('FICTIF – TEST – Smith-Lemli-Opitz'));
 // Toutes les rubriques utilisent les modules ordinaires et le même bouton d'enregistrement.
 for(const mod of ['administratif','examen_clinique','biometrie_clinique','radio','autopsie','macro_placenta','micro','neuropath']){
  const page=await context.newPage();page.on('dialog',d=>d.accept());page.on('pageerror',e=>errors.push(mod+': '+e.message));
  await page.goto(url+'/modules/'+mod+'?dossier=DEMO_SLO_001&operateur=Codex');
  await page.locator('#hubRelire').click();
  await page.waitForFunction(()=>document.getElementById('hubMsg')?.textContent.includes('restituée'));
  const doc=await page.evaluate(()=>collecter());
  assert.equal(doc.dossier,'DEMO_SLO_001');
  if(mod==='micro') assert.equal(doc.sections.length,6);
  if(mod==='examen_clinique'){
    const anomalies=doc.etages.flatMap(e=>e.items).filter(i=>i.etat==='anormal');
    assert.ok(anomalies.some(i=>i.anomalies.some(a=>a.hpo_id==='HP:0000252')));
    assert.ok(anomalies.some(i=>i.anomalies.some(a=>a.hpo_id==='HP:0004691')));
  }
  let marqueur=null;
  if(mod==='biometrie_clinique') await page.locator('#v_main').fill('25.8');
  else{
    if(mod==='micro')await page.locator('.tog button[data-e="anormal"]').first().click();
    const zones=await page.locator('textarea:visible').all();
    let zone;
    for(const z of zones)if(await z.isEditable()){zone=z;break;}
    assert.ok(zone,'Aucun champ de texte modifiable : '+mod);
    marqueur='Correction fictive navigateur '+mod;
    await zone.fill((await zone.inputValue())+'\n'+marqueur);
  }
  const response=page.waitForResponse(r=>r.url()===url+'/api/saisie'&&r.request().method()==='POST');
  await page.locator('#hubSave').click();assert.equal((await response).status(),200);
  const sauve=await (await page.request.get(url+'/api/saisie/DEMO_SLO_001/'+mod)).json();
  if(marqueur)assert.ok(JSON.stringify(sauve).includes(marqueur),'Correction non enregistrée : '+mod);
  await page.close();
 }
 const page2=await context.newPage();await page2.goto(url+'/modules/biometrie_clinique?dossier=DEMO_SLO_001&operateur=Codex');
 await page2.waitForFunction(()=>document.getElementById('v_main').value==='25.8');await page2.close();
 await p.reload();await p.locator('.cas[data-num="DEMO_SLO_001"]').click();
 await p.evaluate(()=>{ONGLET='cr';ouvrir('DEMO_SLO_001',true)});
 await p.locator('#crListe button').first().click();await p.locator('#crPre').waitFor();
 await p.getByRole('button',{name:'Modifier',exact:true}).click();
 await p.locator('#crPre').evaluate(el=>{el.append(document.createTextNode('\nCorrection fictive de test navigateur.'))});
 await p.getByRole('button',{name:'Enregistrer une version',exact:true}).click();
 await p.waitForFunction(()=>CR_AFFICHE.entete.startsWith('Version corrigée'));
 const id=await p.evaluate(()=>CR_AFFICHE.id);await p.reload();
 await p.locator('.cas[data-num="DEMO_SLO_001"]').click();await p.evaluate(()=>{ONGLET='cr';ouvrir('DEMO_SLO_001',true)});
 await p.evaluate(id=>relireCr(id),id);await p.waitForFunction(()=>document.getElementById('crPre')?.textContent.includes('Correction fictive de test navigateur.'));
 // Génération ordinaire des deux gabarits, indépendante des rapports importés.
 for(const g of ['complet','synthese']){
  await p.locator('#crGabarit').selectOption(g);
  await p.getByRole('button',{name:'Produire un brouillon',exact:true}).click();
  await p.waitForFunction(g=>CR_AFFICHE.entete==='Brouillon — '+g,g);
 }
 const [telechargement]=await Promise.all([p.waitForEvent('download'),p.getByRole('link',{name:'Exporter le dossier JSON',exact:true}).click()]);
 const exporte=JSON.parse(fs.readFileSync(await telechargement.path(),'utf8'));
 assert.equal(exporte.saisies.length,8);
 p.once('dialog',d=>d.accept('DEMO_SLO_001'));
 await p.getByRole('button',{name:'Supprimer',exact:true}).click();
 await p.locator('.cas[data-num="DEMO_SLO_001"]').waitFor({state:'detached'});
 await p.reload();assert.equal(await p.locator('.cas[data-num="DEMO_SLO_001"]').count(),0);
 assert.equal(await p.locator('.cas[data-num="TEMOIN_TEST"]').count(),1);
 assert.deepEqual(errors,[]);
 console.log('Import général → huit rubriques modifiables → saisie persistante → CR corrigé persistant → génération complet/synthèse : OK');
}finally{await b.close()}})().catch(e=>{console.error(e);process.exitCode=1});
