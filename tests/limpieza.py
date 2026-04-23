import pytest
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# --- Datos de prueba ---

@pytest.fixture
def df_sucio():
    return pd.DataFrame([
        {"nombre": "Casa Pepe",  "ciudad": "oviedo / uvieu", "cocina": "regional", "amenity": "restaurant"},
        {"nombre": "Bar Pepín",  "ciudad": "gijón/xixón",    "cocina": "spanish",  "amenity": "bar"},
        {"nombre": None,         "ciudad": "avilés",          "cocina": None,       "amenity": "cafe"},
        {"nombre": "El Cachopo", "ciudad": "OVIEDO",          "cocina": "Regional", "amenity": "restaurant"},
        {"nombre": "Sidrería",   "ciudad": "gijon",           "cocina": "regional", "amenity": "restaurant"},
    ])


# --- Tests de normalización ---

def test_dropna_nombre(df_sucio):
    df = df_sucio.dropna(subset=["nombre"])
    assert len(df) == 4
    assert None not in df["nombre"].values

def test_normalizar_ciudades(df_sucio):
    normalizar = {
        "oviedo / uvieu": "oviedo",
        "oviedo/uvieu":   "oviedo",
        "gijón/xixón":    "gijón",
        "gijon/xixon":    "gijón",
        "gijon":          "gijón",
        "OVIEDO":         "oviedo",
    }
    df = df_sucio.copy()
    df["ciudad"] = df["ciudad"].str.strip().str.lower().replace(normalizar)
    assert "oviedo / uvieu" not in df["ciudad"].values
    assert "gijón/xixón"    not in df["ciudad"].values
    assert "gijon"          not in df["ciudad"].values

def test_lowercase_nombre(df_sucio):
    df = df_sucio.dropna(subset=["nombre"]).copy()
    df["nombre"] = df["nombre"].str.strip().str.lower()
    assert all(df["nombre"] == df["nombre"].str.lower())

def test_lowercase_cocina(df_sucio):
    df = df_sucio.dropna(subset=["nombre"]).copy()
    df["cocina"] = df["cocina"].str.strip().str.lower()
    assert "Regional" not in df["cocina"].dropna().values

def test_sin_duplicados(df_sucio):
    df = df_sucio.dropna(subset=["nombre"]).copy()
    df["osm_id"] = [1, 2, 3, 3]
    df = df.drop_duplicates(subset="osm_id")
    assert len(df) == 3