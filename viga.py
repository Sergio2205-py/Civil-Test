import math
import pandas as pd

def calculoFlexion(
    b,
    h,
    fc,
    fy,
    Es,
    Ecu,
    phiFlexion,
    acero,
    r
):
    # Cálculo del factor beta1
    if fc <= 280:
        beta1 = 0.85
    elif fc <= 560:
        beta1 = round(1.05 - 0.714 * (fc / 1000), 3)
    else:
        beta1 = 0.65

    d = h - r

    aceroMinimo = 0.7 * ((math.sqrt(fc)) / fy) * b * d
    aceroBalanceado = (
        b * d * (0.85 * beta1 * fc / fy) * (Ecu / (Ecu + fy / Es))
    )
    aceroMaximo = 0.75 * aceroBalanceado

    if acero < aceroBalanceado:
        # Caso: acero fluye
        T = acero * fy
        a = T / (0.85 * fc * b)
        c = a / beta1
        Mn = T * (d - a / 2) / (1000 * 100)
        phiMn = phiFlexion * Mn
        Cc = (0.85 * fc * b * a)/10**3   # <-- ahora también defines Cc aquí
    else:
        # Caso: acero no fluye
        A = (0.85 * fc) / (Ecu * Es * (acero / (b * d)))
        B = d
        C = -beta1 * d * d

        a = (-B + math.sqrt(B * B - 4 * A * C)) / (2 * A)
        c = a / beta1
        Mn = (0.85 * fc * a * b * (d - a / 2)) / (1000 * 100)
        phiMn = phiFlexion * Mn
        Cc = (0.85 * fc * b * a)/10**3    # ya estaba aquí

    # Tipo de falla
    if round(acero, 2) < round(aceroBalanceado, 2):
        tipoFalla = "Tracción"
    elif round(acero, 2) > round(aceroBalanceado, 2):
        tipoFalla = "Compresión"
    else:
        tipoFalla = "Balanceada"

    defAs = round(Ecu * (d - c) / c, 6)

    resultado = {
        "beta1": beta1,
        "d": d,
        "aceroMinimo_val": aceroMinimo,
        "aceroBalanceado_val": aceroBalanceado,
        "aceroMaximo_val": aceroMaximo,
        "a_val": a,
        "c_val": c,
        "Mn_val": Mn,
        "phiMn_val": phiMn,
        "defAs": defAs,
        "Cc_val": Cc,
        "aceroMinimo": f"{aceroMinimo:.2f} cm²",
        "aceroBalanceado": f"{aceroBalanceado:.2f} cm²",
        "aceroMaximo": f"{aceroMaximo:.2f} cm²",
        "a": f"{a:.2f} cm",
        "c": f"{c:.2f} cm",
        "Mn": f"{Mn:.2f} ton·m",
        "phiMn": f"{phiMn:.2f} ton·m",
        "tipoFalla": tipoFalla,
        "Cc": f"{Cc:.2f} kgf"
    }

    return resultado



tablaAceros = pd.DataFrame(
    {
        "Diametro": [
            "6mm",
            '1/4"',
            "8mm",
            '3/8"',
            "12mm",
            '1/2"',
            '5/8"',
            '3/4"',
            '1"',
            '1 3/8"',
        ],
        "Área(cm2)": [0.28, 0.32, 0.5, 0.71, 1.13, 1.29, 2, 2.84, 5.1, 10.06],
    }
)
#tablaAceros = tablaAceros.set_index("Diametro")

def areaAs (numero, diametro):
    return numero * tablaAceros.loc[tablaAceros['Diametro'] == diametro, "Área(cm2)"].values[0] 


