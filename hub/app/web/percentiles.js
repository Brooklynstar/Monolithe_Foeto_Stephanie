// SPDX-License-Identifier: CC-BY-NC-SA-4.0
// Noyau commun, intégré aux HTML autonomes par les outils de génération.
var Percentiles = (function(){
  "use strict";
  function calculer(z){
    if (typeof z !== "number" || !isFinite(z)) return null;
    var x = Math.abs(z), queue;
    if (x < 2){
      // Série convergente de l'intégrale normale autour de zéro.
      var terme = x, somme = x;
      for (var n = 1; n < 100; n++){
        terme *= x * x / (2 * n + 1);
        somme += terme;
        if (Math.abs(terme) < 1e-16 * Math.abs(somme)) break;
      }
      queue = 0.5 - Math.exp(-x * x / 2) * somme / Math.sqrt(2 * Math.PI);
    } else {
      // Fraction continue du rapport de Mills : conserve les petites queues.
      var fraction = 0;
      for (var k = 200; k >= 1; k--) fraction = k / (x + fraction);
      queue = Math.exp(-x * x / 2) / (Math.sqrt(2 * Math.PI) * (x + fraction));
    }
    return 100 * (z < 0 ? queue : 1 - queue);
  }
  function formater(p){
    if (typeof p !== "number" || !isFinite(p)) return "—";
    if (p < 0.01) return "P < 0,01";
    if (p > 99.99) return "P > 99,99";
    return "P" + p.toFixed(2).replace(".", ",");
  }
  function formaterZ(z){
    if (typeof z !== "number" || !isFinite(z)) return "—";
    return (z >= 0 ? "+" : "") + z.toFixed(2);
  }
  return {calculer: calculer, formater: formater, formaterZ: formaterZ};
})();
