"""
Definición del Proceso de Decisión de Markov para la granja cafetalera guatemalteca.
Estados: condiciones de la granja, clima, enfermedades
Acciones: fertilizar, fungicida, podar, cosechar_temprano, replantar
Transiciones: probabilidades calibradas con conocimiento del dominio cafetalero
              (fuentes: FAO Guatemala coffee resilience data, USDA FAS Coffee Annual)
"""

from itertools import product

ACCIONES = ["fertilizar", "fungicida", "podar", "cosechar_temprano", "replantar"]

# Rangos de cada dimensión del estado:
# salud_cultivo : 0=malo, 1=regular, 2=bueno
# presupuesto   : 0=bajo, 1=medio, 2=alto
# temporada     : 0=seca, 1=lluvia
# riesgo_roya   : 0=bajo, 1=alto

RANGO_SALUD      = [0, 1, 2]
RANGO_PRESUPUESTO = [0, 1, 2]
RANGO_TEMPORADA  = [0, 1]
RANGO_RIESGO     = [0, 1]

def todos_los_estados():
    """Producto cartesiano de todos los estados posibles."""
    return list(product(RANGO_SALUD, RANGO_PRESUPUESTO, RANGO_TEMPORADA, RANGO_RIESGO))


def recompensa(estado, accion):
    """
    Recompensa inmediata R(s, a) en quetzales por hectárea.
    """
    salud, presupuesto, temporada, riesgo = estado

    costos = {
        "fertilizar":      -200,
        "fungicida":       -150,
        "podar":           -100,
        "cosechar_temprano": -50,
        "replantar":       -500,
    }

    ganancia_base = salud * 800          # Q/ha según salud actual
    penalizacion_roya = -600 if riesgo == 1 and accion != "fungicida" else 0
    # Penalizar acciones costosas cuando no hay presupuesto
    penalizacion_sin_presupuesto = -100 if presupuesto == 0 and costos[accion] < -100 else 0

    return ganancia_base + costos[accion] + penalizacion_roya + penalizacion_sin_presupuesto


def _clamp(valor, minimo, maximo):
    """Ajusta un valor dentro del rango válido."""
    return max(minimo, min(maximo, valor))


