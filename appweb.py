import streamlit as st
import viga
import matplotlib.pyplot as plt
import plotly.graph_objects as go

# ---------- FUNCIONES AUXILIARES ----------
def diametro_cm(diametro_str):
    area = viga.tablaAceros.loc[
        viga.tablaAceros["Diametro"] == diametro_str,
        "Área(cm2)"
    ].values[0]
    return (4 * area / 3.1416) ** 0.5

st.markdown("""
<style>
body {
    background-color: #0e1117;
}
.card {
    background-color: #1c1f26;
    padding: 10px;
    border-radius: 10px;
    margin-bottom: 12px;
    border-left: 4px solid #1f77b4;
}
.card-title {
    font-size: 17px;
    font-weight: 600; 
    color: #c7d0db;
}
.card-value {
    font-size: 22px;
    font-weight: bold;
    color: white;
}
</style>
""", unsafe_allow_html=True)

# ---------- TITULO PRINCIPAL ----------
st.markdown("""
<h1 style='color:#4da3ff; margin-bottom: 0;'>CÁLCULO DE VIGAS DE CONCRETO ARMADO A FLEXIÓN SIMPLE</h1>
""", unsafe_allow_html=True)

# ---------- SIDEBAR ----------
with st.sidebar:

    st.title("Propiedades Geométricas")
    b = st.number_input("Base (cm)", value=30.0)
    h = st.number_input("Altura (cm)", value=50.0)
    
    r_1capa = st.number_input(
    "Recubrimiento (1 capa)",
    value=6.0,
    help="Caso típico: d = h - 6 cm"
    )

    r_2capas = st.number_input(
    "Recubrimiento (2 capas)",
    value=8.0,
    help="Caso típico Ø 3/4'': d = h - 8 cm"
    )

    st.title("Propiedades de los materiales")
    fc = st.number_input("$f'c \ (kg/cm^2)$", value=210.0)
    fy = st.number_input("$f_y \ (kg/cm^2)$", value=4200.0)
    Es = st.number_input("$E_s \ (kg/cm^2)$", value=2000000.0)
    ecu = st.number_input(
        "$\\varepsilon_{c \\mu}$",
        value=0.003,
        step=0.001,
        format="%.3f"
    )
    phiFlexion = st.number_input("$\\phi_{flexión}$", value=0.9)

    st.title("Solicitación")
    Mu = st.number_input(
        "Momento último Mu (ton·m)",
        value=50.0,
        min_value=0.0,
        help="Momento flector último actuante en la sección"
    )


    st.title("Disposición del acero")
    num_capas = st.radio(
    "Número de capas de acero",
    options=[1, 2],
    horizontal=True
    )

    if num_capas == 1:
        r = r_1capa
    else:
        r = r_2capas

# ---------- ACERO SUPERIOR (COMPRESIÓN / NEGATIVO) ----------
st.markdown(
    "<h4 style='margin-bottom:-30px;'>🔼 Acero superior (compresión)</h4>",
    unsafe_allow_html=True
)

col1s, col2s, col3s, col4s, col5s, col6s, col7s, col8s = st.columns(
    [1, 2, 0.7, 1, 2, 0.7, 1, 2]
)

numero1s = col1s.number_input("", value=0, min_value=0, key="numero1s")
diametro1s = col2s.selectbox("", viga.tablaAceros["Diametro"], index=8, key="diametro1s")
col3s.markdown("# +")

numero2s = col4s.number_input("", value=0, min_value=0, key="numero2s")
diametro2s = col5s.selectbox("", viga.tablaAceros["Diametro"], key="diametro2s")
col6s.markdown("# +")

numero3s = col7s.number_input("", value=0, min_value=0, key="numero3s")
diametro3s = col8s.selectbox("", viga.tablaAceros["Diametro"], key="diametro3s")

# Área de acero en compresión
As_comp = (
    viga.areaAs(numero1s, diametro1s)
    + viga.areaAs(numero2s, diametro2s)
    + viga.areaAs(numero3s, diametro3s)
)
As_comp = round(As_comp, 2)

if As_comp > 0:
    tipoFlexion = "doble"
else:
    tipoFlexion = "simple"


