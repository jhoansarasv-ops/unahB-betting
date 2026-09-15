import streamlit as st
import sqlite3
import pandas as pd
import random
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# ==========================================
# CONFIGURACIÓN
# ==========================================
st.set_page_config(page_title="UNAH Betting", page_icon="⚽", layout="wide")

# Auto-refresh cada 15 segundos para "tiempo real"
st_autorefresh(interval=15000, key="autorefresh")

DB_PATH = "unah_bets.db"

# ==========================================
# ESTILOS - VINO ROJIZO Y DORADO
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
    .odds-row {
        display: flex;
        gap: 8px;
        margin-top: 10px;
    }
    .odd-box {
        flex: 1;
        background: linear-gradient(135deg, #6b1010 0%, #4a0e0e 100%);
        border: 1px solid #d4af37;
        border-radius: 8px;
        padding: 8px;
        text-align: center;
        color: #f5e6c8;
    }
    .odd-label {
        font-size: 11px;
        color: #d4af37;
        text-transform: uppercase;
    }
    .odd-value {
        font-size: 20px;
        font-weight: bold;
        color: #ffd700;
    }
    .cupon-box {
        background: linear-gradient(135deg, #3d0808 0%, #1a0505 100%);
        border: 2px solid #d4af37;
        border-radius: 12px;
        padding: 15px;
        position: sticky;
        top: 20px;
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
    }
    .stMetric {
        background: rgba(74, 14, 14, 0.5);
        border-radius: 8px;
        padding: 10px;
        border: 1px solid #d4af37;
    }
    div[data-testid="stMetricValue"] {
        color: #ffd700 !important;
    }
    .user-balance {
        background: linear-gradient(135deg, #d4af37 0%, #b8860b 100%);
        color: #1a0505;
        padding: 8px 15px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
    }
    .stRadio label, .stSelectbox label, .stNumberInput label {
        color: #f5e6c8 !important;
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
# DATOS DE JUGADORES
# ==========================================
EQUIPO_90 = ["Frandu", "Kleyder", "Andrey", "Daniel", "Jota", "Kevin"]
EQUIPO_BAJO = ["Brayan", "Michael", "Francisco", "Urbachs", "Lucho", "Fede"]

# Cuotas base (varían ligeramente en cada refresh para simular "tiempo real")
def cuota_viva(base):
    variacion = random.uniform(-0.08, 0.08)
    return round(max(1.01, base + variacion), 2)

# ==========================================
# SESSION STATE
# ==========================================
if 'usuario_id' not in st.session_state:
    st.session_state.usuario_id = None
if 'usuario_nombre' not in st.session_state:
    st.session_state.usuario_nombre = None
if 'puntos' not in st.session_state:
    st.session_state.puntos = 0
if 'cupon' not in st.session_state:
    st.session_state.cupon = []

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
st.sidebar.caption(f"🕐 Actualizado: {datetime.now().strftime('%H:%M:%S')}")

# ==========================================
# FUNCIONES AUXILIARES
# ==========================================
def añadir_al_cupon(mercado, seleccion, cuota, evento="Equipo 90 vs Equipo Bajo"):
    st.session_state.cupon.append({
        "evento": evento,
        "mercado": mercado,
        "seleccion": seleccion,
        "cuota": cuota
    })
    st.toast(f"✅ Añadido: {seleccion} @ {cuota}")

def limpiar_cupon():
    st.session_state.cupon = []

def realizar_apuestas():
    if not st.session_state.cupon:
        st.warning("El cupón está vacío.")
        return
    total_monto = sum(c.get("monto", 0) for c in st.session_state.cupon)
    if total_monto <= 0:
        st.warning("Asigna un monto a cada apuesta.")
        return
    if total_monto > st.session_state.puntos:
        st.error("No tienes suficientes puntos.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for ap in st.session_state.cupon:
        c.execute("""INSERT INTO apuestas (usuario_id, evento, mercado, seleccion, cuota, monto, estado, fecha)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                  (st.session_state.usuario_id, ap["evento"], ap["mercado"],
                   ap["seleccion"], ap["cuota"], ap["monto"], "Pendiente",
                   datetime.now().strftime("%Y-%m-%d %H:%M")))
    nuevo_saldo = st.session_state.puntos - total_monto
    c.execute("UPDATE usuarios SET puntos=? WHERE id=?", (nuevo_saldo, st.session_state.usuario_id))
    conn.commit()
    conn.close()
    st.session_state.puntos = nuevo_saldo
    limpiar_cupon()
    st.success(f"✅ Apuestas realizadas: {total_monto:.0f} pts")
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
    st.info("🎁 Regístrate y obtén **1000 puntos** gratis. Apuesta en tiempo real con cuotas dinámicas.")
    
    st.markdown("### 🔥 Partido destacado")
    st.markdown(f"""
    <div class="match-card">
        <div class="match-title">⚽ Equipo 90 vs Equipo Bajo</div>
        <p style="color: #d4af37;">📅 Próximo partido - Retos UNAH</p>
        <div class="odds-row">
            <div class="odd-box">
                <div class="odd-label">Gana Equipo 90</div>
                <div class="odd-value">{cuota_viva(1.85)}</div>
            </div>
            <div class="odd-box">
                <div class="odd-label">Empate</div>
                <div class="odd-value">{cuota_viva(3.20)}</div>
            </div>
            <div class="odd-box">
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
                st.success(f"¡Bienvenido {r[1]}!")
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
        
        # ---------- COLUMNA IZQUIERDA: PARTIDOS ----------
        with col_izq:
            st.markdown(f"## 🎯 Apuestas en Vivo")
            st.caption(f"🔄 Actualización automática cada 15s · 💰 Saldo: {st.session_state.puntos:.0f} pts")
            
            # --- MERCADO 1X2 ---
            st.markdown(f"""
            <div class="match-card">
                <div class="match-title">⚽ Equipo 90 vs Equipo Bajo · GANADOR</div>
            </div>
            """, unsafe_allow_html=True)
            
            c90 = cuota_viva(1.85)
            cE = cuota_viva(3.20)
            cB = cuota_viva(2.10)
            
            col1, col2, col3 = st.columns(3)
            if col1.button(f"1️⃣ Equipo 90\n\n{c90}", key="btn_90", use_container_width=True):
                añadir_al_cupon("Ganador", "Equipo 90", c90)
            if col2.button(f"⚖️ Empate\n\n{cE}", key="btn_E", use_container_width=True):
                añadir_al_cupon("Ganador", "Empate", cE)
            if col3.button(f"2️⃣ Equipo Bajo\n\n{cB}", key="btn_B", use_container_width=True):
                añadir_al_cupon("Ganador", "Equipo Bajo", cB)
            
            st.markdown("---")
            
            # --- OVER/UNDER GOLES ---
            st.markdown("### 📊 Total de Goles (Over/Under)")
            c_o25 = cuota_viva(1.90)
            c_u25 = cuota_viva(1.95)
            c_o35 = cuota_viva(2.60)
            c_u35 = cuota_viva(1.50)
            
            col1, col2 = st.columns(2)
            if col1.button(f"⬆️ Más de 2.5 goles ({c_o25})", key="o25", use_container_width=True):
                añadir_al_cupon("Total Goles", "Over 2.5", c_o25)
            if col2.button(f"⬇️ Menos de 2.5 goles ({c_u25})", key="u25", use_container_width=True):
                añadir_al_cupon("Total Goles", "Under 2.5", c_u25)
            
            col1, col2 = st.columns(2)
            if col1.button(f"⬆️ Más de 3.5 goles ({c_o35})", key="o35", use_container_width=True):
                añadir_al_cupon("Total Goles", "Over 3.5", c_o35)
            if col2.button(f"⬇️ Menos de 3.5 goles ({c_u35})", key="u35", use_container_width=True):
                añadir_al_cupon("Total Goles", "Under 3.5", c_u35)
            
            st.markdown("---")
            
            # --- AMBOS ANOTAN ---
            st.markdown("### 🎯 Ambos Equipos Anotan")
            c_si = cuota_viva(1.75)
            c_no = cuota_viva(2.05)
            col1, col2 = st.columns(2)
            if col1.button(f"✅ Sí ({c_si})", key="bts_si", use_container_width=True):
                añadir_al_cupon("Ambos Anotan", "Sí", c_si)
            if col2.button(f"❌ No ({c_no})", key="bts_no", use_container_width=True):
                añadir_al_cupon("Ambos Anotan", "No", c_no)
            
            st.markdown("---")
            
            # --- PRIMER GOLEADOR ---
            st.markdown("### 🥇 Primer Goleador")
            primer_goleador = st.selectbox("Selecciona jugador:",
                ["-- Elegir --"] + EQUIPO_90 + EQUIPO_BAJO, key="pg")
            if primer_goleador != "-- Elegir --":
                cuota_pg = cuota_viva(4.50)
                if st.button(f"➕ Añadir {primer_goleador} como primer goleador ({cuota_pg})", key="add_pg"):
                    añadir_al_cupon("Primer Goleador", primer_goleador, cuota_pg)
            
            st.markdown("---")
            
            # --- GOLEADORES INDIVIDUALES ---
            st.markdown("### ⚽ Goles por Jugador (Anota en cualquier momento)")
            equipo_sel = st.radio("Equipo:", ["Equipo 90", "Equipo Bajo"], horizontal=True, key="eq_goles")
            jugadores_equipo = EQUIPO_90 if equipo_sel == "Equipo 90" else EQUIPO_BAJO
            
            cols = st.columns(3)
            for i, jug in enumerate(jugadores_equipo):
                base = 2.5 + random.uniform(0, 2)
                cuota_j = cuota_viva(base)
                with cols[i % 3]:
                    if st.button(f"⚽ {jug}\n\n{cuota_j}", key=f"gol_{jug}", use_container_width=True):
                        añadir_al_cupon(f"Gol de {equipo_sel}", jug, cuota_j)
            
            st.markdown("---")
            
            # --- TIROS AL ARCO ---
            st.markdown("### 🎯 Tiros al Arco por Jugador")
            equipo_tiros = st.radio("Equipo:", ["Equipo 90", "Equipo Bajo"], horizontal=True, key="eq_tiros")
            jugadores_tiros = EQUIPO_90 if equipo_tiros == "Equipo 90" else EQUIPO_BAJO
            
            cols = st.columns(3)
            for i, jug in enumerate(jugadores_tiros):
                base = 1.5 + random.uniform(0, 1.5)
                cuota_t = cuota_viva(base)
                with cols[i % 3]:
                    if st.button(f"🎯 {jug}\n\n{cuota_t}", key=f"tiro_{jug}", use_container_width=True):
                        añadir_al_cupon(f"Tiro al arco de {equipo_tiros}", jug, cuota_t)
            
            st.markdown("---")
            
            # --- MARCADOR EXACTO ---
            st.markdown("### 🔢 Marcador Exacto")
            marcadores = {
                "1-0": 6.50, "2-0": 9.00, "2-1": 8.00, "3-0": 15.00,
                "0-0": 8.50, "1-1": 6.00, "0-1": 7.00, "0-2": 11.00,
                "1-2": 9.50, "2-2": 12.00, "3-1": 14.00, "3-2": 20.00,
            }
            marcador_sel = st.selectbox("Elige marcador:", ["-- Elegir --"] + list(marcadores.keys()), key="marc")
            if marcador_sel != "-- Elegir --":
                cuota_m = cuota_viva(marcadores[marcador_sel])
                if st.button(f"➕ Apostar al {marcador_sel} ({cuota_m})", key="add_marc"):
                    añadir_al_cupon("Marcador Exacto", marcador_sel, cuota_m)
        
        # ---------- COLUMNA DERECHA: CUPÓN ----------
        with col_der:
            st.markdown("### 🎟️ Cupón de Apuestas")
            
            if not st.session_state.cupon:
                st.info("Tu cupón está vacío. Haz clic en las cuotas para añadir apuestas.")
            else:
                total_cuota = 1
                for i, ap in enumerate(st.session_state.cupon):
                    st.markdown(f"""
                    <div class="cupon-box" style="margin-bottom: 8px;">
                        <small style="color: #d4af37;">{ap['mercado'].upper()}</small><br>
                        <b>{ap['seleccion']}</b><br>
                        <span style="color: #ffd700;">Cuota: {ap['cuota']}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    monto_ap = st.number_input(
                        f"Monto para '{ap['seleccion']}'",
                        min_value=10, value=50, step=10,
                        key=f"monto_{i}"
                    )
                    st.session_state.cupon[i]["monto"] = monto_ap
                
                total_monto = sum(c.get("monto", 0) for c in st.session_state.cupon)
                
                st.markdown("---")
                st.metric("Total a apostar", f"{total_monto:.0f} pts")
                
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
    st.markdown("# 📋 Historial de Apuestas")
    if not st.session_state.usuario_id:
        st.warning("Inicia sesión primero.")
    else:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(
            f"SELECT fecha, evento, mercado, seleccion, cuota, monto, estado FROM apuestas WHERE usuario_id={st.session_state.usuario_id} ORDER BY id DESC",
            conn)
        conn.close()
        if df.empty:
            st.info("Aún no has realizado apuestas.")
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
    st.success("Sesión cerrada.")
    st.rerun()
