#!/usr/bin/env python3
"""
Module pour enrichir la base de films en cherchant des films similaires
Utilise Cinemagoer pour trouver des films avec les mêmes acteurs, réalisateurs, etc.
"""
import json
import os
from imdb import Cinemagoer
import scraperFilms


def trouver_films_par_acteur(ia, nom_acteur, limite=5):
    """
    Trouve des films avec un acteur donné
    Retourne une liste d'IDs IMDb
    """
    try:
        personnes = ia.search_person(nom_acteur)
        if not personnes:
            return []
        
        personne = ia.get_person(personnes[0].personID)
        films = personne.get('filmography', {}).get('actor', [])
        if not films:
            films = personne.get('filmography', {}).get('actress', [])
        
        # Filtrer pour ne garder que les films (pas les séries)
        film_ids = []
        for film in films[:limite * 2]:  # Prendre plus pour filtrer
            if hasattr(film, 'get') or isinstance(film, dict):
                movie_id = film.get('movieID') if isinstance(film, dict) else getattr(film, 'movieID', None)
                if movie_id:
                    try:
                        movie = ia.get_movie(movie_id)
                        if movie.get('kind') == 'movie':  # Uniquement les films
                            film_ids.append(str(movie_id).zfill(7))
                            if len(film_ids) >= limite:
                                break
                    except:
                        continue
        
        return film_ids
    except Exception as e:
        print(f"  ⚠ Erreur pour l'acteur '{nom_acteur}': {e}")
        return []


def trouver_films_par_realisateur(ia, nom_realisateur, limite=5):
    """
    Trouve des films d'un réalisateur donné
    Retourne une liste d'IDs IMDb
    """
    try:
        personnes = ia.search_person(nom_realisateur)
        if not personnes:
            return []
        
        personne = ia.get_person(personnes[0].personID)
        films = personne.get('filmography', {}).get('director', [])
        
        film_ids = []
        for film in films[:limite]:
            if hasattr(film, 'get') or isinstance(film, dict):
                movie_id = film.get('movieID') if isinstance(film, dict) else getattr(film, 'movieID', None)
                if movie_id:
                    try:
                        movie = ia.get_movie(movie_id)
                        if movie.get('kind') == 'movie':
                            film_ids.append(str(movie_id).zfill(7))
                    except:
                        continue
        
        return film_ids
    except Exception as e:
        print(f"  ⚠ Erreur pour le réalisateur '{nom_realisateur}': {e}")
        return []


def trouver_films_par_genre(ia, genre, limite=10):
    """
    Trouve des films d'un genre donné (moins précis, utilise la recherche)
    Retourne une liste d'IDs IMDb
    """
    try:
        # Recherche simple par genre (limitation de l'API)
        # On pourrait utiliser une base de données de films par genre
        # Pour l'instant, on retourne une liste vide
        # (Cinemagoer ne permet pas facilement de chercher par genre)
        return []
    except Exception as e:
        print(f"  ⚠ Erreur pour le genre '{genre}': {e}")
        return []