# ---------- ACERO INFERIOR (TRACCIÓN / POSITIVO) ----------
st.markdown(
    "<h4 style='margin-bottom:-30px; margin-top:-30px;'>🔽 Acero inferior (tracción)</h4>",
    unsafe_allow_html=True
)

col1, col2, col3, col4, col5, col6, col7, col8 = st.columns(
    [1, 2, 0.7, 1, 2, 0.7, 1, 2]
)

numero1 = col1.number_input("", value=1, min_value=0, key="numero1")
diametro1 = col2.selectbox("", viga.tablaAceros["Diametro"], index=8, key="diametro1")
col3.markdown("# +")

numero2 = col4.number_input("", value=0, min_value=0, key="numero2")
diametro2 = col5.selectbox("", viga.tablaAceros["Diametro"], key="diametro2")
col6.markdown("# +")

numero3 = col7.number_input("", value=0, min_value=0, key="numero3")
diametro3 = col8.selectbox("", viga.tablaAceros["Diametro"], key="diametro3")

# Área de acero a tracción
As_trac = (
    viga.areaAs(numero1, diametro1)
    + viga.areaAs(numero2, diametro2)
    + viga.areaAs(numero3, diametro3)
)
As_trac = round(As_trac, 2)

# ---------- GRUPOS DE ACERO INFERIOR (para ancho mínimo) ----------
grupos_acero = []

if numero1 > 0:
    grupos_acero.append((numero1, diametro1))

if numero2 > 0:
    grupos_acero.append((numero2, diametro2))

if numero3 > 0:
    grupos_acero.append((numero3, diametro3))

b_min, n_barras = viga.ancho_minimo_acero(
    grupos_acero,
    recubrimiento=4.0,
    diam_estribo=1.0,
    sep_min_aci=2.54
)

st.markdown("### 📐 Resumen de áreas de acero")

colA, colB = st.columns(2)

with colA:
    st.metric("As tracción (cm²)", As_trac)

with colB:
    st.metric("As compresión (cm²)", As_comp)

hay_acero_compresion = As_comp > 0

# ---------- DISEÑO POR MOMENTO ÚLTIMO ----------
As_req = None
a_req = None

# ---------- CÁLCULO DE FLEXIÓN ----------
if tipoFlexion == "simple":

    calculoViga = viga.calculoFlexion(
        b=b,
        h=h,
        fc=fc,
        fy=fy,
        Es=Es,
        Ecu=ecu,
        phiFlexion=phiFlexion,
        acero=As_trac,
        r=r
    )

else:
    calculoViga = viga.calculoFlexionDoble(
        b=b,
        h=h,
        fc=fc,
        fy=fy,
        Es=Es,
        Ecu=ecu,
        phiFlexion=phiFlexion,
        As_trac=As_trac,
        As_comp=As_comp,
        r_trac=r,
        r_comp=r
    )

# ---------- ACERO REQUERIDO POR Mu ----------
As_req = None
a_req = None

if tipoFlexion == "simple":
    As_req, a_req = viga.acero_requerido_flexion_simple_formula(
        b=b,
        h=h,
        r=r,
        fc=fc,
        fy=fy,
        phi=phiFlexion,
        Mu=Mu
    )

# ------------------ GRÁFICO DE SECCIÓN ------------------
def graficoSeccion(b, h, r):

    seccion_x = [0, b, b, 0, 0]
    seccion_y = [0, 0, h, h, 0]

    fig, ax = plt.subplots(figsize=(4, 7))
    ax.plot(seccion_x, seccion_y, color='black', linewidth=2)

    # Bloque de compresión (concreto)
    c = float(calculoViga["c"].replace("cm", "").strip())
    ax.fill_between([0, b], h - c, h, color='gray', alpha=0.4)

    # ---------------- ACERO INFERIOR ----------------
    alto_barra = 3
    ancho_barra = b - 2*r

    ax.fill_between([r, r + ancho_barra], r, r + alto_barra, color='black')
    ax.text(
        b / 2,
        r + alto_barra + 1,
        f'$A_s={As_trac} \\, cm^2$',
        ha='center',
        color='red'
    )

    # ---------------- ACERO SUPERIOR ----------------
    if As_comp > 0:
        y_sup = h - r - alto_barra

        ax.fill_between(
            [r, r + ancho_barra],
            y_sup,
            y_sup + alto_barra,
            color='blue'
        )

        ax.text(
            b / 2,
            y_sup - 2,
            f"$A'_s={As_comp} \\, cm^2$",
            ha='center',
            color='blue'
        )

    ax.set_aspect("equal")
    ax.axis("off")

    return fig

