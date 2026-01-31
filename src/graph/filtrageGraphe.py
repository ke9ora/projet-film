#!/usr/bin/env python3
"""
Module de filtrage du graphe et calcul des positions 3D
Filtre les arêtes selon un seuil de poids et calcule un layout 3D
"""
import json
import math
import os
import random

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Seuil de poids configurable
# Les arêtes avec un poids inférieur seront supprimées
SEUIL_POIDS = 0.5


def filtrer_aretes(aretes, seuil=SEUIL_POIDS):
    """
    Filtre les arêtes selon un seuil de poids
    Retourne uniquement les arêtes dont le poids >= seuil
    """
    aretes_filtrees = [a for a in aretes if a.get("weight", 0) >= seuil]
    return aretes_filtrees


def calculer_layout_simple(films_data, aretes):
    """
    Calcule un layout 3D simple basé sur les connexions
    Utilise un algorithme de force-directed simplifié
    """
    n = len(films_data)
    if n == 0:
        return []
    
    # Initialiser les positions aléatoirement dans une sphère
    positions = []
    for i in range(n):
        # Position initiale aléatoire
        angle1 = random.uniform(0, 2 * math.pi)
        angle2 = random.uniform(0, math.pi)
        radius = random.uniform(5, 15)
        
        x = radius * math.sin(angle2) * math.cos(angle1)
        y = radius * math.sin(angle2) * math.sin(angle1)
        z = radius * math.cos(angle2)
        
        positions.append({"x": x, "y": y, "z": z})
    
    # Itérations de force-directed layout
    iterations = 50
    k = math.sqrt((15 * 15) / n)  # Constante de répulsion
    
    for iteration in range(iterations):
        forces = [{"x": 0, "y": 0, "z": 0} for _ in range(n)]
        
        # Forces de répulsion entre tous les nœuds
        for i in range(n):
            for j in range(i + 1, n):
                dx = positions[i]["x"] - positions[j]["x"]
                dy = positions[i]["y"] - positions[j]["y"]
                dz = positions[i]["z"] - positions[j]["z"]
                dist = math.sqrt(dx*dx + dy*dy + dz*dz) + 0.1  # Éviter division par zéro
                
                # Force de répulsion
                force = k * k / dist
                fx = (dx / dist) * force
                fy = (dy / dist) * force
                fz = (dz / dist) * force
                
                forces[i]["x"] += fx
                forces[i]["y"] += fy
                forces[i]["z"] += fz
                forces[j]["x"] -= fx
                forces[j]["y"] -= fy
                forces[j]["z"] -= fz
        
        # Forces d'attraction le long des arêtes
        for arete in aretes:
            i = arete["from"]
            j = arete["to"]
            poids = arete.get("weight", 0.5)
            
            dx = positions[j]["x"] - positions[i]["x"]
            dy = positions[j]["y"] - positions[i]["y"]
            dz = positions[j]["z"] - positions[i]["z"]
            dist = math.sqrt(dx*dx + dy*dy + dz*dz) + 0.1
            
            # Force d'attraction proportionnelle au poids
            force = dist * poids * 0.1
            fx = (dx / dist) * force
            fy = (dy / dist) * force
            fz = (dz / dist) * force
            
            forces[i]["x"] += fx
            forces[i]["y"] += fy
            forces[i]["z"] += fz
            forces[j]["x"] -= fx
            forces[j]["y"] -= fy
            forces[j]["z"] -= fz
        
        # Appliquer les forces avec un facteur d'amortissement
        damping = 0.8
        for i in range(n):
            positions[i]["x"] += forces[i]["x"] * damping
            positions[i]["y"] += forces[i]["y"] * damping
            positions[i]["z"] += forces[i]["z"] * damping
    
    return positions


def generer_graph_json(films_data, aretes_filtrees, positions, output_file="graph.json"):
    """
    Génère le fichier graph.json avec la structure attendue
    """
    nodes = []
    for i, film in enumerate(films_data):
        pos = positions[i] if i < len(positions) else {"x": 0, "y": 0, "z": 0}
        node = {
            "id": i,
            "x": round(pos["x"], 2),
            "y": round(pos["y"], 2),
            "z": round(pos["z"], 2),
            "texture": film.get("poster", "default.jpg")
        }
        nodes.append(node)
    
    # S'assurer que les arêtes référencent des IDs valides
    edges = []
    for arete in aretes_filtrees:
        if arete["from"] < len(nodes) and arete["to"] < len(nodes):
            edges.append({
                "from": arete["from"],
                "to": arete["to"],
                "weight": arete["weight"]
            })
    
    graph = {
        "nodes": nodes,
        "edges": edges
    }
    
    output_dir = os.path.dirname(output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2, ensure_ascii=False)
    
    print(f"✔ Graphe généré : {len(nodes)} nœuds, {len(edges)} arêtes")
    return graph


def filtrer_et_generer_graphe(films_data, aretes, seuil=SEUIL_POIDS, output_file="graph.json"):
    """
    Fonction principale : filtre les arêtes et génère le graphe
    """
    print(f"Filtrage des arêtes avec seuil = {seuil}...")
    aretes_filtrees = filtrer_aretes(aretes, seuil)
    print(f"  {len(aretes)} arêtes initiales -> {len(aretes_filtrees)} arêtes après filtrage")
    
    print("Calcul du layout 3D...")
    positions = calculer_layout_simple(films_data, aretes_filtrees)
    
    print("Génération du fichier graph.json...")
    graph = generer_graph_json(films_data, aretes_filtrees, positions, output_file)
    
    return graph


if __name__ == "__main__":
    # Test du module
    try:
        from src.graph import calculSimilarites
        
        films = calculSimilarites.charger_films_data()
        if films:
            aretes = calculSimilarites.calculer_toutes_aretes(films)
            graph = filtrer_et_generer_graphe(films, aretes, seuil=0.3)
            print(f"\nGraphe généré avec succès !")
        else:
            print("✖ Aucune donnée de film disponible")
    except ImportError:
        print("✖ Module calculSimilarites non trouvé")
