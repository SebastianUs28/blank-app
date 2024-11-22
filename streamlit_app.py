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

# Función para realizar consultas a MongoDB
def query_mongo(collection, query):
    return list(collection.find(query))

# Función para transformar resultados a DataFrame
def results_to_dataframe(results):
    if results:
        df = pd.DataFrame(results)
        df.drop(columns=["_id"], inplace=True)  # Opcional: eliminar columna _id
        return df
    return pd.DataFrame(columns=["No hay resultados"])

# Función para obtener similitudes desde MongoDB (para el grafo)
def get_similitudes_from_mongo(senten_id, max_similitud):
    client = MongoClient(mongo_uri_d)
    db = client[database_name_d]
    collection = db[collection_name_d]
    
    # Consulta para obtener similitudes para una sentencia específica y un rango de similitudes
    query = {
        "$or": [
            {"providencia1": senten_id},
            {"providencia2": senten_id}
        ],
        "similitud": {"$lte": max_similitud}  # Solo consideramos el máximo de similitud
    }
    
    # Recuperar los datos
    similitudes = list(collection.find(query))
    return similitudes
# Función para obtener las providencias de la colección de similitudes
def get_similitudes_providencias(collection_d):
    return collection_d.distinct("providencia1") + collection_d.distinct("providencia2")

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
        providencia1 = record["providencia1"]
        providencia2 = record["providencia2"]
        similitud = record["similitud"]
        
        # Añadir los nodos y aristas con la similitud como peso
        G.add_edge(providencia1, providencia2, weight=similitud)
    
    return G

# Visualizar el grafo con pyvis
def visualize_graph(G):
    net = Network(height="600px", width="100%", bgcolor="#222222", font_color="white")
    
    # Añadir nodos y aristas al grafo de pyvis
    for node in G.nodes:
        net.add_node(node, label=node)
        
    for edge in G.edges(data=True):
        net.add_edge(edge[0], edge[1], value=edge[2]['weight'])
    
    # Mostrar el grafo
    net.show("graph.html")
    st.write("Visualización interactiva disponible en el siguiente enlace:")
    st.markdown("[Abrir grafo interactivo](graph.html)", unsafe_allow_html=True)

# Interfaz Streamlit: Selección de la página (Filtros o Similitudes)
page = st.sidebar.radio("Selecciona una sección", ["Resultados de los Filtros", "Filtrar por Similitudes"])

if page == "Resultados de los Filtros":
    # Mostrar los resultados basados en los filtros de consulta

    # Conexión para el sistema de consultas
    collection = get_mongo_connection()

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

elif page == "Filtrar por Similitudes":
    # Mostrar la interfaz para filtrar similitudes

    st.title("Filtrar por Similitudes")
    
    # Filtro: Selección de providencia
    collection_similitudes = get_mongo_connection_similitudes()
    providencias_similitudes = get_similitudes_providencias(collection_similitudes)
    selected_providencia = st.sidebar.selectbox("Selecciona una providencia de similitudes", providencias_similitudes)

    # Barra deslizadora para el máximo de similitud
    max_similitud = st.sidebar.slider("Similitud máxima", 0.0, 100.0, 100.0, 0.1)

    if selected_providencia:
        # Obtener las similitudes de la sentencia seleccionada dentro del rango
        similitudes = get_similitudes_from_mongo(selected_providencia, max_similitud)
        
        if similitudes:
            st.write(f"Similitudes encontradas para la providencia {selected_providencia} con similitud máxima de {max_similitud}:")
            
            # Crear grafo de similitudes
            G = create_similarity_graph(similitudes)
            
            # Visualizar el grafo
            visualize_graph(G)
        else:
            st.write(f"No se encontraron similitudes para la providencia {selected_providencia} dentro del rango de similitudes especificado.")