# ---------- FUNCIÓN CARD ----------
def card(titulo, valor):
    st.markdown(f"""
    <div class="card">
        <div class="card-title">{titulo}</div>
        <div class="card-value">{valor}</div>
    </div>
    """, unsafe_allow_html=True)
# ---------- DIBUJO ----------
st.pyplot(graficoSeccion(b, h, r), use_container_width=True)

# ---------- CARD ANCHO MÍNIMO ----------
card("Ancho mínimo requerido", f"{round(b_min,2)} cm")

if b < b_min:
    st.warning("⚠️ El ancho de la viga NO permite acomodar el acero en una sola capa")
else:
    st.success("✅ El acero cabe en una sola capa")

st.divider()
st.divider()
st.subheader("🧮 Diseño por momento último")

phiMn = calculoViga["phiMn_val"]

# ---------------- CARD PRINCIPAL ----------------
card("Momento solicitado Mu", f"{Mu:.2f} ton·m")
card("Resistencia φMn", f"{phiMn:.2f} ton·m")

if phiMn >= Mu:
    st.success("✅ La sección resiste el momento solicitado")
else:
    st.error("❌ La sección NO resiste el momento solicitado")

# -------------------------------------------------
# SOLO FLEXIÓN SIMPLE
# -------------------------------------------------
if tipoFlexion == "simple" and As_req is not None:

    card("As requerido", f"{As_req:.2f} cm²")
    card("As instalado", f"{As_trac:.2f} cm²")

    ratio = As_trac / As_req

    card("% acero colocado", f"{ratio*100:.1f}%")

    if ratio >= 1.00:
        st.success("✅ El acero colocado cumple totalmente")

    elif ratio >= 0.90:
        st.warning("⚠️ Dentro del margen permitido")

    else:
        st.error("❌ Acero insuficiente")

    # NUEVO CONTROL Asmax
    As_max = calculoViga["aceroMaximo_val"]

    card("As máximo permitido", f"{As_max:.2f} cm²")

    if As_trac > As_max:
        st.error("❌ Supera As máximo")
    else:
        st.success("✅ No supera As máximo")

# ---------------- TIPO DE FALLA ----------------
color_falla = "#2ecc71" if calculoViga["tipoFalla"] == "Tracción" else "#e74c3c"
icono = "✔️" if calculoViga["tipoFalla"] == "Tracción" else "⚠️"

st.markdown(f"""
<h3 style="color:{color_falla};">
{icono} Tipo de falla: {calculoViga['tipoFalla']}
</h3>
""", unsafe_allow_html=True)

# ---------------- RESULTADOS ----------------
colA, colB = st.columns(2)

with colA:
    card("As mínimo", calculoViga["aceroMinimo"])
    card("As balanceado", calculoViga["aceroBalanceado"])
    card("As máximo", calculoViga["aceroMaximo"])
    card("a", calculoViga["a"])
    card("cb", calculoViga["cb"])

with colB:
    card("c", calculoViga["c"])
    card("ØMn", calculoViga["phiMn"])
    card("εs", calculoViga["defAs"])

# ---------- INDICADOR c / cb ----------
c_real = calculoViga["c_val"]
cb = calculoViga["cb_val"]

relacion = c_real / cb

st.markdown("### 📊 Estado de ductilidad")

# limitar barra visual a 100%
valor_barra = min(relacion, 1.0)

st.progress(valor_barra)

st.markdown(f"**Relación c / cb = {relacion:.2f}**")

if As_trac > calculoViga["aceroMaximo_val"]:
    st.error("❌ Acero instalado supera As máximo permitido")

elif relacion < 0.75:
    st.success("✅ Sección dúctil (subreforzada)")

