#!/usr/bin/env python3
"""
Module de web scraping pour récupérer les données de films.
Cinemagoer (IMDb) : recherche, métadonnées (titre, acteurs, réalisateur, genres, etc.).
OMDb : uniquement pour les posters (téléchargement d’image) ; pas de recherche ni de données.
"""
import json
import os
import re
import unicodedata
from imdb import Cinemagoer
import requests
from urllib.parse import quote_plus

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
POSTERS_DIR = os.path.join(OUTPUT_DIR, "posters")

# Charger la clé API depuis .env ou utiliser une variable d'environnement
def _load_env_key(prefix):
    """Charge une clé depuis .env ou variable d'environnement (ex: OMDB_API_KEY)."""
    key_name = f"{prefix}_API_KEY"
    api_key = os.getenv(key_name)
    if api_key:
        return api_key
    env_paths = [
        os.path.join(PROJECT_ROOT, ".env"),
        os.path.join(PROJECT_ROOT, "config", ".env"),
    ]
    for env_file in env_paths:
        if os.path.exists(env_file):
            try:
                with open(env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith(f"{key_name}="):
                            return line.split("=", 1)[1].strip()
            except Exception:
                pass
    return os.getenv(key_name)


def load_api_key():
    """Clé OMDb."""
    return _load_env_key("OMDB") or os.getenv("OMDB_API_KEY", "b64880b7")

API_KEY = load_api_key()

# Mapping simple FR -> EN pour améliorer la recherche et les posters
FR_EN_TITRES = {
    "le parrain": "the godfather",
    "le parrain 2": "the godfather part ii",
    "le parrain 3": "the godfather part iii",
    "les affranchis": "goodfellas",
    "les evades": "the shawshank redemption",
    "le seigneur des anneaux": "the lord of the rings",
    "la guerre des etoiles": "star wars",
    "indiana jones et les aventuriers de l'arche perdue": "raiders of the lost ark",
}

NON_MOVIE_KEYWORDS = [
    "making of",
    "behind the scenes",
    "featurette",
    "bonus",
    "deleted scene",
    "deleted scenes",
    "trailer",
    "teaser",
    "promo",
    "special",
    "recap",
    "short",
    "episode",
    "tv",
    "clip",
    "interview",
    "documentary",
]

def _normalize_title_key(value):
    if not value:
        return ""
    text = unicodedata.normalize("NFKD", value)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text).strip()
    text = re.sub(r"\s+", " ", text)
    return text

_FR_EN_TITRES_NORM = {_normalize_title_key(k): v for k, v in FR_EN_TITRES.items()}

def map_title_fr_en(titre):
    if not titre:
        return titre
    key = _normalize_title_key(titre)
    return _FR_EN_TITRES_NORM.get(key, titre)

def _is_non_movie_title(title):
    if not title:
        return False
    norm = _normalize_title_key(title)
    for kw in NON_MOVIE_KEYWORDS:
        if kw in norm:
            return True
    return False

def _fetch_omdb_by_title(titre_film):
    if not titre_film:
        return None
    encoded = quote_plus(titre_film)
    url = f"http://www.omdbapi.com/?t={encoded}&apikey={API_KEY}"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    data = r.json()
    if data.get("Response") == "True":
        return data
    mapped = map_title_fr_en(titre_film)
    if mapped and mapped.lower() != (titre_film or "").lower():
        encoded = quote_plus(mapped)
        url = f"http://www.omdbapi.com/?t={encoded}&apikey={API_KEY}"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        if data.get("Response") == "True":
            return data
    return None

