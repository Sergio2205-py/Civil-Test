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
    
    ####### Cálculos generales #############

    # Cálculo del factor beta1
    if fc <= 280:
        beta1 = 0.85
    elif fc <= 560:
        beta1 = round(1.05 - 0.714 * (fc / 1000), 3)
    else:
        beta1 = 0.65

    # Cálculo de la deformación inicial del concreto comprimido
    E0 = round(Ecu * (1 - beta1), 5)

    ### 1.1 Cálculo de acero minimo############

    d = h - r

    aceroMinimo = 0.7 * ((math.sqrt(fc)) / (fy)) * b * d

    ###1.2 Acero balanceado y acero máximo
    aceroBalanceado = (
        b * d * (0.85 * beta1 * fc / fy) * ((Ecu) / (Ecu + fy / Es))
    )
    aceroMaximo = 0.75 * aceroBalanceado

    if  acero < aceroBalanceado:
        ###1.3 Calculo de a, c y Mn

        ### Asumiendo que el acero fluye (se debe verificar)
        T = acero * fy
        a = T / (0.85 * fc * b)
        c = a / beta1
        Mn = T * (d - a / 2) / (1000 * 100)
        phiMn = phiFlexion * Mn

    else:
        A = (0.85 * fc) / (Ecu * Es * (acero / (b * d)))
        B = d
        C = -beta1 * d * d

        a = (
            -B
            + math.sqrt(B * B - 4 * A * C)
        ) / (2 * A)

        c = a / beta1

        Mn = (0.85 * fc * a * b * (d - a / 2) / (1000 * 100)
        )
        phiMn = phiFlexion * Mn   

    if round(acero,2) < round(aceroBalanceado,2):
        tipoFalla = "Tracción"
    elif round(acero,2) > round(aceroBalanceado,2):
        tipoFalla = "Compresión"
    else:
        tipoFalla = "Balanceada"
        
    defAs = Ecu * (d-c)/c
    
    
    resultado = {}
    resultado["aceroMinimo"] = f'{round(aceroMinimo, 2)} cm^2'
    resultado["aceroBalanceado"] = f'{round(aceroBalanceado, 2)} cm^2'
    resultado["aceroMaximo"] = f'{round(aceroMaximo, 2)} cm^2'
    resultado["a"] = f'{round(a, 2)} cm'
    resultado["c"] = f'{round(c, 2)} cm'
    resultado["Mn"] = f'{round(Mn, 2)} ton-m'
    resultado["phiMn"] = f'{round(phiMn, 2)} ton-m'
    resultado["tipoFalla"] = tipoFalla
    resultado["defAs"] = f'{round(defAs, 5)}'
    resultado["c_value"] = c

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
    Cálculo de viga a flexión DOBLE
    """

    # Parámetros del concreto
    if fc <= 280:
        beta1 = 0.85
    elif fc <= 560:
        beta1 = round(1.05 - 0.714 * (fc / 1000), 3)
    else:
        beta1 = 0.65

    d_trac = h - r_trac
    d_comp = r_comp

    # Iteración para encontrar c
    c = 0.1 * h
    tol = 1e-3
    max_iter = 100

    for _ in range(max_iter):
        a = beta1 * c
        eps_s = Ecu * (d_trac - c) / c
        eps_sp = Ecu * (c - d_comp) / c

        fs = fy if eps_s >= fy / Es else Es * eps_s
        fs_p = min(Es * eps_sp, fy)

        T = As_trac * fs
        Cc = 0.85 * fc * b * a
        Cs = As_comp * fs_p

        error = T - (Cc + Cs)

        if abs(error) < tol:
            break

        c += error / (0.85 * fc * b)
        c = max(c, tol)

    # Momento nominal
    Mn = (Cc * (d_trac - a / 2) + Cs * (d_trac - d_comp)) / (1000 * 100)
    phiMn = phiFlexion * Mn

    # Tipo de falla
    if eps_s >= 0.005:
        tipoFalla = "Tracción"
    else:
        tipoFalla = "Compresión"

    # Aceros de referencia
    As_min = 0.25 * (fc ** 0.5) / fy * b * d_trac
    eps_y = fy / 2000000
    c_bal = (0.003 / (0.003 + eps_y)) * d_trac
    a_bal = beta1 * c_bal
    As_bal = 0.85 * fc * b * a_bal / fy
    As_max = 0.75 * As_bal

    # Retorno como diccionario (compatible con appweb.py)
    resultado = {
        "aceroMinimo": f"{As_min:.2f} cm²",
        "aceroBalanceado": f"{As_bal:.2f} cm²",
        "aceroMaximo": f"{As_max:.2f} cm²",
        "a": f"{a:.2f} cm",
        "c": f"{c:.2f} cm",
        "phiMn": f"{phiMn:.2f} ton-m",
        "defAs": f"{eps_s:.5f}",
        "tipoFalla": tipoFalla
    }

    return resultado