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

import requests
from bs4 import BeautifulSoup

def extraer_datos_noticia(url):
    """Extrae datos clave de una noticia"""
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code != 200:
            print(f"⚠️ No se pudo obtener la noticia: {url}")
            return None

        sopa = BeautifulSoup(response.text, "html.parser")
        texto = sopa.get_text().lower()

        # 📌 1️⃣ Extraer título de la noticia (o conflicto)
        titulo = sopa.title.string.strip() if sopa.title else "Título desconocido"

        # 📌 2️⃣ Extraer fecha (solo año)
        fecha = "Desconocida"
        for palabra in texto.split():
            if palabra.isdigit() and len(palabra) == 4:  # Buscar años como "2023"
                fecha = palabra
                break

        # 📌 3️⃣ Extraer ubicación (ciudad/localidad)
        ubicacion = None
        provincias = ["buenos aires", "santa fe", "córdoba", "mendoza", "entre ríos", "chaco"]  # Expandir con más provincias
        for palabra in texto.split():
            if palabra in provincias:
                ubicacion = palabra
                break
        
        # 📌 4️⃣ Extraer mención a agua
        menciona_agua = any(agua in texto for agua in ["río", "laguna", "napas", "agua", "contaminación hídrica"])

        # 📌 5️⃣ Buscar agroquímicos
        AGROQUIMICOS_CATEGORIAS = {
            "herbicida": ["glifosato", "atrazina", "2,4-D"],
            "insecticida": ["clorpirifos", "imidacloprid", "cipermetrina"],
            "fungicida": ["mancozeb", "carbendazim", "triazol"]
        }
        agroquimicos = []
        categoria_filtro = []
        for categoria, lista in AGROQUIMICOS_CATEGORIAS.items():
            for quimico in lista:
                if quimico in texto:
                    agroquimicos.append(quimico)
                    categoria_filtro.append(categoria)

        # 📌 6️⃣ Detectar protestas o denuncias
        menciona_protesta = any(palabra in texto for palabra in ["denuncia", "protesta", "marcha", "juicio", "vecinos", "movilización"])

        # 📌 7️⃣ Devolver la noticia en formato diccionario
        noticia = {
            "conflicto": titulo,
            "url": url,
            "fecha": fecha,
            "fuente": url.split("/")[2],  # Extrae el dominio como fuente
            "ubicacion": ubicacion if ubicacion else "Desconocida",
            "agua": "Sí" if menciona_agua else "No",
            "agroquimicos": ", ".join(agroquimicos),
            "categoria_filtro": ", ".join(categoria_filtro),
            "protestas": "Sí" if menciona_protesta else "No"
        }

        print(f"✅ Noticia extraída: {noticia}")
        return noticia

    except Exception as e:
        print(f"❌ Error al extraer la noticia: {url} - {e}")
        return None

        
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
        if isinstance(noticias_extraidas, list):  # Asegurar que es una lista
            nuevas_noticias.extend(noticias_extraidas)  
        else:
            print(f"⚠️ Advertencia: {fuente} devolvió un tipo inesperado: {type(noticias_extraidas)}")
    time.sleep(2)  # Para evitar bloqueos

print(f"🔍 Se encontraron {len(nuevas_noticias)} noticias nuevas para agregar.")


for noticia in nuevas_noticias:
    print(f"🛠 Tipo de noticia: {type(noticia)} - Contenido: {noticia}")  # Depuración

    if not isinstance(noticia, dict):  # Verificar si noticia es un diccionario
        print(f"❌ ERROR: noticia con formato incorrecto, no es un diccionario: {noticia}")
        continue  # Saltar esta noticia si tiene formato incorrecto

    if noticia["url"] not in urls_existentes:
        datos["features"].append({
            "type": "Feature",
            "properties": {
                "conflicto": noticia["conflicto"],
                "url": noticia["url"],
                "fecha": noticia["fecha"],
                "fuente": noticia["fuente"],
                "ubicacion": noticia["ubicacion"],
                "agua": noticia["agua"],
                "agroquimicos": noticia["agroquimicos"],
                "categoria_filtro": noticia["categoria_filtro"],
                "protestas": noticia["protestas"]
            },
            "geometry": {
                "type": "Point",
                "coordinates": noticia["coordenadas"]
            }
        })
        print(f"✅ Noticia agregada al GeoJSON: {noticia['conflicto']} - {noticia['url']}")

print(f"📌 Total de noticias en el archivo después de la actualización: {len(datos['features'])}")


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
