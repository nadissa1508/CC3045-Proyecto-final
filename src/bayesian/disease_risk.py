"""
Red bayesiana para evaluación de riesgo de roya del café (Hemileia vastatrix)
basada en variables climáticas.

Estructura causal:
    Lluvia → Humedad → RiesgoRoya ← Temperatura
                           ↓
                  RendimientoEsperado

Variables (discretas):
    Temperatura       : 0=fresca (<18°C), 1=óptima (18-24°C), 2=caliente (>24°C)
    Humedad           : 0=baja (<70%),    1=alta (≥70%)
    Lluvia            : 0=poca,           1=moderada,           2=intensa
    RiesgoRoya        : 0=bajo,           1=alto
    RendimientoEsperado: 0=bajo,          1=medio,              2=alto

CPDs calibradas con:
    - FAO Guatemala coffee resilience data (2015)
    - USDA FAS Guatemala Coffee Annual (2013)
    - IICA / PROMECAFE: Hemileia vastatrix prospera con
      humedad >70% y temperatura 18-24°C (condición óptima).
"""

import os
import pickle
from pathlib import Path

from pgmpy.models import DiscreteBayesianNetwork
from pgmpy.factors.discrete import TabularCPD
from pgmpy.inference import VariableElimination

# Ruta absoluta a models/ independiente del directorio de trabajo
_MODELS_DIR = Path(__file__).resolve().parent.parent.parent / "models"
_MODEL_PATH = _MODELS_DIR / "bayesian_model.pkl"


def _build_model() -> DiscreteBayesianNetwork:
    """Construye y retorna el modelo bayesiano con CPDs hardcodeadas."""

    # ---- Estructura causal ----
    model = DiscreteBayesianNetwork([
        ("Lluvia",      "Humedad"),
        ("Temperatura", "RiesgoRoya"),
        ("Humedad",     "RiesgoRoya"),
        ("RiesgoRoya",  "RendimientoEsperado"),
    ])

    # ---- P(Temperatura) — nodo raíz ----
    # Guatemala: clima diverso por altitud. Zonas cafetaleras (1000-2000 m)
    # tienen predominio de temperatura óptima para Hemileia.
    # Fuente: USDA FAS Guatemala Coffee Annual 2013.
    cpd_temperatura = TabularCPD(
        variable="Temperatura",
        variable_card=3,
        values=[[0.30],   # fresca (<18°C) — zonas muy altas
                [0.50],   # óptima (18-24°C) — mayoría de fincas
                [0.20]],  # caliente (>24°C) — zonas bajas
    )

    # ---- P(Lluvia) — nodo raíz ----
    # Guatemala: estación lluviosa intensa (mayo-octubre).
    # Promedio anual: 1200-3000 mm según región cafetalera.
    # Fuente: INSIVUMEH / FAO Guatemala 2015.
    cpd_lluvia = TabularCPD(
        variable="Lluvia",
        variable_card=3,
        values=[[0.25],   # poca
                [0.50],   # moderada
                [0.25]],  # intensa
    )

    # ---- P(Humedad | Lluvia) ----
    # Lluvia intensa genera humedad ambiental >70% casi siempre.
    # Lluvia poca: humedad generalmente baja en zonas cafetaleras.
    # Columnas: Lluvia=poca, Lluvia=moderada, Lluvia=intensa
    cpd_humedad = TabularCPD(
        variable="Humedad",
        variable_card=2,
        values=[[0.80, 0.30, 0.05],   # Humedad=baja
                [0.20, 0.70, 0.95]],  # Humedad=alta
        evidence=["Lluvia"],
        evidence_card=[3],
    )

    # ---- P(RiesgoRoya | Temperatura, Humedad) ----
    # Hemileia vastatrix: condición ÓPTIMA = Temp 18-24°C + Humedad ≥70%.
    # En esa combinación la prob. de riesgo alto sube a 0.85.
    # Temp caliente o fresca reduce la viabilidad de esporas.
    # Fuente: PROMECAFE 2013; IICA "La roya del cafeto" 2013.
    #
    # Orden de columnas (Temperatura varía lento, Humedad varía rápido):
    #   Col 0: T=fresca,  H=baja  → riesgo bajo (esporas no germinan bien)
    #   Col 1: T=fresca,  H=alta  → riesgo moderado-bajo
    #   Col 2: T=óptima,  H=baja  → riesgo moderado (falta humedad)
    #   Col 3: T=óptima,  H=alta  → riesgo ALTO (condición ideal para roya)
    #   Col 4: T=caliente,H=baja  → riesgo muy bajo (calor inhibe esporas)
    #   Col 5: T=caliente,H=alta  → riesgo moderado
    cpd_riesgo_roya = TabularCPD(
        variable="RiesgoRoya",
        variable_card=2,
        values=[
            [0.90, 0.75, 0.70, 0.15, 0.85, 0.60],  # RiesgoRoya=bajo
            [0.10, 0.25, 0.30, 0.85, 0.15, 0.40],  # RiesgoRoya=alto
        ],
        evidence=["Temperatura", "Humedad"],
        evidence_card=[3, 2],
    )

    # ---- P(RendimientoEsperado | RiesgoRoya) ----
    # Roya alta reduce rendimiento drásticamente: pérdidas del 30-70%
    # documentadas en la crisis 2012-2013 (USDA FAS 2013).
    # Columnas: Riesgo=bajo, Riesgo=alto
    cpd_rendimiento = TabularCPD(
        variable="RendimientoEsperado",
        variable_card=3,
        values=[
            [0.10, 0.60],   # Rendimiento=bajo
            [0.30, 0.30],   # Rendimiento=medio
            [0.60, 0.10],   # Rendimiento=alto
        ],
        evidence=["RiesgoRoya"],
        evidence_card=[2],
    )

    # ---- Agregar CPDs y verificar ----
    model.add_cpds(
        cpd_temperatura,
        cpd_lluvia,
        cpd_humedad,
        cpd_riesgo_roya,
        cpd_rendimiento,
    )
    assert model.check_model(), "El modelo bayesiano no es válido — revisar CPDs."
    return model


