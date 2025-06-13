
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

# --- CARGA DE EJERCICIOS ---
@st.cache_data
def cargar_ejercicios():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nombre, url, zona_corporal, implemento, articularidad FROM ejercicios")
    rows = cur.fetchall()
    colnames = [desc[0] for desc in cur.description]
    df = pd.DataFrame(rows, columns=colnames)
    cur.close()
    conn.close()
    return df

df_ejercicios = cargar_ejercicios()

# --- OBTENER RUTINAS DISPONIBLES ---
def obtener_rutinas_usuario(nombre_clave):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id_rutina, nombre_rutina, fecha_creacion FROM rutinas WHERE nombre_clave = %s ORDER BY fecha_creacion DESC", (nombre_clave,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return pd.DataFrame(rows, columns=["id_rutina", "nombre_rutina", "fecha_creacion"])

# --- OBTENER DETALLE RUTINA ---
def obtener_detalle_rutina(id_rutina):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id_ejercicio, repeticiones, series FROM detalle_rutina WHERE id_rutina = %s", (id_rutina,))
    datos = cur.fetchall()
    cur.close()
    conn.close()
    return pd.DataFrame(datos, columns=["id_ejercicio", "repeticiones", "series"])

# --- APP ---
modo = st.sidebar.radio("Selecciona el modo:", ["Usuario", "Administrador"])

if modo == "Usuario":
    nombre_usuario = st.sidebar.text_input("Ingresa tu nombre_clave")
    if nombre_usuario:
        st.title(f"Rutinas de {nombre_usuario}")
        df_rutinas = obtener_rutinas_usuario(nombre_usuario)
        if not df_rutinas.empty:
            rutina_seleccionada = st.selectbox("Selecciona una rutina", df_rutinas["nombre_rutina"])
            id_rutina = int(df_rutinas[df_rutinas["nombre_rutina"] == rutina_seleccionada]["id_rutina"].values[0])
            df_detalle = obtener_detalle_rutina(id_rutina)
            df_final = df_detalle.merge(df_ejercicios, left_on="id_ejercicio", right_on="id")
            for _, row in df_final.iterrows():
                st.markdown(f"**{row['nombre']}**")
                st.markdown(f"Repeticiones: {row['repeticiones']} | Series: {row['series']}")
                st.markdown(f"[🔗 Ver video de {row['nombre']}]({row['url']})", unsafe_allow_html=True)
        else:
            st.warning("No se encontraron rutinas.")

elif modo == "Administrador":
    password = st.sidebar.text_input("Contraseña secreta", type="password")
    if password == "dioses123":
        st.title("Panel de Administrador")
        conn = get_connection()
        cur = conn.cursor()

        # Crear nuevo usuario
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

        # Obtener usuarios
        cur.execute("SELECT nombre_clave FROM usuarios")
        usuarios = [row[0] for row in cur.fetchall()]

        # Crear nueva rutina
        st.markdown("### ✏️ Crear nueva rutina")
        usuario_seleccionado = st.selectbox("Selecciona usuario", usuarios, key="mod")
        nombre_rutina = st.text_input("Nombre de la nueva rutina")

        zona_filtro = st.selectbox("Filtrar por zona corporal", ["Todas"] + sorted(df_ejercicios["zona_corporal"].dropna().unique()))
        # Filtrar primero por zona seleccionada para obtener los implementos disponibles en esa zona
        if zona_filtro != "Todas":
            implementos_filtrados = df_ejercicios[df_ejercicios["zona_corporal"] == zona_filtro]["implemento"].dropna().unique()
        else:
            implementos_filtrados = df_ejercicios["implemento"].dropna().unique()
        
        implemento_filtro = st.selectbox("Filtrar por implemento", ["Todos"] + sorted(implementos_filtrados))
        # implemento_filtro = st.selectbox("Filtrar por implemento", ["Todos"] + sorted(df_ejercicios["implemento"].dropna().unique()))

        df_filtrado = df_ejercicios.copy()
        if zona_filtro != "Todas":
            df_filtrado = df_filtrado[df_filtrado["zona_corporal"] == zona_filtro]
        if implemento_filtro != "Todos":
            df_filtrado = df_filtrado[df_filtrado["implemento"] == implemento_filtro]

        ejercicios_seleccionados = st.multiselect("Selecciona ejercicios", df_filtrado["nombre"].tolist())
        repeticiones = st.number_input("N° Repeticiones", min_value=1, max_value=100, value=10)
        series = st.number_input("N° Series", min_value=1, max_value=20, value=3)

        if st.button("Guardar nueva rutina"):
            try:
                cur.execute("""
                    SELECT id_rutina FROM rutinas
                    WHERE nombre_clave = %s AND nombre_rutina = %s
                """, (usuario_seleccionado, nombre_rutina))
                resultado = cur.fetchone()
                
                if resultado:
                    id_rutina = resultado[0]  # Ya existe, usarlo
                else:
                    cur.execute("""
                        INSERT INTO rutinas (nombre_clave, nombre_rutina, fecha_creacion)
                        VALUES (%s, %s, %s) RETURNING id_rutina
                    """, (usuario_seleccionado, nombre_rutina, datetime.now()))
                    id_rutina = cur.fetchone()[0]

                # Insertar ejercicios asociados
                for nombre_ejercicio in ejercicios_seleccionados:
                    id_ej = int(df_ejercicios[df_ejercicios["nombre"] == nombre_ejercicio]["id"].values[0])
                    cur.execute("INSERT INTO detalle_rutina (id_rutina, id_ejercicio, repeticiones, series) VALUES (%s, %s, %s, %s)",
                                (id_rutina, id_ej, repeticiones, series))
                conn.commit()
                st.success("Rutina guardada exitosamente.")
            except Exception as e:
                conn.rollback()
                st.error("Error al guardar la rutina: " + str(e))

        cur.close()
        conn.close()
    else:
        st.warning("Contraseña incorrecta")
