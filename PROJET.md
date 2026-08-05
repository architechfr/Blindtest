# 🎵 DJ Blind Test — état du projet

> **À lire en premier dans une nouvelle session.** Ce fichier résume tout ce qu'il faut
> savoir pour reprendre le développement sans relire l'historique.

---

## 1. L'essentiel

| | |
|---|---|
| **En ligne** | https://architechfr.github.io/Blindtest/ |
| **Dépôt** | `architechfr/Blindtest` (public), branche `main` → GitHub Pages |
| **Dossier local** | `…/APPLICATIONS-CLAUDE/BLINDTEST` |
| **Déploiement** | `git add -A && git commit -m "…" && git push` → en ligne en 1-3 min |
| **Auteur / crédits** | Florian — archi.tech.fr@gmail.com |

**Blind test musical multijoueur en temps réel.** Un fichier autonome `index.html`
(~4000 lignes) + PWA installable. L'hôte héberge la partie, les joueurs rejoignent
par QR code ou code à 6 caractères.

### Fichiers
- `index.html` — **toute l'application** (HTML + CSS + JS, un seul fichier)
- `manifest.json`, `sw.js` — PWA (installation, plein écran, cache)
- `assets/icon-192.png`, `assets/icon-512.png` — icônes cassette
- `make_icons.py`, `make_og.py` — génération des visuels (Pillow)

---

## 2. Stack technique

- **HTML + Tailwind (CDN)** — aucun build, aucune dépendance npm
- **Supabase Realtime** (Broadcast + Presence, **aucune table SQL**) — le jeu est
  éphémère et tient en mémoire. Clés publiques intégrées en dur (clé anon = publique
  par conception).
- **Deezer** (JSONP, sans clé) et **Apple/iTunes** (fetch, CORS `*`) — extraits 30 s
  gratuits, sans compte, sans pub. Bascule dans Réglages → « Banque d'extraits ».
- **qrcode 1.5.1** (⚠️ 1.5.3 renvoie une 404 sur le CDN), **html2canvas**, **jsQR**

### Architecture « autorité hôte »
L'écran hôte détient l'état complet et le diffuse (`broadcast: state`). Les joueurs
envoient des **intentions** (`broadcast: intent` — join / buzz / answer / vote / race /
judge / grade / nextRound / forceJudge…). La présence Supabase gère connexions et
déconnexions.

> ⚠️ **Règle d'or** : ne **jamais** `publish()` l'état complet sur un évènement qui
> n'intéresse pas tout le monde — cela redessine l'écran de tous et **efface les
> saisies en cours**. Utiliser `chan.sendProgress()` (canal léger) pour les infos
> ciblées (ex. avancement des réponses, destiné au seul DJ).

---

## 3. Modes et fonctionnalités

### Styles de partie (préréglages, en haut du menu de création)
| Style | Ce qu'il fait |
|---|---|
| 🎧 **Tournoi des DJ** | Rotation : chacun est DJ pour 3/5/10 titres, puis manches à l'aveugle |
| 🕶️ **Tous à l'aveugle** | Aucun DJ, l'app choisit/joue/corrige, N manches |
| ⚔️ **Duel à deux** | Aveugle + buzz + réponse « titre OU artiste » |
| 🔊 **Animateur unique** | L'hôte anime et valide, il ne joue pas |
| 🎡 **Soirée surprise** | Rotation + roue des défis |

**Tous les réglages détaillés sont repliés sous « ⚙️ Personnaliser (facultatif) »** —
les joueurs veulent démarrer sans lire.

