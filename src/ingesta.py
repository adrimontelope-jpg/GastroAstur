import requests
import json
import os
import time
from datetime import datetime
 
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "restaurantes_raw.json")
 
 
def build_query(amenity: str = "restaurant") -> str:
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
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Enviando consulta a Overpass API...")
    response = requests.post(
        OVERPASS_URL,
        data={"data": query},
        headers={"User-Agent": "GastroAstur/1.0 (proyecto educativo)"},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()
 
 
def save_raw(data: dict, filepath: str) -> None:
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
    if amenities is None:
        amenities = ["restaurant", "bar", "cafe", "fast_food", "pub"]
 
    all_elements = []
 
    for amenity in amenities:
        print(f"\n--- Descargando: {amenity} ---")
        query = build_query(amenity)
        try:
            data = fetch_data(query)
            elements = data.get("elements", [])
            for el in elements:
                el.setdefault("tags", {})["_amenity_query"] = amenity
            all_elements.extend(elements)
            print(f"  → {len(elements)} elementos encontrados")
            time.sleep(30)
        except requests.exceptions.RequestException as e:
            print(f"  ERROR al descargar {amenity}: {e}")
 
    combined = {"elements": all_elements}
    save_raw(combined, OUTPUT_FILE)
 
 
def fetch_poblacion_asturias() -> None:
    print("\n--- Descargando población desde INE ---")
    url = "https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/2886?nult=1"
 
    try:
        response = requests.get(url, timeout=30,
                                headers={"User-Agent": "GastroAstur/1.0"})
        response.raise_for_status()
        data = response.json()
        print(f"  Total entradas recibidas: {len(data)}")
 
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
 
 
def fetch_nominatim() -> None:
    print("\n--- Descargando coordenadas de concejos desde Nominatim ---")
 
    concejos = [
        "Oviedo", "Gijón", "Avilés", "Siero", "Langreo", "Mieres",
        "Cangas de Onís", "Llanes", "Villaviciosa", "Navia", "Luarca",
        "Ribadesella", "Arriondas", "Pola de Siero", "Cangas del Narcea"
    ]
 
    url = "https://nominatim.openstreetmap.org/search"
    headers = {"User-Agent": "GastroAstur/1.0 (proyecto educativo)"}
    resultados = []
 
    for concejo in concejos:
        params = {
            "q":              f"{concejo}, Asturias, Spain",
            "format":         "json",
            "limit":          1,
            "addressdetails": 1,
        }
        try:
            response = requests.get(url, params=params,
                                    headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
            if data:
                r = data[0]
                resultados.append({
                    "concejo":    concejo,
                    "lat":        float(r["lat"]),
                    "lon":        float(r["lon"]),
                    "nombre_osm": r.get("display_name", ""),
                })
                print(f"  ✓ {concejo}")
            time.sleep(1)
        except requests.exceptions.RequestException as e:
            print(f"  ERROR {concejo}: {e}")
 
    output_path = os.path.join(OUTPUT_DIR, "concejos_nominatim.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
 
    print(f"Concejos geocodificados: {len(resultados)}")
    print(f"Guardado en: {output_path}")
 
 
def fetch_wikidata_gastronomia() -> None:
    print("\n--- Descargando gastronomía asturiana desde Wikidata ---")

    url = "https://query.wikidata.org/sparql"

    # Busca platos y productos cuya descripción o nombre contiene "asturiano/a"
    query = """
    SELECT DISTINCT ?item ?itemLabel ?itemDescription WHERE {
      {
        ?item wdt:P31/wdt:P279* wd:Q2095.
        ?item rdfs:label ?label.
        FILTER(LANG(?label) = "es")
        FILTER(
          CONTAINS(LCASE(STR(?label)), "astur")
        )
      } UNION {
        ?item wdt:P31/wdt:P279* wd:Q2095.
        ?item schema:description ?desc.
        FILTER(LANG(?desc) = "es")
        FILTER(CONTAINS(LCASE(STR(?desc)), "astur"))
      }
      SERVICE wikibase:label {
        bd:serviceParam wikibase:language "es,en".
      }
    }
    LIMIT 100
    """

    headers = {
        "User-Agent": "GastroAstur/1.0 (proyecto educativo)",
        "Accept":     "application/json"
    }

    try:
        response = requests.get(
            url,
            params={"query": query, "format": "json"},
            headers=headers,
            timeout=60
        )
        response.raise_for_status()
        data = response.json()

        resultados = [
            {
                "id":          r["item"]["value"].split("/")[-1],
                "nombre":      r.get("itemLabel", {}).get("value", ""),
                "descripcion": r.get("itemDescription", {}).get("value", ""),
            }
            for r in data["results"]["bindings"]
            if not r.get("itemLabel", {}).get("value", "").startswith("Q")
        ]

        output_path = os.path.join(OUTPUT_DIR, "wikidata_gastronomia.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(resultados, f, ensure_ascii=False, indent=2)

        print(f"Platos y productos encontrados: {len(resultados)}")
        for r in resultados[:5]:
            print(f"  · {r['nombre']} — {r['descripcion']}")
        print(f"Guardado en: {output_path}")

    except requests.exceptions.RequestException as e:
        print(f"  ERROR: {e}")
 
    
if __name__ == "__main__":
    run_ingesta()
    fetch_poblacion_asturias()
    fetch_nominatim()
    fetch_wikidata_gastronomia()
 