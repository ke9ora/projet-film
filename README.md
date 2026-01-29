# Système de Recommandation de Films avec Graphe Pondéré

Un système complet de recommandation de films basé sur un graphe pondéré, avec web scraping, calcul automatique des similarités, et visualisation 3D interactive.

## 🎬 Fonctionnalités

- **Web Scraping** : Récupération automatique des données de films via OMDb API et Cinemagoer
- **Calcul de Similarités** : Calcul automatique des poids des arêtes basé sur :
  - Acteurs communs (poids 0.4)
  - Même réalisateur (poids 0.3)
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

3. **Configurer la clé API**
   ```bash
   cp .env.example .env
   # Éditer .env et remplacer "votre_cle_api_ici" par votre clé OMDb
   ```

4. **Préparer la liste de films**
   - Éditer `listeFilms.txt` (un film par ligne)
   - Format : `Titre du film` ou `Titre du film|imdb_id`

## 📖 Utilisation

### Générer le graphe complet

```bash
python genererGrapheComplet.py
```

**Options disponibles :**
- `--force` ou `-f` : Force le re-scraping (ignore le cache)
- `--seuil 0.3` : Change le seuil de filtrage des arêtes (défaut: 0.5)
- `--enrichir` ou `-e` : Enrichit automatiquement la base avec des films similaires
- `--max-films 5` : Nombre max de films à ajouter par critère (avec --enrichir)

### Visualiser le graphe

```bash
# Lancer le serveur
python serveurFichier.py

# Ouvrir dans le navigateur
# http://localhost:8000/index.html
```

**Contrôles 3D :**
- Clic : Activer les contrôles FPS
- WASD / Flèches : Déplacer la caméra
- Souris : Regarder autour

## 📁 Structure du Projet

```
exemple_filmGraph/
├── scraperFilms.py              # Web scraping avec Cinemagoer + OMDb
├── enrichirBaseFilms.py         # Enrichissement avec films similaires
├── calculSimilarites.py         # Calcul des poids des arêtes
├── filtrageGraphe.py            # Filtrage et layout 3D
├── algorithmeRecommandation.py  # Système de recommandation
├── genererGrapheComplet.py      # Script principal
├── exempleFilm2Graph.py         # Exemple simple
├── serveurFichier.py            # Serveur HTTP
├── index.html                   # Visualisation 3D
├── billboard.vert/.frag         # Shaders WebGL
├── listeFilms.txt               # Liste des films à traiter
├── requirements.txt             # Dépendances Python
├── .env.example                 # Modèle de configuration
└── README.md                    # Ce fichier
```

## 🔒 Sécurité

- La clé API est stockée dans `.env` (ignoré par Git)
- Ne jamais commiter le fichier `.env`
- Utiliser `.env.example` comme modèle

## 📝 Exemple de Sortie

Le script génère :
- `films_data.json` : Cache des données scrappées
- `graph.json` : Graphe avec positions 3D et arêtes filtrées
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