def transicion(estado, accion):
    """
    Retorna una lista de (probabilidad, estado_siguiente).
    Las probabilidades suman exactamente 1.0.

    Reglas de diseño basadas en el dominio cafetalero:
    - Hemileia vastatrix prospera en temporada de lluvia (temporada=1):
      probabilidad espontánea de contagio 0.4 si riesgo_roya=0.
    - Fungicida reduce riesgo de roya con alta efectividad (~85%).
    - Fertilizar mejora salud del cultivo con probabilidad moderada (~60%).
    - Podar mejora salud gradualmente (~40%) y reduce riesgo de roya (~20%).
    - Replantar reinicia salud a 0 (costo inmediato); en siguiente estado
      la salud puede subir a 1 con prob 0.5 (plántula se establece).
    - Cosechar_temprano con roya reduce levemente el riesgo (se elimina
      tejido infectado) pero reduce salud futura.
    - Sin presupuesto: acciones costosas no producen mejora en salud.
    """
    salud, presupuesto, temporada, riesgo = estado

    # ---- Evolución de temporada: ciclo determinista seca↔lluvia ----
    # La temporada alterna cada ciclo (simplificación: determinista)
    nueva_temporada = 1 - temporada  # 0→1, 1→0

    # ---- Probabilidad de contagio espontáneo de roya ----
    # Fuente: en Guatemala, Hemileia vastatrix tiene mayor incidencia
    # en meses lluviosos (mayo-octubre). Prob. de infección ~40% si
    # las condiciones son favorables y no se aplicó fungicida.
    prob_contagio_espontaneo = 0.40 if temporada == 1 else 0.10

    # Helper: construir distribución sobre (salud, riesgo) finales
    # y combinar con la temporada determinista.
    resultados = []  # lista de (prob, (salud_f, presupuesto_f, temp_f, riesgo_f))

    if accion == "fertilizar":
        # --- FERTILIZAR ---
        # Mejora salud con prob 0.60 si hay presupuesto; 0.0 si no hay.
        # No afecta directamente el riesgo de roya.
        # Fuente: fertilización nitrogenada mejora vigor del cafeto (FAO 2015).
        if presupuesto == 0:
            # Sin presupuesto: ningún efecto positivo en salud
            p_sube_salud = 0.0
        else:
            p_sube_salud = 0.60

        salud_mas = _clamp(salud + 1, 0, 2)
        salud_igual = salud

        # Riesgo: evolución natural por temporada
        riesgo_nuevo_si_hay   = 1  # contagio ocurre
        riesgo_nuevo_si_no_hay = riesgo  # se mantiene

        for p_sal, s_f in [(p_sube_salud, salud_mas), (1 - p_sube_salud, salud_igual)]:
            for p_ryg, r_f in [(prob_contagio_espontaneo, riesgo_nuevo_si_hay),
                               (1 - prob_contagio_espontaneo, riesgo_nuevo_si_no_hay)]:
                if riesgo == 1:
                    # Si ya hay riesgo, no puede empeorar (ya está en 1)
                    r_final = 1
                    p_ryg_final = 1.0 if r_f == 1 else 0.0
                else:
                    r_final = r_f
                    p_ryg_final = p_ryg
                resultados.append((p_sal * p_ryg_final, (s_f, presupuesto, nueva_temporada, r_final)))

    elif accion == "fungicida":
        # --- FUNGICIDA ---
        # Alta efectividad para reducir riesgo: 85% de éxito si riesgo=1.
        # Si riesgo=0, lo mantiene bajo (prevención) con prob 0.95.
        # No afecta salud directamente.
        # Fuente: fungicidas cúpricos usados en Guatemala reducen Hemileia
        # en 70-90% (USDA FAS Guatemala Coffee Annual 2013).
        if riesgo == 1:
            p_baja_riesgo = 0.85
        else:
            p_baja_riesgo = 0.95  # prevención exitosa (roya no aparece)

        for p_r, r_f in [(p_baja_riesgo, 0), (1 - p_baja_riesgo, 1)]:
            resultados.append((p_r, (salud, presupuesto, nueva_temporada, r_f)))

    elif accion == "podar":
        # --- PODAR ---
        # Mejora salud gradualmente (0.40) al eliminar ramas enfermas.
        # Reduce riesgo de roya levemente (0.20) al mejorar aireación.
        # Fuente: poda mejora circulación de aire reduciendo microclima
        # favorable para Hemileia (PROMECAFE 2013).
        p_sube_salud = 0.40
        p_baja_riesgo_podar = 0.20 if riesgo == 1 else 0.0

        salud_mas = _clamp(salud + 1, 0, 2)
        for p_sal, s_f in [(p_sube_salud, salud_mas), (1 - p_sube_salud, salud)]:
            for p_r, r_f in [(p_baja_riesgo_podar, 0),
                             (1 - p_baja_riesgo_podar, riesgo)]:
                # Contagio espontáneo si riesgo ya era 0 y no bajó
                if riesgo == 0:
                    for p_con, r_con in [(prob_contagio_espontaneo, 1),
                                         (1 - prob_contagio_espontaneo, 0)]:
                        resultados.append((p_sal * p_con, (s_f, presupuesto, nueva_temporada, r_con)))
                else:
                    resultados.append((p_sal * p_r, (s_f, presupuesto, nueva_temporada, r_f)))

    elif accion == "cosechar_temprano":
        # --- COSECHAR TEMPRANO ---
        # Elimina tejido infectado: reduce riesgo con prob 0.30 si hay roya.
        # Pero reduce salud futura en 1 nivel con prob 0.50 (planta estresada).
        # Fuente: cosecha temprana como medida sanitaria (IICA 2013).
        p_baja_riesgo_cosecha = 0.30 if riesgo == 1 else 0.0
        p_baja_salud = 0.50

        salud_menos = _clamp(salud - 1, 0, 2)
        for p_sal, s_f in [(p_baja_salud, salud_menos), (1 - p_baja_salud, salud)]:
            for p_r, r_f in [(p_baja_riesgo_cosecha, 0),
                             (1 - p_baja_riesgo_cosecha, riesgo)]:
                if riesgo == 0:
                    for p_con, r_con in [(prob_contagio_espontaneo, 1),
                                         (1 - prob_contagio_espontaneo, 0)]:
                        resultados.append((p_sal * p_con, (s_f, presupuesto, nueva_temporada, r_con)))
                else:
                    resultados.append((p_sal * p_r, (s_f, presupuesto, nueva_temporada, r_f)))

    elif accion == "replantar":
        # --- REPLANTAR ---
        # Reinicia salud a 0 inmediatamente (costo de establecimiento).
        # Con prob 0.50 la plántula se establece y sube a salud=1.
        # Elimina riesgo de roya (campo nuevo): prob 0.90 de riesgo=0.
        # Fuente: replante con variedades resistentes (Catimor, Marsellesa)
        # reduce susceptibilidad a Hemileia (ANACAFE Guatemala 2014).
        p_establece = 0.50
        p_limpia_roya = 0.90

        for p_sal, s_f in [(p_establece, 1), (1 - p_establece, 0)]:
            for p_r, r_f in [(p_limpia_roya, 0), (1 - p_limpia_roya, 1)]:
                resultados.append((p_sal * p_r, (s_f, presupuesto, nueva_temporada, r_f)))

    # ---- Consolidar: sumar probabilidades de estados duplicados ----
    consolidado = {}
    for prob, estado_sig in resultados:
        if estado_sig not in consolidado:
            consolidado[estado_sig] = 0.0
        consolidado[estado_sig] += prob

    # ---- Normalizar para garantizar que la suma sea exactamente 1.0 ----
    total = sum(consolidado.values())
    return [(prob / total, est) for est, prob in consolidado.items()]