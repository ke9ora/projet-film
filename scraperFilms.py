#!/usr/bin/env python3
"""
Module de web scraping pour récupérer les données de films
Utilise Cinemagoer pour les données détaillées et OMDb pour les posters
"""
import json
import os
from imdb import Cinemagoer
import requests
from urllib.parse import quote_plus

# Charger la clé API depuis .env ou utiliser une variable d'environnement
def load_api_key():
    """Charge la clé API depuis .env ou variable d'environnement"""
    # D'abord essayer la variable d'environnement
    api_key = os.getenv('OMDB_API_KEY')
    if api_key:
        return api_key
    
    # Sinon, essayer de charger depuis .env
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_file):
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('OMDB_API_KEY='):
                        return line.split('=', 1)[1].strip()
        except Exception:
            pass
    
    # Fallback (ne devrait pas arriver en production)
    return os.getenv('OMDB_API_KEY', 'b64880b7')

API_KEY = load_api_key()

def filenamePoster(titre):
    """Convertit un titre de film en nom de fichier valide"""
    filename = titre.replace(" ", "_")
    filename = filename.replace("'", "_")
    filename = filename.replace(":", "_")
    filename = filename.replace("/", "_")
    filename = filename.replace("\\", "_")
    filename = filename.replace("?", "_")
    filename = filename.replace("*", "_")
    filename = filename.replace('"', "_")
    filename = filename.replace("<", "_")
    filename = filename.replace(">", "_")
    filename = filename.replace("|", "_")
    return filename + ".jpg"


def telecharger_poster_omdb(titre_film, imdb_id=None):
    """
    Télécharge le poster d'un film via l'API OMDb
    Retourne le nom du fichier ou None
    """
    try:
        if imdb_id:
            url = f"http://www.omdbapi.com/?i=tt{imdb_id}&apikey={API_KEY}"
        else:
            encoded = quote_plus(titre_film)
            url = f"http://www.omdbapi.com/?t={encoded}&apikey={API_KEY}"
        
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        
        if data.get("Response") != "True":
            return None
        
        poster_url = data.get("Poster")
        if poster_url and poster_url != "N/A":
            filename = filenamePoster(titre_film)
            img = requests.get(poster_url, timeout=10)
            img.raise_for_status()
            with open(filename, 'wb') as f:
                f.write(img.content)
            print(f"✔ Poster téléchargé : {filename}")
            return filename
    except Exception as e:
        print(f"✖ Erreur lors du téléchargement du poster pour '{titre_film}': {e}")
    return None


def scraper_film_omdb(titre_film, imdb_id=None):
    """
    Scrape les données d'un film avec OMDb API (plus fiable que Cinemagoer)
    """
    try:
        if imdb_id:
            url = f"http://www.omdbapi.com/?i=tt{imdb_id}&apikey={API_KEY}"
        else:
            encoded = quote_plus(titre_film)
            url = f"http://www.omdbapi.com/?t={encoded}&apikey={API_KEY}"
        
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        
        if data.get("Response") != "True":
            print(f"✖ Film '{titre_film}' non trouvé via OMDb")
            return None
        
        titre = data.get("Title", titre_film)
        imdb_id_omdb = data.get("imdbID", "").replace("tt", "")
        annee = int(data.get("Year", 0)) if data.get("Year", "").isdigit() else None
        note = float(data.get("imdbRating", 0)) if data.get("imdbRating") and data.get("imdbRating") != "N/A" else None
        genres = [g.strip() for g in data.get("Genre", "").split(",")] if data.get("Genre") else []
        realisateur = data.get("Director", None) if data.get("Director") != "N/A" else None
        acteurs_str = data.get("Actors", "")
        acteurs = [a.strip() for a in acteurs_str.split(",")[:5]] if acteurs_str and acteurs_str != "N/A" else []
        
        # Télécharger le poster
        poster = telecharger_poster_omdb(titre, imdb_id_omdb)
        if not poster:
            poster = telecharger_poster_omdb(titre)
        
        film_data = {
            "titre": titre,
            "titre_original": titre_film,
            "imdb_id": imdb_id_omdb.zfill(7) if imdb_id_omdb else None,
            "genres": genres,
            "annee": annee,
            "acteurs": acteurs,
            "realisateur": realisateur,
            "note": note,
            "poster": poster
        }
        
        print(f"✔ Film scrappé : {titre} ({annee})")
        return film_data
        
    except Exception as e:
        print(f"✖ Erreur lors du scraping de '{titre_film}' via OMDb: {e}")
        return None


