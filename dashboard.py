# -*- coding: utf-8 -*-
"""Genere le tableau de bord carburant : une page HTML autonome.

Aucune bibliotheque externe, aucun CDN : la page fonctionne hors ligne
et peut s'ouvrir dans n'importe quel navigateur. Les donnees calculees
sont embarquees en JSON dans la page ; les graphiques sont dessines en
HTML/SVG par le script embarque.

Le script signale les anomalies, il ne corrige jamais la donnee
d'origine : les lignes INVALIDE ou A_VERIFIER restent visibles et sont
exclues des totaux.
"""

import json

_STATUTS = ["OK", "ELEVE", "ANORMAL", "A_VERIFIER", "INVALIDE",
            "SANS_APPRO"]


def _modele(analyse, kpis, demo=False):
    engins = []
    for e in analyse["engins"]:
        engins.append({
            "code": e["code"], "type": e["type"],
            "chantier": e["chantier"], "cpt": e["type_compteur"],
            "ref": e["ref"], "litres": e["litres"], "unites": e["unites"],
            "conso": e["conso"], "ecart": e["ecart"],
            "statut": e["statut"], "nbSig": e["nb_sig"],
            "compte": e["compte"], "jours": e["jours"],
        })
    return {
        "periode": "%s au %s" % (analyse["periode"][0],
                                 analyse["periode"][1]),
        "demo": bool(demo),
        "engins": engins,
        "anomalies": analyse["anomalies"],
        "joursParc": analyse["jours_parc"],
    }


def generer_dashboard(analyse, kpis, chemin_sortie, demo=False):
    modele = _modele(analyse, kpis, demo)
    donnees = json.dumps({"m": modele, "k": kpis}, ensure_ascii=False)
    page = _GABARIT.replace("__DONNEES__", donnees)
    with open(chemin_sortie, "w", encoding="utf-8") as f:
        f.write(page)
    return chemin_sortie


