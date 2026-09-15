import streamlit as st

st.title("🔧 Prueba de diagnóstico")

menu = st.sidebar.selectbox("Menú", ["Inicio", "Registrarse", "Iniciar Sesión"])
st.write(f"✅ El código SE ACTUALIZÓ. Elegiste: **{menu}**")

if menu == "Registrarse":
    st.success("¡Aquí funcionaría el registro!")
elif menu == "Iniciar Sesión":
    st.info("¡Aquí funcionaría el login!")