def scraper_film(titre_film, ia, imdb_id=None):
    """
    Scrape les données d'un film avec Cinemagoer
    Retourne un dictionnaire avec les données du film
    
    Args:
        titre_film: Titre du film à chercher
        ia: Instance de Cinemagoer
        imdb_id: ID IMDb optionnel (si fourni, utilise directement cet ID)
    """
    try:
        movie = None
        movie_id = None
        
        # Si un ID IMDb est fourni, l'utiliser directement
        if imdb_id:
            try:
                movie_id = int(imdb_id.replace('tt', ''))
                movie = ia.get_movie(movie_id)
                # Charger les données complètes
                ia.update(movie, ['main', 'cast', 'directors'])
                titre_trouve = movie.get('title') if hasattr(movie, 'get') else getattr(movie, 'myTitle', titre_film)
                print(f"  ✓ Film trouvé par ID IMDb: {titre_trouve}")
            except Exception as e:
                print(f"  ⚠ Erreur avec l'ID IMDb {imdb_id}: {e}")
        
        # Sinon, chercher par titre
        if not movie:
            # Normaliser le titre pour la recherche
            titre_recherche = titre_film.lower().strip()
            titre_recherche = titre_recherche.replace("episode iii", "revenge of the sith")
            titre_recherche = titre_recherche.replace("episode ii", "attack of the clones")
            titre_recherche = titre_recherche.replace("episode i", "phantom menace")
            titre_recherche = titre_recherche.replace("i robot", "i, robot")
            titre_recherche = titre_recherche.replace("arche perdue", "raiders of the lost ark")
            
            # Recherche du film
            search_results = ia.search_movie(titre_recherche)
            if not search_results:
                # Essayer avec le titre original
                search_results = ia.search_movie(titre_film)
            
            if not search_results:
                print(f"✖ Film '{titre_film}' non trouvé")
                return None
            
            # Chercher le meilleur résultat (film, pas série)
            for result in search_results[:5]:  # Examiner les 5 premiers résultats
                try:
                    temp_movie = ia.get_movie(result.movieID)
                    if temp_movie.get('kind') == 'movie':
                        movie = temp_movie
                        movie_id = temp_movie.movieID
                        break
                except Exception as e:
                    continue
            
            if not movie:
                # Si aucun film trouvé, prendre le premier résultat
                try:
                    movie = ia.get_movie(search_results[0].movieID)
                    movie_id = search_results[0].movieID
                except Exception as e:
                    print(f"✖ Erreur lors de la récupération du film: {e}")
                    return None
        
        if not movie_id:
            movie_id = movie.movieID
        
        # Extraire les données (movie est déjà chargé)
        # Cinemagoer utilise des attributs directs
        titre = movie.get('title') if hasattr(movie, 'get') else (getattr(movie, 'myTitle', None) or getattr(movie, 'title', titre_film))
        if not titre or titre == titre_film:
            # Essayer avec myTitle
            titre = getattr(movie, 'myTitle', titre_film)
        
        imdb_id = str(movie_id).zfill(7)  # Format: 0133093
        
        genres = movie.get('genres') if hasattr(movie, 'get') else getattr(movie, 'genres', [])
        annee = movie.get('year') if hasattr(movie, 'get') else getattr(movie, 'year', None)
        note = movie.get('rating') if hasattr(movie, 'get') else getattr(movie, 'rating', None)
        
        # Acteurs (limiter à 5 principaux)
        acteurs = []
        try:
            cast = movie.get('cast') if hasattr(movie, 'get') else getattr(movie, 'cast', [])
            if cast:
                # cast peut être une liste de Person objects
                for actor in cast[:5]:
                    if hasattr(actor, 'name'):
                        acteurs.append(actor.name)
                    elif hasattr(actor, 'myName'):
                        acteurs.append(actor.myName)
                    else:
                        acteurs.append(str(actor))
        except Exception as e:
            print(f"  ⚠ Erreur lors de l'extraction des acteurs: {e}")
        
        # Réalisateur
        realisateur = None
        try:
            directors = movie.get('directors') if hasattr(movie, 'get') else getattr(movie, 'directors', [])
            if directors:
                director = directors[0]
                if hasattr(director, 'name'):
                    realisateur = director.name
                elif hasattr(director, 'myName'):
                    realisateur = director.myName
                else:
                    realisateur = str(director)
        except Exception as e:
            print(f"  ⚠ Erreur lors de l'extraction du réalisateur: {e}")
        
        # Télécharger le poster
        poster = telecharger_poster_omdb(titre, imdb_id)
        if not poster:
            poster = telecharger_poster_omdb(titre)  # Essayer sans ID
        
        film_data = {
            "titre": titre,
            "titre_original": titre_film,  # Garder le titre de recherche
            "imdb_id": imdb_id,
            "genres": genres,
            "annee": annee,
            "acteurs": acteurs,
            "realisateur": realisateur,
            "note": note,
            "poster": poster
        }
        
        print(f"✔ Film scrappé : {titre} ({annee})")
        return film_data
        
    except Exception as e:
        import traceback
        print(f"✖ Erreur lors du scraping de '{titre_film}': {e}")
        print(f"  Détails: {traceback.format_exc()}")
        return None


