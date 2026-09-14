import streamlit as st
import sqlite3
import pandas as pd

# ==========================================
# CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(page_title="UNAH Betting", page_icon="⚽", layout="wide")

# ==========================================
# BASE DE DATOS
# ==========================================
DB_PATH = "unah_bets.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT UNIQUE, password TEXT, puntos REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS apuestas
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_id INTEGER, evento TEXT,
                  seleccion TEXT, cuota REAL, monto REAL, estado TEXT)''')
    conn.commit()
    conn.close()

init_db()

# ==========================================
# LÓGICA DE CUOTAS
# ==========================================
def calcular_cuota_dinamica(probabilidad_base, monto_total, monto_opcion):
    cuota_base = 1 / probabilidad_base
    if monto_total > 0:
        factor = 1 - (monto_opcion / monto_total) * 0.5
    else:
        factor = 1
    return max(1.01, round(cuota_base * factor, 2))

# ==========================================
# SESSION STATE
# ==========================================
if 'usuario_id' not in st.session_state:
    st.session_state.usuario_id = None
if 'usuario_nombre' not in st.session_state:
    st.session_state.usuario_nombre = None
if 'puntos' not in st.session_state:
    st.session_state.puntos = 0

# ==========================================
# MENÚ LATERAL
# ==========================================
st.sidebar.title("⚽ UNAH Betting")
st.sidebar.markdown("---")

if st.session_state.usuario_id:
    st.sidebar.success(f"👤 {st.session_state.usuario_nombre}")
    st.sidebar.info(f"💰 Puntos: {st.session_state.puntos:.0f}")
    menu = ["Inicio", "Apuestas", "Mis Apuestas", "Cerrar Sesión"]
else:
    menu = ["Inicio", "Registrarse", "Iniciar Sesión"]

choice = st.sidebar.selectbox("Menú", menu)

# ==========================================
# INICIO
# ==========================================
if choice == "Inicio":
    st.title("⚽ Plataforma de Apuestas UNAH")
    st.markdown("### Retos Estudiantiles - Apuestas con Puntos")
    st.markdown("""
    Bienvenido a la plataforma oficial de apuestas de la UNAH.

    **¿Cómo funciona?**
    - 🎁 Al registrarte recibes **1000 puntos** gratis.
    - 🎯 Apuesta a tu equipo o jugador favorito.
    - 📈 Las cuotas cambian según la probabilidad.
    - 🏆 Si aciertas, ganas puntos según la cuota.
    """)

    st.markdown("---")
    st.subheader("🏆 Partidos disponibles")
    col1, col2 = st.columns(2)
    with col1:
        st.info("**Equipo 90 vs Equipo Bajo**\n\n📅 Próximo partido")
    with col2:
        st.info("**Goleadores del Torneo**\n\n⚽ Brandon, Brayan, Michael")

# ==========================================
# REGISTRO
# ==========================================
elif choice == "Registrarse":
    st.title("📝 Crear Cuenta")
    st.markdown("Regístrate y recibe **1000 puntos** gratis.")

    with st.form("registro"):
        nuevo_user = st.text_input("Nombre de usuario")
        nuevo_pass = st.text_input("Contraseña", type="password")
        confirmar = st.text_input("Confirmar contraseña", type="password")
        submit = st.form_submit_button("Registrarme")

        if submit:
            if not nuevo_user or not nuevo_pass:
                st.error("Completa todos los campos.")
            elif nuevo_pass != confirmar:
                st.error("Las contraseñas no coinciden.")
            else:
                try:
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    c.execute("INSERT INTO usuarios (nombre, password, puntos) VALUES (?, ?, ?)",
                              (nuevo_user, nuevo_pass, 1000))
                    conn.commit()
                    conn.close()
                    st.success(f"¡Bienvenido {nuevo_user}! Tienes 1000 puntos.")
                except sqlite3.IntegrityError:
                    st.error("Ese usuario ya existe.")

# ==========================================
# LOGIN
# ==========================================
elif choice == "Iniciar Sesión":
    st.title("🔑 Iniciar Sesión")

    with st.form("login"):
        user = st.text_input("Usuario")
        passw = st.text_input("Contraseña", type="password")
        submit = st.form_submit_button("Entrar")

        if submit:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT id, nombre, puntos FROM usuarios WHERE nombre=? AND password=?",
                      (user, passw))
            resultado = c.fetchone()
            conn.close()

            if resultado:
                st.session_state.usuario_id = resultado[0]
                st.session_state.usuario_nombre = resultado[1]
                st.session_state.puntos = resultado[2]
                st.success(f"¡Bienvenido {resultado[1]}!")
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")

# ==========================================
# APUESTAS
# ==========================================
elif choice == "Apuestas":
    st.title(f"🎯 Apuestas - {st.session_state.usuario_nombre}")

    partido = "Equipo 90 vs Equipo Bajo"
    st.subheader(f"🏆 {partido}")

    monto_total = 1500
    cuota_90 = calcular_cuota_dinamica(0.45, monto_total, 700)
    cuota_empate = calcular_cuota_dinamica(0.25, monto_total, 300)
    cuota_bajo = calcular_cuota_dinamica(0.30, monto_total, 500)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Gana Equipo 90", f"{cuota_90}")
    with col2:
        st.metric("Empate", f"{cuota_empate}")
    with col3:
        st.metric("Gana Equipo Bajo", f"{cuota_bajo}")

    st.markdown("---")

    seleccion = st.radio("Selecciona tu apuesta:",
                         [f"Gana Equipo 90 (x{cuota_90})",
                          f"Empate (x{cuota_empate})",
                          f"Gana Equipo Bajo (x{cuota_bajo})"])

    monto = st.number_input("Monto a apostar:", min_value=10, value=100, step=10)
    cuota_sel = cuota_90 if "Equipo 90" in seleccion else (cuota_empate if "Empate" in seleccion else cuota_bajo)
    ganancia = monto * cuota_sel
    st.info(f"💡 Si aciertas, ganarías **{ganancia:.2f} puntos**")

    if st.button("✅ Realizar Apuesta", type="primary"):
        if st.session_state.puntos < monto:
            st.error("No tienes suficientes puntos.")
        else:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            nuevo_saldo = st.session_state.puntos - monto
            c.execute("UPDATE usuarios SET puntos=? WHERE id=?",
                      (nuevo_saldo, st.session_state.usuario_id))
            c.execute("""INSERT INTO apuestas (usuario_id, evento, seleccion, cuota, monto, estado)
                         VALUES (?, ?, ?, ?, ?, ?)""",
                      (st.session_state.usuario_id, partido, seleccion, cuota_sel, monto, "Pendiente"))
            conn.commit()
            conn.close()
            st.session_state.puntos = nuevo_saldo
            st.success("¡Apuesta realizada!")
            st.rerun()

    st.markdown("---")
    st.subheader("⚽ Goleadores del partido")

    jugadores = {
        "Brandon (Equipo 90)": 2.50,
        "Brayan (Equipo Bajo)": 3.00,
        "Michael (Equipo Bajo)": 3.75,
        "Kevin (Equipo 90)": 4.00,
        "Franco (Equipo 90)": 5.00,
    }
    jugador_sel = st.selectbox("¿Quién anota gol?", list(jugadores.keys()))
    cuota_jugador = jugadores[jugador_sel]
    monto_gol = st.number_input("Monto:", min_value=10, value=50, step=10, key="monto_gol")
    st.info(f"💡 Si {jugador_sel} anota, ganas **{monto_gol * cuota_jugador:.2f} puntos**")

    if st.button("⚽ Apostar a goleador"):
        if st.session_state.puntos < monto_gol:
            st.error("Puntos insuficientes.")
        else:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            nuevo_saldo = st.session_state.puntos - monto_gol
            c.execute("UPDATE usuarios SET puntos=? WHERE id=?",
                      (nuevo_saldo, st.session_state.usuario_id))
            c.execute("""INSERT INTO apuestas (usuario_id, evento, seleccion, cuota, monto, estado)
                         VALUES (?, ?, ?, ?, ?, ?)""",
                      (st.session_state.usuario_id, f"Gol de {jugador_sel}", "Sí", cuota_jugador, monto_gol, "Pendiente"))
            conn.commit()
            conn.close()
            st.session_state.puntos = nuevo_saldo
            st.success("¡Apuesta a goleador realizada!")
            st.rerun()

# ==========================================
# MIS APUESTAS
# ==========================================
elif choice == "Mis Apuestas":
    st.title("📋 Historial de Apuestas")
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        f"SELECT evento, seleccion, cuota, monto, estado FROM apuestas WHERE usuario_id={st.session_state.usuario_id} ORDER BY id DESC",
        conn)
    conn.close()

    if df.empty:
        st.info("Aún no has realizado apuestas.")
    else:
        st.dataframe(df, use_container_width=True)
        st.metric("Total apostado", f"{df['monto'].sum():.0f} puntos")

# ==========================================
# CERRAR SESIÓN
# ==========================================
elif choice == "Cerrar Sesión":
    st.session_state.usuario_id = None
    st.session_state.usuario_nombre = None
    st.session_state.puntos = 0
    st.success("Sesión cerrada.")
    st.rerun()
