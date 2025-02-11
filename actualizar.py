import requests
import json
import time
import re
from geopy.geocoders import Nominatim
from bs4 import BeautifulSoup

# Lista de fuentes de noticias
FUENTES = [
    "https://www.lanacion.com.ar",
    "https://www.pagina12.com.ar",
    "https://www.ellitoral.com",
    "https://www.infobae.com",
    "https://www.perfil.com",
    "https://www.clarin.com",
    "https://tn.com.ar",
    "https://www.ambito.com",
    "https://www.argentinamunicipal.com.ar",
    "https://www.diarionecochea.com",
    "https://www.eldiarioar.com",
    "https://www.lavoz.com.ar",
    "https://www.tiempoar.com.ar",
    "https://www.lacapital.com.ar",
    "https://www.elonce.com",
    "https://www.chacodiapordia.com",
    "https://www.mdzol.com",
    "https://www.misionesonline.net",
    "https://www.eltribuno.com",
    "https://www.unoentrerios.com.ar",
    "https://www.lagaceta.com.ar",
    "https://www.losandes.com.ar",
    "https://www.elcomercial.com.ar",
    "https://www.cadena3.com",
    "https://www.era-verde.com.ar",
    "https://www.elpopular.com.ar",
    "https://www.laverdadonline.com",
    "https://www.noticiaslasflores.com.ar",
    "https://www.realpolitik.com.ar",
    "https://www.bichosdecampo.com",
    "https://www.laizquierdadiario.com",
    "https://www.eldiarionorte.com.ar",
    "https://www.ruralaldia.com.ar",
    "https://www.agrositio.com.ar",
    "https://www.elmensajerodiario.com.ar",
    "https://www.lavozdelpueblo.com.ar",
    "https://www.entrelineas.info",
    "https://www.quedigital.com.ar",
    "https://www.elecodetandil.com.ar",
    "https://www.lanueva.com",
    "https://www.infocielo.com"
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

def obtener_enlaces_de_busqueda(url_base):
    """Extrae enlaces de artículos reales desde la página principal del medio"""
    try:
        response = requests.get(url_base, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code != 200:
            print(f"⚠️ No se pudo acceder a: {url_base}")
            return []

        sopa = BeautifulSoup(response.text, "html.parser")
        enlaces = []

        for link in sopa.find_all("a", href=True):
            href = link["href"]
            
            # 📌 Reglas específicas para cada medio
            if "pagina12.com.ar" in url_base and "/nota/" in href:
                enlaces.append("https://www.pagina12.com.ar" + href)
            elif "lanacion.com.ar" in url_base and "/nota/" in href:
                enlaces.append("https://www.lanacion.com.ar" + href)
            elif "infobae.com" in url_base and ("/sociedad/" in href or "/politica/" in href):
                enlaces.append("https://www.infobae.com" + href)
            elif "clarin.com" in url_base and "/politica/" in href:
                enlaces.append("https://www.clarin.com" + href)
            elif "lavoz.com.ar" in url_base and "/ciudadanos/" in href:
                enlaces.append("https://www.lavoz.com.ar" + href)
            elif "losandes.com.ar" in url_base and "/article/view" in href:
                enlaces.append("https://www.losandes.com.ar" + href)

        print(f"🔗 Se encontraron {len(enlaces)} artículos en {url_base}")
        return enlaces[:5]  # Limitar para evitar demasiadas solicitudes

    except Exception as e:
        print(f"❌ Error al obtener enlaces de {url_base}: {e}")
        return []

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
        return noticia  # ✅ AQUÍ TERMINA LA FUNCIÓN CORRECTAMENTE

    except Exception as e:
        print(f"❌ Error al extraer la noticia: {url} - {e}")
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

# 📌 Recorrer todas las fuentes y extraer noticias nuevas
nuevas_noticias = []
for fuente in FUENTES:
    enlaces_noticias = obtener_enlaces_de_busqueda(fuente)  # Obtener los artículos reales
    for enlace in enlaces_noticias:
        noticia = extraer_datos_noticia(enlace)
        if noticia:
            nuevas_noticias.append(noticia)

    time.sleep(2)  # Para evitar bloqueos entre solicitudes

print(f"🔍 Se encontraron {len(nuevas_noticias)} noticias nuevas para agregar.")

# 📌 Agregar noticias nuevas al GeoJSON si no están duplicadas
urls_existentes = {f["properties"]["url"] for f in datos["features"] if "url" in f["properties"]}

for noticia in nuevas_noticias:
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

# 📌 Guardar el nuevo GeoJSON con las noticias nuevas y corregidas
with open("ConflictosGeorref_final_DEF.geojson", "w", encoding="utf-8") as f:
    json.dump(datos, f, indent=4, ensure_ascii=False)

print("✅ Base de datos actualizada con nuevas noticias.")

