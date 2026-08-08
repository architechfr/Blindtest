/* v3 : le palier 🤪 est-il inatteignable PAR CONSTRUCTION ?
   Hypothèse : le palier 🧊 (gain ×0) est un PLAFOND. Un meneur qui ne gagne plus
   ne peut plus creuser ; les autres, boostés, ne peuvent que se rapprocher. Le
   palier au-dessus serait donc mort quel que soit le nombre de joueurs.
   On teste 3 variantes pour départager. */
const BON = 5, MAL = -2;

const TABLES = {
  actuelle:      [[3,-1,1],[2,0,1],[1,.5,1],[-1,1,1],[-2,1.5,.5],[-99,2,0]],
  plafondPercé:  [[3,-1,1],[2,.25,1],[1,.5,1],[-1,1,1],[-2,1.5,.5],[-99,2,0]],
  malusRendu:    [[3,-1,1],[2,0,1],[1,.5,1],[-1,1,1],[-2,1.5,1],[-99,2,.5]]
};
/* Deux façons de mesurer l'avance :
   - moyenne  : (score - moyenne de TOUS) / unite   ← ce que fait l'app
   - dupack   : (score - moyenne des AUTRES) / unite ← indépendant du nb de joueurs */
function avance(scores, i, mode) {
  const n = scores.length, tot = scores.reduce((a, b) => a + b, 0);
  if (mode === 'dupack') return n < 2 ? 0 : (scores[i] - (tot - scores[i]) / (n - 1)) / BON;
  return (scores[i] - tot / n) / BON;
}
function palier(table, a) { for (const p of table) if (a >= p[0]) return { k: p[1], m: p[2], top: p[0] === 3 }; return null; }

function partie(table, mesure, nJ, nManches, niveaux) {
  const s = new Array(nJ).fill(0); let top = false, morts = 0;
  for (let r = 0; r < nManches; r++) {
    const ps = s.map((_, i) => palier(table, avance(s, i, mesure)));
    ps.forEach(p => { if (p.top) top = true; });
    const cands = [];
    for (let i = 0; i < nJ; i++) { if (ps[i].k > 0 && Math.random() < 0.85) cands.push(i); }
    if (!cands.length) { morts++; continue; }
    const b = cands[(Math.random() * cands.length) | 0];
    s[b] += (Math.random() < niveaux[b]) ? Math.round(BON * ps[b].k) : Math.round(MAL * ps[b].m);
  }
  const ec = (Math.max.apply(null, s) - Math.min.apply(null, s)) / BON;
  return { top, morts, ec };
}

function etude(nomTable, mesure, nJ, niveaux) {
  let top = 0, morts = 0, ec = 0; const N = 3000;
  for (let t = 0; t < N; t++) {
    const r = partie(TABLES[nomTable], mesure, nJ, 20, niveaux);
    if (r.top) top++; morts += r.morts; ec += r.ec;
  }
  return { pct: 100 * top / N, morts: morts / N, ec: ec / N };
}

const CAS = { 2: [0.85, 0.35], 3: [0.85, 0.5, 0.35], 5: [0.9, 0.6, 0.5, 0.45, 0.3] };
console.log('Palier 🤪 atteint (% de parties de 20 manches) · écart final moyen (titres)\n');
console.log('table            mesure    | 2 joueurs        | 3 joueurs        | 5 joueurs');
['actuelle', 'plafondPercé', 'malusRendu'].forEach(tb => {
  ['moyenne', 'dupack'].forEach(m => {
    const l = [2, 3, 5].map(nJ => { const r = etude(tb, m, nJ, CAS[nJ]); return (r.pct.toFixed(1) + '%').padStart(6) + ' / ' + r.ec.toFixed(1) + 't'; });
    console.log(tb.padEnd(16) + m.padEnd(9) + ' | ' + l.join(' | '));
  });
});

console.log('\n--- Seuil de déclenchement de 🤪, en écart RÉEL meneur/dernier ---');
console.log('mesure    | 2 j. | 3 j. | 5 j.');
['moyenne', 'dupack'].forEach(m => {
  const l = [2, 3, 5].map(nJ => {
    for (let g = 0; g <= 40; g += 0.5) {
      const s = new Array(nJ).fill(0); s[0] = g * BON;
      if (avance(s, 0, m) >= 3) return g;
    }
    return '>40';
  });
  console.log(m.padEnd(9) + ' | ' + l.map(x => String(x).padStart(4)).join(' | '));
});
