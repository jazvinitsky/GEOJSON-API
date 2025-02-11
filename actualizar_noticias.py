import requests
import json
import time
import re
from geopy.geocoders import Nominatim

# Configurar OpenStreetMap
geolocator = Nominatim(user_agent="geo_conflictos")

# API de NewsAPI (Obtén tu API Key en https://newsapi.org/)
NEWS_API_KEY = "TU_API_KEY"

# Palabras clave para búsqueda
keywords = [
    "contaminación agroquímicos Argentina",
    "agrotóxicos Argentina",
    "fumigaciones ilegales Argentina",
    "glifosato Argentina",
    "intoxicación agroquímicos Argentina",
    "derrame agroquímicos Argentina",
    "denuncias agroquímicos Argentina"
]

# Diccionario con propiedades toxicológicas por agroquímico
agroquimicos_info = {
    "Glifosato": {"VIDA_MEDIA": "3-130 días", "MOVILIDAD_AGUA": "Baja", "DISPERSION_ATMOSFERICA": "Baja", "TOXICIDAD": "Baja", "BIOACUMULACION": "Baja"},
    "Atrazina": {"VIDA_MEDIA": "60-100 días", "MOVILIDAD_AGUA": "Alta", "DISPERSION_ATMOSFERICA": "Media", "TOXICIDAD": "Media", "BIOACUMULACION": "Alta"},
    "2,4-D": {"VIDA_MEDIA": "7-10 días", "MOVILIDAD_AGUA": "Alta", "DISPERSION_ATMOSFERICA": "Alta", "TOXICIDAD": "Media", "BIOACUMULACION": "Baja"},
    "Clorpirifos": {"VIDA_MEDIA": "60-120 días", "MOVILIDAD_AGUA": "Baja", "DISPERSION_ATMOSFERICA": "Alta", "TOXICIDAD": "Alta", "BIOACUMULACION": "Alta"},
    "Paraquat": {"VIDA_MEDIA": "Muy larga", "MOVILIDAD_AGUA": "Baja", "DISPERSION_ATMOSFERICA": "Baja", "TOXICIDAD": "Alta", "BIOACUMULACION": "Baja"}
}

# Función para obtener noticias desde NewsAPI
def get_news():
    news_list = []
    for keyword in keywords:
        url = f"https://newsapi.org/v2/everything?q={keyword}&language=es&apiKey={NEWS_API_KEY}"
        response = requests.get(url)
        if response.status_code == 200:
            articles = response.json().get("articles", [])
            for article in articles:
                title = article["title"]
                link = article["url"]
                source = article["source"]["name"]
                date = article["publishedAt"][:4]  # Solo año
                news_list.append({"title": title, "link": link, "source": source, "year": date})
        time.sleep(2)
    return news_list

# Extraer ubicación de la noticia
def extract_location(text):
    match = re.search(r'(\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)?,\s[A-Z][a-z]+\b)', text)
    if match:
        location = match.group(0)
        try:
            location_data = geolocator.geocode(location + ", Argentina", timeout=10)
            if location_data:
                return location, location_data.latitude, location_data.longitude
        except:
            return None, None, None
    return None, None, None

# Clasificar agroquímicos y asignar propiedades
def classify_agrochemicals(text):
    detected = []
    
    if "glifosato" in text.lower():
        detected.append("Glifosato")
    if "atrazina" in text.lower():
        detected.append("Atrazina")
    if "2,4-D" in text.lower():
        detected.append("2,4-D")
    if "clorpirifos" in text.lower():
        detected.append("Clorpirifos")
    if "paraquat" in text.lower():
        detected.append("Paraquat")
    if "herbicida" in text.lower():
        detected.extend(["Glifosato", "Atrazina", "2,4-D"])
    if "insecticida" in text.lower():
        detected.append("Clorpirifos")

    detected = list(dict.fromkeys(detected))  # Eliminar duplicados
    
    if not detected:
        return "No especificado", "No especificado", "Desconocida", "Desconocida", "Desconocida", "Desconocida", "Desconocida"

    vida_media = ", ".join([agroquimicos_info[a]["VIDA_MEDIA"] for a in detected])
    movilidad_agua = ", ".join([agroquimicos_info[a]["MOVILIDAD_AGUA"] for a in detected])
    dispersion_atm = ", ".join([agroquimicos_info[a]["DISPERSION_ATMOSFERICA"] for a in detected])
    toxicidad = ", ".join([agroquimicos_info[a]["TOXICIDAD"] for a in detected])
    bioacumulacion = ", ".join([agroquimicos_info[a]["BIOACUMULACION"] for a in detected])

    categoria_filtro = detected[0] if detected else "No especificado"

    return ", ".join(detected), categoria_filtro, vida_media, movilidad_agua, dispersion_atm, toxicidad, bioacumulacion

# Obtener noticias y procesarlas
news_articles = get_news()

# Procesar noticias con ubicación específica
filtered_news = []
for news in news_articles:
    location, lat, lon = extract_location(news["title"])
    if location and lat and lon:
        agroquimicos, categoria, vida_media, movilidad, dispersion, toxicidad, bioacumulacion = classify_agrochemicals(news["title"])
        
        news["location"] = location
        news["lat"] = lat
        news["lon"] = lon
        news["agroquimicos"] = agroquimicos
        news["categoria"] = categoria
        news["vida_media"] = vida_media
        news["movilidad_agua"] = movilidad
        news["dispersion_atm"] = dispersion
        news["toxicidad"] = toxicidad
        news["bioacumulacion"] = bioacumulacion

        filtered_news.append(news)

# Convertir a GeoJSON
geojson_data = {"type": "FeatureCollection", "features": []}

for news in filtered_news:
    geojson_data["features"].append({
        "type": "Feature",
        "properties": news,
        "geometry": {"type": "Point", "coordinates": [news["lon"], news["lat"]]}
    })

# Guardar en el repositorio
with open("conflictos_actualizados.geojson", "w", encoding="utf-8") as f:
    json.dump(geojson_data, f, ensure_ascii=False, indent=4)

print("✅ Noticias actualizadas y guardadas en 'conflictos_actualizados.geojson'.")
