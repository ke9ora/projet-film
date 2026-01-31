#!/usr/bin/env python3
"""
Module de calcul des similarités entre films
Calcule les poids des arêtes du graphe basé sur les similarités
"""
import json
import math
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")


def calculer_similarite_acteurs(film1, film2):
    """
    Calcule la similarité basée sur les acteurs communs
    Retourne un score entre 0 et 1
    """
    acteurs1 = set(film1.get("acteurs", []))
    acteurs2 = set(film2.get("acteurs", []))
    
    if not acteurs1 or not acteurs2:
        return 0.0
    
    acteurs_communs = acteurs1.intersection(acteurs2)
    total_acteurs = len(acteurs1.union(acteurs2))
    
    if total_acteurs == 0:
        return 0.0
    
    # Plus il y a d'acteurs communs, plus le score est élevé
    # Normalisé par le nombre total d'acteurs uniques
    score = len(acteurs_communs) / total_acteurs
    
    # Bonus si plusieurs acteurs communs
    if len(acteurs_communs) > 1:
        score = min(1.0, score * (1 + 0.2 * len(acteurs_communs)))
    
    return score


def calculer_similarite_realisateur(film1, film2):
    """
    Calcule la similarité basée sur le réalisateur
    Retourne 1.0 si même réalisateur, 0.0 sinon
    """
    real1 = film1.get("realisateur")
    real2 = film2.get("realisateur")
    
    if not real1 or not real2:
        return 0.0
    
    return 1.0 if real1.lower() == real2.lower() else 0.0


def calculer_similarite_genres(film1, film2):
    """
    Calcule la similarité basée sur les genres communs
    Retourne un score entre 0 et 1
    """
    genres1 = set(film1.get("genres", []))
    genres2 = set(film2.get("genres", []))
    
    if not genres1 or not genres2:
        return 0.0
    
    genres_communs = genres1.intersection(genres2)
    total_genres = len(genres1.union(genres2))
    
    if total_genres == 0:
        return 0.0
    
    # Score basé sur le ratio de genres communs
    score = len(genres_communs) / total_genres
    
    # Bonus si plusieurs genres communs
    if len(genres_communs) > 1:
        score = min(1.0, score * (1 + 0.15 * len(genres_communs)))
    
    return score


def calculer_similarite_annee(film1, film2):
    """
    Calcule la similarité basée sur la proximité des années
    Retourne un score entre 0 et 1 (décroît avec l'écart d'années)
    """
    annee1 = film1.get("annee")
    annee2 = film2.get("annee")
    
    if not annee1 or not annee2:
        return 0.0
    
    ecart = abs(annee1 - annee2)
    
    # Score décroît exponentiellement avec l'écart
    # Films de la même année = 1.0
    # Écart de 10 ans ≈ 0.5
    # Écart de 20 ans ≈ 0.25
    if ecart == 0:
        return 1.0
    
    score = math.exp(-ecart / 10.0)
    return score


def calculer_poids(film1, film2):
    """
    Calcule le poids total d'une arête entre deux films
    Combine plusieurs critères de similarité avec des poids
    
    Retourne un score entre 0 et 1
    """
    # Poids des différents critères
    POIDS_ACTEURS = 0.3
    POIDS_REALISATEUR = 0.4
    POIDS_GENRES = 0.2
    POIDS_ANNEE = 0.1
    
    sim_acteurs = calculer_similarite_acteurs(film1, film2)
    sim_realisateur = calculer_similarite_realisateur(film1, film2)
    sim_genres = calculer_similarite_genres(film1, film2)
    sim_annee = calculer_similarite_annee(film1, film2)
    
    # Calcul du score pondéré
    poids_total = (
        sim_acteurs * POIDS_ACTEURS +
        sim_realisateur * POIDS_REALISATEUR +
        sim_genres * POIDS_GENRES +
        sim_annee * POIDS_ANNEE
    )
    
    # Normaliser entre 0 et 1 (déjà normalisé mais on s'assure)
    poids_total = max(0.0, min(1.0, poids_total))
    
    return poids_total


def calculer_toutes_aretes(films_data):
    """
    Calcule toutes les arêtes possibles entre les films
    Retourne une liste de dictionnaires {from, to, weight}
    """
    aretes = []
    n = len(films_data)
    
    for i in range(n):
        for j in range(i + 1, n):
            poids = calculer_poids(films_data[i], films_data[j])
            aretes.append({
                "from": i,
                "to": j,
                "weight": round(poids, 4)  # Arrondir à 4 décimales
            })
    
    return aretes


def charger_films_data(fichier="films_data.json"):
    """
    Charge les données des films depuis un fichier JSON
    """
    if not os.path.isabs(fichier):
        fichier = os.path.join(OUTPUT_DIR, fichier)
    try:
        with open(fichier, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("films", [])
    except FileNotFoundError:
        print(f"✖ Fichier '{fichier}' non trouvé")
        return []
    except Exception as e:
        print(f"✖ Erreur lors du chargement: {e}")
        return []


if __name__ == "__main__":
    # Test du module
    films = charger_films_data()
    if films:
        print(f"Calcul des similarités pour {len(films)} films...")
        aretes = calculer_toutes_aretes(films)
        print(f"✔ {len(aretes)} arêtes calculées")
        
        # Afficher quelques exemples
        print("\nExemples d'arêtes (top 5 par poids):")
        aretes_triees = sorted(aretes, key=lambda x: x["weight"], reverse=True)
        for arete in aretes_triees[:5]:
            film1 = films[arete["from"]]
            film2 = films[arete["to"]]
            print(f"  {film1['titre']} <-> {film2['titre']}: {arete['weight']:.4f}")
