import streamlit as st
from pymongo import MongoClient
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from neo4j import GraphDatabase

# Configuración de conexión a MongoDB para transcripciones
MONGO_URI = "mongodb+srv://sebastian_us:4254787Jus@cluster0.ecyx6.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DATABASE_NAME = "transcripciones"
COLLECTION_NAME = "transcripciones"

# Configuración de conexión a MongoDB para similitudes
URI_NEO = "neo4j+s://08d5f7d0.databases.neo4j.io"
AUTH = ("neo4j", "IuWbeyZ2oHy3QCL7mPk4QU32dxzfy4O6yRCnfbydym8")

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

# Función para graficar el grafo filtrado por una providencia y similitud mínima
def graficar_grafo_por_providencia(driver, providencia, similitud_minima):
    query = """
    MATCH (a:Providencia {id: $providencia})-[r:SIMILAR]->(b:Providencia)
    WHERE r.similitud >= $similitud_minima
    RETURN a.id AS origen, b.id AS destino, r.similitud AS similitud
    """

    G = nx.DiGraph()
    with driver.session() as session:
        result = session.run(query, providencia=providencia, similitud_minima=similitud_minima)
        for record in result:
            G.add_edge(
                record["origen"],
                record["destino"],
                weight=record["similitud"]
            )

    if not G:
        st.warning(f"No se encontraron relaciones para la providencia: {providencia}")
        return

    plt.figure(figsize=(10, 8))
    pos = nx.spring_layout(G)
    weights = nx.get_edge_attributes(G, 'weight')

    nx.draw(
        G, pos, with_labels=True, node_color="lightblue",
        node_size=2000, font_size=10, font_color="black",
        edge_color="gray", arrowsize=20
    )
    nx.draw_networkx_edge_labels(
        G, pos, edge_labels=weights, font_size=8
    )
    plt.title(f"Grafo de Providencia: {providencia}", fontsize=14)
    st.pyplot(plt)
    plt.clf()  # Limpia la figura para evitar superposiciones

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
    # Configurar la interfaz de Streamlit
    st.title("Visualización de Grafos de Providencias")
    st.sidebar.header("Configuración")
    
    # Obtener la lista de providencias
    with GraphDatabase.driver(URI_NEO, auth=AUTH) as driver:
        providencias = obtener_providencias(driver)
    
    # Menú desplegable para seleccionar providencias
    providencia_usuario = st.sidebar.selectbox("Seleccione la providencia que desea analizar:", options=providencias)
    
    # Control deslizante para la similitud mínima
    similitud_minima = st.sidebar.slider("Similitud mínima:", min_value=0.0, max_value=100.0, value=1, step=1)
    
    # Botón para generar el grafo
    if st.sidebar.button("Generar Grafo"):
        if providencia_usuario:
            with GraphDatabase.driver(URI, auth=AUTH) as driver:
                graficar_grafo_por_providencia(driver, providencia_usuario, similitud_minima)
        else:
            st.error("Por favor, seleccione una providencia.")

