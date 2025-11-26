import streamlit as st
import psycopg2
import pandas as pd

# ============================
# CONEXIÓN A SUPABASE
# ============================

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
        SELECT id, nombre, url, zona_corporal, implemento, 
               articularidad, lateralidad, musculo
        FROM ejercicios
        ORDER BY nombre
    """)
    rows = cur.fetchall()
    colnames = [desc[0] for desc in cur.description]
    df = pd.DataFrame(rows, columns=colnames)
    cur.close()
    conn.close()
    return df


# ============================
# CONFIGURACIÓN DE LA PÁGINA
# ============================

st.set_page_config(
    page_title="Biblioteca de Ejercicios",
    layout="wide"
)

# LOGO
ruta_logo = "https://raw.githubusercontent.com/betho141/imagenes/main/logo.jpg"

st.markdown(f"""
    <div style='text-align: center; padding-top: 20px;'>
        <img src='{ruta_logo}' width='200'/>
        <h2 style='color: white;'>Biblioteca de Ejercicios</h2>
        <p style='color: #cccccc;'>Filtra por zona, implemento, articularidad, lateralidad o músculo… o busca directamente por nombre.</p>
    </div>
""", unsafe_allow_html=True)


# ============================
# CARGA DE DATOS
# ============================

df = cargar_ejercicios()

st.markdown("## 🔍 Filtros y Búsqueda")


# ============================
# FILTROS
# ============================

buscar_nombre = st.text_input("Buscar ejercicio por nombre:", "")

col1, col2, col3 = st.columns(3)
col4, col5 = st.columns(2)

with col1:
    zona = st.selectbox(
        "Zona corporal:",
        ["Todas"] + sorted(df["zona_corporal"].dropna().unique())
    )

with col2:
    implemento = st.selectbox(
        "Implemento:",
        ["Todos"] + sorted(df["implemento"].dropna().unique())
    )

with col3:
    articularidad = st.selectbox(
        "Articularidad:",
        ["Todas"] + sorted(df["articularidad"].dropna().unique())
    )

with col4:
    lateralidad = st.selectbox(
        "Lateralidad:",
        ["Todas"] + sorted(df["lateralidad"].dropna().unique())
    )

with col5:
    musculo = st.selectbox(
        "Músculo:",
        ["Todos"] + sorted(df["musculo"].dropna().unique())
    )


# ============================
# APLICAR FILTROS
# ============================

df_filtrado = df.copy()

if buscar_nombre.strip():
    df_filtrado = df_filtrado[
        df_filtrado["nombre"].str.contains(buscar_nombre, case=False, na=False)
    ]

if zona != "Todas":
    df_filtrado = df_filtrado[df_filtrado["zona_corporal"] == zona]

if implemento != "Todos":
    df_filtrado = df_filtrado[df_filtrado["implemento"] == implemento]

if articularidad != "Todas":
    df_filtrado = df_filtrado[df_filtrado["articularidad"] == articularidad]

if lateralidad != "Todas":
    df_filtrado = df_filtrado[df_filtrado["lateralidad"] == lateralidad]

if musculo != "Todos":
    df_filtrado = df_filtrado[df_filtrado["musculo"] == musculo]


# ============================
# LISTA DE RESULTADOS
# ============================

st.markdown("---")
st.subheader("📋 Lista de Ejercicios")

if df_filtrado.empty:
    st.warning("No se encontraron ejercicios con esos filtros o nombre.")
else:
    for _, row in df_filtrado.iterrows():

        with st.expander(f"▶ {row['nombre']}", expanded=False):

            st.video(row["url"])

            st.write(f"**Zona corporal:** {row['zona_corporal']}")
            st.write(f"**Implemento:** {row['implemento']}")
            st.write(f"**Articularidad:** {row['articularidad']}")
            st.write(f"**Lateralidad:** {row['lateralidad']}")
            st.write(f"**Músculo:** {row['musculo']}")