def _load_or_build_model() -> tuple:
    """
    Carga el modelo desde disco si existe; si no, lo construye y lo guarda.
    Retorna (model, inference_engine).
    """
    if _MODEL_PATH.exists():
        with open(_MODEL_PATH, "rb") as f:
            model = pickle.load(f)
    else:
        model = _build_model()
        _MODELS_DIR.mkdir(parents=True, exist_ok=True)
        with open(_MODEL_PATH, "wb") as f:
            pickle.dump(model, f)
        print(f"Modelo bayesiano guardado en {_MODEL_PATH}")

    inference = VariableElimination(model)
    return model, inference


# Instancia global — se inicializa al importar el módulo
_model, _inference = _load_or_build_model()


def evaluate_disease_risk(temperatura: int, humedad: int, lluvia: int) -> dict:
    """
    Estima el riesgo de roya dado el estado climático actual.

    Parámetros
    ----------
    temperatura : int  0=fresca, 1=óptima (18-24°C), 2=caliente
    humedad     : int  0=baja (<70%), 1=alta (≥70%)
    lluvia      : int  0=poca, 1=moderada, 2=intensa

    Retorna
    -------
    dict con claves:
        'riesgo_bajo' : float  probabilidad de riesgo bajo
        'riesgo_alto' : float  probabilidad de riesgo alto
        'nivel'       : str    'BAJO' o 'ALTO' (umbral 0.5)
    """
    evidencia = {
        "Temperatura": temperatura,
        "Humedad":     humedad,
        "Lluvia":      lluvia,
    }
    resultado = _inference.query(
        variables=["RiesgoRoya"],
        evidence=evidencia,
        show_progress=False,
    )
    probs = resultado.values  # array [P(bajo), P(alto)]
    return {
        "riesgo_bajo": float(probs[0]),
        "riesgo_alto": float(probs[1]),
        "nivel":       "ALTO" if probs[1] >= 0.5 else "BAJO",
    }


def get_yield_forecast(temperatura: int, humedad: int, lluvia: int) -> dict:
    """
    Estima la distribución de rendimiento esperado dadas las condiciones climáticas.

    Retorna
    -------
    dict con claves:
        'rendimiento_bajo'  : float
        'rendimiento_medio' : float
        'rendimiento_alto'  : float
        'nivel_esperado'    : str  'BAJO', 'MEDIO' o 'ALTO' (argmax)
    """
    evidencia = {
        "Temperatura": temperatura,
        "Humedad":     humedad,
        "Lluvia":      lluvia,
    }
    resultado = _inference.query(
        variables=["RendimientoEsperado"],
        evidence=evidencia,
        show_progress=False,
    )
    probs = resultado.values  # array [P(bajo), P(medio), P(alto)]
    niveles = ["BAJO", "MEDIO", "ALTO"]
    return {
        "rendimiento_bajo":   float(probs[0]),
        "rendimiento_medio":  float(probs[1]),
        "rendimiento_alto":   float(probs[2]),
        "nivel_esperado":     niveles[int(probs.argmax())],
    }
