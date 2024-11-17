import streamlit as st
from pymongo import MongoClient
import pandas as pd

# Configuración de conexión a MongoDB
MONGO_URI = "mongodb+srv://sebastian_us:4254787Jus@cluster0.ecyx6.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DATABASE_NAME = "transcripciones"
COLLECTION_NAME = "transcripciones"

# Función para conectarse a MongoDB
@st.cache_resource
def get_mongo_connection():
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    return collection

# Función para obtener valores únicos de un campo
def get_unique_values(collection, field):
    return collection.distinct(field)

# Función para realizar consultas a MongoDB
def query_mongo(collection, query):
    return list(collection.find(query))

# Función para transformar resultados a DataFrame
def results_to_dataframe(results):
    if results:
        df = pd.DataFrame(results)
        df.drop(columns=["_id"], inplace=True)  # Opcional: eliminar columna _id
        return df
    else:
        return pd.DataFrame(columns=["No hay resultados"])

# Crear un índice de texto en MongoDB
def create_text_index(collection, field):
    collection.create_index([(field, "text")])

collection = get_mongo_connection()

# Título y descripción
st.title("Sistema de Consulta de Providencias")
st.markdown("""
Bienvenido al sistema de consulta de providencias judiciales. 
Aquí puedes filtrar y buscar por diferentes criterios, como:
- **Nombre de la providencia**.
- **Tipo de providencia**.
- **Año de emisión**.
- **Texto en el contenido de la providencia**.

Selecciona los filtros desde la barra lateral y observa los resultados en tiempo real a la derecha.
""")

# Barra lateral para filtros
st.sidebar.title("Filtros")

# Filtro: Consulta por nombre de providencia
st.sidebar.subheader("Nombre de Providencia")
providencias = get_unique_values(collection, "providencia")
selected_providencia = st.sidebar.selectbox("Selecciona una providencia", [""] + providencias)

# Filtro: Consulta por tipo
st.sidebar.subheader("Tipo de Providencia")
tipos = get_unique_values(collection, "tipo")
selected_tipo = st.sidebar.selectbox("Selecciona un tipo de providencia", [""] + tipos)

# Filtro: Consulta por año
st.sidebar.subheader("Año")
anios = get_unique_values(collection, "anio")
selected_anio = st.sidebar.selectbox("Selecciona un año", [""] + anios)

# Filtro: Consulta por texto
st.sidebar.subheader("Texto en Providencia")
create_text_index(collection, "texto")  # Crear índice de texto (si no existe)
texto_clave = st.sidebar.text_input("Escribe una palabra clave para buscar en el texto")

# Mostrar resultados en el cuerpo principal
st.title("Resultados de la Consulta")

if selected_providencia:
    st.subheader(f"Resultados para Providencia: {selected_providencia}")
    results = query_mongo(collection, {"providencia": selected_providencia})
    df = results_to_dataframe(results)
    st.dataframe(df)

elif selected_tipo:
    st.subheader(f"Resultados para Tipo: {selected_tipo}")
    results = query_mongo(collection, {"tipo": selected_tipo})
    df = results_to_dataframe(results)
    st.dataframe(df)

elif selected_anio:
    st.subheader(f"Resultados para Año: {selected_anio}")
    results = query_mongo(collection, {"anio": selected_anio})
    df = results_to_dataframe(results)
    st.dataframe(df)

elif texto_clave:
    st.subheader(f"Resultados para Texto: {texto_clave}")
    results = query_mongo(collection, {"$text": {"$search": texto_clave}})
    df = results_to_dataframe(results)
    st.dataframe(df)
