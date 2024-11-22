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

# Conexión a MongoDB
def get_mongo_connection(uri, database_name, collection_name):
    client = MongoClient(uri)
    db = client[database_name]
    return db[collection_name]

# Función para obtener valores únicos de un campo
def get_unique_values(collection, field):
    return sorted(collection.distinct(field))

# Función para realizar consultas a MongoDB
def query_mongo(collection, query):
    return list(collection.find(query))

# Función para transformar resultados a DataFrame
def results_to_dataframe(results):
    if results:
        df = pd.DataFrame(results)
        df.drop(columns=["_id"], inplace=True, errors="ignore")
        return df
    return pd.DataFrame(columns=["No hay resultados"])

# Obtener providencias únicas para la página de similitudes
def get_unique_providencias_similitudes():
    collection = get_mongo_connection(mongo_uri_d, database_name_d, collection_name_d)
    providencia1_list = collection.distinct("providencia1")
    providencia2_list = collection.distinct("providencia2")
    return sorted(set(providencia1_list + providencia2_list))

# Obtener similitudes desde MongoDB
def get_similitudes_from_mongo(providencia, min_similitud, max_similitud):
    collection = get_mongo_connection(mongo_uri_d, database_name_d, collection_name_d)
    query = {
        "$or": [
            {"providencia1": providencia},
            {"providencia2": providencia}
        ],
        "similitud": {"$gte": min_similitud, "$lte": max_similitud}
    }
    return list(collection.find(query))

# Transformar resultados de similitud a DataFrame
def similitudes_to_dataframe(similitudes, providencia_elegida):
    data = []
    for sim in similitudes:
        related_prov = sim["providencia2"] if sim["providencia1"] == providencia_elegida else sim["providencia1"]
        data.append({"Providencia Relacionada": related_prov, "Similitud": sim["similitud"]})
    return pd.DataFrame(data)

# Interfaz Streamlit: Selección de la página
page = st.sidebar.radio("Selecciona una sección", ["Resultados de los Filtros", "Filtrar por Similitudes"])

if page == "Resultados de los Filtros":
    # Conexión para el sistema de consultas
    collection = get_mongo_connection(MONGO_URI, DATABASE_NAME, COLLECTION_NAME)
    
    # Título y descripción del sistema de consulta
    st.title("Sistema de Consulta de Providencias")
    st.markdown("""
    Bienvenido al sistema de consulta de providencias judiciales. 
    Aquí puedes filtrar y buscar por diferentes criterios, como:
    - **Nombre de la providencia**.
    - **Tipo de providencia**.
    - **Año de emisión**.
    - **Texto en el contenido de la providencia**.
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
    texto_clave = st.sidebar.text_input("Escribe una palabra clave para buscar en el texto")

    # Mostrar resultados en el cuerpo principal
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

elif page == "Filtrar por Similitudes":
    st.title("Filtrar por Similitudes")
    
    # Menú desplegable para seleccionar providencia
    providencias_similitudes = get_unique_providencias_similitudes()
    selected_providencia = st.sidebar.selectbox("Selecciona una providencia", [""] + providencias_similitudes)

    # Barra deslizadora para rango de similitud
    min_similitud, max_similitud = st.sidebar.slider(
        "Rango de Similitud", 0.0, 100.0, (0.0, 100.0), 0.1
    )

    if selected_providencia:
        st.subheader(f"Similitudes para la providencia: {selected_providencia}")
        similitudes = get_similitudes_from_mongo(selected_providencia, min_similitud, max_similitud)

        if similitudes:
            st.write(f"Se encontraron {len(similitudes)} similitudes.")
            df_similitudes = similitudes_to_dataframe(similitudes, selected_providencia)
            st.dataframe(df_similitudes)
        else:
            st.write("No se encontraron similitudes en el rango especificado.")

