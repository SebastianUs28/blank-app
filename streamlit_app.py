import streamlit as st
from pymongo import MongoClient
import pandas as pd
from pyvis.network import Network
import networkx as nx

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

# Función para obtener similitudes desde MongoDB
def get_similitudes_from_mongo(providencia1, min_similitud, max_similitud):
    client = MongoClient(mongo_uri_d)
    db = client[database_name_d]
    collection = db[collection_name_d]

    query = {
        "providencia1": providencia1,
        "similitud": {"$gte": min_similitud, "$lte": max_similitud}
    }
    
    similitudes = list(collection.find(query))
    return similitudes

# Crear un grafo con las similitudes
def create_similarity_graph(similitudes):
    G = nx.Graph()
    
    for record in similitudes:
        providencia1 = record.get("providencia1")
        providencia2 = record.get("providencia2")
        similitud = record.get("similitud")
        
        if providencia1 and providencia2 and similitud is not None:
            # Similitud inversa para calcular distancia
            distance = 100 - similitud
            G.add_edge(providencia1, providencia2, weight=similitud, distance=distance)
        else:
            st.write("Registro inválido encontrado:", record)
    
    return G

# Visualizar el grafo con pyvis
def visualize_graph(G):
    net = Network(height="600px", width="100%", bgcolor="#222222", font_color="white")
    
    for node in G.nodes:
        net.add_node(node, label=node)
        
    for edge in G.edges(data=True):
        net.add_edge(edge[0], edge[1], value=edge[2]['weight'], title=f"Similitud: {edge[2]['weight']}")
    
    net.show("graph.html")
    st.write("Visualización interactiva disponible en el siguiente enlace:")
    st.markdown("[Abrir grafo interactivo](graph.html)", unsafe_allow_html=True)

# Interfaz Streamlit: Selección de la página (Filtros o Similitudes)
page = st.sidebar.radio("Selecciona una sección", ["Resultados de los Filtros", "Filtrar por Similitudes"])

if page == "Resultados de los Filtros":
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
    providencias = get_unique_values(collection, "providencia")
    selected_providencia = st.sidebar.selectbox("Selecciona una providencia", [""] + providencias)

    if selected_providencia:
        st.subheader(f"Resultados para Providencia: {selected_providencia}")
        results = list(collection.find({"providencia": selected_providencia}))
        df = pd.DataFrame(results).drop(columns=["_id"], errors="ignore")
        st.dataframe(df)

elif page == "Filtrar por Similitudes":
    st.title("Filtrar por Similitudes")
    collection = get_mongo_connection()
    
    providencias = get_unique_values(collection, "providencia")
    selected_providencia = st.sidebar.selectbox("Selecciona una providencia", [""] + providencias)

    min_similitud, max_similitud = st.sidebar.slider(
        "Rango de Similitud",
        0.0, 100.0, (0.0, 100.0), 0.1
    )

    if selected_providencia:
        st.subheader(f"Similitudes para la providencia: {selected_providencia}")
        similitudes = get_similitudes_from_mongo(selected_providencia, min_similitud, max_similitud)

        if similitudes:
            st.write(f"Se encontraron {len(similitudes)} similitudes.")
            G = create_similarity_graph(similitudes)
            visualize_graph(G)
        else:
            st.write("No se encontraron similitudes en el rango especificado.")

