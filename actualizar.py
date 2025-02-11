import requests
import json
import time
import re
from geopy.geocoders import Nominatim
from bs4 import BeautifulSoup

# Lista de fuentes de noticias
FUENTES = [
    "https://www.lanacion.com.ar/buscar/agroquimicos",
    "https://www.pagina12.com.ar/buscar?q=agrotoxicos",
    "https://www.ellitoral.com/buscar?query=agrotoxicos",
    "https://www.infobae.com/buscar/?q=agrotoxicos",
    "https://www.perfil.com/buscar/agroquimicos"
    # Agregar más fuentes aquí...
]

# Diccionario de agroquímicos con sus categorías
AGROQUIMICOS_CATEGORIAS = {
    "herbicida": ["glifosato", "2,4-D", "atrazina", "paraquat"],
    "fungicida": ["mancozeb", "clorotalonil", "tebuconazol"],
    "insecticida": ["clorpirifos", "imidacloprid", "cipermetrina"]
}

# Configuración del geolocalizador
geolocalizador = Nominatim(user_agent="geo_scraper")

def obtener_coordenadas(ubicacion):
    """Convierte una ciudad/localidad en coordenadas (lat, lon)"""
    try:
        ubicacion_info = geolocalizador.geocode(f"{ubicacion}, Argentina")
        if ubicacion_info:
            return [ubicacion_info.longitude, ubicacion_info.latitude]
    except:
        return None
    return None

def extraer_datos_noticia(url):
    """Extrae datos clave de una noticia"""
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code != 200:
            return None

        sopa = BeautifulSoup(response.text, "html.parser")
        texto = sopa.get_text().lower()
        
        # Buscar menciones a ubicaciones (ciudades/localidades)
        ubicacion = None
        for palabra in texto.split():
            if "buenos aires" in palabra or "santa fe" in palabra:  # Expandir con más provincias
                ubicacion = palabra

        # Buscar menciones a agua
        menciona_agua = any(x in texto for x in ["río", "napas", "laguna", "acuífero", "contaminación hídrica"])
        
        # Buscar agroquímicos y clasificarlos
        agroquimicos = []
        categoria_filtro = []
        for categoria, lista in AGROQUIMICOS_CATEGORIAS.items():
            for quimico in lista:
                if quimico in texto:
                    agroquimicos.append(quimico)
                    categoria_filtro.append(categoria)

        # Determinar si la noticia menciona protestas
        menciona_protesta = any(x in texto for x in ["denuncia", "movilización", "marcha", "protesta", "juicio"])

        # Año de publicación (suponiendo que se puede extraer desde la URL o texto)
        anio = re.search(r"20\d{2}", url)  # Buscar año en la URL
        anio = anio.group(0) if anio else "Desconocido"

        return {
            "conflicto": "Noticia sobre agroquímicos",
            "url": url,
            "fecha": anio,
            "fuente": url.split("/")[2],
            "ubicacion": ubicacion,
            "coordenadas": obtener_coordenadas(ubicacion) if ubicacion else None,
            "agua": "Sí" if menciona_agua else "No",
            "agroquimicos": ", ".join(agroquimicos),
            "categoria_filtro": ", ".join(set(categoria_filtro)),
            "protestas": "Sí" if menciona_protesta else "No"
        }
    except:
        return None

# Cargar datos existentes en el GeoJSON
try:
    with open("ConflictosGeorref_final_DEF.geojson", "r", encoding="utf-8") as f:
        datos = json.load(f)  # <-- Esta línea estaba mal indentada
except FileNotFoundError:
    datos = {"type": "FeatureCollection", "features": []}

# Extraer noticias de las fuentes
nuevas_noticias = []
for fuente in FUENTES:
    noticias_extraidas = extraer_datos_noticia(fuente)
    if noticias_extraidas:
        nuevas_noticias.append(noticias_extraidas)
    time.sleep(2)  # Para evitar bloqueos

# Actualizar solo noticias ya existentes sin coordenadas
for noticia in datos["features"]:  # Recorremos solo las noticias que ya están en el GeoJSON
    if noticia["geometry"]["coordinates"] == [0, 0]:  # Si la noticia no tiene coordenadas correctas
        print(f"🔄 Actualizando coordenadas para: {noticia['properties']['conflicto']}")
        coordenadas_actualizadas = obtener_coordenadas(noticia["properties"]["ubicacion"])

        if coordenadas_actualizadas:
            noticia["geometry"]["coordinates"] = coordenadas_actualizadas
            print(f"✅ Coordenadas actualizadas: {noticia['geometry']['coordinates']}")
        else:
            print(f"⚠️ No se encontraron coordenadas para {noticia['properties']['ubicacion']}")

# Guardar el nuevo GeoJSON
with open("ConflictosGeorref_final_DEF.geojson", "w", encoding="utf-8") as f:
    json.dump(datos, f, indent=4, ensure_ascii=False)

print("✅ Base de datos actualizada con nuevas noticias.")
