# Suivi carburant engins : consommation, alertes et tableau de bord

Projet Python personnel de **suivi de la consommation de gasoil d'un
parc d'engins de chantier** : consommation par engin en L/h (ou
L/100km pour les camions), comparaison à une référence réglable par
engin, détection des consommations anormales, et un **tableau de bord
HTML autonome** généré à partir des données.

Projet personnel, utilisable sans aucune configuration.
Aucune donnée d'entreprise, aucune URL, aucun identifiant dans ce dépôt.
Le script **signale** les anomalies ; il ne corrige jamais les données
d'origine et la décision finale reste à l'humain.

Python 3 standard, **aucune bibliothèque à installer**, aucun service
externe obligatoire. Le tableau de bord est une page HTML autonome
(sans CDN) qui s'ouvre dans n'importe quel navigateur.

## Ce qu'il fait

1. **Lecture des relevés** (`data/carburant.csv`) : pour chaque engin
   et chaque journée d'activité, le compteur de fin de journée
   (horaire ou kilométrique) et les litres approvisionnés.
2. **Contrôle et calculs** : consommation = litres / hausse du
   compteur (L/h, ou L/100km pour les engins à compteur kilométrique).
   Chaque engin a sa **référence de consommation** et sa **tolérance**
   dans `data/engins.csv`. Le script signale :
   - consommation au-dessus de la tolérance → **élevée** ;
   - consommation très au-dessus (plus de deux tolérances) →
     **anormale** : fuite ou vol possible ;
   - **pic de consommation** par rapport à la propre moyenne de
     l'engin, même sans connaître sa référence → **anormale** ;
   - consommation anormalement basse → **à vérifier** (souvent une
     erreur de saisie) ;
   - approvisionnement sans hausse du compteur → **à vérifier** ;
   - compteur en baisse, saut de compteur (> 24 h ou > 2000 km sur une
     journée), litres négatifs ou consommation physiquement
     impossible → **invalide** (exclu des totaux, jamais corrigé).
   Les lignes signalées restent **visibles mais exclues des totaux**.
3. **Tableau de bord** (`rapports/dashboard.html`) : indicateurs de la
   période (litres, consommations moyennes, signalements, coût estimé
   au prix du litre configurable), **tableau par engin** avec
   recherche et filtres (code, chantier, type de compteur, statut),
   litres par jour (parc entier ou engin au choix, les journées
   anormales en rouge), répartition des journées par statut, plus gros
   consommateurs, et la liste des **signalements à revoir**.

## Utilisation

Essai rapide (aucune configuration requise) :

```bash
python3 main.py                              # contrôle CSV + rapports + dashboard.html
python3 -m unittest discover -s tests -v     # tests
python3 generer_donnees.py                   # régénère le jeu de données de data/
```

Ouvrir ensuite `rapports/dashboard.html` dans un navigateur.

## Données d'entrée

```
data/engins.csv      code,type,chantier,compteur,conso_ref,tolerance_pct
                     compteur = h  -> référence en L/h
                                = km -> référence en L/100km
data/carburant.csv   date,engin,compteur_fin,litres
data/config.json     {"prix_litre": 11.5, "devise": "MAD"}  (coût estimé)
```

Pour suivre un vrai parc, remplacer ces fichiers par les relevés
réels au même format. Les rapports générés (`rapports/`) sont ignorés
par git : **aucune donnée de l'entreprise ne peut finir dans le dépôt
ou sur GitHub**.

## Fichiers

```
main.py               point d'entrée (contrôle + rapports + tableau de bord)
carburant.py          règles de contrôle et calculs de consommation
dashboard.py          génération du tableau de bord HTML autonome
generer_donnees.py    générateur du jeu de données
data/*.csv, config    données générées (régénérables)
tests/                tests automatiques (règles + jeu généré)
rapports/             sorties (ignoré par git)
```

## Limites assumées

- La consommation d'une journée suppose que les litres approvisionnés
  correspondent au travail de la journée ; si les approvisionnements
  sont groupés tous les plusieurs jours, la référence se règle engin
  par engin et les pics se lisent sur plusieurs journées.
- Les références de consommation sont des réglages, pas des mesures :
  elles se reprennent engin par engin à partir de l'historique.
- Le coût estimé dépend du prix du litre saisi dans `config.json`.

## Auteur

Projet personnel de **Rachid Fadili**, conçu à partir de son
expérience terrain dans le suivi d'engins de chantier.
Contact : rachidfadili2002@outlook.com
GitHub : https://github.com/rachidfadili-ai
