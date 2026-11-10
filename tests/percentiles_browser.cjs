// SPDX-License-Identifier: CC-BY-NC-SA-4.0
// Lancé par test_parcours_percentiles.py : assertions sur les fichiers et CR réels.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const {chromium} = require('playwright');
const depot = path.resolve(__dirname, '..');
const [casPath, url, sortie] = process.argv.slice(2);
const {cas, historique} = JSON.parse(fs.readFileSync(casPath, 'utf8'));
const compteur = {dossiers: 0, percentilesSaisie: 0, percentilesJSON: 0, percentilesCR: 0, percentilesCalculateur: 0, selftests: []};
const correspondance = {
  masse: ['masse', 1], pied: ['pied', 1], bip: ['bpd', 1], fo: ['fod', 1],
  main: ['main', 1], vt: ['vt', .1], vc: ['vc', .1], pc: ['pc', .1],
  pt: ['tc', .1], pa: ['ac', .1]
};
function proche(a, b, contexte){
  assert.equal(typeof a, 'number', contexte);
  assert.ok(Math.abs(a - b) <= 2e-11, `${contexte} : ${a} ≠ ${b}`);
}
function pTexte(p){
  if(p < .01) return 'P < 0,01';
  if(p > 99.99) return 'P > 99,99';
  return 'P' + p.toFixed(2).replace('.', ',');
}
function zTexte(z){ return ((z >= 0 ? '+' : '') + z.toFixed(2) + ' DS').replace('.', ',').replace('-', '−'); }
async function jsonReponse(reponse){
  assert.equal(reponse.status(), 200, await reponse.text());
  return reponse.json();
}
async function saisir(page, d){
  await page.locator('#dossier').fill(d.dossier);
  await page.locator('#operateur').fill('TEST');
  await page.waitForSelector('#secTerme:not(.off)');
  await page.locator('#terme_sa').fill(d.sa == null ? '' : String(d.sa));
  for(const [cle, valeur] of Object.entries(d.mesures)) await page.locator('#v_' + cle).fill(String(valeur));
}
async function telecharger(page, nom){
  const [download] = await Promise.all([page.waitForEvent('download'), page.locator('#btnExport').click()]);
  const cible = path.join(sortie, nom);
  await download.saveAs(cible);
  return JSON.parse(fs.readFileSync(cible, 'utf8'));
}
function verifierExport(doc, d){
  assert.equal(doc.schema_version, '0.1.0');
  for(const [cle, sources] of Object.entries(d.attendus)){
    assert.equal(doc.mesures[cle], d.mesures[cle]);
    assert.deepEqual(Object.keys(doc.percentiles[cle] || {}).sort(), Object.keys(sources).sort());
    for(const [src, r] of Object.entries(sources)){
      proche(doc.percentiles[cle][src], r.p, `JSON ${d.dossier}/${cle}/${src}`);
      proche(doc.ecarts_non_arrondis[cle][src], r.z, `Z exact JSON ${cle}/${src}`);
      proche(doc.ecarts[cle][src], Number(r.z.toFixed(2)), `Z historique JSON ${cle}/${src}`);
      compteur.percentilesJSON++;
    }
  }
}