def search_omdb_by_title(keyword, max_results=10):
    """
    Recherche des films via OMDb (endpoint s=) et retourne des imdb_id.
    """
    try:
        if not keyword:
            return []
        candidates = []
        base = keyword.strip()
        mapped = map_title_fr_en(base)
        if mapped and mapped.lower() != base.lower():
            candidates.append(mapped)
        candidates.append(base)
        # variantes simples
        if base.lower().startswith("the "):
            candidates.append(base[4:])
        # nettoyer les annÃ©es / parenthÃ¨ses
        clean = re.sub(r"\(\d{4}\)$", "", base).strip()
        if clean and clean.lower() != base.lower():
            candidates.append(clean)

        results = []
        for query in candidates:
            encoded = quote_plus(query)
            page = 1
            while len(results) < max_results:
                url = f"http://www.omdbapi.com/?s={encoded}&type=movie&page={page}&apikey={API_KEY}"
                r = requests.get(url, timeout=10)
                r.raise_for_status()
                data = r.json()
                if data.get("Response") != "True":
                    break
                for item in data.get("Search", []):
                    imdb_id = item.get("imdbID", "").replace("tt", "")
                    if imdb_id:
                        results.append(imdb_id.zfill(7))
                    if len(results) >= max_results:
                        break
                page += 1
                if page > 3:
                    break
            if results:
                break
        return results
    except Exception:
        return []


