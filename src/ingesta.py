import requests
import json
import os
import time
from datetime import datetime

# URL del endpoint público de Overpass
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Ruta de salida
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "restaurantes_raw.json")


def build_query(amenity: str = "restaurant") -> str:
    """
    Construye una query OverpassQL para obtener todos los nodos,
    ways y relaciones de un tipo de amenity dentro de Asturias (relation 80569).
    """
    return f"""
    [out:json][timeout:60];
    area["ISO3166-2"="ES-AS"]->.asturias;
    (
      node["amenity"="{amenity}"](area.asturias);
      way["amenity"="{amenity}"](area.asturias);
      relation["amenity"="{amenity}"](area.asturias);
    );
    out body;
    >;
    out skel qt;
    """


def fetch_data(query: str) -> dict:
    """Lanza la petición a Overpass y devuelve el JSON."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Enviando consulta a Overpass API...")
    response = requests.post(
        OVERPASS_URL,
        data={"data": query},
        headers={"User-Agent": "GastroAstur/1.0 (proyecto educativo)"},
        timeout=90,
    )
    response.raise_for_status()
    return response.json()


def save_raw(data: dict, filepath: str) -> None:
    """Guarda el JSON crudo en disco con metadatos de descarga."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    output = {
        "metadata": {
            "descargado_en": datetime.now().isoformat(),
            "fuente": OVERPASS_URL,
            "total_elementos": len(data.get("elements", [])),
        },
        "data": data,
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"Guardado en: {filepath}")
    print(f"Total elementos descargados: {output['metadata']['total_elementos']}")


def run_ingesta(amenities: list[str] | None = None) -> None:
    """
    Punto de entrada principal. Descarga varios tipos de amenity
    relacionados con gastronomía asturiana.
    """
    if amenities is None:
        amenities = ["restaurant", "bar", "cafe", "fast_food", "pub"]

    all_elements = []

    for amenity in amenities:
        print(f"\n--- Descargando: {amenity} ---")
        query = build_query(amenity)
        try:
            data = fetch_data(query)
            elements = data.get("elements", [])
            # Añade el tipo de amenity a cada elemento para distinguirlos después
            for el in elements:
                el.setdefault("tags", {})["_amenity_query"] = amenity
            all_elements.extend(elements)
            print(f"  → {len(elements)} elementos encontrados")
            # Pausa entre peticiones para no sobrecargar la API (buenas prácticas)
            time.sleep(30)
        except requests.exceptions.RequestException as e:
            print(f"  ERROR al descargar {amenity}: {e}")

    # Guarda todo junto en un solo archivo
    combined = {"elements": all_elements}
    save_raw(combined, OUTPUT_FILE)

def fetch_poblacion_asturias() -> None:
    """
    Descarga población de municipios asturianos desde la API del INE.
    Tabla 2886: Asturias, población por municipios y sexo.
    """
    print("\n--- Descargando población desde INE ---")

    url = "https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/2886?nult=1"

    try:
        response = requests.get(url, timeout=30,
                                headers={"User-Agent": "GastroAstur/1.0"})
        response.raise_for_status()
        data = response.json()

        print(f"  Total entradas recibidas: {len(data)}")

        # Filtra solo "Total" (excluye filas de hombres y mujeres por separado)
        asturias = []
        for entry in data:
            nombre = entry.get("Nombre", "")
            if "Total" in nombre and "Hombres" not in nombre and "Mujeres" not in nombre:
                asturias.append({
                    "nombre":     nombre.replace(". Total. Total habitantes. Personas.", "").strip(),
                    "codigo_ine": entry.get("COD"),
                    "poblacion":  entry["Data"][0].get("Valor") if entry.get("Data") else None,
                    "anio":       entry["Data"][0].get("Anyo")  if entry.get("Data") else None,
                })

        output_path = os.path.join(OUTPUT_DIR, "poblacion_asturias.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(asturias, f, ensure_ascii=False, indent=2)

        print(f"Municipios descargados: {len(asturias)}")
        print(f"Guardado en: {output_path}")

    except requests.exceptions.RequestException as e:
        print(f"ERROR al descargar población: {e}")
if __name__ == "__main__":
    run_ingesta()
    fetch_poblacion_asturias() 