elif relacion <= 1.0:
    st.warning("⚠️ Cercana al estado balanceado")

else:
    st.error("❌ Sección sobrerreforzada")


# ---------- DETALLE DE CÁLCULOS ----------
with st.expander("📐 Ver cálculos"):

    st.markdown("### 🔹 Parámetros del concreto")

    st.latex(r"""
    \beta_1 =
    \begin{cases}
    0.85 & f'_c \le 280 \\
    1.05 - 0.714 \frac{f'_c}{1000} & 280 < f'_c \le 560 \\
    0.65 & f'_c > 560
    \end{cases}
    """)

    st.markdown(f"**β₁ = {calculoViga['beta1']}**")

    st.divider()

    st.markdown("### 🔹 Peralte efectivo (As tracción)")

    st.latex(r"d = h - r")
    st.markdown(
        f"d = {h} − {r} = **{calculoViga['d']:.2f} cm**"
    )

    st.divider()

    st.markdown("### 🔹 Acero mínimo (As tracción)")

    st.latex(r"""
    A_{s,min} = 0.7 \frac{\sqrt{f'_c}}{f_y} b d
    """)

    st.markdown("### 🔹 Acero balanceado (As tracción)")

    if tipoFlexion == "simple":

        st.latex(r"""
        A_{s,bal} =
        b d \left(\frac{0.85 \beta_1 f'_c}{f_y}\right)
        \left(\frac{\varepsilon_{cu}}
        {\varepsilon_{cu}+f_y/E_s}\right)
        """)

    else:

        st.latex(r"""
        A_{s,bal} f_y =
        0.85 f'_c b a_{bal}
        + A'_s f'_s
        """)

    st.markdown(
        f"Aₛ,bal = **{calculoViga['aceroBalanceado_val']:.2f} cm²**"
    )

    st.divider()

    st.markdown("### 🔹 Compresión del concreto")

    st.latex(r"""
    C_c = 0.85 \, f'_c \, b \, a
    """)

    st.markdown(
        f"Cc = **{calculoViga['Cc_val']:.2f} tonf**"
    )

    st.divider()

    st.markdown("### 🔹 Momento nominal")

    st.latex(r"""
    M_n = T(d - a/2) \quad \text{o} \quad
    M_n = C_c(d - a/2) + C_s(d - d')
    """)

    st.markdown(
        f"Mₙ = **{calculoViga['Mn_val']:.2f} ton·m**"
    )

    st.divider()

    st.markdown("### 🔹 Eje neutro balanceado")

    st.latex(r"""
    c_b =
    d\left(
    \frac{\varepsilon_{cu}}
    {\varepsilon_{cu}+\varepsilon_y}
    \right)
    """)

    st.markdown(
        f"c_b = **{calculoViga['cb_val']:.2f} cm**"
    )

# ------------------ GRÁFICO ESFUERZO-DEFORMACIÓN DEL ACERO A TRACCIÓN ------------------
def graficoDeformacionAcero(defAs, fy, Es):

    eps_y = fy / Es
    defAs = float(defAs)

    fs = Es * defAs if defAs < eps_y else fy

    # Límite superior automático del eje de deformaciones
    eps_max = max(defAs, eps_y) * 1.15  # 15% extra de margen visual                          

    x = [0, eps_y, eps_max]
    y = [0, fy, fy]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, mode='lines', name='Modelo bilineal'))
    fig.add_trace(go.Scatter(
        x=[defAs],
        y=[fs],
        mode='markers',
        name='Estado del acero',
        marker=dict(color='red', size=10)
    ))
    # ---- Línea vertical ε = 0.005 (límite ductilidad E.060) ----
    fig.add_vline(
        x=0.005,
        line_width=2,
        line_dash="dash",
        line_color="gray",
        annotation_text="(Límite dúctil E.060)",
        annotation_position="top"
        )

    fig.update_layout(
        title="Gráfico Deformación del acero a tracción",
        xaxis_title="Deformación unitaria εs",
        yaxis_title="Esfuerzo fs (kg/cm²)"
    )

    return fig

st.plotly_chart(graficoDeformacionAcero(calculoViga["defAs"], fy, Es))