def ancho_minimo_acero(
    grupos_acero,
    recubrimiento=4.0,
    diam_estribo=1.0,
    sep_min_aci=2.54
):
    """
    Calcula el ancho mínimo necesario para alojar el acero en una capa
    grupos_acero: lista de tuplas (n_barras, diametro_str)
    """

    diametros_cm = []

    for n, diametro_str in grupos_acero:
        if n == 0:
            continue

        area = tablaAceros.loc[
            tablaAceros["Diametro"] == diametro_str,
            "Área(cm2)"
        ].values[0]

        db_cm = (4 * area / 3.1416) ** 0.5
        diametros_cm.append((n, db_cm))

    if not diametros_cm:
        return 0.0, 0

    # Ancho ocupado por barras
    ancho_barras = sum(n * db for n, db in diametros_cm)

    # Separaciones entre barras
    n_total = sum(n for n, _ in diametros_cm)
    ancho_separaciones = (n_total - 1) * sep_min_aci

    # Ancho total requerido
    b_min = (
        ancho_barras
        + ancho_separaciones
        + 2 * recubrimiento
        + 2 * diam_estribo
    )

    return round(b_min, 2), n_total


def calculoFlexionDoble(
    b,
    h,
    fc,
    fy,
    Es,
    Ecu,
    phiFlexion,
    As_trac,
    As_comp,
    r_trac,
    r_comp
):
    """
    Flexión DOBLE: acero inferior (tracción) que fluye y acero superior (compresión) que NO fluye.
    Se resuelve c con una cuadrática derivada del equilibrio de fuerzas.
    """

    # Parámetros del concreto
    if fc <= 280:
        beta1 = 0.85
    elif fc <= 560:
        beta1 = round(1.05 - 0.714 * (fc / 1000), 3)
    else:
        beta1 = 0.65

    # Peraltes efectivos
    d_trac = h - r_trac   # acero inferior
    d_comp = r_comp       # acero superior (d')

    # Coeficientes de la cuadrática en c
    A = 0.85 * fc * beta1 * b
    B = As_comp * Es * Ecu - As_trac * fy
    C = -As_comp * Es * Ecu * d_comp

    # Solución de c (usar la raíz positiva)
    discriminante = B**2 - 4 * A * C
    c = (-B + math.sqrt(discriminante)) / (2 * A)

    # Derivados
    a = beta1 * c
    eps_s = Ecu * (d_trac - c) / c           # deformación acero tracción
    eps_sp = Ecu * (c - d_comp) / c          # deformación acero compresión

    # Esfuerzos del acero
    fs = min(Es * eps_s, fy)
    fs_p = min(Es * eps_sp, fy)

    # Fuerzas
    T = As_trac * fs
    Cc = 0.85 * fc * b * a
    Cs = As_comp * fs_p

    # Momento nominal
    Mn = (Cc * (d_trac - a / 2) + Cs * (d_trac - d_comp)) / (1000 * 100)
    phiMn = phiFlexion * Mn

    # Tipo de falla (criterio por εs)
    tipoFalla = "Tracción" if eps_s >= 0.005 else "Compresión"

    # Aceros de referencia
    As_min = 0.7 * (fc ** 0.5) / fy * b * d_trac
    eps_y = fy / Es
    c_bal = (Ecu / (Ecu + eps_y)) * d_trac
    a_bal = beta1 * c_bal
    As_bal = 0.85 * fc * b * a_bal / fy
    As_max = 0.75 * As_bal

    resultado = {
        "beta1": beta1,
        "d": d_trac,
        "aceroMinimo_val": As_min,
        "aceroBalanceado_val": As_bal,
        "aceroMaximo_val": As_max,
        "a_val": a,
        "c_val": c,
        "phiMn_val": phiMn,
        "defAs": round(eps_s, 5),
        "Cc_val": Cc/10**3,
        "Mn_val": Mn,
        "aceroMinimo": f"{As_min:.2f} cm²",
        "aceroBalanceado": f"{As_bal:.2f} cm²",
        "aceroMaximo": f"{As_max:.2f} cm²",
        "a": f"{a:.2f} cm",
        "c": f"{c:.2f} cm",
        "phiMn": f"{phiMn:.2f} ton·m",
        "tipoFalla": tipoFalla
    }

    return resultado
