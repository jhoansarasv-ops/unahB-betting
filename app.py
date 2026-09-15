import streamlit as st
import sqlite3
import pandas as pd
import random
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh

# ==========================================
# CONFIGURACIÓN
# ==========================================
st.set_page_config(page_title="UNAH Betting", page_icon="⚽", layout="wide")
st_autorefresh(interval=15000, key="autorefresh")

DB_PATH = "unah_bets.db"

# ⏰ FECHA Y HORA DEL PARTIDO (cámbiala cuando quieras)
FECHA_PARTIDO = datetime(2026, 9, 15, 20, 30)  # 15/09/2026 20:30

# ==========================================
# ESTILOS
# ==========================================
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #1a0505 0%, #2d0808 100%);
        color: #f5e6c8;
    }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #3d0808 0%, #1a0505 100%);
        border-right: 2px solid #d4af37;
    }
    h1, h2, h3, h4 { color: #d4af37 !important; }
    .match-card {
        background: linear-gradient(135deg, #4a0e0e 0%, #2d0808 100%);
        border: 1px solid #d4af37;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 4px 15px rgba(212, 175, 55, 0.2);
    }
    .match-title {
        color: #f5e6c8;
        font-size: 18px;
        font-weight: bold;
        margin-bottom: 10px;
        border-bottom: 1px solid #d4af37;
        padding-bottom: 8px;
    }
    .odd-box {
        background: linear-gradient(135deg, #6b1010 0%, #4a0e0e 100%);
        border: 1px solid #d4af37;
        border-radius: 8px;
        padding: 12px;
        text-align: center;
        color: #f5e6c8;
    }
    .odd-label {
        font-size: 12px;
        color: #d4af37;
        text-transform: uppercase;
        font-weight: bold;
    }
    .odd-value {
        font-size: 22px;
        font-weight: bold;
        color: #ffd700;
        margin-top: 5px;
    }
    .cupon-box {
        background: linear-gradient(135deg, #3d0808 0%, #1a0505 100%);
        border: 2px solid #d4af37;
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 8px;
    }
    .countdown {
        background: linear-gradient(135deg, #d4af37 0%, #b8860b 100%);
        color: #1a0505;
        padding: 12px;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        font-size: 16px;
        margin: 10px 0;
    }
    .stButton > button {
        background: linear-gradient(135deg, #d4af37 0%, #b8860b 100%);
        color: #1a0505;
        font-weight: bold;
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        width: 100%;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #ffd700 0%, #d4af37 100%);
        color: #000;
    }
    div[data-testid="stMetricValue"] { color: #ffd700 !important; }
    .user-balance {
        background: linear-gradient(135deg, #d4af37 0%, #b8860b 100%);
        color: #1a0505;
        padding: 8px 15px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
    }
    .player-card {
        background: linear-gradient(135deg, #4a0e0e 0%, #2d0808 100%);
        border: 1px solid #d4af37;
        border-radius: 8px;
        padding: 10px;
        text-align: center;
        margin-bottom: 8px;
    }
    .player-name {
        color: #ffd700;
        font-weight: bold;
        font-size: 15px;
        margin-bottom: 5px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 5px;
        background-color: #2d0808;
        padding: 5px;
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #4a0e0e;
        color: #f5e6c8;
        border-radius: 8px;
        padding: 8px 15px;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #d4af37 0%, #b8860b 100%) !important;
        color: #1a0505 !important;
        font-weight: bold;
    }
    .vs-box {
        text-align: center;
        font-size: 22px;
        font-weight: bold;
        color: #d4af37;
        padding: 15px 0;
    }
    .team-name {
        font-size: 20px;
        font-weight: bold;
        color: #ffd700;
    }
    .team-label {
        font-size: 12px;
        color: #d4af37;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# BASE DE DATOS
# ==========================================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT UNIQUE, password TEXT, puntos REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS apuestas
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_id INTEGER, evento TEXT,
                  mercado TEXT, seleccion TEXT, cuota REAL, monto REAL, estado TEXT, fecha TEXT)''')
    conn.commit()
    conn.close()

init_db()

# ==========================================
# DATOS
# ==========================================
EQUIPO_90 = ["Frandu", "Kleyder", "Andrey", "Daniel", "Jota", "Kevin"]
EQUIPO_BAJO = ["Brayan", "Michael", "Francisco", "Urbachs", "Lucho", "Fede"]

def cuota_viva(base):
    variacion = random.uniform(-0.08, 0.08)
    return round(max(1.01, base + variacion), 2)

def tiempo_restante():
    ahora = datetime.now()
    diff = FECHA_PARTIDO - ahora
    if diff.total_seconds() < 0:
        return "🔴 PARTIDO EN VIVO"
    dias = diff.days
    horas = diff.seconds // 3600
    minutos = (diff.seconds % 3600) // 60
    if dias > 0:
        return f"⏰ Comienza en {dias}d {horas}h {minutos}m"
    elif horas > 0:
        return f"⏰ Comienza en {horas}h {minutos}m"
    else:
        return f"⏰ Comienza en {minutos} minutos"

# ==========================================
# SESSION STATE
# ==========================================
for key, default in [('usuario_id', None), ('usuario_nombre', None),
                     ('puntos', 0), ('cupon', [])]:
    if key not in st.session_state:
        st.session_state[key] = default

# ==========================================
# SIDEBAR
# ==========================================
st.sidebar.markdown("# ⚽ UNAH BETTING")
st.sidebar.markdown("---")

if st.session_state.usuario_id:
    st.sidebar.markdown(f"""
    <div class="user-balance">
        👤 {st.session_state.usuario_nombre}<br>
        💰 {st.session_state.puntos:.0f} pts
    </div>
    """, unsafe_allow_html=True)
    st.sidebar.markdown("---")
    menu = ["🏠 Inicio", "🎯 Apuestas", "📋 Mis Apuestas", "🚪 Cerrar Sesión"]
else:
    menu = ["🏠 Inicio", "📝 Registrarse", "🔑 Iniciar Sesión"]

choice = st.sidebar.selectbox("Menú", menu)
st.sidebar.markdown("---")
st.sidebar.caption(f"🕐 {datetime.now().strftime('%H:%M:%S')}")

# ==========================================
# FUNCIONES
# ==========================================
def añadir_al_cupon(mercado, seleccion, cuota, evento="Equipo 90 vs Equipo Bajo"):
    st.session_state.cupon.append({
        "evento": evento, "mercado": mercado,
        "seleccion": seleccion, "cuota": cuota, "monto": 50
    })
    st.toast(f"✅ Añadido: {seleccion} @ {cuota}")

def limpiar_cupon():
    st.session_state.cupon = []

def realizar_apuestas():
    if not st.session_state.cupon:
        st.warning("El cupón está vacío.")
        return
    total = sum(c.get("monto", 0) for c in st.session_state.cupon)
    if total > st.session_state.puntos:
        st.error("Saldo insuficiente.")
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for ap in st.session_state.cupon:
        c.execute("""INSERT INTO apuestas (usuario_id, evento, mercado, seleccion, cuota, monto, estado, fecha)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                  (st.session_state.usuario_id, ap["evento"], ap["mercado"],
                   ap["seleccion"], ap["cuota"], ap["monto"], "Pendiente",
                   datetime.now().strftime("%Y-%m-%d %H:%M")))
    nuevo = st.session_state.puntos - total
    c.execute("UPDATE usuarios SET puntos=? WHERE id=?", (nuevo, st.session_state.usuario_id))
    conn.commit()
    conn.close()
    st.session_state.puntos = nuevo
    limpiar_cupon()
    st.success(f"✅ Apuestas realizadas ({total:.0f} pts)")
    st.rerun()

# ==========================================
# INICIO
# ==========================================
if choice == "🏠 Inicio":
    st.markdown("# ⚽ Bienvenido a UNAH Betting")
    st.markdown("### 🏆 Retos Estudiantiles - Apuestas con Puntos")

    col1, col2, col3 = st.columns(3)
    col1.metric("Partidos", "1")
    col2.metric("Jugadores", "12")
    col3.metric("Mercados", "8")

    st.markdown("---")
    st.info("🎁 Regístrate y obtén **1000 puntos** gratis.")

    st.markdown("### 🔥 Partido destacado")

    # Tarjeta VS
    st.markdown(f"""
    <div class="match-card">
        <div class="match-title">⚽ Reto UNAH - Partido Oficial</div>
        <div style="display: flex; justify-content: space-around; align-items: center; margin: 15px 0;">
            <div style="text-align: center;">
                <div class="team-label">EQUIPO 90</div>
                <div class="team-name">🟡 Equipo 90</div>
                <div style="color: #d4af37; font-size: 12px;">Frandu · Kleyder · Andrey<br>Daniel · Jota · Kevin</div>
            </div>
            <div class="vs-box">VS</div>
            <div style="text-align: center;">
                <div class="team-label">EQUIPO BAJO</div>
                <div class="team-name">🔴 Equipo Bajo</div>
                <div style="color: #d4af37; font-size: 12px;">Brayan · Michael · Francisco<br>Urbachs · Lucho · Fede</div>
            </div>
        </div>
        <div class="countdown">{tiempo_restante()}</div>
        <p style="text-align: center; color: #d4af37; margin: 5px 0;">
            📅 {FECHA_PARTIDO.strftime('%d/%m/%Y · %H:%M')}
        </p>
        <div style="display: flex; gap: 8px; margin-top: 10px;">
            <div class="odd-box" style="flex: 1;">
                <div class="odd-label">Gana Equipo 90</div>
                <div class="odd-value">{cuota_viva(1.85)}</div>
            </div>
            <div class="odd-box" style="flex: 1;">
                <div class="odd-label">Empate</div>
                <div class="odd-value">{cuota_viva(3.20)}</div>
            </div>
            <div class="odd-box" style="flex: 1;">
                <div class="odd-label">Gana Equipo Bajo</div>
                <div class="odd-value">{cuota_viva(2.10)}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# REGISTRO
# ==========================================
elif choice == "📝 Registrarse":
    st.markdown("# 📝 Crear Cuenta")
    st.markdown("🎁 Recibe **1000 puntos** al registrarte.")
    with st.form("registro"):
        u = st.text_input("Nombre de usuario")
        p = st.text_input("Contraseña", type="password")
        p2 = st.text_input("Confirmar contraseña", type="password")
        if st.form_submit_button("✅ Registrarme"):
            if not u or not p:
                st.error("Completa los campos.")
            elif p != p2:
                st.error("Las contraseñas no coinciden.")
            else:
                try:
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    c.execute("INSERT INTO usuarios (nombre, password, puntos) VALUES (?, ?, ?)", (u, p, 1000))
                    conn.commit()
                    conn.close()
                    st.success(f"¡Bienvenido {u}! Ya puedes iniciar sesión.")
                except sqlite3.IntegrityError:
                    st.error("Ese usuario ya existe.")

# ==========================================
# LOGIN
# ==========================================
elif choice == "🔑 Iniciar Sesión":
    st.markdown("# 🔑 Iniciar Sesión")
    with st.form("login"):
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        if st.form_submit_button("Entrar"):
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT id, nombre, puntos FROM usuarios WHERE nombre=? AND password=?", (u, p))
            r = c.fetchone()
            conn.close()
            if r:
                st.session_state.usuario_id = r[0]
                st.session_state.usuario_nombre = r[1]
                st.session_state.puntos = r[2]
                st.rerun()
            else:
                st.error("Credenciales incorrectas.")

# ==========================================
# APUESTAS
# ==========================================
elif choice == "🎯 Apuestas":
    if not st.session_state.usuario_id:
        st.warning("Inicia sesión para apostar.")
    else:
        col_izq, col_der = st.columns([2.2, 1])

        # ---------------- COLUMNA IZQUIERDA ----------------
        with col_izq:
            st.markdown("## 🎯 Apuestas en Vivo")
            st.caption(f"🔄 Actualización automática · 💰 Saldo: {st.session_state.puntos:.0f} pts")

            # Tarjeta del partido con countdown
            st.markdown(f"""
            <div class="match-card">
                <div class="match-title">⚽ Equipo 90 vs Equipo Bajo</div>
                <div class="countdown">{tiempo_restante()} · 📅 {FECHA_PARTIDO.strftime('%d/%m/%Y %H:%M')}</div>
            </div>
            """, unsafe_allow_html=True)

            # ------------ PESTAÑAS DE MERCADOS ------------
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "🏆 Ganador", "📊 Goles", "⚽ Jugadores", "🎯 Tiros", "🔢 Marcador"
            ])

            # ===== TAB 1: GANADOR =====
            with tab1:
                st.markdown("### 🏆 Ganador del Partido")
                c90, cE, cB = cuota_viva(1.85), cuota_viva(3.20), cuota_viva(2.10)
                col1, col2, col3 = st.columns(3)
                if col1.button(f"1️⃣ Equipo 90\n\n{c90}", key="btn_90", use_container_width=True):
                    añadir_al_cupon("Ganador", "Equipo 90", c90)
                if col2.button(f"⚖️ Empate\n\n{cE}", key="btn_E", use_container_width=True):
                    añadir_al_cupon("Ganador", "Empate", cE)
                if col3.button(f"2️⃣ Equipo Bajo\n\n{cB}", key="btn_B", use_container_width=True):
                    añadir_al_cupon("Ganador", "Equipo Bajo", cB)

                st.markdown("---")
                st.markdown("### 🎯 Ambos Equipos Anotan")
                c_si, c_no = cuota_viva(1.75), cuota_viva(2.05)
                col1, col2 = st.columns(2)
                if col1.button(f"✅ Sí ({c_si})", key="bts_si", use_container_width=True):
                    añadir_al_cupon("Ambos Anotan", "Sí", c_si)
                if col2.button(f"❌ No ({c_no})", key="bts_no", use_container_width=True):
                    añadir_al_cupon("Ambos Anotan", "No", c_no)

                st.markdown("---")
                st.markdown("### 🥇 Primer Goleador")
                primer = st.selectbox("Selecciona jugador:",
                    ["-- Elegir --"] + EQUIPO_90 + EQUIPO_BAJO, key="pg")
                if primer != "-- Elegir --":
                    cuota_pg = cuota_viva(4.50)
                    st.info(f"Cuota actual: **{cuota_pg}**")
                    if st.button(f"➕ Añadir {primer} como primer goleador", key="add_pg"):
                        añadir_al_cupon("Primer Goleador", primer, cuota_pg)

            # ===== TAB 2: GOLES =====
            with tab2:
                st.markdown("### 📊 Total de Goles")
                c_o25, c_u25 = cuota_viva(1.90), cuota_viva(1.95)
                c_o35, c_u35 = cuota_viva(2.60), cuota_viva(1.50)

                st.markdown("**Over/Under 2.5 goles**")
                col1, col2 = st.columns(2)
                if col1.button(f"⬆️ Más de 2.5 ({c_o25})", key="o25", use_container_width=True):
                    añadir_al_cupon("Total Goles", "Over 2.5", c_o25)
                if col2.button(f"⬇️ Menos de 2.5 ({c_u25})", key="u25", use_container_width=True):
                    añadir_al_cupon("Total Goles", "Under 2.5", c_u25)

                st.markdown("**Over/Under 3.5 goles**")
                col1, col2 = st.columns(2)
                if col1.button(f"⬆️ Más de 3.5 ({c_o35})", key="o35", use_container_width=True):
                    añadir_al_cupon("Total Goles", "Over 3.5", c_o35)
                if col2.button(f"⬇️ Menos de 3.5 ({c_u35})", key="u35", use_container_width=True):
                    añadir_al_cupon("Total Goles", "Under 3.5", c_u35)

            # ===== TAB 3: JUGADORES (GOLES) =====
            with tab3:
                st.markdown("### ⚽ Goles por Jugador")
                eq = st.radio("Equipo:", ["Equipo 90", "Equipo Bajo"], horizontal=True, key="eq_goles")
                jugs = EQUIPO_90 if eq == "Equipo 90" else EQUIPO_BAJO

                for jug in jugs:
                    c_j = cuota_viva(2.5 + random.uniform(0, 2))
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**{jug}** anota en cualquier momento")
                    with col2:
                        if st.button(f"{c_j}", key=f"gol_{jug}", use_container_width=True):
                            añadir_al_cupon(f"Gol de {eq}", jug, c_j)

            # ===== TAB 4: TIROS AL ARCO =====
            with tab4:
                st.markdown("### 🎯 Tiros al Arco por Jugador")
                eq_t = st.radio("Equipo:", ["Equipo 90", "Equipo Bajo"], horizontal=True, key="eq_tiros")
                jugs_t = EQUIPO_90 if eq_t == "Equipo 90" else EQUIPO_BAJO

                for jug in jugs_t:
                    c_t = cuota_viva(1.5 + random.uniform(0, 1.5))
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**{jug}** realiza tiro al arco")
                    with col2:
                        if st.button(f"{c_t}", key=f"tiro_{jug}", use_container_width=True):
                            añadir_al_cupon(f"Tiro al arco de {eq_t}", jug, c_t)

            # ===== TAB 5: MARCADOR EXACTO =====
            with tab5:
                st.markdown("### 🔢 Marcador Exacto")
                marcadores = {
                    "1-0": 6.50, "2-0": 9.00, "2-1": 8.00, "3-0": 15.00,
                    "0-0": 8.50, "1-1": 6.00, "0-1": 7.00, "0-2": 11.00,
                    "1-2": 9.50, "2-2": 12.00, "3-1": 14.00, "3-2": 20.00,
                }

                cols = st.columns(4)
                for i, (marc, base) in enumerate(marcadores.items()):
                    c_m = cuota_viva(base)
                    with cols[i % 4]:
                        if st.button(f"{marc}\n\n{c_m}", key=f"marc_{marc}", use_container_width=True):
                            añadir_al_cupon("Marcador Exacto", marc, c_m)

        # ---------------- COLUMNA DERECHA ----------------
        with col_der:
            st.markdown("### 🎟️ Cupón")
            if not st.session_state.cupon:
                st.info("Cupón vacío. Haz clic en las cuotas.")
            else:
                total = 0
                for i, ap in enumerate(st.session_state.cupon):
                    st.markdown(f"""
                    <div class="cupon-box">
                        <small style="color: #d4af37;">{ap['mercado'].upper()}</small><br>
                        <b style="color: #ffd700;">{ap['seleccion']}</b><br>
                        <span>Cuota: {ap['cuota']}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    monto = st.number_input(
                        f"Monto #{i+1}", min_value=10, value=ap.get("monto", 50),
                        step=10, key=f"monto_{i}"
                    )
                    st.session_state.cupon[i]["monto"] = monto
                    total += monto

                st.metric("Total a apostar", f"{total:.0f} pts")
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("✅ Apostar", key="btn_apostar"):
                        realizar_apuestas()
                with col_b:
                    if st.button("🗑️ Limpiar", key="btn_limpiar"):
                        limpiar_cupon()
                        st.rerun()

# ==========================================
# MIS APUESTAS
# ==========================================
elif choice == "📋 Mis Apuestas":
    st.markdown("# 📋 Historial")
    if not st.session_state.usuario_id:
        st.warning("Inicia sesión primero.")
    else:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(
            f"SELECT fecha, evento, mercado, seleccion, cuota, monto, estado FROM apuestas WHERE usuario_id={st.session_state.usuario_id} ORDER BY id DESC",
            conn)
        conn.close()
        if df.empty:
            st.info("Sin apuestas aún.")
        else:
            st.dataframe(df, use_container_width=True)
            st.metric("Total apostado", f"{df['monto'].sum():.0f} pts")

# ==========================================
# CERRAR SESIÓN
# ==========================================
elif choice == "🚪 Cerrar Sesión":
    st.session_state.usuario_id = None
    st.session_state.usuario_nombre = None
    st.session_state.puntos = 0
    limpiar_cupon()
    st.rerun()