def search_omdb_similar_strict(titre_film, annee, max_results=5):
    """
    Recherche OMDb par titre et ne garde que les films dont le titre correspond
    vraiment (exact ou début du titre) et l'année est proche (±3 ans).
    Évite d'ajouter "Lady Hamilton" quand on enrichit "Hamilton".
    """
    if not titre_film or annee is None:
        return []
    try:
        encoded = quote_plus(titre_film.strip())
        url = f"http://www.omdbapi.com/?s={encoded}&type=movie&page=1&apikey={API_KEY}"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        if data.get("Response") != "True":
            return []
        titre_ref = titre_film.strip().lower()
        annee_ref = int(annee)
        results = []
        for item in data.get("Search", []):
            if len(results) >= max_results:
                break
            title = (item.get("Title") or "").strip()
            year_str = (item.get("Year") or "")[:4]
            if not year_str.isdigit():
                continue
            year = int(year_str)
            # ±10 ans pour inclure remakes / rééditions (ex. Challengers 2016 vs 2024)
            if abs(year - annee_ref) > 10:
                continue
            # Titre du film doit être le début du résultat (exact ou suivi de " :", " (", etc.)
            title_lower = title.lower()
            if title_lower != titre_ref and not (
                title_lower.startswith(titre_ref)
                and (len(title_lower) == len(titre_ref) or title_lower[len(titre_ref) : len(titre_ref) + 1] in " (:-")
            ):
                continue
            imdb_id = item.get("imdbID", "").replace("tt", "")
            if imdb_id:
                results.append(imdb_id.zfill(7))
        return results
    except Exception:
        return []


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
    Télécharge le poster d'un film via l'API OMDb (seul usage d'OMDb : posters uniquement).
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
            safe_title = titre_film.strip() if titre_film else ""
            if not safe_title:
                safe_title = f"tt{imdb_id}" if imdb_id else "poster"
            filename = filenamePoster(safe_title)
            os.makedirs(POSTERS_DIR, exist_ok=True)
            poster_path = os.path.join(POSTERS_DIR, filename)
            img = requests.get(poster_url, timeout=10)
            img.raise_for_status()
            with open(poster_path, "wb") as f:
                f.write(img.content)
            print(f"✔ Poster téléchargé : {filename}")
            return os.path.join("output", "posters", filename)
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
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            data = r.json()
        else:
            data = _fetch_omdb_by_title(titre_film)
        
        if not data or data.get("Response") != "True":
            print(f"✖ Film '{titre_film}' non trouvé via OMDb")
            return None

        if data.get("Type") and data.get("Type") != "movie":
            print(f"- Ignore (type={data.get('Type')}) : {data.get('Title') or titre_film}")
            return None

        if _is_non_movie_title(data.get("Title") or titre_film):
            print(f"- Ignore (non-film) : {data.get('Title') or titre_film}")
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
                # Charger full credits d'abord (URL /fullcredits), puis main (URL /reference peut 404)
                try:
                    ia.update(movie, ['full credits'])
                except Exception:
                    pass
                try:
                    ia.update(movie, ['main'])
                except Exception:
                    pass
                titre_trouve = movie.get('title') if hasattr(movie, 'get') else getattr(movie, 'myTitle', titre_film)
                print(f"  ✓ Film trouvé par ID IMDb: {titre_trouve}")
            except Exception as e:
                print(f"  ⚠ Erreur avec l'ID IMDb {imdb_id}: {e}")
        
        # OMDb n'est utilisé que pour les posters ; on ne résout pas l'ID via OMDb.

        # Sinon, chercher par titre
        if not movie:
            # Normaliser le titre pour la recherche
            titre_recherche = map_title_fr_en(titre_film).lower().strip()
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
        def get_movie_value(keys, default=None):
            for key in keys:
                try:
                    value = movie.get(key) if hasattr(movie, 'get') else getattr(movie, key, None)
                except Exception:
                    value = None
                if value:
                    return value
            return default

        titre = get_movie_value(
            ['title', 'localized title', 'long imdb title', 'original title', 'canonical title'],
            default=titre_film
        )
        if not titre:
            titre = titre_film

        kind = get_movie_value(['kind'], default=None)
        if kind and kind != "movie":
            print(f"- Ignore (type={kind}) : {titre}")
            return None

        if _is_non_movie_title(titre):
            print(f"- Ignore (non-film) : {titre}")
            return None
        
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
        
        # Réalisateur (Cinemagoer utilise parfois 'director' ou 'directors', et le parsing peut échouer)
        realisateur = None
        try:
            directors = (
                movie.get('directors') if hasattr(movie, 'get') else getattr(movie, 'directors', [])
            ) or (
                movie.get('director') if hasattr(movie, 'get') else getattr(movie, 'director', [])
            )
            if directors:
                director = directors[0] if directors else None
                if director is not None:
                    if hasattr(director, 'name') and director.name:
                        realisateur = director.name
                    elif hasattr(director, 'myName') and director.myName:
                        realisateur = director.myName
                    elif hasattr(director, 'get') and director.get('name'):
                        realisateur = director['name']
                    else:
                        realisateur = str(director) if director else None
        except Exception as e:
            print(f"  ⚠ Erreur lors de l'extraction du réalisateur: {e}")
        
        # Télécharger le poster
        poster = telecharger_poster_omdb(titre, imdb_id)
        if not poster:
            poster = telecharger_poster_omdb(titre)  # Essayer sans ID
        if not poster:
            mapped = map_title_fr_en(titre_film)
            if mapped and mapped.lower() != (titre_film or "").lower():
                poster = telecharger_poster_omdb(mapped)
        
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

        # OMDb uniquement pour le poster : compléter le poster si manquant (pas les autres champs)
        if not film_data.get("poster"):
            poster = telecharger_poster_omdb(titre, imdb_id)
            if not poster:
                poster = telecharger_poster_omdb(titre_film)
            if not poster and map_title_fr_en(titre_film).lower() != (titre_film or "").lower():
                poster = telecharger_poster_omdb(map_title_fr_en(titre_film))
            if poster:
                film_data["poster"] = poster

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
    if not os.path.isabs(fichier):
        fichier = os.path.join(PROJECT_ROOT, "data", fichier)
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
    if not os.path.isabs(cache_file):
        cache_file = os.path.join(OUTPUT_DIR, cache_file)
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
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
        
        # Cinemagoer uniquement pour les données ; OMDb uniquement pour les posters (dans scraper_film)
        film_data = scraper_film(titre, ia, imdb_id=imdb_id)
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
    if not os.path.isabs(fichier):
        fichier = os.path.join(OUTPUT_DIR, fichier)
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
