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
| 🤪 **Mode Dingo** | Aveugle + buzz, **handicap permanent** selon l'écart, puis **⚡ tac o tac** obligatoire |

**Tous les réglages détaillés sont repliés sous « ⚙️ Personnaliser (facultatif) »** —
les joueurs veulent démarrer sans lire.

**Chaque style masque les options qui le contredisent** (`syncSections`, sections
`secXxx`). Afficher un réglage qui ne s'appliquera pas, c'est promettre pour rien :

| Style | Ce qui disparaît (et pourquoi) |
|---|---|
| 🎧 Tournoi | Partie à l'aveugle (le style inverse existe déjà) |
| 🕶️ Tous à l'aveugle | Source du son, mode de départ, roue, finale, fin de partie, temps de vote — l'app choisit, joue et corrige seule |
| ⚔️ Duel | Idem + équipes (on est deux) |
| 🔊 Animateur unique | « Je joue aussi » (le style **est** « l'hôte ne joue pas »), partie à l'aveugle, finale à l'aveugle |
| 🎡 Soirée surprise | Partie à l'aveugle + mode de départ (la roue l'écrase à chaque manche) |
| 🤪 Mode Dingo | Comme « Tous à l'aveugle » + équipes (le handicap est **individuel**) |

Le bloc « rotation du DJ » et les « manches à l'aveugle en fin de tour » suivent
`syncDjUI()` : sans rotation, il n'y a pas de fin de tour.
Chaque style **éteint** aussi ce qu'il ne veut pas (`press('#suBlind', 0)`…) : sinon
passer d'« aveugle » à « tournoi » laissait l'aveugle actif *en silence*, et la
section une fois masquée, plus personne ne pouvait le voir. `finalN` est remis à 0
sans rotation, pour qu'aucun réglage enregistré ne contredise le style.

