#!/usr/bin/env python3
"""
Script principal pour générer le graphe complet de films
Orchestre tous les modules : scraping, calcul de similarités, filtrage, recommandations
"""
import os
import sys
import scraperFilms
import calculSimilarites
import filtrageGraphe
import algorithmeRecommandation
import enrichirBaseFilms


def main():
    """
    Fonction principale qui orchestre tout le processus
    """
    print("="*60)
    print("GÉNÉRATION DU GRAPHE DE FILMS")
    print("="*60)
    print()
    
    # 1. Lire la liste des films
    print("Étape 1: Lecture de la liste des films...")
    liste_films = scraperFilms.lire_liste_films()
    if not liste_films:
        print("✖ Aucun film dans listeFilms.txt")
        return
    
    print(f"✔ {len(liste_films)} films à traiter")
    print()
    
    # 2. Scraper les données (ou charger depuis cache)
    print("Étape 2: Scraping des données de films...")
    force_reload = "--force" in sys.argv or "-f" in sys.argv
    films_data = scraperFilms.scraper_tous_films(
        liste_films=liste_films,
        force_reload=force_reload
    )
    
    if not films_data:
        print("✖ Aucune donnée de film disponible")
        return
    
    print(f"✔ {len(films_data)} films disponibles")
    print()
    
    # 2.5. Enrichir la base avec des films similaires (optionnel)
    enrichir = "--enrichir" in sys.argv or "-e" in sys.argv
    if enrichir:
        print("Étape 2.5: Enrichissement de la base avec des films similaires...")
        max_par_critere = 3
        if "--max-films" in sys.argv:
            try:
                idx = sys.argv.index("--max-films")
                max_par_critere = int(sys.argv[idx + 1])
            except (ValueError, IndexError):
                pass
        
        films_data = enrichirBaseFilms.enrichir_base_films(
            films_data,
            max_films_par_critere=max_par_critere
        )
        print(f"✔ Base enrichie : {len(films_data)} films au total")
        print()
    
    # 3. Calculer les similarités et créer les arêtes
    print("Étape 3: Calcul des similarités entre films...")
    aretes = calculSimilarites.calculer_toutes_aretes(films_data)
    print(f"✔ {len(aretes)} arêtes calculées")
    
    # Afficher quelques statistiques
    if aretes:
        poids_moyen = sum(a["weight"] for a in aretes) / len(aretes)
        poids_max = max(a["weight"] for a in aretes)
        poids_min = min(a["weight"] for a in aretes)
        print(f"   Poids moyen: {poids_moyen:.4f}")
        print(f"   Poids min: {poids_min:.4f}, max: {poids_max:.4f}")
    print()
    
    # 4. Filtrer le graphe et générer les positions 3D
    print("Étape 4: Filtrage du graphe et calcul du layout 3D...")
    seuil = filtrageGraphe.SEUIL_POIDS
    
    # Permettre de changer le seuil via argument
    if "--seuil" in sys.argv:
        try:
            idx = sys.argv.index("--seuil")
            seuil = float(sys.argv[idx + 1])
            print(f"   Seuil personnalisé: {seuil}")
        except (ValueError, IndexError):
            print(f"   Utilisation du seuil par défaut: {seuil}")
    
    graph = filtrageGraphe.filtrer_et_generer_graphe(
        films_data,
        aretes,
        seuil=seuil,
        output_file="graph.json"
    )
    print()
    
    # 5. Générer les recommandations
    print("Étape 5: Génération des recommandations...")
    aretes_filtrees = [a for a in aretes if a.get("weight", 0) >= seuil]
    recommandations = algorithmeRecommandation.recommander(
        films_data,
        aretes_filtrees,
        top_n=10
    )
    
    if recommandations:
        algorithmeRecommandation.afficher_recommandations(recommandations)
    else:
        print("Aucune recommandation disponible")
    print()
    
    # Résumé final
    print("="*60)
    print("RÉSUMÉ")
    print("="*60)
    print(f"Films traités: {len(films_data)}")
    print(f"Arêtes totales: {len(aretes)}")
    print(f"Arêtes après filtrage (seuil={seuil}): {len(graph['edges'])}")
    print(f"Recommandations générées: {len(recommandations)}")
    print()
    print("✔ Graphe généré avec succès dans graph.json")
    print("   Lancez le serveur: python serveurFichier.py")
    print("   Puis ouvrez: http://localhost:8000/index.html")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✖ Interruption par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n✖ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