def lire_liste_films(fichier="listeFilms.txt"):
    """
    Lit la liste des films depuis un fichier texte
    Format: "Titre du film" ou "Titre du film|imdb_id"
    Un film par ligne
    """
    if not os.path.exists(fichier):
        print(f"✖ Fichier '{fichier}' non trouvé")
        return []
    
    films = []
    with open(fichier, "r", encoding="utf-8") as f:
        for ligne in f:
            ligne = ligne.strip()
            if not ligne:
                continue
            # Support du format "Titre|imdb_id"
            if '|' in ligne:
                titre, imdb_id = ligne.split('|', 1)
                films.append((titre.strip(), imdb_id.strip()))
            else:
                films.append((ligne, None))
    return films


def scraper_tous_films(liste_films=None, cache_file="films_data.json", force_reload=False):
    """
    Scrape tous les films de la liste
    Utilise un cache pour éviter de re-scraper
    """
    # Charger depuis le cache si disponible
    films_data = []
    if os.path.exists(cache_file) and not force_reload:
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                films_data = data.get("films", [])
                print(f"✔ {len(films_data)} films chargés depuis le cache")
        except Exception as e:
            print(f"✖ Erreur lors du chargement du cache: {e}")
    
    # Si pas de liste fournie, lire depuis le fichier
    if liste_films is None:
        liste_films = lire_liste_films()
    
    if not liste_films:
        print("✖ Aucun film à scraper")
        return films_data
    
    # Initialiser Cinemagoer
    ia = Cinemagoer()
    
    # Scraper les nouveaux films
    titres_scrapes = {f.get("titre_original", "").upper() for f in films_data}
    nouveaux_films = []
    
    for item in liste_films:
        # item peut être un tuple (titre, imdb_id) ou juste un titre
        if isinstance(item, tuple):
            titre, imdb_id = item
        else:
            titre = item
            imdb_id = None
        
        titre_upper = titre.upper()
        # Vérifier si le film est déjà dans le cache
        if titre_upper in titres_scrapes:
            print(f"⊘ Film '{titre}' déjà dans le cache, ignoré")
            continue
        
        # Utiliser OMDb en priorité (plus fiable)
        film_data = scraper_film_omdb(titre, imdb_id=imdb_id)
        # Si OMDb échoue, essayer Cinemagoer (pour l'instant désactivé car peu fiable)
        # if not film_data:
        #     film_data = scraper_film(titre, ia, imdb_id=imdb_id)
        if film_data:
            nouveaux_films.append(film_data)
            films_data.append(film_data)
    
    # Sauvegarder dans le cache
    if nouveaux_films:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump({"films": films_data}, f, indent=2, ensure_ascii=False)
        print(f"✔ {len(nouveaux_films)} nouveaux films ajoutés au cache")
    
    return films_data


def charger_films_data(fichier="films_data.json"):
    """
    Charge les données des films depuis le fichier de cache
    """
    if not os.path.exists(fichier):
        return []
    
    try:
        with open(fichier, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("films", [])
    except Exception as e:
        print(f"✖ Erreur lors du chargement: {e}")
        return []


if __name__ == "__main__":
    # Test du module
    films = scraper_tous_films()
    print(f"\nTotal de films scrappés : {len(films)}")
