import requests
from urllib.parse import quote_plus
import json
import os

# Charger la clé API depuis .env ou variable d'environnement
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
    
    # Fallback
    return os.getenv('OMDB_API_KEY', 'b64880b7')

API_KEY = load_api_key()
# https://www.omdbapi.com/ > API KEY

def filenamePoster(titre) :
    filename = titre.replace(" ", "_")
    filename = filename.replace("'", "_") + ".jpg"
    return filename



def telecharger_poster_imdb_id(movie_id):
    """
    Télécharge le poster d'un film à partir de son ID IMDb (ex: '0468569')
    """
    url = f"http://www.omdbapi.com/?i=tt{movie_id}&apikey={API_KEY}"
    r = requests.get(url, timeout=10).json()

    titre = r.get('Title', movie_id)
    poster_url = r.get('Poster')

    if poster_url and poster_url != 'N/A':
        filename = filenamePoster(titre)
        img = requests.get(poster_url, timeout=10).content
        with open(filename, 'wb') as f:
            f.write(img)
        print(f"✔ Poster téléchargé : {filename}")
        return filename
    else:
        print("✖ Aucun poster disponible pour ce film")
        return None



def telecharger_poster_titre(titre):
    from urllib.parse import quote_plus
    encoded = quote_plus(titre)

    url = f"http://www.omdbapi.com/?t={encoded}&apikey={API_KEY}"
    r = requests.get(url, timeout=10).json()

    if r.get("Response") != "True":
        print(f"✖ Film '{titre}' non trouvé")
        return None

    poster_url = r.get("Poster")
    titre_film = r.get("Title", titre)

    if poster_url and poster_url != "N/A":
        filename = filenamePoster(titre)
        img = requests.get(poster_url, timeout=10).content
        with open(filename, "wb") as f:
            f.write(img)
        print(f"✔ Poster téléchargé : {filename}")
        return filename

    print("✖ Aucun poster disponible")
    return None


# Exemple d'utilisation
movie1 = telecharger_poster_imdb_id("0468569")   # The Dark Knight
movie2 = telecharger_poster_imdb_id("3896198")   # les gardien de la galaxie
movie3 = telecharger_poster_imdb_id("0133093")   # matrix
movie4 = telecharger_poster_imdb_id("0110912")   # pulp fiction
movie5 = telecharger_poster_titre("retour vers le futur") # Par titre
movie6 = telecharger_poster_titre("her") # Par titre





nodes = [
    { "id": 0, "x": 0, "y": 0, "z": 0, "texture": movie1 },
    { "id": 1, "x": 5, "y": 0, "z": 0, "texture": movie2 },
    { "id": 2, "x": 0, "y": 0, "z": 5, "texture": movie3 },
    { "id": 3, "x": 5, "y": 0, "z": 5, "texture": movie4 },
    { "id": 4, "x": 5, "y": 5, "z": 5, "texture": movie5 },
    { "id": 5, "x": 5, "y": -5, "z": 5, "texture": movie6 },
]

edges = [
    { "from": 0, "to": 1, "weight": 1.2 },
    { "from": 0, "to": 2, "weight": 0.8 },
    { "from": 1, "to": 3, "weight": 1.5 },
    { "from": 2, "to": 3, "weight": 1.1 },
    { "from": 3, "to": 4, "weight": 1.1 },
    { "from": 4, "to": 5, "weight": 1.1 },
]

graph = { "nodes": nodes, "edges": edges }

with open("graph.json", "w") as f:
    json.dump(graph, f, indent=2)