(async()=>{
  const executablePath = process.env.MONOLITHE_CHROMIUM || (fs.existsSync('/usr/bin/chromium') ? '/usr/bin/chromium' : undefined);
  const browser = await chromium.launch({headless: true, executablePath});
  // Le Chromium géré bloque file://. Servir les fichiers sans modification ni
  // injection du hub, et sans aucune dépendance réseau extérieure.
  const statique = http.createServer((req,res)=>{
    const fichier = path.resolve(depot, '.' + decodeURIComponent(new URL(req.url, 'http://localhost').pathname));
    if(!fichier.startsWith(depot + path.sep) || !fs.existsSync(fichier) || !fs.statSync(fichier).isFile()){
      res.writeHead(404);res.end();return;
    }
    res.setHeader('Content-Type', fichier.endsWith('.html') ? 'text/html; charset=utf-8' : 'application/octet-stream');
    res.end(fs.readFileSync(fichier));
  });
  await new Promise(resolve=>statique.listen(0,'127.0.0.1',resolve));
  const fichierURL = fichier=>`http://127.0.0.1:${statique.address().port}/${fichier}`;
  try {
    for(const d of cas){
      const context = await browser.newContext({acceptDownloads: true});
      const page = await context.newPage();
      const erreurs = [];
      context.on('request', r=>{if(!r.url().startsWith('http://127.0.0.1:')) erreurs.push('Requête extérieure : '+r.url());});
      page.on('pageerror', e=>erreurs.push(e.message));
      // Le module est servi seul, sans les scripts de liaison du hub.
      await page.goto(fichierURL('Macro/biometrie_clinique.html'));
      await saisir(page, d);
      for(const [cle, sources] of Object.entries(d.attendus)){
        assert.equal(await page.locator(`#z_${cle} tbody tr`).count(), Object.keys(sources).length);
        for(const [src, r] of Object.entries(sources)){
          const ligne = page.locator(`#z_${cle} [data-reference="${src}"]`);
          assert.equal(await ligne.locator('[data-valeur="percentile"]').textContent(), pTexte(r.p));
          assert.equal(await ligne.locator('[data-valeur="z"]').textContent(), (r.z >= 0 ? '+' : '') + r.z.toFixed(2));
          compteur.percentilesSaisie++;
        }
      }
      const doc = await telecharger(page, `${d.dossier}_biometrie_clinique.json`);
      verifierExport(doc, d);
      if(d.administratif) await jsonReponse(await context.request.post(url + '/api/saisie', {data: d.administratif}));
      await jsonReponse(await context.request.post(url + '/api/saisie', {data: doc}));
      for(const suffixe of ['', '?cliches=1']){
        const relu = await jsonReponse(await context.request.get(`${url}/api/saisie/${d.dossier}/biometrie_clinique${suffixe}`));
        assert.deepEqual(relu.percentiles, doc.percentiles);
        assert.deepEqual(relu.ecarts, doc.ecarts);
      }
      const dossierHub = await jsonReponse(await context.request.get(`${url}/api/dossiers/${d.dossier}`));
      assert.deepEqual(dossierHub.saisies.find(s=>s.module === 'biometrie_clinique').donnees.percentiles, doc.percentiles);
      for(const gabarit of ['complet', 'synthese']){
        const rapport = await jsonReponse(await context.request.post(`${url}/api/dossiers/${d.dossier}/cr`, {data: {gabarit}}));
        fs.writeFileSync(path.join(sortie, `${d.dossier}_${gabarit}.${gabarit === 'complet' ? 'html' : 'txt'}`), rapport.texte);
        const relu = await jsonReponse(await context.request.get(`${url}/api/cr/${rapport.id}`));
        assert.equal(relu.texte, rapport.texte);
        const rendu = await context.newPage();
        if(gabarit === 'complet') await rendu.setContent(rapport.texte);
        for(const [cle, sources] of Object.entries(d.attendus)){
          let cellules;
          if(gabarit === 'complet'){
            const key = {vt:'VT', vc:'VC', pc:'PC'}[cle] || cle;
            cellules = await rendu.locator(`[data-mesure="${key}"] td`).allTextContents();
            assert.ok(cellules.length >= 2, `Ligne finale manquante : ${cle}`);
            const headers = await rendu.locator(`[data-mesure="${key}"]`).locator('xpath=ancestor::table').locator('th').allTextContents();
            cellules = Object.fromEntries(headers.map((h,i)=>[h,cellules[i]]));
          }
          const ligneTexte = rapport.texte.split('\n').find(l=>l.includes('· ' + doc.libelles[cle] + ' :')) || '';
          for(const [src, i] of [['GC',3], ['MA',5], ['MB',7]]){
            if(sources[src]){
              const r = sources[src];
              if(cellules){
                assert.equal(cellules['Percentile ' + src], pTexte(r.p), `CR ${d.dossier}/${cle}/${src}`);
                assert.equal(cellules['Z-score ' + src], zTexte(r.z));
              } else {
                assert.ok(ligneTexte.includes(src + ' ' + zTexte(r.z) + ' · ' + pTexte(r.p)), ligneTexte);
              }
              compteur.percentilesCR++;
            } else if(cellules) assert.ok(cellules['Percentile ' + src] == null || cellules['Percentile ' + src] === '—', `Percentile hors domaine : ${cle}/${src}`);
          }
        }
        await rendu.close();
      }
      // Même référence, unités converties, dans le calculateur unifié.
      const calc = await context.newPage();
      calc.on('pageerror', e=>erreurs.push(e.message));
      await calc.goto(fichierURL('hub/calculateur-unifie.html'));
      const visible = Number.isInteger(d.sa) && d.sa >= 12 && d.sa <= 43;
      if(visible) await calc.locator('#ga').selectOption(String(d.sa));
      for(const [cle, [id, facteur]] of Object.entries(correspondance)) await calc.locator('#in_' + id).fill(String(d.mesures[cle] * facteur));
      const calculs = await calc.evaluate(({d, correspondance})=>{
        const out = {};
        for(const [cle, [id, facteur]] of Object.entries(correspondance)){
          const item = ITEMS.find(i=>i.id === id);
          const z = lookupZ(item, d.sa, d.mesures[cle] * facteur, '0-1');
          out[cle] = {z, p: lookupPercentiles(item, z)};
        }
        return out;
      }, {d, correspondance});
      for(const [cle, sources] of Object.entries(d.attendus)){
        if(!correspondance[cle]) continue;
        const {z,p} = calculs[cle];
        for(const [src, k, i] of [['GC','gc',2], ['MA','mar',3], ['MB',z.mbb != null ? 'mbb' : 'mbo',4]]){
          if(sources[src]){
            proche(z[k], sources[src].z, `Calculateur Z ${d.dossier}/${cle}/${src}`);
            proche(p[k], sources[src].p, `Calculateur P ${d.dossier}/${cle}/${src}`);
            if(visible){
              const cellule = await calc.locator(`[data-mesure="${correspondance[cle][0]}"] td`).nth(i).textContent();
              assert.ok(cellule.includes(pTexte(sources[src].p)), cellule);
              const copie = await calc.evaluate(()=>window._copyData);
              const libelle = await calc.locator(`[data-mesure="${correspondance[cle][0]}"] td`).first().textContent();
              const ligne = copie.split('\n').find(l=>l.startsWith(libelle + '\t')) || '';
              // Vérification du texte effectivement préparé pour le copier-coller.
              assert.ok(ligne.includes(pTexte(sources[src].p)), ligne);
            }
            compteur.percentilesCalculateur++;
          } else assert.equal(p[k] ?? null, null, `Calculateur hors domaine ${cle}/${src}`);
        }
      }
      // Colonnes visibles, zéro conservé, police et en-têtes sans coupure.
      if(visible){
        const presentation = await calc.evaluate(()=>{
          const table=document.querySelector('table.res');
          const rows=Array.from(table.querySelectorAll('tr[data-mesure]'));
          return {font:getComputedStyle(table).fontFamily, size:getComputedStyle(table).fontSize,
            columns:Array.from(table.rows[0].cells, (h,i)=>({hidden:h.hidden,
              nonempty:rows.some(r=>!['','—'].includes(r.cells[i].textContent.trim()))}))};
        });
        assert.ok(presentation.font.startsWith('Cambria'));
        assert.ok(Math.abs(parseFloat(presentation.size)-44/3)<.1);
        for(const col of presentation.columns) assert.equal(col.hidden,!col.nonempty);
      }
      // Aucune colonne de percentile ajoutée aux masses d'organes.
      await calc.locator('#ga').selectOption('16');
      await calc.locator('#in_foie').fill('100');
      assert.ok(!(await calc.locator('[data-mesure="foie"]').textContent()).includes('P'));
      assert.deepEqual(await calc.evaluate(()=>lookupPercentiles(ITEMS.find(i=>i.id === 'foie'), {gc:1})), {});
      assert.deepEqual(erreurs, []);
      await page.screenshot({path:path.join(sortie, `${d.dossier}_saisie.png`), fullPage:true});
      await context.close();
      compteur.dossiers++;
    }
    // Fiche biométrique ordinaire du Hub : zéro et colonnes sans référence.
    const fiche = await browser.newPage();
    await fiche.goto(url);
    const presentationHub = await fiche.evaluate(()=>{
      const conteneur=document.createElement('div');
      conteneur.innerHTML=rendreMesures({mesures:{zero:0,absente:null},
        ecarts_non_arrondis:{zero:{GC:0}},percentiles:{zero:{GC:50}}});
      document.body.append(conteneur);
      const table=conteneur.querySelector('table');
      return {headers:[...table.querySelectorAll('th')].map(c=>c.textContent),
        text:table.textContent,font:getComputedStyle(table).fontFamily,size:getComputedStyle(table).fontSize};
    });
    assert.deepEqual(presentationHub.headers,['Mesure','Valeur','Z-score GC','Percentile GC']);
    assert.ok(presentationHub.text.includes('P50,00'));
    assert.ok(presentationHub.font.startsWith('Cambria'));
    assert.ok(Math.abs(parseFloat(presentationHub.size)-44/3)<.1);
    await fiche.close();
    // Ancien export importé par le vrai sélecteur de fichier, puis réexporté.
    const context = await browser.newContext({acceptDownloads:true});
    const ancien = JSON.parse(fs.readFileSync(path.join(depot, 'hub/exemples/26P0123_biometrie_clinique.json'), 'utf8'));
    const page = await context.newPage();
    await page.goto(fichierURL('pack_telephone/biometrie_clinique.html'));
    await page.locator('#operateur').fill('TEST');
    await page.locator('#jsonPick').setInputFiles(path.join(depot, 'hub/exemples/26P0123_biometrie_clinique.json'));
    await page.waitForFunction(()=>document.getElementById('dossier').value === '26P0123' && !document.getElementById('btnExport').disabled);
    const rafraichi = await telecharger(page, '26P0123_reexport_historique.json');
    assert.deepEqual(rafraichi.mesures, ancien.mesures);
    assert.equal(rafraichi.schema_version, ancien.schema_version);
    verifierExport(rafraichi, historique);
    await context.close();

    // Le module greffé par le hub doit aussi relire et réafficher les valeurs.
    const cHub = await browser.newContext();
    const pageHub = await cHub.newPage();
    const reluHub = cas[1];
    await pageHub.goto(`${url}/modules/biometrie_clinique?dossier=${reluHub.dossier}&operateur=TEST`);
    await pageHub.waitForFunction(v=>document.getElementById('v_bip').value === String(v), reluHub.mesures.bip);
    for(const [cle,sources] of Object.entries(reluHub.attendus)){
      for(const [src,r] of Object.entries(sources)){
        assert.equal(await pageHub.locator(`#z_${cle} [data-reference="${src}"] [data-valeur="percentile"]`).textContent(),pTexte(r.p));
      }
    }
    await cHub.close();

    for(const fichier of ['Macro/biometrie_clinique.html','pack_telephone/biometrie_clinique.html',
      'Macro/examen_clinique.html','Macro/autopsie.html','Macro/neuropath.html','Macro/macro_placenta.html','Radio/radio.html']){
      const c = await browser.newContext();
      const p = await c.newPage();
      await p.goto(fichierURL(fichier) + '?selftest=1');
      await p.waitForFunction(()=>Array.from(document.querySelectorAll('pre')).some(e=>/OK : \d+\/\d+/.test(e.textContent)), undefined, {timeout:30000});
      const resultat = await p.locator('pre').allTextContents();
      const bilan = resultat.find(t=>/OK : \d+\/\d+/.test(t));
      assert.ok(!bilan.includes('ÉCHEC'), `${fichier}: ${bilan}`);
      const n = bilan.match(/OK : (\d+)\/(\d+)/);
      assert.equal(n[1],n[2], `${fichier}: ${bilan}`);
      compteur.selftests.push({fichier,bilan:bilan.trim()});
      await c.close();
    }
    fs.writeFileSync(path.join(sortie, 'resultats.json'), JSON.stringify(compteur,null,2));
    console.log(JSON.stringify(compteur));
  } finally {
    await browser.close();
    await new Promise(resolve=>statique.close(resolve));
  }
})().catch(e=>{console.error(e);process.exitCode=1;});
