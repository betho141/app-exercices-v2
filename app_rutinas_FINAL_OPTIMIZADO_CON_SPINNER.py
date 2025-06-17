
import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime
from PIL import Image
import base64


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

# --- CAMBIAR FONDO DE LA PÁGINA (RGB) ---
st.markdown(
    """
    <style>
    body {
        background-color: rgb(0, 0, 0); /* Cambia aquí el color RGB que desees */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# # Cargar imagen y convertirla en base64
# def get_base64_of_bin_file(bin_file):
#     with open(bin_file, 'rb') as f:
#         data = f.read()
#     return base64.b64encode(data).decode()

# logo_path = "logo.jpg"
# logo_base64 = get_base64_of_bin_file(logo_path)

# st.markdown(
#     f"""
#     <div style="text-align: center;">
#         <img src="data:image/png;base64,{logo_base64}" width="500"/>
#     </div>
#     """,
#     unsafe_allow_html=True
# )

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
        if "refresh_ejercicios" in st.session_state and st.session_state["refresh_ejercicios"]:
            st.session_state["refresh_ejercicios"] = False
            st.experimental_rerun()

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
        if zona_filtro != "Todas":
            implementos_filtrados = df_ejercicios[df_ejercicios["zona_corporal"] == zona_filtro]["implemento"].dropna().unique()
        else:
            implementos_filtrados = df_ejercicios["implemento"].dropna().unique()

        implemento_filtro = st.selectbox("Filtrar por implemento", ["Todos"] + sorted(implementos_filtrados))

        df_filtrado = df_ejercicios.copy()
        if zona_filtro != "Todas":
            df_filtrado = df_filtrado[df_filtrado["zona_corporal"] == zona_filtro]
        if implemento_filtro != "Todos":
            df_filtrado = df_filtrado[df_filtrado["implemento"] == implemento_filtro]

        ejercicios_seleccionados = st.multiselect("Selecciona ejercicios", df_filtrado["nombre"].tolist())

        if ejercicios_seleccionados:
            tabla_ejercicios = pd.DataFrame({
                "Ejercicio": ejercicios_seleccionados,
                "N° Repeticiones": [10]*len(ejercicios_seleccionados),
                "N° Series": [3]*len(ejercicios_seleccionados)
            })

            edited_tabla = st.data_editor(
                tabla_ejercicios,
                num_rows="fixed",
                use_container_width=True,
                key="tabla_rutina"
            )
        else:
            edited_tabla = pd.DataFrame(columns=["Ejercicio", "N° Repeticiones", "N° Series"])

        if st.button("Guardar nueva rutina"):
            if not edited_tabla.empty:
                try:
                    cur.execute("""
                        SELECT id_rutina FROM rutinas
                        WHERE nombre_clave = %s AND nombre_rutina = %s
                    """, (usuario_seleccionado, nombre_rutina))
                    resultado = cur.fetchone()
        
                    if resultado:
                        id_rutina = resultado[0]
                    else:
                        cur.execute("""
                            INSERT INTO rutinas (nombre_clave, nombre_rutina, fecha_creacion)
                            VALUES (%s, %s, %s) RETURNING id_rutina
                        """, (usuario_seleccionado, nombre_rutina, datetime.now()))
                        id_rutina = cur.fetchone()[0]
        
                    for _, row in edited_tabla.iterrows():
                        id_ej = int(df_ejercicios[df_ejercicios["nombre"] == row["Ejercicio"]]["id"].values[0])
                        rep = int(row["N° Repeticiones"])
                        ser = int(row["N° Series"])
                        cur.execute("""
                            INSERT INTO detalle_rutina (id_rutina, id_ejercicio, repeticiones, series)
                            VALUES (%s, %s, %s, %s)
                        """, (id_rutina, id_ej, rep, ser))
        
                    conn.commit()
                    st.success("Rutina guardada exitosamente.")
                except Exception as e:
                    conn.rollback()
                    st.error("Error al guardar la rutina: " + str(e))

    
        # --- AGREGAR/VER/ELIMINAR EJERCICIOS EN RUTINA EXISTENTE ---
        st.markdown("---")
        st.markdown("### 🛠️ Modificar rutina existente")

        usuario_modificar = st.selectbox("Selecciona usuario para modificar", usuarios, key="modificar_rutina")
        df_rutinas_usuario = obtener_rutinas_usuario(usuario_modificar)
        st.write("Usuario:", usuario_modificar)
        st.write("Rutinas encontradas:", df_rutinas_usuario)

        
        if not df_rutinas_usuario.empty:
            rutina_modificar = st.selectbox("Selecciona rutina", df_rutinas_usuario["nombre_rutina"], key="select_rutina")
            id_rutina_mod = int(df_rutinas_usuario[df_rutinas_usuario["nombre_rutina"] == rutina_modificar]["id_rutina"].values[0])

            df_detalle_actual = obtener_detalle_rutina(id_rutina_mod)
            df_detalle_actual = df_detalle_actual.merge(df_ejercicios, left_on="id_ejercicio", right_on="id")

            st.markdown("#### 📋 Ejercicios actuales en la rutina:")
            for i, row in df_detalle_actual.iterrows():
                col1, col2 = st.columns([4,1])
                with col1:
                    st.markdown(f"• **{row['nombre']}** | Reps: {row['repeticiones']} | Series: {row['series']}")
                with col2:
                    if st.button(f"❌ Eliminar", key=f"del_{row['id_ejercicio']}"):
                with st.spinner("Eliminando ejercicio..."):
                    cur.execute(
                        "DELETE FROM detalle_rutina WHERE id_rutina = %s AND id_ejercicio = %s",
                        (id_rutina_mod, row['id_ejercicio'])
                    )
                    conn.commit()
                    st.success(f"{row['nombre']} eliminado")
                    st.session_state["refresh_ejercicios"] = True

                        except Exception as e:
                            conn.rollback()
                            st.error(f"Error al eliminar ejercicio: {e}")

            st.markdown("#### ➕ Agregar nuevos ejercicios")
            zona_mod = st.selectbox("Filtrar por zona corporal", ["Todas"] + sorted(df_ejercicios["zona_corporal"].dropna().unique()), key="zona_mod")
            if zona_mod != "Todas":
                implementos_mod = df_ejercicios[df_ejercicios["zona_corporal"] == zona_mod]["implemento"].dropna().unique()
            else:
                implementos_mod = df_ejercicios["implemento"].dropna().unique()

            implemento_mod = st.selectbox("Filtrar por implemento", ["Todos"] + sorted(implementos_mod), key="impl_mod")

            df_filtrado_mod = df_ejercicios.copy()
            if zona_mod != "Todas":
                df_filtrado_mod = df_filtrado_mod[df_filtrado_mod["zona_corporal"] == zona_mod]
            if implemento_mod != "Todos":
                df_filtrado_mod = df_filtrado_mod[df_filtrado_mod["implemento"] == implemento_mod]

            ejercicios_disponibles = st.multiselect("Ejercicios a agregar", df_filtrado_mod["nombre"].tolist(), key="multi_agregar")

            if ejercicios_disponibles:
                tabla_nueva = pd.DataFrame({
                    "Ejercicio": ejercicios_disponibles,
                    "N° Repeticiones": [10] * len(ejercicios_disponibles),
                    "N° Series": [3] * len(ejercicios_disponibles)
                })

                tabla_editada = st.data_editor(
                    tabla_nueva,
                    num_rows="fixed",
                    use_container_width=True,
                    key="tabla_nuevos"
                )
            else:
                tabla_editada = pd.DataFrame(columns=["Ejercicio", "N° Repeticiones", "N° Series"])

            if st.button("Agregar ejercicios a rutina"):
                try:
                    ids_existentes = set(df_detalle_actual["id_ejercicio"])
                    count_agregados = 0
                    for _, row in tabla_editada.iterrows():
                        id_ej = int(df_ejercicios[df_ejercicios["nombre"] == row["Ejercicio"]]["id"].values[0])
                        if id_ej in ids_existentes:
                            continue
                        rep = int(row["N° Repeticiones"])
                        ser = int(row["N° Series"])
                        cur.execute(
                            "INSERT INTO detalle_rutina (id_rutina, id_ejercicio, repeticiones, series) VALUES (%s, %s, %s, %s)",
                            (id_rutina_mod, id_ej, rep, ser)
                        )
                        count_agregados += 1
                    conn.commit()
                    if count_agregados > 0:
                        st.success(f"{count_agregados} ejercicio(s) agregado(s) exitosamente.")
                        st.experimental_rerun()
                    else:
                        st.info("No se agregaron nuevos ejercicios (ya estaban en la rutina).")
                except Exception as e:
                    conn.rollback()
                    st.error("Error al agregar ejercicios: " + str(e))
        else:
            st.info("Este usuario aún no tiene rutinas creadas.")

        cur.close()
        conn.close()
    else:
        st.warning("Contraseña incorrecta")