### Modes de jeu
`classic` (buzz) · `turbo` (tout le monde répond, points à la vitesse 60→100) ·
`fredonne` (sans musique) · `year` (deviner l'année)

### Mécaniques
- **Rotation DJ** — le DJ choisit ses morceaux, les lance, **valide** et **enchaîne**
  depuis son propre téléphone. Il ne marque pas de points sur sa série.
- **Durée du tournoi** = `nb_joueurs × titres_par_DJ + manches_à_l'aveugle`
  (3 joueurs × 5 titres + 5 = **20 manches**). Affiché dans le salon et en cours de partie.
- **Équité** — `played` / `djTurns` par joueur ; le classement final est **ajusté**
  (`fairScore`) si tout le monde n'a pas eu le même nombre d'occasions.
- **Combos** (série de bonnes réponses) · **Jokers** (🃏 ×2, 🛡️ bouclier)
- **Roue des défis** — 10 défis tirés au sort (double points, mort subite, titre seul…)
- **Barème** : bonne +5 / mauvaise −2 / bon vote +2 / **mauvais vote −1**
- **Filtres combinables** — 151 artistes étiquetés époque × genre × langue
  (ex. *90s + Rock + Français*), + 10 playlists prédéfinies
- **Validation automatique** — `fuzzyHit()` : Levenshtein + nettoyage des mentions
  d'édition + comparaison par mots porteurs. **24/24 sur les cas de test.**

---

## 4. Pièges déjà rencontrés (ne pas refaire)

1. **Routage par hash** — affecter un hash identique ne déclenche **aucun** événement.
   Toujours passer par `go(h)` qui force `route()` si la cible est la route courante.
2. **UI conditionnée à la phase** — prévoir une **sortie de secours** (« Annuler cette
   manche »), sinon l'utilisateur se retrouve piégé sans bouton.
3. **Presets qui pilotent l'UI par clics simulés** — vérifier que chaque cible
   (`data-*`) **existe** ; un preset silencieusement inactif est pire qu'un réglage
   approximatif. Script `audit.js` fait ça.
4. **Ne pas conditionner une action essentielle à un événement navigateur optionnel**
   (`beforeinstallprompt` n'existe pas sur iPhone → prévoir la voie manuelle).
5. **Tirage aléatoire indépendant** = répétitions garanties. Utiliser un **sac mélangé**
   (`nextArtist`).
6. **Une règle codée mais non affichée est perçue comme absente** (cas de la durée du
   tournoi).
7. **Ne pas imposer un comportement « prudent » qui casse l'outil** — j'avais masqué le
   titre au DJ « par sécurité », alors qu'il en a besoin pour travailler.
8. **Batterie** — pas d'animation plein écran en boucle ; `backdrop-filter` sur chaque
   carte = très coûteux ; pauser les animations quand l'onglet n'est pas visible.

---

## 5. Méthode de vérification (sans navigateur)

L'accès navigateur a été indisponible une grande partie du projet. Vérifications faites
en ligne de commande :

```bash
# 1. Syntaxe des blocs <script>
node -e 'const fs=require("fs"),vm=require("vm");const h=fs.readFileSync("index.html","utf8");
const re=/<script>([\s\S]*?)<\/script>/g;let m,b=[];while((m=re.exec(h)))b.push(m[1]);
let ok=true;b.forEach((c,i)=>{try{new vm.Script(c)}catch(e){ok=false;console.log("bloc"+i+": "+e.message)}});
console.log(ok?"SYNTAXE OK":"ERREUR");'

# 2. Déploiement effectif (GitHub Pages met 1-3 min)
curl -s "https://architechfr.github.io/Blindtest/" | grep -c "unMotCleDuNouveauCode"
```

Extraire une fonction pour la tester : `sed -n 'DEBUT,FINp' index.html > /tmp/f.js`
puis `eval()` dans node. Les simulations de logique (rotation DJ, équité, tirage,
`fuzzyHit`) se testent très bien ainsi.

⚠️ **Attention aux apostrophes** lors des éditions par script Python : les chaînes JS
sont en `'…'`, il faut échapper `\'` — plusieurs erreurs de syntaxe sont venues de là.

---

## 6. Ce qui reste ouvert

- **« Terminer la partie » reste chez l'hôte** — son téléphone est le serveur ; le
  déplacer demanderait de refondre le modèle réseau.
- **Extraits limités à 30 s** et ne commençant pas au début du morceau. Morceau entier
  = Spotify Premium (KO sur iPhone, plafond 25 utilisateurs), Apple MusicKit (99 €/an)
  ou YouTube (**pubs impossibles à retirer** — écarté d'un commun accord).
- **Jamais testé en cliquant** par l'assistant (navigateur indisponible) : la plupart
  des bugs ont été trouvés par l'utilisateur en soirée réelle. **Les retours terrain
  sont la meilleure source de bugs.**
- Idées en réserve : intro seule, l'intrus, génériques TV, mort subite, stats joueurs,
  i18n anglais.

---

## 7. Comment travailler avec l'utilisateur

- Il teste **en conditions réelles, en soirée** — ses retours sont précis et fiables.
- Il veut **jouer vite** : privilégier les formats prêts à l'emploi, cacher la
  configuration.
- Il repère les incohérences d'interface (options qui ne s'appliquent pas, doublons,
  asymétries entre hôte et joueurs). **Quand il dit « je n'ai pas compris », c'est un
  défaut de conception, pas d'attention.**
- Répondre en français, aller droit au but, **dire honnêtement ce qui n'a pas été
  testé**.
