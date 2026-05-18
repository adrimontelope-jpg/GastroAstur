import pytest
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.ingesta import build_query


# --- Tests de build_query ---

def test_build_query_contiene_amenity():
    query = build_query("restaurant")
    assert "restaurant" in query

def test_build_query_contiene_asturias():
    query = build_query("bar")
    assert "ES-AS" in query

def test_build_query_formato_json():
    query = build_query("cafe")
    assert "[out:json]" in query

def test_build_query_amenity_personalizado():
    query = build_query("pub")
    assert '"amenity"="pub"' in query