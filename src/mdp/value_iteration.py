"""
Implementación de Value Iteration para resolver el MDP de la finca cafetalera.
Algoritmo estándar: itera sobre todos los estados hasta convergencia.
"""

from src.mdp.farm_mdp import todos_los_estados, ACCIONES, recompensa, transicion


def value_iteration(mdp_estados=None, gamma=0.9, epsilon=1e-6):
    """
    Resuelve el MDP mediante Value Iteration.

    Parámetros
    ----------
    mdp_estados : list | None
        Lista de estados (tuples). Si es None se generan automáticamente.
    gamma : float
        Factor de descuento (0 < gamma < 1).
    epsilon : float
        Criterio de convergencia: máxima diferencia |V_nuevo - V_viejo|.

    Retorna
    -------
    V : dict  estado → valor esperado
    policy : dict  estado → acción óptima
    """
    estados = mdp_estados if mdp_estados is not None else todos_los_estados()

    # Inicializar función de valor en 0
    V = {s: 0.0 for s in estados}

    iteracion = 0
    while True:
        delta = 0.0
        V_nuevo = {}

        for s in estados:
            # Calcular Q(s, a) para cada acción y quedarse con el máximo
            mejor_valor = None
            for a in ACCIONES:
                q_sa = recompensa(s, a)
                for prob, s_sig in transicion(s, a):
                    q_sa += gamma * prob * V.get(s_sig, 0.0)
                if mejor_valor is None or q_sa > mejor_valor:
                    mejor_valor = q_sa

            V_nuevo[s] = mejor_valor
            delta = max(delta, abs(V_nuevo[s] - V[s]))

        V = V_nuevo
        iteracion += 1

        if iteracion % 100 == 0:
            print(f"  Iteración {iteracion:4d} — delta = {delta:.8f}")

        if delta < epsilon:
            print(f"Value Iteration convergió en {iteracion} iteraciones (delta={delta:.2e})")
            break

    policy = extract_policy(V, estados)
    return V, policy


def extract_policy(V, estados=None):
    """
    Reconstruye la política óptima π(s) = argmax_a Q(s, a)
    a partir de la función de valor V.

    Parámetros
    ----------
    V : dict  estado → valor
    estados : list | None
        Si es None se generan automáticamente.

    Retorna
    -------
    policy : dict  estado → acción óptima
    """
    if estados is None:
        estados = todos_los_estados()

    policy = {}
    for s in estados:
        mejor_accion = None
        mejor_valor = None
        for a in ACCIONES:
            q_sa = recompensa(s, a)
            for prob, s_sig in transicion(s, a):
                q_sa += 0.9 * prob * V.get(s_sig, 0.0)
            if mejor_valor is None or q_sa > mejor_valor:
                mejor_valor = q_sa
                mejor_accion = a
        policy[s] = mejor_accion

    return policy


# Mensajes explicativos en español para el agricultor
_JUSTIFICACIONES = {
    "fertilizar": (
        "Fertilizar mejora la salud del cultivo incrementando el rendimiento esperado. "
        "Recomendado cuando la planta está débil y hay presupuesto disponible."
    ),
    "fungicida": (
        "Aplicar fungicida es la acción más efectiva contra la roya del café. "
        "Reduce el riesgo de infección en ~85% y protege el rendimiento de la cosecha."
    ),
    "podar": (
        "Podar mejora la circulación de aire, reduce la humedad en el follaje "
        "y ayuda gradualmente a recuperar la salud del cultivo."
    ),
    "cosechar_temprano": (
        "Cosechar antes de tiempo elimina tejido infectado y reduce la propagación "
        "de enfermedades, aunque puede estresar la planta a corto plazo."
    ),
    "replantar": (
        "Replantar con variedades resistentes (ej. Catimor) elimina focos de roya "
        "y reinicia el ciclo productivo. Es costoso a corto plazo pero maximiza "
        "el rendimiento a largo plazo."
    ),
}


def get_action_recommendation(estado, policy):
    """
    Retorna la acción recomendada y una justificación legible para el agricultor.

    Parámetros
    ----------
    estado : tuple  (salud_cultivo, presupuesto, temporada, riesgo_roya)
    policy : dict   estado → acción óptima (resultado de value_iteration)

    Retorna
    -------
    dict con claves:
        'accion'       : str   nombre de la acción óptima
        'justificacion': str   explicación en español
        'estado'       : dict  descripción legible del estado actual
    """
    _labels_salud      = {0: "Malo", 1: "Regular", 2: "Bueno"}
    _labels_presupuesto = {0: "Bajo", 1: "Medio", 2: "Alto"}
    _labels_temporada  = {0: "Temporada seca", 1: "Temporada de lluvia"}
    _labels_riesgo     = {0: "Bajo", 1: "Alto"}

    salud, presupuesto, temporada, riesgo = estado
    accion = policy.get(estado)

    return {
        "accion": accion,
        "justificacion": _JUSTIFICACIONES.get(accion, "Acción recomendada por el sistema."),
        "estado": {
            "Salud del cultivo": _labels_salud[salud],
            "Presupuesto":       _labels_presupuesto[presupuesto],
            "Temporada":         _labels_temporada[temporada],
            "Riesgo de roya":    _labels_riesgo[riesgo],
        },
    }