def enrichir_base_films(films_data, max_films_par_critere=3, cache_file="films_data.json"):
    """
    Enrichit la base de films en cherchant des films similaires
    
    Args:
        films_data: Liste des films existants
        max_films_par_critere: Nombre max de films à ajouter par critère (acteur, réalisateur)
        cache_file: Fichier de cache
    
    Returns:
        Liste enrichie de films
    """
    print("="*60)
    print("ENRICHISSEMENT DE LA BASE DE FILMS")
    print("="*60)
    print()
    
    # Récupérer les IDs IMDb déjà présents
    imdb_ids_existants = {f.get("imdb_id") for f in films_data if f.get("imdb_id")}
    
    ia = Cinemagoer()
    nouveaux_ids = set()
    
    # Pour chaque film, chercher des films similaires
    for film in films_data:
        print(f"Recherche de films similaires à '{film.get('titre', 'Inconnu')}'...")
        
        # Par réalisateur
        realisateur = film.get("realisateur")
        if realisateur:
            ids = trouver_films_par_realisateur(ia, realisateur, limite=max_films_par_critere)
            for movie_id in ids:
                if movie_id not in imdb_ids_existants:
                    nouveaux_ids.add(movie_id)
            if ids:
                print(f"  ✔ {len([id for id in ids if id not in imdb_ids_existants])} nouveaux films trouvés (réalisateur)")
        
        # Par acteurs principaux (limiter à 2 acteurs pour éviter trop de résultats)
        acteurs = film.get("acteurs", [])[:2]
        for acteur in acteurs:
            ids = trouver_films_par_acteur(ia, acteur, limite=max_films_par_critere)
            for movie_id in ids:
                if movie_id not in imdb_ids_existants:
                    nouveaux_ids.add(movie_id)
            if ids:
                print(f"  ✔ {len([id for id in ids if id not in imdb_ids_existants])} nouveaux films trouvés (acteur: {acteur})")
    
    print(f"\n✔ {len(nouveaux_ids)} nouveaux films identifiés à scraper")
    
    # Scraper les nouveaux films
    nouveaux_films = []
    for movie_id in nouveaux_ids:
        print(f"\nScraping du film IMDb ID: {movie_id}...")
        try:
            movie = ia.get_movie(int(movie_id))
            titre = movie.get('title', f'Film {movie_id}')
            
            # Utiliser la fonction de scraping existante mais adaptée
            film_data = scraper_film_par_id(ia, movie_id, movie)
            if film_data:
                nouveaux_films.append(film_data)
                films_data.append(film_data)
        except Exception as e:
            print(f"  ✖ Erreur lors du scraping de {movie_id}: {e}")
    
    # Sauvegarder dans le cache
    if nouveaux_films:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump({"films": films_data}, f, indent=2, ensure_ascii=False)
        print(f"\n✔ {len(nouveaux_films)} nouveaux films ajoutés à la base")
    
    return films_data


def scraper_film_par_id(ia, movie_id, movie=None):
    """
    Scrape un film directement par son ID IMDb
    Version simplifiée de scraper_film pour les films déjà récupérés
    """
    try:
        if movie is None:
            movie = ia.get_movie(int(movie_id))
        
        titre = movie.get('title', f'Film {movie_id}')
        imdb_id = str(movie_id).zfill(7)
        
        genres = movie.get('genres', [])
        annee = movie.get('year')
        note = movie.get('rating')
        
        cast = movie.get('cast', [])
        acteurs = [actor['name'] for actor in cast[:5]] if cast else []
        
        directors = movie.get('directors', [])
        realisateur = directors[0]['name'] if directors else None
        
        # Télécharger le poster
        poster = scraperFilms.telecharger_poster_omdb(titre, imdb_id)
        if not poster:
            poster = scraperFilms.telecharger_poster_omdb(titre)
        
        film_data = {
            "titre": titre,
            "titre_original": titre,  # Pas de titre de recherche original ici
            "imdb_id": imdb_id,
            "genres": genres,
            "annee": annee,
            "acteurs": acteurs,
            "realisateur": realisateur,
            "note": note,
            "poster": poster
        }
        
        print(f"  ✔ Film scrappé : {titre} ({annee})")
        return film_data
        
    except Exception as e:
        print(f"  ✖ Erreur lors du scraping: {e}")
        return None


if __name__ == "__main__":
    # Test du module
    films = scraperFilms.charger_films_data() if hasattr(scraperFilms, 'charger_films_data') else []
    if not films:
        # Charger depuis le fichier JSON
        try:
            with open("films_data.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                films = data.get("films", [])
        except:
            print("✖ Aucune donnée de film disponible. Lancez d'abord scraperFilms.py")
            exit(1)
    
    films_enrichis = enrichir_base_films(films, max_films_par_critere=3)
    print(f"\nTotal de films dans la base: {len(films_enrichis)}")
