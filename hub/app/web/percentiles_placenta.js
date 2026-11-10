// SPDX-License-Identifier: CC-BY-NC-SA-4.0
var PlacentaPercentiles=(function(){
  var references=/* BEGIN REFERENCES */
{"Redline":{"18":{"moyenne":107,"sd":23,"P10":52,"P50":89,"P90":181,"source":"Extrapol"},"19":{"moyenne":113,"sd":25,"P10":56,"P50":94,"P90":196,"source":"Extrapol"},"20":{"moyenne":130,"sd":26,"P10":82,"P50":110,"P90":214,"source":"Extrapol"},"21":{"moyenne":150,"sd":25,"P10":95,"P50":130,"P90":230,"source":"Extrapol"},"22":{"moyenne":189,"sd":89,"P10":107,"P50":166,"P90":285,"source":"Redline"},"23":{"moyenne":190,"sd":41,"P10":127,"P50":188,"P90":262,"source":"Redline"},"24":{"moyenne":190,"sd":42,"P10":128,"P50":192,"P90":252,"source":"Redline"},"25":{"moyenne":197,"sd":70,"P10":128,"P50":184,"P90":299,"source":"Redline"},"26":{"moyenne":226,"sd":100,"P10":138,"P50":200,"P90":281,"source":"Redline"},"27":{"moyenne":240,"sd":77,"P10":130,"P50":242,"P90":332,"source":"Redline"},"28":{"moyenne":223,"sd":66,"P10":140,"P50":214,"P90":321,"source":"Redline"},"29":{"moyenne":269,"sd":96,"P10":161,"P50":252,"P90":352,"source":"Redline"},"30":{"moyenne":324,"sd":88,"P10":208,"P50":316,"P90":433,"source":"Redline"},"31":{"moyenne":314,"sd":105,"P10":175,"P50":313,"P90":417,"source":"Redline"},"32":{"moyenne":325,"sd":77,"P10":241,"P50":318,"P90":436,"source":"Redline"},"33":{"moyenne":351,"sd":83,"P10":252,"P50":352,"P90":446,"source":"Redline"},"34":{"moyenne":381,"sd":84,"P10":283,"P50":382,"P90":479,"source":"Redline"},"35":{"moyenne":411,"sd":99,"P10":291,"P50":401,"P90":544,"source":"Redline"},"36":{"moyenne":447,"sd":110,"P10":320,"P50":440,"P90":580,"source":"Redline"},"37":{"moyenne":467,"sd":107,"P10":349,"P50":452,"P90":607,"source":"Redline"},"38":{"moyenne":493,"sd":103,"P10":365,"P50":484,"P90":629,"source":"Redline"},"39":{"moyenne":500,"sd":103,"P10":379,"P50":490,"P90":635,"source":"Redline"},"40":{"moyenne":510,"sd":100,"P10":390,"P50":501,"P90":643,"source":"Redline"},"41":{"moyenne":524,"sd":100,"P10":403,"P50":515,"P90":655,"source":"Redline"},"42":{"moyenne":532,"sd":99,"P10":412,"P50":525,"P90":658,"source":"Redline"}}}
/* END REFERENCES */;
  function calculer(sa,masse,conditions){
    var out={terme_sa:sa,masse_g:masse,conditions_masse:conditions,reference:'Redline',z_brut:null,
      position_percentile:null,percentile_exact:null,seuils:null,motif:null,
      methode:'position parmi P10, P50, P90 publiés ; pas de loi normale ni interpolation',
      limite_mb:'Müller-Brochut : moyenne/ET présents dans le calculateur, distribution et protocole non établis ; aucun percentile exact déduit.'};
    if(!Number.isInteger(sa)){out.motif='Terme entier nécessaire, sans arrondi ni extrapolation.';return out;}
    if(typeof masse!=='number'||!Number.isFinite(masse)||masse<0){out.motif='Masse manquante ou invalide.';return out;}
    if(conditions!=='fraiche_paree'){out.motif='Référence non appliquée : préciser un poids frais paré ; poids fixé ou protocole inconnu non comparé.';return out;}
    var ref=references.Redline[sa];
    if(!ref||ref.source!=='Redline'){out.motif='Pas de quantiles publiés exploités à ce terme (22–42 SA) ; valeurs extrapolées 18–21 exclues.';return out;}
    out.z_brut=(masse-ref.moyenne)/ref.sd;
    out.seuils={P10:ref.P10,P50:ref.P50,P90:ref.P90};
    out.position_percentile=masse===ref.P10?'P10':masse===ref.P50?'P50':masse===ref.P90?'P90':masse<ref.P10?'< P10':masse<ref.P50?'P10–P50':masse<ref.P90?'P50–P90':'> P90';
    return out;
  }
  function html(r){
    function e(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
    var titres=['Valeur','Référence','Z-score','Position percentile','Limite'];
    var cells=[r.masse_g==null?null:r.masse_g+' g',r.reference,r.z_brut==null?null:(r.z_brut>=0?'+':'')+r.z_brut.toFixed(2)+' DS',r.position_percentile,r.motif];
    var style='border:1px solid #999;padding:5px 7px;word-break:normal;overflow-wrap:normal;text-decoration:none';
    return '<table style="font:11pt Cambria,\'Times New Roman\',serif;border-collapse:collapse;width:100%"><thead><tr>'+titres.map(function(t,i){return cells[i]==null?'':'<th style="'+style+';white-space:nowrap">'+e(t)+'</th>';}).join('')+'</tr></thead><tbody><tr>'+cells.map(function(c){return c==null?'':'<td style="'+style+'">'+e(c)+'</td>';}).join('')+'</tr></tbody></table>';
  }
  return {calculer:calculer,html:html};
})();
