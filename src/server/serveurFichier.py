#!/usr/bin/env python3
from http.server import HTTPServer, SimpleHTTPRequestHandler, test
import json
import os
import sys
import time
from urllib.parse import urlparse

from src.data import enrichirBaseFilms
from src.data import scraperFilms
from src.graph import calculSimilarites
from src.graph import filtrageGraphe
from src.reco import algorithmeRecommandation

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def _completer_films_manquants(films_data):
    """
    Complète les champs vides via OMDb pour permettre l'enrichissement.
    """
    updated = 0
    for film in films_data:
        if not isinstance(film, dict):
            continue
        missing = (
            not film.get("genres")
            or not film.get("acteurs")
            or not film.get("realisateur")
            or not film.get("poster")
        )
        if not missing:
            continue
        titre = film.get("titre_original") or film.get("titre")
        imdb_id = film.get("imdb_id")
        omdb = scraperFilms.scraper_film_omdb(titre, imdb_id=imdb_id)
        if not omdb:
            continue
        for key in ["genres", "annee", "acteurs", "realisateur", "note", "poster", "titre"]:
            if not film.get(key):
                film[key] = omdb.get(key)
        updated += 1
    return updated

class CORSRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PROJECT_ROOT, **kwargs)

    def end_headers (self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        # Eviter les caches navigateur sur les JSON
        self.send_header('Cache-Control', 'no-store')
        SimpleHTTPRequestHandler.end_headers(self)

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def _send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/reset":
            try:
                payload = {}
                try:
                    content_length = int(self.headers.get("Content-Length", "0"))
                except ValueError:
                    content_length = 0
                if content_length > 0:
                    raw = self.rfile.read(content_length)
                    payload = json.loads(raw.decode("utf-8"))
            except Exception:
                payload = {}

            include_posters = bool(payload.get("include_posters", False))
            deleted = []
            for rel in [
                os.path.join("output", "films_data.json"),
                os.path.join("output", "graph.json"),
                os.path.join("output", "nodes.csv"),
                os.path.join("output", "edges.csv"),
            ]:
                path = os.path.join(PROJECT_ROOT, rel)
                if os.path.exists(path):
                    try:
                        os.remove(path)
                        deleted.append(rel)
                    except Exception:
                        pass

            posters_dir = os.path.join(PROJECT_ROOT, "output", "posters")
            if include_posters and os.path.isdir(posters_dir):
                for name in os.listdir(posters_dir):
                    p = os.path.join(posters_dir, name)
                    try:
                        os.remove(p)
                        deleted.append(os.path.join("output", "posters", name))
                    except Exception:
                        pass

            self._send_json(200, {"ok": True, "deleted": deleted})
            return

        if parsed.path != "/api/reco":
            self._send_json(404, {"error": "Not found"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            content_length = 0

        if content_length <= 0:
            self._send_json(400, {"error": "Empty body"})
            return

        try:
            raw = self.rfile.read(content_length)
            payload = json.loads(raw.decode("utf-8"))
        except Exception:
            self._send_json(400, {"error": "Invalid JSON"})
            return

        films_input = payload.get("films", [])
        if not isinstance(films_input, list) or not films_input:
            self._send_json(400, {"error": "films must be a non-empty list"})
            return

        force_reload = bool(payload.get("force", False))
        enrichir = bool(payload.get("enrichir", True))
        max_films = int(payload.get("max_films", 12))
        seuil = float(payload.get("seuil", filtrageGraphe.SEUIL_POIDS))
        write_list = bool(payload.get("write_list", True))

        liste_films = []
        titres_connus = set()
        for item in films_input:
            if not isinstance(item, str):
                continue
            line = item.strip()
            if not line:
                continue
            # Nettoyer un annee entre parentheses ou en fin de ligne
            clean_line = line
            clean_line = clean_line.replace("(", " (")
            if clean_line.endswith(")"):
                base = clean_line.rsplit("(", 1)[0].strip()
                if base:
                    clean_line = base
            parts = clean_line.strip().split()
            if parts and parts[-1].isdigit() and len(parts[-1]) == 4:
                clean_line = " ".join(parts[:-1]).strip()

            titres_connus.add(clean_line.upper())
            if "|" in line:
                titre, imdb_id = line.split("|", 1)
                liste_films.append((titre.strip(), imdb_id.strip()))
            elif clean_line.lower().startswith("tt") and clean_line[2:].isdigit():
                liste_films.append((clean_line, clean_line))
            else:
                liste_films.append((clean_line, None))

        if not liste_films:
            self._send_json(400, {"error": "no valid films"})
            return

        started = time.time()
        try:
            if write_list:
                os.makedirs(os.path.join(PROJECT_ROOT, "data"), exist_ok=True)
                with open(os.path.join(PROJECT_ROOT, "data", "listeFilms.txt"), "w", encoding="utf-8") as f:
                    for titre, imdb_id in liste_films:
                        if imdb_id:
                            f.write(f"{titre}|{imdb_id}\n")
                        else:
                            f.write(f"{titre}\n")

            films_data = scraperFilms.scraper_tous_films(
                liste_films=liste_films,
                force_reload=force_reload
            )

            updated = _completer_films_manquants(films_data)

            nb_films_saisis = len(films_data)  # avant enrichissement
            if enrichir:
                films_data = enrichirBaseFilms.enrichir_base_films(
                    films_data,
                    max_films_par_critere=max_films
                )

            aretes = calculSimilarites.calculer_toutes_aretes(films_data)
            graph = filtrageGraphe.filtrer_et_generer_graphe(
                films_data,
                aretes,
                seuil=seuil,
                output_file=os.path.join("output", "graph.json")
            )

            # Mettre à jour le cache films_data.json pour l'IHM
            os.makedirs(os.path.join(PROJECT_ROOT, "output"), exist_ok=True)
            with open(os.path.join(PROJECT_ROOT, "output", "films_data.json"), "w", encoding="utf-8") as f:
                json.dump({"films": films_data}, f, indent=2, ensure_ascii=False)

            aretes_filtrees = [a for a in aretes if a.get("weight", 0) >= seuil]
            recommandations = algorithmeRecommandation.recommander(
                films_data,
                aretes_filtrees,
                titres_connus=titres_connus,
                top_n=40,
                nb_films_saisis=nb_films_saisis,
            )

            reco_payload = []
            for idx, score, film in recommandations:
                film = film if isinstance(film, dict) else {}
                reco_payload.append({
                    "id": idx,
                    "score": score,
                    "titre": film.get("titre"),
                    "annee": film.get("annee"),
                    "note": film.get("note"),
                    "genres": film.get("genres"),
                    "poster": film.get("poster"),
                })

            duration = time.time() - started
            self._send_json(200, {
                "ok": True,
                "films_count": len(films_data),
                "edges_count": len(aretes),
                "edges_filtered": len(graph.get("edges", [])),
                "seuil": seuil,
                "updated_from_omdb": updated,
                "duration_sec": round(duration, 2),
                "recommandations": reco_payload
            })
        except Exception as e:
            self._send_json(500, {"error": str(e)})

if __name__ == '__main__':
    test(CORSRequestHandler, HTTPServer, port=int(sys.argv[1]) if len(sys.argv) > 1 else 8000)
