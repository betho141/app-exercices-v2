import streamlit as st
import psycopg2
import pandas as pd

# --- CONEXIÓN ---
def get_connection():
    return psycopg2.connect(
        host=st.secrets["DB_HOST"],
        dbname=st.secrets["DB_NAME"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASSWORD"],
        port=st.secrets["DB_PORT"],
        sslmode="require"
    )

@st.cache_data
def cargar_ejercicios():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, nombre, url, zona_corporal, implemento, articularidad, lateralidad, musculo
        FROM ejercicios
        ORDER BY nombre
    """)
    rows = cur.fetchall()
    colnames = [desc[0] for desc in cur.description]
    df = pd.DataFrame(rows, columns=colnames)
    cur.close()
    conn.close()
    return df


# --- APP ---
st.title("📹 Biblioteca de Ejercicios con Video")

df = cargar_ejercicios()

# --- FILTROS ---
col1, col2 = st.columns(2)

with col1:
    zona = st.selectbox(
        "Zona corporal",
        ["Todas"] + sorted(df["zona_corporal"].dropna().unique())
    )

with col2:
    implemento = st.selectbox(
        "Implemento",
        ["Todos"] + sorted(df["implemento"].dropna().unique())
    )

df_filtrado = df.copy()

if zona != "Todas":
    df_filtrado = df_filtrado[df_filtrado["zona_corporal"] == zona]

if implemento != "Todos":
    df_filtrado = df_filtrado[df_filtrado["implemento"] == implemento]

# --- MOSTRAR EJERCICIOS ---
st.markdown("---")
st.subheader("Resultados")

for _, row in df_filtrado.iterrows():
    st.markdown(f"### {row['nombre']}")

    # Mostrar video directamente en la app
    st.video(row["url"])

    # Info extra
    st.write(f"Zona corporal: **{row['zona_corporal']}**")
    st.write(f"Implemento: **{row['implemento']}**")
    st.write("---")
