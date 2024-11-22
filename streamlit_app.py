import streamlit as st
from pymongo import MongoClient
import pandas as pd
from pyvis.network import Network
import networkx as nx
from streamlit.components.v1 import html

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

# Función para transformar resultados a DataFrame
def results_to_dataframe(results):
    if results:
        df = pd.DataFrame(results)
        df.drop(columns=["_id"], inplace=True, errors="ignore")  # Ignorar error si no existe "_id"
        return df
    return pd.DataFrame(columns=["No hay resultados"])

# Función para obtener similitudes desde MongoDB
def get_similitudes_from_mongo(senten_id, max_similitud):
    client = MongoClient(mongo_uri_d)
    db = client[database_name_d]
    collection = db[collection_name_d]
    
    # Convertir similitud máxima a float
    max_similitud = float(max_similitud)
    
    # Consulta a MongoDB
    query = {
        "$or": [
            {"providencia1": senten_id},
            {"providencia2": senten_id}
        ],
        "similitud": {"$lte": max_similitud}
    }
    similitudes = list(collection.find(query))
    
    # Depuración
    st.write("Consulta MongoDB realizada:", query)
    st.write("Resultados obtenidos:", similitudes)
    
    return similitudes

# Función para obtener providencias únicas
def get_similitudes_providencias(collection_d):
    providencia1_list = collection_d.distinct("providencia1")
    providencia2_list = collection_d.distinct("providencia2")
    return list(set(providencia1_list + providencia2_list))

# Conexión a MongoDB para similitudes
def get_mongo_connection_similitudes():
    client = MongoClient(mongo_uri_d)
    db = client[database_name_d]
    collection = db[collection_name_d]
    return collection

# Crear un grafo con las similitudes
def create_similarity_graph(similitudes):
    G = nx.Graph()
    
    for record in similitudes:
        providencia1 = record.get("providencia1")
        providencia2 = record.get("providencia2")
        similitud = record.get("similitud")
        if providencia1 and providencia2 and similitud is not None:
            G.add_edge(providencia1, providencia2, weight=similitud)
        else:
            st.write("Registro inválido encontrado:", record)
    
    return G

# Visualizar el grafo con pyvis
def visualize_graph(G):
    net = Network(height="600px", width="100%", bgcolor="#222222", font_color="white")
    
    # Añadir nodos y aristas al grafo de pyvis
    for node in G.nodes:
        net.add_node(node, label=node)
        
    for edge in G.edges(data=True):
        net.add_edge(edge[0], edge[1], value=edge[2]['weight'])
    
    # Generar el grafo como HTML y mostrarlo
    net_html = net.generate_html()
    html(net_html, height=600)

# Interfaz Streamlit: Selección de la página
page = st.sidebar.radio("Selecciona una sección", ["Resultados de los Filtros", "Filtrar por Similitudes"])

if page == "Resultados de los Filtros":
    # Lógica para resultados de filtros (idéntica a la original)

    # Conexión a MongoDB
    collection = get_mongo_connection()

    # Título y filtros
    st.title("Sistema de Consulta de Providencias")
    st.sidebar.title("Filtros")

    providencias = get_unique_values(collection, "providencia")
    selected_providencia = st.sidebar.selectbox("Nombre de la Providencia", [""] + providencias)
    tipos = get_unique_values(collection, "tipo")
    selected_tipo = st.sidebar.selectbox("Tipo de Providencia", [""] + tipos)
    anios = get_unique_values(collection, "anio")
    selected_anio = st.sidebar.selectbox("Año", [""] + anios)
    texto_clave = st.sidebar.text_input("Texto en la Providencia")

    # Resultados
    if selected_providencia:
        results = query_mongo(collection, {"providencia": selected_providencia})
    elif selected_tipo:
        results = query_mongo(collection, {"tipo": selected_tipo})
    elif selected_anio:
        results = query_mongo(collection, {"anio": selected_anio})
    elif texto_clave:
        results = query_mongo(collection, {"$text": {"$search": texto_clave}})
    else:
        results = []

    df = results_to_dataframe(results)
    st.dataframe(df)

elif page == "Filtrar por Similitudes":
    # Conexión y datos
    collection_similitudes = get_mongo_connection_similitudes()
    providencias_similitudes = get_similitudes_providencias(collection_similitudes)
    
    # Filtros
    st.title("Filtrar por Similitudes")
    selected_providencia = st.sidebar.selectbox("Selecciona una providencia", providencias_similitudes)
    max_similitud = st.sidebar.slider("Similitud máxima", 0.0, 100.0, 100.0, 0.1)

    # Resultados
    if selected_providencia:
        similitudes = get_similitudes_from_mongo(selected_providencia, max_similitud)
        
        if similitudes:
            st.write(f"Similitudes encontradas para {selected_providencia} (máximo {max_similitud}):")
            G = create_similarity_graph(similitudes)
            visualize_graph(G)
        else:
            st.write(f"No se encontraron similitudes para {selected_providencia} dentro del rango.")