_GABARIT = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Suivi carburant engins - Tableau de bord</title>
<style>
:root{--fond:#14100a;--carte:#211a10;--encre:#f0ead9;--doux:#b0a284;--ligne:#382c17;
--accent:#f59e0b;--ok:#22c55e;--info:#38bdf8;--warn:#f59e0b;--bad:#ef4444;--eleve:#eab308;--na:#64748b}
*{box-sizing:border-box}
body{font-family:"Segoe UI",system-ui,-apple-system,sans-serif;background:var(--fond);color:var(--encre);padding:18px}
h1{margin:0 0 4px;font-size:22px}
h2{font-size:16px;margin:0 0 10px}
.sous{color:var(--doux);font-size:13px}
.badge-demo{background:#fef3c7;color:#92400e;border:1px solid #fcd34d;border-radius:6px;padding:2px 8px;font-size:12px;font-weight:600;margin-left:8px}
.cartes{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:14px 0}
.carte{background:var(--carte);border:1px solid var(--ligne);border-radius:10px;padding:12px 14px}
.carte .v{font-size:22px;font-weight:700}
.carte .l{font-size:12px;color:var(--doux);margin-top:2px}
.section{background:var(--carte);border:1px solid var(--ligne);border-radius:10px;padding:14px;margin-bottom:16px;overflow-x:auto}
table{border-collapse:collapse;font-size:12.5px;width:100%}
th,td{border:1px solid #e5e7eb;padding:4px 6px;text-align:center;white-space:nowrap}
thead th{background:#eef2f9;font-weight:600}
.codecol{text-align:left;font-weight:600;position:sticky;left:0;background:var(--carte)}
.stOK{color:var(--ok);font-weight:600}
.stELEVE{color:var(--eleve);font-weight:600}
.stANORMAL{color:var(--bad);font-weight:700}
.stA_VERIFIER{color:var(--warn);font-weight:600}
.stINVALIDE{color:var(--bad);font-weight:600;text-decoration:line-through}
.stSANS_APPRO{color:var(--na)}
.pastille{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:4px;vertical-align:-1px}
.legende{display:flex;flex-wrap:wrap;gap:8px;font-size:11px;color:var(--doux);margin:6px 0 10px}
.filtres{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:10px}
.filtres input,.filtres select{padding:5px 8px;border:1px solid var(--ligne);border-radius:6px;font-size:13px;background:#fff}
.note{font-size:12px;color:var(--doux);margin-top:8px}
.graphwrap{display:flex;gap:8px;align-items:stretch;margin-top:6px}
.axey{display:flex;flex-direction:column;justify-content:space-between;font-size:10px;color:var(--doux);text-align:right;padding-bottom:18px}
.barscol{flex:1}
.bars{display:flex;align-items:flex-end;gap:2px;height:180px;border-left:1px solid #cbd5e1;border-bottom:1px solid #cbd5e1;padding:0 4px}
.bar{flex:1;background:var(--accent);border-radius:3px 3px 0 0;min-width:6px;position:relative;cursor:pointer}
.bar:hover,.bar.actif{background:#b45309}
.bar .tip{display:none;position:absolute;bottom:105%;left:50%;transform:translateX(-50%);background:#111827;color:#fff;font-size:11px;padding:2px 6px;border-radius:4px;white-space:nowrap;z-index:2}
.bar:hover .tip{display:block}
.axesx{display:flex;gap:2px;padding:4px 4px 0}
.axesx span{flex:1;min-width:6px;text-align:center;font-size:10px;color:var(--doux)}
.repligne{display:flex;align-items:center;gap:6px;font-size:11px;margin:3px 0}
.repligne .code{width:86px;text-align:right;color:var(--doux);white-space:nowrap}
.repbar{flex:1;display:flex;height:12px;border-radius:3px;overflow:hidden;background:#e2e8f0}
.repbar div{height:100%}
.topligne{display:flex;align-items:center;gap:8px;font-size:12px;margin:4px 0}
.topligne .code{width:90px;text-align:right;color:var(--doux);white-space:nowrap}
.topbar{height:14px;border-radius:3px;background:var(--accent)}
.compte{font-size:12px;color:var(--doux)}
.pager{display:flex;gap:8px;align-items:center;margin-top:8px;font-size:12px;color:var(--doux)}
.pager button{padding:3px 10px;border:1px solid var(--ligne);border-radius:6px;background:#fff;cursor:pointer;font-size:12px}
.pager button:disabled{opacity:.4;cursor:default}

/* theme sombre + bandeau engins (SVG embarque, aucun fichier externe) */
body{padding:0}
body::before{content:"";display:block;height:210px;
background:linear-gradient(180deg,#2e1c06 0%,#7a4a12 55%,#b5701a 100%)}
header,.cartes,.section,.note,footer{margin-left:22px;margin-right:22px}
header{margin-top:-190px;position:relative;z-index:2;
background:url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxNjAwIiBoZWlnaHQ9IjIyMCIgdmlld0JveD0iMCAwIDE2MDAgMjIwIj4KPGcgZmlsbD0iIzI0MTUwMyI+CjxyZWN0IHg9IjAiIHk9IjE5MCIgd2lkdGg9IjE2MDAiIGhlaWdodD0iMzAiLz4KPGc+CjxyZWN0IHg9IjYwIiB5PSIxMjAiIHdpZHRoPSIxNTAiIGhlaWdodD0iNTUiIHJ4PSI2Ii8+CjxwYXRoIGQ9Ik0yMTAgMTc1IHYtNzAgaDU1IGwzNSAzNSB2MzUgeiIvPgo8cmVjdCB4PSIyMjUiIHk9IjExNSIgd2lkdGg9IjI4IiBoZWlnaHQ9IjIyIiByeD0iMyIgZmlsbD0iIzI0MTUwMyIvPgo8Y2lyY2xlIGN4PSI5NSIgY3k9IjE4NSIgcj0iMjIiLz48Y2lyY2xlIGN4PSIxODUiIGN5PSIxODUiIHI9IjIyIi8+PGNpcmNsZSBjeD0iMjQ1IiBjeT0iMTg1IiByPSIyMiIvPgo8Y2lyY2xlIGN4PSI5NSIgY3k9IjE4NSIgcj0iOSIgZmlsbD0iIzRhMzAxMCIvPjxjaXJjbGUgY3g9IjE4NSIgY3k9IjE4NSIgcj0iOSIgZmlsbD0iIzRhMzAxMCIvPjxjaXJjbGUgY3g9IjI0NSIgY3k9IjE4NSIgcj0iOSIgZmlsbD0iIzRhMzAxMCIvPgo8cGF0aCBkPSJNNjAgMTIwIGgxNTAgbC0xMiAtMjggaC0xMjYgeiIvPgo8L2c+CjxnPgo8cmVjdCB4PSI0MzAiIHk9IjE1MCIgd2lkdGg9IjEyMCIgaGVpZ2h0PSIzMiIgcng9IjE0Ii8+CjxyZWN0IHg9IjQ1NSIgeT0iMTEyIiB3aWR0aD0iNjAiIGhlaWdodD0iNDIiIHJ4PSI2Ii8+CjxwYXRoIGQ9Ik01MTUgMTMwIEw2MDAgODggTDY0MCA5NiBMNTYwIDE0MCBaIi8+CjxwYXRoIGQ9Ik02MDAgODggTDY2OCAxMzAgTDY2MCAxNDIgTDYzMiAxMDAgWiIvPgo8cGF0aCBkPSJNNjYwIDE0MiBxMTggMTAgNiAyNiBsLTI0IDQgcTE0IC0xNiA2IC0zMCB6Ii8+CjxjaXJjbGUgY3g9IjQ3MCIgY3k9IjE4NiIgcj0iMTYiLz48Y2lyY2xlIGN4PSI1MTUiIGN5PSIxODYiIHI9IjE2Ii8+CjwvZz4KPGc+CjxyZWN0IHg9Ijc2MCIgeT0iNjAiIHdpZHRoPSIxNCIgaGVpZ2h0PSIxMzAiLz4KPHBhdGggZD0iTTc2NyAzMCBMOTgwIDg0IEw5NzUgOTIgTDc2NyA0OCBaIi8+CjxwYXRoIGQ9Ik03NjcgMzAgTDcxMiA3OCBMNzIwIDg2IEw3NjcgNDggWiIvPgo8cmVjdCB4PSI3MDAiIHk9Ijc4IiB3aWR0aD0iMjIiIGhlaWdodD0iMTYiLz4KPGxpbmUgeDE9Ijk1MCIgeTE9Ijg2IiB4Mj0iOTUwIiB5Mj0iMTUwIiBzdHJva2U9IiMyNDE1MDMiIHN0cm9rZS13aWR0aD0iNSIvPgo8cmVjdCB4PSI5MzgiIHk9IjE1MCIgd2lkdGg9IjI0IiBoZWlnaHQ9IjE4IiByeD0iMyIvPgo8cmVjdCB4PSI3NDIiIHk9IjE5MCIgd2lkdGg9IjUwIiBoZWlnaHQ9IjEwIi8+CjwvZz4KPGcgb3BhY2l0eT0iMC44NSI+CjxyZWN0IHg9IjEwNTAiIHk9IjE0MCIgd2lkdGg9IjEyMCIgaGVpZ2h0PSI0NCIgcng9IjUiLz4KPHBhdGggZD0iTTExNzAgMTg0IHYtNTYgaDQ0IGwyOCAyOCB2MjggeiIvPgo8Y2lyY2xlIGN4PSIxMDgwIiBjeT0iMTkyIiByPSIxNyIvPjxjaXJjbGUgY3g9IjExNTAiIGN5PSIxOTIiIHI9IjE3Ii8+PGNpcmNsZSBjeD0iMTIxOCIgY3k9IjE5MiIgcj0iMTciLz4KPHBhdGggZD0iTTEwNTAgMTQwIGgxMjAgbC0xMCAtMjIgaC0xMDAgeiIvPgo8L2c+CjxnPgo8cmVjdCB4PSIxMzMwIiB5PSIxNTAiIHdpZHRoPSI5MCIgaGVpZ2h0PSIzNCIgcng9IjgiLz4KPHJlY3QgeD0iMTM2MCIgeT0iMTE4IiB3aWR0aD0iNDAiIGhlaWdodD0iMzYiIHJ4PSI1Ii8+CjxwYXRoIGQ9Ik0xMzMwIDE2MCBMMTI3MCAxNTAgTDEyNjYgMTY4IEwxMzMwIDE3NiBaIi8+CjxwYXRoIGQ9Ik0xMjcwIDE1MCBxLTIyIDQgLTE4IDI4IGwyMCAyIHEtNiAtMTYgNiAtMjQgeiIvPgo8Y2lyY2xlIGN4PSIxMzUyIiBjeT0iMTkwIiByPSIxOCIvPjxjaXJjbGUgY3g9IjE0MDgiIGN5PSIxOTAiIHI9IjE4Ii8+CjxjaXJjbGUgY3g9IjEzNTIiIGN5PSIxOTAiIHI9IjciIGZpbGw9IiM0YTMwMTAiLz48Y2lyY2xlIGN4PSIxNDA4IiBjeT0iMTkwIiByPSI3IiBmaWxsPSIjNGEzMDEwIi8+CjwvZz4KPC9nPgo8L3N2Zz4=) bottom center/cover no-repeat;
border-radius:14px;padding:26px 24px 20px;color:#fff;
box-shadow:0 8px 30px rgba(10,6,1,.5)}
h1{font-size:26px;letter-spacing:.3px;text-shadow:0 2px 8px rgba(10,6,1,.6)}
header .sous{color:#f0e2c8}
.badge-demo{background:rgba(250,204,21,.18);color:#fde68a;border-color:#f59e0b}
.carte,.section{background:rgba(33,26,16,.94);box-shadow:0 4px 18px rgba(10,6,1,.35)}
.carte .v{color:#fff}
h2{color:#fff}
thead th{background:#2b2110;color:#e8dfc8}
th,td{border-color:#382c17}
.codecol{background:#251c0d;color:#f0ead9}
select,.filtres input{background:#14100a;color:#f0ead9;border-color:#4a3a1d}
.pager button{background:#14100a;color:#f0ead9;border-color:#4a3a1d}
.bar:hover,.bar.actif{background:#d97706}
.bars{border-color:#4a3a1d}
.repbar{background:#2a2113}
footer{color:var(--doux);font-size:12px;margin-bottom:18px}
</style>
</head>
<body>
<header>
  <h1>Suivi carburant engins</h1>
  <span class="sous" id="periode"></span>
  <span class="badge-demo" id="demo" style="display:none">JEU DE DONNEES GENERE</span>
  <div class="note">Projet personnel de Rachid Fadili (rachidfadili2002@outlook.com) - concu a partir de son experience terrain dans le suivi d'engins de chantier.</div>
</header>
<div class="cartes" id="kpis"></div>

<div class="section">
  <h2>Consommation par engin</h2>
  <div class="legende">
    <span><i class="pastille" style="background:var(--ok)"></i>OK</span>
    <span><i class="pastille" style="background:var(--eleve)"></i>Eleve</span>
    <span><i class="pastille" style="background:var(--bad)"></i>Anormal</span>
    <span><i class="pastille" style="background:var(--warn)"></i>A verifier</span>
    <span><i class="pastille" style="background:var(--na)"></i>Invalide (exclu des totaux)</span>
    <span>L/h = litres par heure de fonctionnement, L/100km pour les camions</span>
  </div>
  <div class="filtres" id="filtres">
    <input id="fCode" type="search" placeholder="Rechercher un engin (code)...">
    <select id="fChantier"><option value="">Tous chantiers</option></select>
    <select id="fType"><option value="">Tous compteurs</option><option value="h">Compteurs horaires</option><option value="km">Compteurs kilometres</option></select>
    <select id="fStatut"><option value="">Tous statuts</option><option value="OK">OK</option><option value="ELEVE">Eleve</option><option value="ANORMAL">Anormal</option><option value="A_VERIFIER">A verifier</option><option value="INVALIDE">Invalide</option></select>
    <span class="compte" id="fCompte"></span>
  </div>
  <div id="tableau"></div>
  <div class="note">Consommation = litres approvisionnes / hausse du compteur sur les journees mesurees (lignes invalides exclues, jamais corrigees). Ecart = consommation moyenne vs la reference reglable de l'engin.</div>
</div>

<div class="section">
  <h2>Litres par jour</h2>
  <select id="choix"></select>
  <div class="graphwrap">
    <div class="axey" id="axey"></div>
    <div class="barscol">
      <div class="bars" id="bars"></div>
      <div class="axesx" id="axesx"></div>
    </div>
  </div>
  <div class="note" id="totEngin"></div>
</div>

<div class="section">
  <h2>Repartition des journees par statut</h2>
  <div id="repartition"></div>
</div>

<div class="section">
  <h2>Plus gros consommateurs (litres sur la periode)</h2>
  <div id="top"></div>
</div>

<div class="section" id="secAno">
  <h2>Signalements a revoir</h2>
  <div id="anomalies"></div>
  <div class="note">Le script signale, il ne corrige jamais la donnee d'origine : la decision finale reste a l'humain. Une consommation anormale durable peut indiquer une fuite, un probleme moteur ou un vol ; une consommation tres basse est souvent une erreur de saisie.</div>
</div>

<footer>Suivi carburant engins - tableau de bord genere automatiquement, page autonome sans connexion.</footer>

<script>
var D = __DONNEES__;
var M = D.m, K = D.k;
var PAGE = 50;
function tranche(arr, page) { return arr.slice(page.n * PAGE, (page.n + 1) * PAGE); }
function navHtml(nom, page, total) {
  var pages = Math.max(1, Math.ceil(total / PAGE));
  if (page.n >= pages) page.n = pages - 1;
  if (page.n < 0) page.n = 0;
  if (pages <= 1) return "";
  return "<div class='pager'><button onclick='" + nom + "(-1)'" + (page.n <= 0 ? " disabled" : "") + ">&larr; Precedent</button>" +
    "Page " + (page.n + 1) + " / " + pages + " (" + total + " lignes)" +
    "<button onclick='" + nom + "(1)'" + (page.n >= pages - 1 ? " disabled" : "") + ">Suivant &rarr;</button></div>";
}
var COUL = {"OK":"#16a34a","ELEVE":"#eab308","ANORMAL":"#dc2626","A_VERIFIER":"#f59e0b","INVALIDE":"#64748b","SANS_APPRO":"#3b3527"};
var LIB = {"OK":"OK","ELEVE":"Eleve","ANORMAL":"Anormal","A_VERIFIER":"A verifier","INVALIDE":"Invalide","SANS_APPRO":"Sans appro"};
function unite(e){ return e.cpt === "km" ? "L/100km" : "L/h"; }
function fmt(n, d){ return (n === null || n === undefined) ? "-" : Number(n).toFixed(d === undefined ? 1 : d); }
function dateFR(j){ var p = j.split("-"); return p[2] + "/" + p[1]; }

document.getElementById("periode").textContent = "Periode : " + M.periode;
if (M.demo) document.getElementById("demo").style.display = "";

var kpis = [
  [K.nb_engins, "engins suivis"],
  [K.litres_totaux + " L", "litres sur la periode"],
  [K.conso_moy_h !== null ? K.conso_moy_h + " L/h" : "-", "conso moyenne (engins horaires)"],
  [K.conso_moy_km !== null ? K.conso_moy_km + " L/100km" : "-", "conso moyenne (camions)"],
  [K.nb_signalements, "signalements a revoir"]
];
if (K.cout_estime)
  kpis.push([K.cout_estime.toLocaleString("fr-FR") + " " + (K.devise || ""), "cout estime (prix configurable)"]);
document.getElementById("kpis").innerHTML = kpis.map(function(k){
  return '<div class="carte"><div class="v">'+k[0]+'</div><div class="l">'+k[1]+'</div></div>';
}).join("");

// --- tableau par engin + filtres ---
var chantiers = {};
M.engins.forEach(function(e){ chantiers[e.chantier] = 1; });
document.getElementById("fChantier").innerHTML += Object.keys(chantiers).sort().map(function(c){
  return '<option value="'+c+'">'+c+'</option>'; }).join("");

function enginsFiltres(){
  var q = document.getElementById("fCode").value.trim().toLowerCase();
  var c = document.getElementById("fChantier").value;
  var t = document.getElementById("fType").value;
  var s = document.getElementById("fStatut").value;
  return M.engins.filter(function(e){
    if (q && e.code.toLowerCase().indexOf(q) < 0) return false;
    if (c && e.chantier !== c) return false;
    if (t && e.cpt !== t) return false;
    if (s && e.statut !== s) return false;
    return true;
  });
}
var pageTab = {n:0};
function pageTabNav(d){ pageTab.n += d; dessineTableau(); }
function dessineTableau(){
  var liste = enginsFiltres();
  document.getElementById("fCompte").textContent = liste.length + " engin(s)";
  var lignes = tranche(liste, pageTab).map(function(e){
    var ecart = (e.ecart === null) ? "-" :
      '<span class="' + (e.ecart > 0 ? "stANORMAL" : "stOK") + '">' + (e.ecart > 0 ? "+" : "") + fmt(e.ecart) + "%</span>";
    return "<tr><td class='codecol'>" + e.code + "</td><td>" + e.type + "</td><td>" + e.chantier + "</td>" +
      "<td>" + (e.cpt === "km" ? "km" : "h") + "</td>" +
      "<td>" + fmt(e.unites, 0) + "</td><td>" + fmt(e.litres, 0) + "</td>" +
      "<td><b>" + fmt(e.conso, 1) + "</b> " + unite(e) + "</td>" +
      "<td>" + fmt(e.ref, 1) + "</td><td>" + ecart + "</td>" +
      "<td class='st" + e.statut + "'>" + LIB[e.statut] + (e.nbSig ? " (" + e.nbSig + ")" : "") + "</td></tr>";
  }).join("");
  document.getElementById("tableau").innerHTML =
    "<table><thead><tr><th>Engin</th><th>Type</th><th>Chantier</th><th>Cpt</th>" +
    "<th>Heures / km</th><th>Litres</th><th>Conso</th><th>Ref</th><th>Ecart</th><th>Statut</th></tr></thead>" +
    "<tbody>" + lignes + "</tbody></table>" + navHtml("pageTabNav", pageTab, liste.length);
}
["fCode","fChantier","fType","fStatut"].forEach(function(id){
  document.getElementById(id).addEventListener("input", function(){ pageTab.n = 0; dessineTableau(); });
});
dessineTableau();

// --- litres par jour (parc entier ou un engin) ---
var choix = document.getElementById("choix");
choix.innerHTML = '<option value="">Parc entier</option>' + M.engins.map(function(e){
  return '<option value="' + e.code + '">' + e.code + '</option>'; }).join("");
function serieCourante(){
  var c = choix.value;
  if (!c) return {jours: M.joursParc, nom: "Parc entier"};
  var e = M.engins.find(function(x){ return x.code === c; });
  return {jours: e.jours.filter(function(j){ return j.litres > 0; }).map(function(j){
    return {j: j.j, litres: j.litres, st: j.st, ratio: j.ratio}; }), nom: c};
}
function dessineGraph(){
  var s = serieCourante();
  var max = 0;
  s.jours.forEach(function(j){ if (j.litres > max) max = j.litres; });
  max = max || 1;
  var axey = "";
  for (var i = 4; i >= 0; i--) axey += "<span>" + Math.round(max * i / 4) + "</span>";
  document.getElementById("axey").innerHTML = axey;
  var bars = "", axes = "", total = 0;
  s.jours.forEach(function(j, i){
    total += j.litres;
    var coul = (j.st === "ANORMAL") ? "#dc2626" : (j.st === "ELEVE" ? "#eab308" : "var(--accent)");
    var tip = dateFR(j.j) + " : " + fmt(j.litres) + " L" +
      (j.ratio ? " (" + fmt(j.ratio, 1) + " " + (choix.value && M.engins.find(function(x){return x.code===choix.value;}).cpt === "km" ? "L/100km" : "L/h") + ")" : "");
    bars += '<div class="bar" style="height:' + Math.max(2, Math.round(j.litres / max * 100)) + '%;background:' + coul + '"><span class="tip">' + tip + '</span></div>';
    if (i % Math.ceil(s.jours.length / 15) === 0 || i === s.jours.length - 1)
      axes += "<span style='flex:none;width:auto;margin-right:8px'>" + dateFR(j.j) + "</span>";
  });
  document.getElementById("bars").innerHTML = bars;
  document.getElementById("axesx").innerHTML = axes;
  document.getElementById("totEngin").textContent =
    s.nom + " : " + fmt(total, 0) + " L sur " + s.jours.length + " journees d'approvisionnement. " +
    "Barre jaune = journee elevee, rouge = anormale.";
}
choix.addEventListener("input", dessineGraph);
dessineGraph();

// --- repartition des journees par statut ---
var rep = document.getElementById("repartition");
rep.innerHTML = M.engins.map(function(e){
  var total = 0;
  for (var k in e.compte) total += e.compte[k];
  if (!total) return "";
  var bar = ["OK","ELEVE","ANORMAL","A_VERIFIER","INVALIDE","SANS_APPRO"].map(function(k){
    var n = e.compte[k] || 0;
    if (!n) return "";
    var pct = n / total * 100;
    return "<div style='width:" + pct + "%;background:" + COUL[k] + "' title='" + LIB[k] + " : " + n + " j (" + Math.round(pct) + "%)'></div>";
  }).join("");
  return "<div class='repligne'><span class='code'>" + e.code + "</span><div class='repbar'>" + bar + "</div></div>";
}).join("");

// --- top consommateurs ---
var topEngins = M.engins.slice().sort(function(a, b){ return b.litres - a.litres; }).slice(0, 5);
var maxL = topEngins.length ? topEngins[0].litres : 1;
document.getElementById("top").innerHTML = topEngins.map(function(e){
  return "<div class='topligne'><span class='code'>" + e.code + "</span>" +
    "<div class='topbar' style='width:" + Math.round(e.litres / maxL * 55) + "%'></div>" +
    "<span>" + fmt(e.litres, 0) + " L</span></div>";
}).join("");

// --- signalements ---
var pageAno = {n:0};
function pageAnoNav(d){ pageAno.n += d; dessineAno(); }
function dessineAno(){
  var liste = M.anomalies;
  if (!liste.length) {
    document.getElementById("anomalies").innerHTML = "<p class='note'>Aucun signalement sur la periode.</p>";
    return;
  }
  var lignes = tranche(liste, pageAno).map(function(a){
    return "<tr><td>" + dateFR(a.date) + "</td><td class='codecol'>" + a.engin + "</td>" +
      "<td class='st" + a.statut + "'>" + LIB[a.statut] + "</td>" +
      "<td style='text-align:left;white-space:normal'>" + a.motif + "</td>" +
      "<td>" + fmt(a.litres) + " L</td>" +
      "<td>" + (a.ratio ? fmt(a.ratio, 1) : "-") + "</td></tr>";
  }).join("");
  document.getElementById("anomalies").innerHTML =
    "<table><thead><tr><th>Date</th><th>Engin</th><th>Gravite</th><th>Motif</th><th>Litres</th><th>Conso mesuree</th></tr></thead>" +
    "<tbody>" + lignes + "</tbody></table>" + navHtml("pageAnoNav", pageAno, liste.length);
}
dessineAno();
</script>
</body>
</html>
"""
