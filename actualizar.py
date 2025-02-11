import requests
import json
import time
import re
from geopy.geocoders import Nominatim
from bs4 import BeautifulSoup

# 📌 Lista de fuentes de noticias (actualizada con medios nacionales y locales)
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
    "https://www.infocielo.com",
    "https://elespectador.com",
    "https://www.eldiariocba.com.ar",
    "https://www.memo.com.ar",
    "https://www.rionegro.com.ar",
    "https://www.elliberal.com.ar",
    "https://www.laarena.com.ar",
    "https://www.tiempodesanjuan.com",
    "https://www.elciudadanoweb.com",
    "https://www.puntal.com.ar",
    "https://www.fundeps.org",
    "https://www.eltrdebaldia.com",
    "https://www.mercedesya.com",
    "https://www.bragadoinforma.com.ar",
    "https://www.canalabierto.com.ar",
    "https://www.periodicoimpacto.com.ar",
    "https://www.elbalcarce.com",
    "https://www.eltime.com.ar",
    "https://www.realpolitik.com.ar",
    "https://www.eltiempo.com.ar",
    "https://www.abcdehoy.com.ar",
    "https://www.diariolaverdad.com.ar",
    "https://www.elcastellidigital.com.ar",
    "https://www.ramonactualidad.com.ar",
    "https://www.elemental.com.ar",
    "https://www.agrositio.com.ar",
    "https://www.noticiasguido.com.ar"
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

# 📌 Función para buscar enlaces en un portal de noticias
def obtener_enlaces_de_busqueda(url_base):
    """Extrae enlaces de artículos desde la página principal del medio"""
    try:
        response = requests.get(url_base, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code != 200:
            print(f"⚠️ No se pudo acceder a: {url_base}")
            return []

        sopa = BeautifulSoup(response.text, "html.parser")
        enlaces = []

        for link in sopa.find_all("a", href=True):
            href = link["href"]
            if any(tema in href.lower() for tema in ["agroquimico", "pesticida", "contaminacion", "fumigacion"]):
                if href.startswith("http"):
                    enlaces.append(href)
                else:
                    enlaces.append(url_base + href)

        print(f"🔗 Se encontraron {len(enlaces)} artículos en {url_base}")
        return enlaces[:5]  # Limitar para evitar demasiadas solicitudes

    except Exception as e:
        print(f"❌ Error al obtener enlaces de {url_base}: {e}")
        return []

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
        ubicacion = None
        for palabra in texto.split():
            if palabra in ["buenos", "santa", "cordoba", "mendoza", "chaco", "misiones"]:
                ubicacion = palabra.capitalize() + ", Argentina"
                break

        coordenadas = obtener_coordenadas(ubicacion) if ubicacion else None

        # 📌 Buscar mención a agroquímicos
        menciona_agua = any(agua in texto for agua in ["río", "laguna", "napas", "agua", "contaminación hídrica"])
        menciona_protesta = any(palabra in texto for palabra in ["denuncia", "protesta", "marcha", "juicio", "vecinos", "movilización"])

        # 📌 Estructurar la noticia
        noticia = {
            "conflicto": titulo,
            "url": url,
            "fecha": fecha,
            "fuente": url.split("/")[2],
            "ubicacion": ubicacion if ubicacion else "Desconocida",
            "coordenadas": coordenadas if coordenadas else [0, 0],
            "agua": "Sí" if menciona_agua else "No",
            "protestas": "Sí" if menciona_protesta else "No"
        }

        print(f"✅ Noticia extraída: {noticia}")
        return noticia

    except Exception as e:
        print(f"❌ Error al extraer la noticia: {url} - {e}")
        return None

# 📌 Extraer noticias de todas las fuentes
nuevas_noticias = []
for fuente in FUENTES:
    enlaces_noticias = obtener_enlaces_de_busqueda(fuente)
    for enlace in enlaces_noticias:
        noticia = extraer_datos_noticia(enlace)
        if noticia:
            nuevas_noticias.append(noticia)

# 📌 Guardar en GeoJSON
with open("ConflictosGeorref_final_DEF.geojson", "w", encoding="utf-8") as f:
    json.dump(nuevas_noticias, f, indent=4, ensure_ascii=False)

print("✅ Base de datos actualizada con nuevas noticias.")
