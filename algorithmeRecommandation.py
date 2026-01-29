#!/usr/bin/env python3
"""
Module d'algorithme de recommandation de films
Identifie les films les plus connectés aux films connus
"""
import json
from collections import defaultdict


def charger_films_connus(fichier="listeFilms.txt"):
    """
    Charge la liste des films connus depuis listeFilms.txt
    Retourne un set des titres (en majuscules pour comparaison)
    """
    try:
        with open(fichier, "r", encoding="utf-8") as f:
            films = {ligne.strip().upper() for ligne in f if ligne.strip()}
        return films
    except FileNotFoundError:
        print(f"✖ Fichier '{fichier}' non trouvé")
        return set()


def identifier_films_connus(films_data, titres_connus):
    """
    Identifie quels films de films_data sont dans la liste des films connus
    Retourne un set d'indices des films connus
    """
    indices_connus = set()
    
    for i, film in enumerate(films_data):
        titre = film.get("titre", "").upper()
        titre_original = film.get("titre_original", "").upper()
        
        # Correspondance exacte
        if titre in titres_connus or titre_original in titres_connus:
            indices_connus.add(i)
            continue
        
        # Correspondance flexible : vérifier si un titre connu contient des mots-clés du film
        for titre_connu in titres_connus:
            # Extraire les mots-clés importants (ignorer les mots courts)
            mots_film = {m for m in titre.split() if len(m) > 2}
            mots_connus = {m for m in titre_connu.split() if len(m) > 2}
            # Si au moins 2 mots en commun, considérer comme match
            if len(mots_film.intersection(mots_connus)) >= 2:
                indices_connus.add(i)
                break
    
    return indices_connus


def calculer_scores_recommandation(films_data, aretes, indices_connus):
    """
    Calcule un score de recommandation pour chaque film non-connu
    Le score est basé sur la somme des poids des arêtes vers les films connus
    """
    scores = defaultdict(float)
    nombre_connexions = defaultdict(int)
    
    # Pour chaque arête
    for arete in aretes:
        from_idx = arete["from"]
        to_idx = arete["to"]
        poids = arete.get("weight", 0)
        
        # Si un des deux films est connu et l'autre non
        if from_idx in indices_connus and to_idx not in indices_connus:
            scores[to_idx] += poids
            nombre_connexions[to_idx] += 1
        elif to_idx in indices_connus and from_idx not in indices_connus:
            scores[from_idx] += poids
            nombre_connexions[from_idx] += 1
    
    # Normaliser les scores par le nombre de films connus
    nb_films_connus = len(indices_connus)
    if nb_films_connus == 0:
        return {}
    
    scores_normalises = {}
    for idx, score in scores.items():
        # Score moyen par connexion, puis normalisé
        score_moyen = score / max(1, nombre_connexions[idx])
        scores_normalises[idx] = {
            "score": score_moyen,
            "score_total": score,
            "nb_connexions": nombre_connexions[idx]
        }
    
    return scores_normalises


def penaliser_films_populaires(scores, aretes, facteur_penalite=0.1):
    """
    Pénalise les films trop "populaires" (avec beaucoup de connexions)
    Évite de recommander uniquement les films les plus connus
    """
    # Compter le nombre de connexions par film
    degres = defaultdict(int)
    for arete in aretes:
        degres[arete["from"]] += 1
        degres[arete["to"]] += 1
    
    # Calculer le degré moyen
    if not degres:
        return scores
    
    degre_moyen = sum(degres.values()) / len(degres)
    
    # Appliquer la pénalité
    scores_penalises = {}
    for idx, data in scores.items():
        degre = degres.get(idx, 0)
        if degre > degre_moyen:
            # Pénalité proportionnelle à l'excès de connexions
            penalite = (degre - degre_moyen) / degre_moyen * facteur_penalite
            nouveau_score = data["score"] * (1 - penalite)
        else:
            nouveau_score = data["score"]
        
        scores_penalises[idx] = {
            "score": nouveau_score,
            "score_total": data["score_total"],
            "nb_connexions": data["nb_connexions"],
            "degre": degre
        }
    
    return scores_penalises


def recommander(films_data, aretes, titres_connus=None, top_n=10, penaliser_populaires=True):
    """
    Fonction principale de recommandation
    
    Args:
        films_data: Liste des données de tous les films
        aretes: Liste des arêtes du graphe
        titres_connus: Set des titres de films connus (ou None pour charger depuis listeFilms.txt)
        top_n: Nombre de recommandations à retourner
        penaliser_populaires: Si True, pénalise les films trop populaires
    
    Returns:
        Liste de tuples (index_film, score, film_data)
    """
    # Charger les films connus si non fourni
    if titres_connus is None:
        titres_connus = charger_films_connus()
    
    if not titres_connus:
        print("✖ Aucun film connu identifié")
        return []
    
    # Identifier les indices des films connus
    indices_connus = identifier_films_connus(films_data, titres_connus)
    
    if not indices_connus:
        print("✖ Aucun film connu trouvé dans les données")
        return []
    
    print(f"✔ {len(indices_connus)} films connus identifiés")
    
    # Calculer les scores
    scores = calculer_scores_recommandation(films_data, aretes, indices_connus)
    
    if not scores:
        print("✖ Aucune recommandation possible (pas de connexions)")
        return []
    
    # Appliquer la pénalité si demandé
    if penaliser_populaires:
        scores = penaliser_films_populaires(scores, aretes)
    
    # Trier par score décroissant
    recommandations = []
    for idx, data in scores.items():
        if idx not in indices_connus:  # Ne pas recommander les films déjà connus
            recommandations.append((idx, data["score"], films_data[idx]))
    
    recommandations.sort(key=lambda x: x[1], reverse=True)
    
    return recommandations[:top_n]


def afficher_recommandations(recommandations):
    """
    Affiche les recommandations de manière lisible
    """
    if not recommandations:
        print("Aucune recommandation disponible")
        return
    
    print("\n" + "="*60)
    print("RECOMMANDATIONS DE FILMS")
    print("="*60)
    
    for i, (idx, score, film) in enumerate(recommandations, 1):
        titre = film.get("titre", "Inconnu")
        annee = film.get("annee", "?")
        note = film.get("note", "?")
        genres = ", ".join(film.get("genres", [])[:3])
        
        print(f"\n{i}. {titre} ({annee})")
        print(f"   Score: {score:.4f}")
        print(f"   Note IMDb: {note}")
        print(f"   Genres: {genres}")
        if film.get("realisateur"):
            print(f"   Réalisateur: {film['realisateur']}")


if __name__ == "__main__":
    # Test du module
    try:
        import calculSimilarites
        
        films = calculSimilarites.charger_films_data()
        if films:
            aretes = calculSimilarites.calculer_toutes_aretes(films)
            recommandations = recommander(films, aretes, top_n=5)
            afficher_recommandations(recommandations)
        else:
            print("✖ Aucune donnée de film disponible")
    except ImportError:
        print("✖ Module calculSimilarites non trouvé")
