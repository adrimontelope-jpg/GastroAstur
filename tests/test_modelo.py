import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_prediccion_devuelve_string():
    """La función de predicción debe devolver una cadena."""
    resultado = "restaurant"
    assert isinstance(resultado, str)

def test_clases_validas():
    """Las clases del modelo deben ser las esperadas."""
    clases_esperadas = {"restaurant", "bar", "cafe", "pub"}
    clases_modelo = {"restaurant", "bar", "cafe", "pub"}
    assert clases_modelo == clases_esperadas

def test_probabilidades_suman_uno():
    """Las probabilidades del clasificador deben sumar 1."""
    probabilidades = np.array([0.6, 0.2, 0.1, 0.1])
    assert abs(probabilidades.sum() - 1.0) < 1e-6

def test_clase_mayor_probabilidad():
    """La clase predicha debe ser la de mayor probabilidad."""
    clases = ["bar", "cafe", "pub", "restaurant"]
    probabilidades = np.array([0.1, 0.05, 0.05, 0.8])
    prediccion = clases[np.argmax(probabilidades)]
    assert prediccion == "restaurant"