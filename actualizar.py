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

# 📌 Configuración del geolocalizador
geolocalizador = Nominatim(user_agent="geo_scraper")

# 📌 Función para obtener coordenadas
def obtener_coordenadas(ubicacion):
    """Convierte una ciudad/localidad en coordenadas (lat, lon)"""
    try:
        ubicacion_info = geolocalizador.geocode(f"{ubicacion}, Argentina")
        if ubicacion_info:
            return [ubicacion_info.longitude, ubicacion_info.latitude]
    except:
        return None
    return None

# 📌 Función para estandarizar ubicaciones
def estandarizar_ubicacion(texto):
    """Busca y estandariza la ubicación en el formato (ciudad, provincia)"""
    provincias = {
        "buenos aires": "Buenos Aires",
        "santa fe": "Santa Fe",
        "cordoba": "Cordoba",
        "mendoza": "Mendoza",
        "entre rios": "Entre Rios",
        "chaco": "Chaco",
        "misiones": "Misiones",
        "corrientes": "Corrientes",
        "neuquen": "Neuquen",
        "rio negro": "Rio Negro",
        "tucuman": "Tucuman"
    }

    ubicacion = None
    for provincia in provincias:
        if provincia in texto.lower():
            coincidencias = re.findall(r"([A-Z][a-z]+) (?:de |en |, )?" + provincia, texto, re.IGNORECASE)
            if coincidencias:
                localidad = coincidencias[0].strip()
                ubicacion = f"{localidad}, {provincias[provincia]}"
            else:
                ubicacion = provincias[provincia]

    return ubicacion

# 📌 Función para buscar enlaces en Google (placeholder)
def buscar_en_google(consulta):
    """Simulación de búsqueda en Google (debe integrarse con un servicio real)"""
    print(f"🔎 Simulando búsqueda en Google: {consulta}")
    return []  # ⚠ Actualmente no devuelve resultados

# 📌 Función para extraer datos de una noticia
def extraer_datos_noticia(url):
    """Extrae datos clave de una noticia"""
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code != 200:
            print(f"⚠️ No se pudo obtener la noticia: {url}")
            return None

        sopa = BeautifulSoup(response.text, "html.parser")
        texto = sopa.get_text().lower()

        # 📌 Extraer título
        titulo = sopa.title.string.strip() if sopa.title else "Título desconocido"

        # 📌 Extraer fecha (solo año)
        fecha = "Desconocida"
        for palabra in texto.split():
            if palabra.isdigit() and len(palabra) == 4:
                fecha = palabra
                break

        # 📌 Extraer ubicación
        ubicacion = estandarizar_ubicacion(texto)
        coordenadas = obtener_coordenadas(ubicacion) if ubicacion else None

        # 📌 Buscar mención a agua
        menciona_agua = any(agua in texto for agua in ["río", "laguna", "napas", "agua", "contaminación hídrica"])

        # 📌 Buscar agroquímicos
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

        # 📌 Detectar protestas o denuncias
        menciona_protesta = any(palabra in texto for palabra in ["denuncia", "protesta", "marcha", "juicio", "vecinos", "movilización"])

        # 📌 Estructurar la noticia
        noticia = {
            "conflicto": titulo,
            "url": url,
            "fecha": fecha,
            "fuente": url.split("/")[2],
            "ubicacion": ubicacion if ubicacion else "Desconocida",
            "coordenadas": coordenadas if coordenadas else [0, 0],  # 🔹 Siempre devuelve coordenadas válidas
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

# 📌 Cargar datos existentes en el GeoJSON
try:
    with open("ConflictosGeorref_final_DEF.geojson", "r", encoding="utf-8") as f:
        datos = json.load(f)
except FileNotFoundError:
    datos = {"type": "FeatureCollection", "features": []}

# 📌 Buscar noticias en Google para todas las fuentes
nuevas_noticias = []
consultas_google = [f"contaminación por agroquímicos site:{fuente}" for fuente in FUENTES]

for consulta in consultas_google:
    enlaces_google = buscar_en_google(consulta)
    for enlace in enlaces_google:
        noticia = extraer_datos_noticia(enlace)
        if noticia:
            nuevas_noticias.append(noticia)

# 📌 Agregar noticias nuevas al GeoJSON
urls_existentes = {f["properties"]["url"] for f in datos["features"] if "url" in f["properties"]}

for noticia in nuevas_noticias:
    if noticia["url"] not in urls_existentes:
        datos["features"].append({
            "type": "Feature",
            "properties": noticia,
            "geometry": {
                "type": "Point",
                "coordinates": noticia["coordenadas"]
            }
        })
        print(f"✅ Noticia agregada al GeoJSON: {noticia['conflicto']} - {noticia['url']}")

# 📌 Guardar el nuevo GeoJSON
with open("ConflictosGeorref_final_DEF.geojson", "w", encoding="utf-8") as f:
    json.dump(datos, f, indent=4, ensure_ascii=False)

print("✅ Base de datos actualizada con nuevas noticias.")
