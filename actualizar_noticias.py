import requests
import json
import time
import re
from geopy.geocoders import Nominatim
import geopandas as gpd

# Configurar OpenStreetMap (OSM)
geolocator = Nominatim(user_agent="geo_conflictos")

# API de NewsAPI (PON TU API KEY AQUÍ)
NEWS_API_KEY = "cd31ff8bc0c44cb7bd729c4de52b2068"

# Archivo original del GeoJSON a actualizar
geojson_file = "ConflictosGeorref_final_DEF.geojson"

# Función para obtener coordenadas desde OSM después de estandarizar ubicación
def get_coordinates(location):
    try:
        location_data = geolocator.geocode(location + ", Argentina", timeout=10)
        if location_data:
            return location_data.latitude, location_data.longitude
    except Exception as e:
        print(f"⚠️ Error al obtener coordenadas de '{location}': {e}")
    return None, None

# Extraer ubicación de la noticia (ciudad/localidad, provincia)
def extract_location(text):
    match = re.search(r'(\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)?,\s[A-Z][a-z]+\b)', text)
    if match:
        location = match.group(0)
        return location
    return None

# Obtener noticias desde NewsAPI
def get_news():
    news_list = []
    for keyword in ["contaminación agroquímicos Argentina", "glifosato Argentina"]:
        url = f"https://newsapi.org/v2/everything?q={keyword}&language=es&apiKey={NEWS_API_KEY}"
        response = requests.get(url)
        if response.status_code == 200:
            articles = response.json().get("articles", [])
            for article in articles:
                title = article["title"]
                link = article["url"]
                source = article["source"]["name"]
                date = article["publishedAt"][:4]
                news_list.append({"title": title, "link": link, "source": source, "year": date})
        time.sleep(2)
    return news_list

# Cargar GeoJSON existente
gdf = gpd.read_file(geojson_file)

# Obtener noticias y procesarlas
news_articles = get_news()
if not news_articles:
    print("❌ No se encontraron noticias. Revisa la API Key o las palabras clave.")
    exit()

# Procesar noticias con ubicación específica
for news in news_articles:
    location = extract_location(news["title"])
    if location:
        lat, lon = get_coordinates(location)
        if lat and lon:
            new_entry = {
                "CONFLICTO": news["title"],
                "UBICACIÓN": location,
                "FUENTE": news["source"],
                "AÑO": news["year"],
                "LINK": news["link"],
                "AGUA (SI/N)": "No",
                "AGROQUÍMICOS": "Pendiente",
                "CATEGORIA_FILTRO": "Pendiente",
                "VIDA_MEDIA": "Pendiente",
                "MOVILIDAD_AGUA": "Pendiente",
                "DISPERSION_ATMOSFERICA": "Pendiente",
                "TOXICIDAD": "Pendiente",
                "BIOACUMULACION": "Pendiente",
                "geometry": f"POINT ({lon} {lat})"
            }
            gdf = gdf.append(new_entry, ignore_index=True)
        else:
            print(f"⚠️ No se encontraron coordenadas para {location}, noticia omitida.")

# Guardar actualización en el GeoJSON original
gdf.to_file(geojson_file, driver="GeoJSON")
print(f"✅ Noticias agregadas correctamente a {geojson_file}")
