# Système de Recommandation de Films avec Graphe Pondéré

Un système complet de recommandation de films basé sur un graphe pondéré, avec web scraping, calcul automatique des similarités, et visualisation 3D interactive.

## 🎬 Fonctionnalités

- **Web Scraping** : Récupération automatique des données de films via OMDb API et Cinemagoer
- **Calcul de Similarités** : Calcul automatique des poids des arêtes basé sur :
  - Acteurs communs (poids 0.3)
  - Même réalisateur (poids 0.4)
  - Genres communs (poids 0.2)
  - Proximité d'année (poids 0.1)
- **Filtrage du Graphe** : Suppression des arêtes faibles selon un seuil configurable
- **Algorithme de Recommandation** : Identification des films les plus connectés aux films connus
- **Visualisation 3D** : Affichage interactif du graphe avec Three.js

## 🚀 Installation

### Prérequis

- Python 3.7+
- Une clé API OMDb (gratuite sur [omdbapi.com](https://www.omdbapi.com/))

### Étapes

1. **Cloner le dépôt**
   ```bash
   git clone <url-du-repo>
   cd exemple_filmGraph
   ```

2. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurer la clé API** (dans `.env`)
   - `OMDB_API_KEY` : obligatoire (posters, infos films). Ex. : `cp config/.env.example .env`

4. **Cinemagoer (IMDb)** : si réalisateur/acteurs/recommandations restent vides, IMDb a peut‑être changé ses pages. Mettre à jour : `pip install -U git+https://github.com/cinemagoer/cinemagoer.git`

5. **Préparer la liste de films**
   - Éditer `data/listeFilms.txt` (un film par ligne)
   - Format : `Titre du film` ou `Titre du film|imdb_id`

## 📖 Utilisation

### Générer le graphe et les recommandations

Pour obtenir des **recommandations** (films proches de ceux que vous aimez), il faut enrichir la base avec des films similaires. Depuis la racine du projet :

```bash
python -m src.graph.genererGrapheComplet --enrichir
```

Sans `--enrichir`, seuls les films de `data/listeFilms.txt` sont utilisés ; ils sont tous considérés comme « connus », donc aucune recommandation n’est affichée.

**Options disponibles :**
- `--force` ou `-f` : Force le re-scraping (ignore le cache)
- `--seuil 0.3` : Change le seuil de filtrage des arêtes (défaut : 0.25)
- `--enrichir` ou `-e` : Enrichit la base avec des films similaires (recommandé pour avoir des reco)
- `--max-films 5` : Nombre max de films à ajouter par critère (avec `--enrichir`)

### Démo web (recommandations)

Interface pour saisir une liste de films et afficher les recommandations :

```bash
# Lancer le serveur
python -m src.server.serveurFichier

# Ouvrir dans le navigateur
# http://localhost:8000/web/reco.html
```

Saisir un ou plusieurs films (un par ligne), cocher « Enrichir la base » si besoin, puis cliquer sur « Calculer les recommandations ».

### Visualiser le graphe 3D

```bash
# Même serveur que ci-dessus
python -m src.server.serveurFichier

# Ouvrir dans le navigateur
# http://localhost:8000/web/index.html
```

**Contrôles 3D :**
- Clic : Activer les contrôles FPS
- WASD / Flèches : Déplacer la caméra
- Souris : Regarder autour

### Tests et diagnostic (pourquoi on n’a pas de films à recommander ?)

- **Tests unitaires dédup** : `python -m unittest tests.test_dedup_titres -v`
- **Tests recommandation (position)** : `python -m unittest tests.test_reco_position -v`
- **Tests directs des bibliothèques** (Cinemagoer + OMDb, nécessite le réseau) :
  ```bash
  python -m unittest tests.test_bibliotheques -v
  ```
  Chaque test affiche ce que Cinemagoer et OMDb renvoient (search_movie, get_movie recommendations, réalisateur, acteur, OMDb strict). Ex. : si « Recommandations IMDb » = 0, c’est normal (IMDb a changé sa page) ; on s’appuie sur réalisateur, acteur et OMDb strict.
- **Diagnostic flux complet** (scraping → enrichissement → arêtes → reco) pour un film :
  ```bash
  python tests/diagnostic_flux_reco.py Inception
  python tests/diagnostic_flux_reco.py Challengers
  ```
  Affiche à chaque étape les entrées/sorties et un résumé des raisons possibles quand il n’y a pas de recommandations (0 films scrapés, 0 IDs nouveaux à l’enrichissement, 0 arêtes, etc.).

## 📁 Structure du Projet

```
exemple_filmGraph/
├── src/
│   ├── data/
│   │   ├── scraperFilms.py              # Web scraping avec Cinemagoer + OMDb
│   │   └── enrichirBaseFilms.py         # Enrichissement avec films similaires
│   ├── graph/
│   │   ├── calculSimilarites.py         # Calcul des poids des arêtes
│   │   ├── filtrageGraphe.py            # Filtrage et layout 3D
│   │   └── genererGrapheComplet.py      # Script principal
│   ├── reco/
│   │   └── algorithmeRecommandation.py  # Système de recommandation
│   ├── examples/
│   │   └── exempleFilm2Graph.py         # Exemple simple
│   └── server/
│       └── serveurFichier.py            # Serveur HTTP
├── web/
│   ├── index.html                       # Visualisation 3D du graphe
│   ├── reco.html                        # Interface recommandations (liste + reco)
│   └── shaders/
│       ├── billboard.vert               # Shader vertex
│       └── billboard.frag               # Shader fragment
├── data/
│   └── listeFilms.txt                   # Liste des films à traiter
├── tests/
│   ├── test_dedup_titres.py             # Tests dédup par titre
│   ├── test_bibliotheques.py            # Tests directs Cinemagoer + OMDb
│   └── diagnostic_flux_reco.py          # Diagnostic flux (scraping → reco)
├── output/                              # Sorties générées (graphe + posters)
├── requirements.txt                     # Dépendances Python
├── config/
│   └── .env.example                     # Modèle de configuration
└── README.md                            # Ce fichier
```

## 🔒 Sécurité

- La clé API est stockée dans `.env` (ignoré par Git)
- Ne jamais commiter le fichier `.env`
- Utiliser `config/.env.example` comme modèle

## 📝 Exemple de Sortie

Le script génère :
- `output/films_data.json` : Cache des données scrappées
- `output/graph.json` : Graphe avec positions 3D et arêtes filtrées
- Recommandations affichées dans la console

## 🛠️ Technologies

- **Python** : Scraping et traitement
- **Three.js** : Visualisation 3D
- **WebGL Shaders** : Rendu performant des billboards
- **OMDb API** : Données de films
- **Cinemagoer** : Données détaillées IMDb

## 📄 Licence

Ce projet est un exemple éducatif.

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou une pull request.
