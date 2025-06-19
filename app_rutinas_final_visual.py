import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime

# --- CONEXIÓN A SUPABASE ---
def get_connection():
    return psycopg2.connect(
        host="aws-0-us-east-2.pooler.supabase.com",
        dbname="postgres",
        user="postgres.nwjuqqfsquvytbwslqrw",
        password="Dibujolavida141",
        port=6543
    )

# --- CONFIG STREAMLIT ---
st.set_page_config(page_title="App Rutinas Supabase", layout="wide")

# --- MENÚ VISUAL ADMIN ---
def mostrar_menu_visual():
    st.markdown("### Selecciona una opción del administrador")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("👤\nCrear nuevo usuario"):
            st.session_state.opcion_admin = "crear_usuario"

    with col2:
        if st.button("📝\nCrear nueva rutina"):
            st.session_state.opcion_admin = "crear_rutina"

    with col3:
        if st.button("🛠️\nModificar rutina existente"):
            st.session_state.opcion_admin = "modificar_rutina"

# --- APP ---
modo = st.sidebar.radio("Selecciona el modo:", ["Usuario", "Administrador"])

if modo == "Administrador":
    password = st.sidebar.text_input("Contraseña secreta", type="password")
    if password == "dioses123":
        st.title("Panel de Administrador")

        if "opcion_admin" not in st.session_state:
            st.session_state.opcion_admin = None

        mostrar_menu_visual()

        conn = get_connection()
        cur = conn.cursor()

        # Opción: Crear usuario
        if st.session_state.opcion_admin == "crear_usuario":
            st.markdown("### ➕ Crear nuevo usuario")
            nuevo_nombre = st.text_input("Nombre_clave nuevo")
            if st.button("Agregar usuario"):
                if nuevo_nombre:
                    try:
                        cur.execute("INSERT INTO usuarios (nombre_clave) VALUES (%s) ON CONFLICT DO NOTHING", (nuevo_nombre,))
                        conn.commit()
                        st.success(f"Usuario '{nuevo_nombre}' creado.")
                    except Exception as e:
                        st.error("Error al crear usuario: " + str(e))

        # Opción: Crear nueva rutina
        elif st.session_state.opcion_admin == "crear_rutina":
            st.markdown("### ✏️ Crear nueva rutina")
            # Aquí insertarás el código que ya tenías para crear rutina

        # Opción: Modificar rutina existente
        elif st.session_state.opcion_admin == "modificar_rutina":
            st.markdown("### 🛠️ Modificar rutina existente")
            # Aquí insertarás el código que ya tenías para modificar rutina

        cur.close()
        conn.close()
    else:
        st.warning("Contraseña incorrecta")
