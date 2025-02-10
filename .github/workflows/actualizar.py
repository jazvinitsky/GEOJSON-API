import requests
import json
import time

# URLs de noticias sobre contaminación (ajustar según el medio que desees)
URLS = [
    "https://www.lanacion.com.ar/buscar/agroquimicos",
    "https://www.pagina12.com.ar/buscar?q=agrotoxicos",
    "https://www.ellitoral.com/buscar?query=agrotoxicos"
]

def obtener_nuevas_noticias():
    nuevas_noticias = []
    headers = {'User-Agent': 'Mozilla/5.0'}

    for url in URLS:
        respuesta = requests.get(url, headers=headers)
        if respuesta.status_code == 200:
            # Simulación de scraping (para mejorar con BeautifulSoup)
            nuevas_noticias.append({
                "titulo": f"Noticia encontrada en {url}",
                "url": url
            })
        time.sleep(1)  # Para evitar bloqueos del servidor

    return nuevas_noticias

# Cargar datos existentes en el GeoJSON
with open("conflictos.geojson", "r", encoding="utf-8") as f:
    datos = json.load(f)

# Agregar nuevas noticias con coordenadas (ficticias por ahora)
nuevas = obtener_nuevas_noticias()
datos["features"].extend([
    {
        "type": "Feature",
        "properties": noticia,
        "geometry": {
            "type": "Point",
            "coordinates": [-60.0, -32.0]  # Mejorar geolocalización en el futuro
        }
    } for noticia in nuevas
])

# Guardar la actualización en el GeoJSON
with open("conflictos.geojson", "w", encoding="utf-8") as f:
    json.dump(datos, f, indent=4, ensure_ascii=False)

print("Base de datos actualizada con nuevas noticias.")