### Modes de jeu
`classic` (buzz) · `turbo` (tout le monde répond, points à la vitesse 60→100) ·
`year` (deviner l'année)

> **Fredonne a été retiré** (jamais utilisé en soirée) : plus aucun point d'entrée —
> ni dans la création, ni dans le sélecteur de mode, ni dans la roue des défis. Le
> code interne (`state.source`, `mode === 'fredonne'`) reste en place mais **inerte** :
> l'arracher aurait touché les chemins de buzz et de verdict tout juste corrigés.

### 🤪 Mode Dingo (`state.dingo`) — équilibrage forcé
Un style à part : **l'avance se paie**. Le coefficient dépend de l'écart à la
**moyenne**, mesuré en « titres » (1 titre = `pointsBuzz`, ou 80 en Turbo) —
`dingoNiveau(s, id)`, table `DINGO_PALIERS` :

| Avance (en titres) | Gains | Malus | Libellé |
|---|---|---|---|
| ≥ +3 | **une bonne réponse coûte 1 titre** | ×1 | 🤪 Trop d'avance |
| ≥ +2 | ×0 | ×1 | 🧊 Plus rien à gagner |
| ≥ +1 | ×0,5 | ×1 | 🪫 Demi-points |
| −1 → +1 | ×1 | ×1 | 🎵 Normal |
| ≥ −2 | ×1,5 | ×0,5 | 🔥 Distancé |
| < −2 | ×2 | **×0** | 🚀 Largué : l'erreur est gratuite |

Points de vigilance :
- Le handicap s'applique **en dernier**, après combo et joker : appliqué avant, un
  meneur bien lancé y échappait en empilant combo × ×2 — la situation même que le
  mode existe pour corriger.
- Il vaut **aussi sur les votes** (sinon le meneur bridé se refaisait en jugeant) et
  **aussi en Turbo** (`applyTurbo` distribue par un chemin à lui — sans ça, changer
  de mode annulait le mode).
- Il est **annoncé avant le buzz** sur l'écran de chacun (`dingoBadge`) : c'est le
  cœur du jeu (le meneur peut choisir de se taire), et un malus découvert après coup
  serait vécu comme un bug.

**⚡ Tac o tac** (`state.tac`) — atteindre l'objectif n'arrête pas la partie :
`nivelle()` **écrase les écarts** (l'ordre du classement est conservé, ex aequo
compris, mais il ne reste qu'un pas de `pointsBuzz` entre chaque rang), puis
`max(3, min(7, nb_joueurs + 1))` manches à l'aveugle qui valent **×2**, sans aucun
handicap. Le dernier peut donc repasser devant **par le calcul**, pas par chance.
La partie se termine toute seule quand `tacLeft` tombe à 0. `replay()` remet
`tac/tacLeft/tacTotal/_blindDone/_finTour` à zéro — sans quoi la partie suivante
repartait directement en tac o tac.

### 🎯 Mode solo entraînement (`#solo`, `startSolo`)
Contrôleur autonome : **aucun canal temps réel, aucun joueur, aucun hôte**. L'app
tire un morceau, le joue, corrige (`fuzzyHit`) et compte. Barème : 12 points pour une
réponse immédiate, −1 toutes les 2,5 s, plancher à 3 ; moitié pour un « à moitié ».
Record dans `bt.soloBest`, réglages dans `bt.soloPls` / `bt.soloAns` / `bt.soloTotal`.
- La **mémoire musicale est partagée** avec les parties : s'entraîner l'après-midi ne
  fait pas ressortir les mêmes titres le soir.
- `appAudioMode`/`blindAudio` sont forcés puis **restaurés au `destroy`** : sans ça un
  réglage « source à part » laissé par une soirée précédente rendait le solo muet.
- Le chrono met à jour **son seul élément** (`#soChrono`) : redessiner effacerait la
  réponse en cours de saisie.

### 🚫 Le contre et ses effets (`CONTRE_EFFETS`, réglage « Effet du contre »)
Le seul joker qui vise **quelqu'un d'autre** : il cible automatiquement le meneur,
s'utilise avant le premier buzz, une seule fois par manche pour toute la table, et
jamais par le meneur lui-même. Six effets + **🎲 Au hasard** (tirage à chaque contre).

| Effet | Ce qu'il fait | Nature |
|---|---|---|
| 🧊 **Écran gelé** | Givre à frotter au doigt pour revenir | fait perdre du temps |
| 🐢 **Ralenti** | Son buzz s'ouvre 5 s après les autres | fait perdre du temps |
| 🎯 **Exigence** | Il doit donner titre **ET** artiste | relève la barre |
| 💸 **Quitte ou double** | Ses points comptent double, en bien comme en mal | pari |
| 🥈 **Second couteau** | Ne peut buzzer qu'après une 1ʳᵉ tentative | fait patienter |
| 🚫 **Barré sec** | Ne joue pas ce titre | élimine (assumé) |

**Trois règles d'arbitrage que tout nouvel effet doit respecter** (écrites dans le code
au-dessus de la table) :
1. **Aucun n'élimine définitivement** — sauf « barré sec », assumé comme la version brutale.
2. **Aucun ne demande d'arbitrage humain** : la règle se résout seule, sinon la soirée
   s'arrête pour discuter.
3. **Tous fonctionnent avec une enceinte unique.** C'est pour ça qu'il n'y a pas de
   « son coupé » : couper le son du visé couperait celui de toute la table.

Points d'implémentation :
- `contreEmpeche(id)` est **séparé** de `canBuzz`/`eligibleBuzzers` : le visé reste
  « quelqu'un qui peut encore répondre », sinon la manche se clôturait toute seule en
  le croyant hors jeu alors qu'il allait pouvoir jouer.
- `modeReponse(id)` porte l'exigence : c'est un `answerMode` **par joueur**.
- 🐢 Ralenti a besoin d'un `setTimeout` côté joueur (`_slowT`) : la fin du délai n'est
  pas un évènement réseau, personne ne rafraîchira l'écran sinon.

### Mécaniques
- **Rotation DJ** — le DJ choisit ses morceaux, les lance, **valide**, **enchaîne** et
  peut **terminer la partie** depuis son propre téléphone (intention `endGame`, limitée
  aux phases de révélation ; le téléphone de l'hôte reste le serveur et exécute).
  Il ne marque pas de points sur sa série.
- **Durée du tournoi** = `nb_joueurs × titres_par_DJ + manches_à_l'aveugle`
  (3 joueurs × 5 titres + 5 = **20 manches**). Affiché dans le salon et en cours de partie.
- **Équité** — `played` / `djTurns` par joueur ; le classement final est **ajusté**
  (`fairScore`) si tout le monde n'a pas eu le même nombre d'occasions.
- **Anti-triche : personne ne juge sa propre réponse.** Celui qui crée la partie tient
  le serveur, mais ça ne lui donne aucun pouvoir sur les points. Dès qu'il répond :
  à l'aveugle l'app tranche (`hostAnswer` fait exactement ce que fait un joueur —
  c'était **le trou** : il n'avait ni suggestion ni validation auto et arrivait
  toujours sur un écran qu'il pouvait trancher) ; sinon c'est le DJ / le fredonneur,
  ou à défaut la **majorité des votes des autres**, résolue automatiquement.
  En Turbo sa propre note est celle de l'app (`_autoGraded`, bouton verrouillé).
  En mode Année, l'année du morceau s'impose s'il a deviné lui aussi.
  Les scores ne se corrigent pas à la main non plus.
- **Combos** (série de bonnes réponses) · **Jokers** (🃏 ×2, 🛡️ bouclier, 🧊 contre)
- **🧊 Contre** — le seul joker **offensif**, réservé à ceux qui ne mènent pas. Il vise
  **le meneur** (`leaderId()`, personne en cas d'égalité en tête), s'utilise **avant le
  premier buzz** et **une seule fois par manche** pour toute la table. Deux effets au
  choix (réglage *Effet du contre*) :
  · `ice` (défaut) — **écran gelé** : le meneur voit son écran pris par le givre et doit
  le **frotter au doigt** pour le dégager (55 % de surface). Il perd des secondes mais
  reste dans la manche. Filet : libération automatique au bout de 12 s si le calcul de
  dégagement échoue — on ne piège jamais personne dans un écran bloqué.
  · `block` — **barré sec** : ajouté à `tried`, il ne joue pas ce titre.
  Le canvas du givre vit **hors de `#app`** : les rendus joueur reconstruisent `#app`
  en permanence et l'effaceraient.
- **Après une tentative ratée, on ne vote plus** — celui qui a répondu faux (−2)
  récupérait aussitôt +2 en votant sur la réponse du rebond : son erreur ne lui coûtait
  plus rien. Ceux qui sont dans `tried` sont exclus du vote **et** du décompte des
  votants attendus (sinon le total n'était jamais atteint).
- **Bouton plein écran flottant** (`#fsFloat`), présent sur **tous** les écrans — il
  n'existait que dans les Réglages.
- **Bonus qui reviennent** (`grantBonuses`) — un joker consommé était perdu pour toute
  la partie. Deux robinets opposés : **3 bonnes réponses d'affilée → 🃏 ×2** (récompense
  les forts) et **distancé de 3 × la valeur d'une bonne réponse → 🛡️** (fait revenir les
  autres, seulement si on n'a plus rien en main). Plafonné à 3.
- **Rotation DJ** : off · chaque titre · tous les 2 · 3 · 5 · **🎲 aléatoire** (1 à 5,
  retiré au sort à chaque passage de main). Le compteur est `_djLeft` / `_djSpan`, pas
  un modulo sur `djEvery` — un modulo ne peut pas décrire une série tirée au sort.
- **« 🤷 Je ne sais pas »** (intention `pass`) — chacun peut renoncer pendant le buzz.
  Quand plus personne ne peut répondre, l'app **révèle le titre et clôt la manche**
  (`noOneKnows`, `result.none`). Sans ça, un extrait que personne ne reconnaissait
  tournait en boucle sans aucune sortie.
  L'animateur voit **les noms** de ceux qui passent et de ceux qu'on attend encore,
  plus un toast à chaque passe : un compteur discret (« 1 joueur peut encore
  répondre ») ne lui disait ni qu'on passait, ni qui — il attendait un buzz qui ne
  venait jamais. Pas de bouton « Rebond » quand `result.none` : plus personne à qui
  rouvrir le buzz.
- **Le renommage par l'hôte fait autorité** (`renamedByHost`). `ensurePlayer()` ne
  réécrit **plus** le pseudo à chaque intention reçue : chaque buzz / passe / réponse
  porte le nom stocké sur le téléphone du joueur, et le réappliquer annulait la
  correction de l'hôte dès la première action. Le nom du téléphone ne s'applique
  qu'à la **première** arrivée, et jamais si l'hôte a corrigé — un joueur qui revient
  garde son nom, sinon il lui suffisait de se reconnecter pour se rebaptiser en pleine
  partie. L'en-tête du joueur affiche le nom **de la partie**, pas le sien en local.
- **Qui peut encore buzzer** = `eligibleBuzzers()` / `canBuzz(id)`, **une seule
  définition** partagée par le buzz joueur, le buzz hôte, le « je passe » et le calcul
  du rebond. La règle existait en trois exemplaires : l'hôte y échappait (il rebuzzait
  juste après avoir perdu) et le DJ comptait à tort comme rebondisseur possible.
  `validate()` inscrit désormais le perdant dans `tried` tout de suite.
- **Roue des défis** — 10 défis tirés au sort (double points, mort subite, titre seul…)
- **Barème** : bonne +5 / mauvaise −2 / bon vote +2 / **mauvais vote −1**
  Les scores ne sont **pas** modifiables à la main : pouvoir les corriger jetait un
  doute sur tout le classement. La fiche joueur ne permet que renommer / retirer.
- **Filtres combinables** — 151 artistes étiquetés époque × genre × langue
  (ex. *90s + Rock + Français*), + 10 playlists prédéfinies **cumulables**
  (Rock + 90s + Disney = union de leurs artistes, sans doublon)
- **Mémoire musicale persistante** (`bt.musicMemory` en localStorage) — sac
  d'artistes + morceaux déjà passés, conservés **d'une partie à l'autre et au
  rechargement**. Avant, tout repartait à zéro à chaque partie et les mêmes
  artistes revenaient aussitôt. Remise à zéro dans Réglages.
  Le tirage automatique demande **50 titres par artiste** (`AUTO_LIMIT`) au lieu des
  12 de l'affichage : avec 12, on retombait forcément sur les mêmes tubes.
- **Source externe** (enceinte, autre appli) — l'app ne choisit **rien** :
  `prefetchAuto()` sort tout de suite si `!canPlayInApp()`. Elle continuait à tirer un
  morceau au hasard (une playlist restait enregistrée d'une partie précédente), et ce
  morceau s'affichait comme « la réponse » sur tous les téléphones alors que la
  chanson venait de l'enceinte. Il faussait aussi la correction automatique. L'hôte
  enregistre lui-même le titre pour la révélation.
- **Connexion joueur** — la demande de `join` est **relancée toutes les 2,5 s** tant
  qu'aucun état n'arrive, et au bout de 3 essais l'écran explique (« vérifie le code
  et que le téléphone de l'hôte est allumé ») avec un bouton *Réessayer*. Avant,
  l'écran restait sur « Connexion… » indéfiniment : vu du joueur, « le code ne
  marche pas ».
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
9. **Une sélection qui masque ses propres options** — choisir une playlist faisait
   disparaître la rangée de puces : impossible d'en ajouter une deuxième. Garder les
   options visibles et cocher celles qui sont actives.
10. **Celui qui tient le serveur ne doit pas tenir l'arbitrage.** Le pouvoir se
   glissait par un chemin discret : l'hôte suivait un code différent des joueurs
   (`hostAnswer` vs l'intention `answer`). Toute asymétrie hôte/joueur est suspecte.
11. **Le décor passait devant le texte.** L'écran de création (formulaire long et
   dense) était posé à même le fond synthwave : soleil clair, bande orange et grille
   animée derrière du `text-white/40` en `text-xs`. Une surface sombre (`.bt-setup`)
   + contrastes remontés règlent ça **par écran**, sans toucher 30 chaînes. Les
   décors animés vont bien derrière un titre, jamais derrière un formulaire.
12. **Annuler une manche sans vider `roundTrack`** — le même morceau repartait au
   lancement suivant, d'où « ce titre revient tout le temps ». Annuler doit **jeter**
   le morceau et en préparer un autre.
13. **Une règle de jeu écrite en plusieurs exemplaires finit par diverger** — « qui
   peut buzzer » existait en trois endroits ; l'hôte échappait au filtre « déjà
   tenté ». Une règle = une fonction (`canBuzz`).
14. **L'hôte gardait les commandes du DJ.** En Turbo avec rotation, l'écran hôte
   affichait « Clore et corriger » et la grille de correction alors qu'un AUTRE
   joueur était DJ : deux personnes pilotaient la même manche, et l'hôte pouvait
   noter sa propre réponse. Garde-fou `jePilote = !s.dj || s.dj.id === ME`, à
   appliquer à **toute** commande de manche (clore, corriger, trancher, enchaîner).
   Le compteur de réponses attendait aussi le DJ (« 0/2 » à deux joueurs).
15. **Un réglage qui survit à la partie et parle plus fort que le mode courant** — la
   playlist enregistrée continuait d'alimenter le tirage en source externe. Toute
   préparation automatique doit d'abord demander : *est-ce que c'est encore mon rôle ?*
16. **Masquer une option ne suffit pas : il faut aussi l'éteindre.** Un réglage
   contradictoire caché mais resté ACTIF est pire qu'affiché — il agit sans que
   personne puisse le voir ni le corriger. Tout masquage doit s'accompagner d'une
   remise à l'état neutre.
17. **Une donnée renvoyée par le client écrase l'autorité du serveur.** Chaque
   intention portait le pseudo du téléphone ; `ensurePlayer()` le réappliquait, ce
   qui annulait silencieusement le renommage fait par l'hôte. Ce que le client
   envoie à chaque message ne doit pas écraser une décision prise côté hôte.
18. **Un compteur n'est pas une information.** « 1 joueur peut encore répondre » ne
   dit ni ce qui vient de se passer, ni qui : l'animateur n'a rien vu et a attendu.
   Un évènement qui attend une réaction doit être **nommé** et **notifié**.
19. **Une attente sans fin est lue comme une panne** — « Connexion… » sans limite ni
   explication, c'est « le code ne marche pas ». Toute attente réseau doit relancer,
   puis dire ce qui cloche.
20. **Une sortie anticipée qui dépend de l'affichage** — `voteTick` faisait
   `if (!el) return` sur le décompte : quand l'élément disparaissait, le verdict
   automatique n'était plus jamais rendu. Ne pas conditionner une règle du jeu à la
   présence d'un élément à l'écran.
21. **Vider une mémoire partagée par référence** — `playedIds` pointe directement sur
   `mem().tracks`. Remplacer l'objet à la remise à zéro laissait la partie en cours
   écrire dans une liste orpheline. Vider **sur place** (`arr.length = 0`).
22. **Un écran d'attente placé après le cas courant ne s'affiche jamais.** Dans
   `startSolo`, la branche `loading` venait après `phase === 'setup'` : la première
   recherche partant de l'écran de réglages, on restait plusieurs secondes dessus
   après avoir cliqué « Commencer », comme si le bouton était mort. **L'attente
   passe en premier.**
23. **À l'aveugle, l'app est le SEUL juge — sans morceau de référence, la table se
   bloque.** Rencontré en soirée en mode Dingo à deux : l'app n'avait plus le morceau
   (recherche échouée / téléphone de l'hôte rechargé), elle est retombée sur le vote…
   que personne ne pouvait trancher (le joueur ne valide pas sa propre réponse, l'autre
   ne connaissait pas le titre). Trois verrous posés :
   · **prévention** — `launchRound` n'ouvre pas le buzz d'une partie à l'aveugle sans
     morceau : il attend la recherche et se relance tout seul (`attenteMorceau`) ;
   · **auto-réparation** — filtres qui ne correspondent à personne, ou recherche
     bredouille : on abandonne les filtres et on retombe sur une playlist sûre. À
     l'aveugle l'hôte n'a **aucun écran** pour les corriger lui-même ;
   · **filet** — `manchePerdue()` : si malgré tout il n'y a pas de référence au moment
     de juger, la manche est annulée (personne ne marque) au lieu d'être renvoyée à
     des gens qui ne peuvent pas décider. Une manche blanche vaut mieux qu'une partie
     à l'arrêt. Vaut aussi pour `closeRacing` (Turbo), qui notait sinon tout le monde
     « faux ».
   Corollaire : **ne jamais armer une attente sans issue.** Chaque chemin qui met
   `attenteMorceau = true` doit avoir quelqu'un qui le remettra à `false`.
24. **Corriger automatiquement ne dispense pas de MONTRER la réponse.** À l'aveugle,
   on passait du buzz au verdict sans jamais afficher ce qui avait été écrit : on
   voyait « Raté » sans savoir de quoi. Or lire la bêtise de l'adversaire est une
   bonne moitié du plaisir en soirée. `reponseDite()` à la révélation (buzz) et le
   texte de chacun dans le récapitulatif Turbo. Règle générale : **un écran de
   verdict doit rappeler ce sur quoi il porte.**
25. **Masquer le titre ne suffit pas à garder un secret : il faut couper le son.**
   À l'aveugle, le lecteur de l'hôte affichait « morceau caché » mais le bouton ▶
   restait actif — et entre deux manches, c'est le morceau **suivant** qui est déjà
   en mémoire. Il suffisait d'écouter avant de lancer. Verrou `opts.verrou` sur
   `playerBar` tant que la manche n'est pas ouverte pour tous.
26. **Un réglage affiché doit être celui qui s'appliquera vraiment.** « Tous à
   l'aveugle » joue en Turbo mais affichait le barème au buzz (+5 / −2), inutilisé ;
   et les points de vote étaient réglables dans des parties où personne ne vote.
   `syncPointsUI()` lit désormais le mode **effectif** (`setupBlindPlay` à l'aveugle,
   `setupMode` sinon). À appeler **après** `syncSections`, qui réaffiche tout.
27. **Deux réglages pour la même chose, dont un inerte.** « Finale à l'aveugle :
   ON/OFF » n'a jamais rien fait : `finalN` (Aucune/3/5/10) est toujours défini et
   `nFinal` le préfère systématiquement. Retiré. Chercher `x != null ? x : y` :
   quand `x` est toujours défini, `y` est du code mort — et son interrupteur aussi.
28. **« À moitié » n'est pas « faux ».** La correction automatique passait
   `validate(suggest === 'ok', suggest === 'half')` : une réponse à moitié bonne
   partait donc en `correct = false` et prenait le **malus complet**, avec un écran
   qui annonçait « Raté ! −2 (à moitié) ». Révélé par l'effet 🎯 Exigence.
29. **Un modificateur de points doit couvrir TOUS les chemins de points.** Le
   handicap Dingo devait être posé dans `validate()` (buzz), sur les votes **et**
   dans `applyTurbo()` — sinon un simple changement de mode l'annulait en silence.
   Même piège que l'asymétrie hôte/joueur : une règle écrite à un seul endroit ne
   couvre jamais le jeu entier.

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

## 5 bis. Tester à plusieurs dans un navigateur

Le pane navigateur de l'assistant sait faire tourner une vraie partie :

```bash
python -m http.server 8777
```

Puis un onglet par participant. **Piège** : deux onglets sur la même origine
partagent le `localStorage`, donc le **même identifiant joueur** — le second écrase
le premier. Utiliser des origines différentes : `localhost:8777` pour l'un,
`127.0.0.1:8777` pour l'autre.

Deux limites du pane : les captures d'écran échouent s'il n'est pas affiché, et les
clics ne portent que dans les ~720 premiers pixels (pas de défilement fiable). Pour
un élément plus bas, déclencher un vrai événement : `el.dispatchEvent(new
MouseEvent('click', {bubbles:true}))` — c'est bien le gestionnaire de l'app qui
s'exécute. Penser aussi à neutraliser `window.confirm` (auto-rejeté en automatisation,
ce qui annule silencieusement l'action testée).

---

## 6. Ce qui reste ouvert

- **Extraits limités à 30 s** et ne commençant pas au début du morceau. Morceau entier
  = Spotify Premium (KO sur iPhone, plafond 25 utilisateurs), Apple MusicKit (99 €/an)
  ou YouTube (**pubs impossibles à retirer** — écarté d'un commun accord).
- L'assistant peut désormais **jouer une vraie partie dans le navigateur** (voir 5 bis),
  mais ça ne remplace pas la soirée réelle : la plupart des bugs sérieux ont été
  trouvés par l'utilisateur en conditions réelles. **Les retours terrain restent la
  meilleure source de bugs.**
- **Mode Dingo : réglage des paliers non validé en soirée.** La table `DINGO_PALIERS`
  a été calibrée au jugé (seuils à 1/2/3 titres d'écart). À confirmer en conditions
  réelles : est-ce que « une bonne réponse coûte des points » frustre ou amuse ?
- **Mode solo : le frottement n'est pas en cause, mais l'autoplay si.** `dzPlay` part
  d'un callback asynchrone (après la recherche du morceau) : sur navigateur strict,
  la lecture peut être refusée. Le bouton « ⏯️ Réécouter depuis le début » sert de
  filet ; à surveiller sur iPhone.
- Idées en réserve : intro seule, l'intrus, génériques TV, mort subite, stats joueurs,
  i18n anglais. Un « mode à réfléchir pour ralentir » a été évoqué par l'utilisateur
  sans être précisé — non implémenté.

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
