import requests
import json
import time
from geopy.geocoders import Nominatim
from bs4 import BeautifulSoup

# URLs de noticias sobre contaminación ambiental
URLS = [
    "https://www.lanacion.com.ar/buscar/agroquimicos",
    "https://www.pagina12.com.ar/buscar?q=agrotoxicos",
    "https://www.ellitoral.com/buscar?query=agrotoxicos"
]

# Inicializar el geocodificador para obtener coordenadas de ciudades
geolocalizador = Nominatim(user_agent="geo_scraper")

def obtener_coordenadas(lugar):
    """Convierte una ciudad en coordenadas (lat, lon)"""
    try:
        ubicacion = geolocalizador.geocode(lugar + ", Argentina")
        if ubicacion:
            return [ubicacion.longitude, ubicacion.latitude]
        else:
            return None
    except:
        return None

def obtener_nuevas_noticias():
    """Scrapea noticias y extrae título, link y ubicación."""
    nuevas_noticias = []
    headers = {'User-Agent': 'Mozilla/5.0'}

    for url in URLS:
        respuesta = requests.get(url, headers=headers)
        if respuesta.status_code != 200:
            continue  # Si falla, pasa a la siguiente URL

        sopa = BeautifulSoup(respuesta.text, "html.parser")
        articulos = sopa.find_all("article")  # Ajustar según cada sitio

        for articulo in articulos:
            titulo = articulo.find("h2") or articulo.find("h3")
            enlace = articulo.find("a")["href"] if articulo.find("a") else None
            fecha = "2024-02-10"  # Debería extraerse del sitio si es posible

            # Ubicación estimada (revisar manualmente los sitios)
            ubicacion = "Pergamino, Buenos Aires"  # Aquí iría la extracción real

            if titulo and enlace:
                coordenadas = obtener_coordenadas(ubicacion)
                if coordenadas:
                    nuevas_noticias.append({
                        "titulo": titulo.text.strip(),
                        "url": enlace,
                        "fecha": fecha,
                        "ubicacion": ubicacion,
                        "coordenadas": coordenadas
                    })

        time.sleep(1)  # Para evitar bloqueos

    return nuevas_noticias

# Cargar datos existentes en el GeoJSON
try:
    with open("conflictos.geojson", "r", encoding="utf-8") as f:
        datos = json.load(f)
except FileNotFoundError:
    datos = {"type": "FeatureCollection", "features": []}

# Obtener nuevas noticias
nuevas = obtener_nuevas_noticias()

# Agregar nuevas noticias al GeoJSON
for noticia in nuevas:
    datos["features"].append({
        "type": "Feature",
        "properties": {
            "titulo": noticia["titulo"],
            "url": noticia["url"],
            "fecha": noticia["fecha"],
            "ubicacion": noticia["ubicacion"]
        },
        "geometry": {
            "type": "Point",
            "coordinates": noticia["coordenadas"]
        }
    })

# Guardar la actualización en el GeoJSON
with open("conflictos.geojson", "w", encoding="utf-8") as f:
    json.dump(datos, f, indent=4, ensure_ascii=False)

print("✅ Base de datos actualizada con nuevas noticias.")

