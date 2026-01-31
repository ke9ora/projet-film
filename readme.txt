
SYSTÈME DE RECOMMANDATION DE FILMS AVEC GRAPHE PONDÉRÉ
======================================================

Ce projet implémente un système complet de recommandation de films basé sur un graphe pondéré,
avec web scraping, calcul automatique des similarités, et visualisation 3D interactive.

MÉTHODE 1 : SYSTÈME COMPLET (RECOMMANDÉ)
----------------------------------------

1. Installation des dépendances :
   pip install -r requirements.txt

2. Configuration :
   - Obtenir une clé API OMDb : https://www.omdbapi.com/
   - Copier .env.example en .env : cp config/.env.example .env
   - Éditer .env et remplacer "votre_cle_api_ici" par votre clé API
   - Le fichier .env est ignoré par Git (sécurisé)

3. Préparer la liste de films :
   - Éditer data/listeFilms.txt (un film par ligne)
   - Exemple fourni avec Star Wars, Blade Runner, etc.

4. Générer le graphe complet :
   python -m src.graph.genererGrapheComplet
   
   Options :
   - --force ou -f : Force le re-scraping (ignore le cache)
   - --seuil 0.3 : Change le seuil de filtrage des arêtes (défaut: 0.5)
   - --enrichir ou -e : Enrichit automatiquement la base avec des films similaires
   - --max-films 5 : Nombre max de films à ajouter par critère (avec --enrichir)

   IMPORTANT : Par défaut, le système ne traite QUE les films de data/listeFilms.txt.
   Pour recommander de NOUVEAUX films, utilisez l'option --enrichir qui :
   - Cherche des films avec les mêmes réalisateurs
   - Cherche des films avec les mêmes acteurs principaux
   - Ajoute ces films à la base de données
   - Permet ensuite de recommander parmi ces nouveaux films

5. Lancer le serveur :
   python -m src.server.serveurFichier

6. Visualiser dans le navigateur :
   http://localhost:8000/web/index.html

Le script génère automatiquement :
- output/films_data.json : Cache des données scrappées
- output/graph.json : Graphe avec positions 3D et arêtes filtrées
- Recommandations affichées dans la console

MÉTHODE 2 : EXEMPLE SIMPLE (ANCIENNE MÉTHODE)
---------------------------------------------

Pour un exemple rapide avec quelques films manuels :

1. Éditer exempleFilm2Graph.py pour ajouter vos films
2. Lancer : python exempleFilm2Graph.py
3. Lancer le serveur : python -m src.server.serveurFichier
4. Ouvrir : http://localhost:8000/web/index.html

STRUCTURE DES MODULES
--------------------

- src/data/scraperFilms.py : Web scraping avec Cinemagoer + OMDb
- src/data/enrichirBaseFilms.py : Enrichit la base en cherchant des films similaires (mêmes acteurs/réalisateurs)
- src/graph/calculSimilarites.py : Calcul des poids des arêtes (acteurs, réalisateur, genres, année)
- src/graph/filtrageGraphe.py : Filtrage des arêtes et calcul du layout 3D
- src/reco/algorithmeRecommandation.py : Système de recommandation basé sur les connexions
- src/graph/genererGrapheComplet.py : Script principal qui orchestre tout

CONTRÔLES DE LA VISUALISATION 3D
--------------------------------

- Clic : Activer les contrôles FPS
- WASD / Flèches : Déplacer la caméra
- Souris : Regarder autour
