import streamlit as st
from pymongo import MongoClient
import pandas as pd

# Configuración de conexión a MongoDB para transcripciones
MONGO_URI = "mongodb+srv://sebastian_us:4254787Jus@cluster0.ecyx6.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DATABASE_NAME = "transcripciones"
COLLECTION_NAME = "transcripciones"

# Configuración de conexión a MongoDB para similitudes
mongo_uri_d = "mongodb+srv://adiazc07:Colombia1.@cluster0.lydnuw6.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
database_name_d = "Providencia"
collection_name_d = "Similitud"

# Conexión a MongoDB para transcripciones
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

# Función para obtener similitudes desde MongoDB
def get_similitudes_from_mongo(providencia1, min_similitud, max_similitud):
    client = MongoClient(mongo_uri_d)
    db = client[database_name_d]
    collection = db[collection_name_d]

    query = {
        "$or": [
            {"providencia1": providencia1},
            {"providencia2": providencia1}
        ],
        "similitud": {"$gte": min_similitud, "$lte": max_similitud}
    }
    
    similitudes = list(collection.find(query))
    return similitudes

# Transformar resultados de similitud a DataFrame
def similitudes_to_dataframe(similitudes, providencia_elegida):
    data = []
    for sim in similitudes:
        # Determinar la providencia relacionada
        related_prov = sim["providencia2"] if sim["providencia1"] == providencia_elegida else sim["providencia1"]
        data.append({"Providencia Relacionada": related_prov, "Similitud": sim["similitud"]})
    
    return pd.DataFrame(data)

# Interfaz Streamlit: Selección de la página
page = st.sidebar.radio("Selecciona una sección", ["Resultados de los Filtros", "Filtrar por Similitudes"])

if page == "Resultados de los Filtros":
    # Página 1: Resultados de los filtros
    collection = get_mongo_connection()
    
    st.title("Sistema de Consulta de Providencias")
    st.markdown("""
    Bienvenido al sistema de consulta de providencias judiciales. 
    Aquí puedes filtrar y buscar por diferentes criterios, como:
    - **Nombre de la providencia**.
    - **Tipo de providencia**.
    - **Año de emisión**.
    - **Texto en el contenido de la providencia**.
    """)

    st.sidebar.title("Filtros")

    # Filtro: Consulta por nombre de providencia
    providencias = get_unique_values(collection, "providencia")
    selected_providencia = st.sidebar.selectbox("Nombre de Providencia", [""] + providencias)

    # Filtro: Consulta por tipo de providencia
    tipos = get_unique_values(collection, "tipo")
    selected_tipo = st.sidebar.selectbox("Tipo de Providencia", [""] + tipos)

    # Filtro: Consulta por año
    anios = get_unique_values(collection, "anio")
    selected_anio = st.sidebar.selectbox("Año de Emisión", [""] + anios)

    # Filtro: Consulta por texto
    texto_clave = st.sidebar.text_input("Texto clave en el contenido")

    # Mostrar resultados
    st.title("Resultados de la Consulta")
    query = {}

    if selected_providencia:
        query["providencia"] = selected_providencia

    if selected_tipo:
        query["tipo"] = selected_tipo

    if selected_anio:
        query["anio"] = selected_anio

    if texto_clave:
        query["$text"] = {"$search": texto_clave}

    if query:
        st.subheader("Resultados de la búsqueda:")
        results = query_mongo(collection, query)
        df = results_to_dataframe(results)
        st.dataframe(df)
    else:
        st.write("Selecciona un filtro para buscar resultados.")

elif page == "Filtrar por Similitudes":
    # Página 2: Filtrar por similitudes
    st.title("Filtrar por Similitudes")
    collection = get_mongo_connection()
    
    # Menú desplegable para seleccionar providencia
    providencias = get_unique_values(collection, "providencia")
    selected_providencia = st.sidebar.selectbox("Selecciona una providencia", [""] + providencias)

    # Barra deslizadora única para rango de similitud
    min_similitud, max_similitud = st.sidebar.slider(
        "Rango de Similitud", 0.0, 100.0, (0.0, 100.0), 0.1
    )

    if selected_providencia:
        st.subheader(f"Similitudes para la providencia: {selected_providencia}")
        similitudes = get_similitudes_from_mongo(selected_providencia, min_similitud, max_similitud)

        if similitudes:
            st.write(f"Se encontraron {len(similitudes)} similitudes.")
            
            # Mostrar las similitudes como una tabla
            df_similitudes = similitudes_to_dataframe(similitudes, selected_providencia)
            st.dataframe(df_similitudes)
        else:
            st.write("No se encontraron similitudes en el rango especificado.")



