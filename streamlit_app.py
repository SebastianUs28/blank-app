import streamlit as st
from pymongo import MongoClient
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from neo4j import GraphDatabase

# Configuración de conexión a MongoDB
MONGO_URI = "mongodb+srv://sebastian_us:4254787Jus@cluster0.ecyx6.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DATABASE_NAME = "transcripciones"
COLLECTION_NAME = "transcripciones"

# Configuración de conexión a Neo4j
URI_NEO = "neo4j+s://08d5f7d0.databases.neo4j.io"
AUTH = ("neo4j", "IuWbeyZ2oHy3QCL7mPk4QU32dxzfy4O6yRCnfbydym8")


# Función para obtener conexión a MongoDB
def get_mongo_connection(uri, database_name, collection_name):
    client = MongoClient(uri)
    db = client[database_name]
    return db[collection_name]


# Función para obtener valores únicos
def get_unique_values(collection, field):
    return sorted(collection.distinct(field))


# Función para obtener datos desde MongoDB
def query_mongo(collection, query):
    return list(collection.find(query))


# Convertir resultados a DataFrame
def results_to_dataframe(results):
    if results:
        df = pd.DataFrame(results)
        df.drop(columns=["_id"], inplace=True, errors="ignore")
        return df
    return pd.DataFrame(columns=["No hay resultados"])


# Función para graficar grafo
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
            G.add_edge(record["origen"], record["destino"], weight=record["similitud"])

    if not G:
        st.warning(f"No se encontraron relaciones para la providencia: {providencia}")
        return

    plt.figure(figsize=(10, 8))
    pos = nx.spring_layout(G)
    weights = nx.get_edge_attributes(G, 'weight')

    nx.draw(G, pos, with_labels=True, node_color="lightblue", node_size=2000,
            font_size=10, font_color="black", edge_color="gray", arrowsize=20)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=weights, font_size=8)
    plt.title(f"Grafo de Providencia: {providencia}", fontsize=14)
    st.pyplot(plt)
    plt.clf()  # Limpia el gráfico después de mostrarlo


# Función para obtener lista de providencias desde Neo4j
def obtener_providencias(driver):
    query = "MATCH (p:Providencia) RETURN p.id AS id"
    with driver.session() as session:
        result = session.run(query)
        return [record["id"] for record in result]


# Configuración de página en Streamlit
st.sidebar.title("Navegación")
page = st.sidebar.radio("Selecciona una página:", ["Resultados de los Filtros", "Filtrar por Similitudes"])

if page == "Resultados de los Filtros":
    # Conexión a MongoDB
    collection = get_mongo_connection(MONGO_URI, DATABASE_NAME, COLLECTION_NAME)

    # Filtros
    st.title("Consulta de Transcripciones")
    st.sidebar.subheader("Filtros")

    providencias = get_unique_values(collection, "providencia")
    selected_providencia = st.sidebar.selectbox("Providencia", [""] + providencias)

    tipos = get_unique_values(collection, "tipo")
    selected_tipo = st.sidebar.selectbox("Tipo", [""] + tipos)

    anios = get_unique_values(collection, "anio")
    selected_anio = st.sidebar.selectbox("Año", [""] + anios)

    texto_clave = st.sidebar.text_input("Texto")

    # Mostrar resultados
    if selected_providencia:
        results = query_mongo(collection, {"providencia": selected_providencia})
        st.dataframe(results_to_dataframe(results))
    elif selected_tipo:
        results = query_mongo(collection, {"tipo": selected_tipo})
        st.dataframe(results_to_dataframe(results))
    elif selected_anio:
        results = query_mongo(collection, {"anio": selected_anio})
        st.dataframe(results_to_dataframe(results))
    elif texto_clave:
        results = query_mongo(collection, {"$text": {"$search": texto_clave}})
        st.dataframe(results_to_dataframe(results))

elif page == "Filtrar por Similitudes":
    st.title("Visualización de Grafos")

    with GraphDatabase.driver(URI_NEO, auth=AUTH) as driver:
        providencias = obtener_providencias(driver)

    selected_providencia = st.sidebar.selectbox("Providencia:", [""] + providencias)
    similitud_minima = st.sidebar.slider("Similitud mínima", 0.0, 100.0, 1.0, 1.0)

    if st.sidebar.button("Generar Grafo"):
        if selected_providencia:
            with GraphDatabase.driver(URI_NEO, auth=AUTH) as driver:
                graficar_grafo_por_providencia(driver, selected_providencia, similitud_minima)
        else:
            st.error("Seleccione una providencia.")

