import pandas as pd
import re
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sqlalchemy import create_engine
from sentence_transformers import SentenceTransformer
import hdbscan
import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.cluster import KMeans

server = 'localhost,1433'   # o la IP de tu contenedor si es externa
database = 'Supermarkets'
username = 'sa'
password = 'Aleja_23'

engine = create_engine(
    f"mssql+pyodbc://sa:{password}@localhost:1433/{database}?driver=ODBC+Driver+17+for+SQL+Server"
)


# ------------------------
# 1. Cargar datos (ejemplo: desde SQL o CSV)
# ------------------------
df = pd.read_sql("SELECT ProductID, Name, Weight, Unit FROM DimProduct", engine)
# df = pd.DataFrame({
#     "ProductID": [1,2,3,4,5],
#     "ProductName": ["Leche Entera 1L", "Leche entera 1000 ml", "Yogur natural 125g", "Yogur Natural 0,125Kg", "Aceite oliva 1L"],
#     "Weight": [1,1,0.125,0.125,1],
#     "Unit": ["L","L","kg","kg","L"]
# })

# ------------------------
# 2. Limpieza de nombres
# ------------------------
def clean_name(name):
    name = name.lower()
    name = re.sub(r"[\d,.]+\s?(kg|g|ml|l|litros?|metros?)", "", name)  # quita unidades si están en el texto
    name = re.sub(r"[^a-záéíóúüñ\s]", "", name)  # quita caracteres raros
    name = re.sub(r"\s+", " ", name).strip()
    return name

df["CleanName"] = df["Name"].apply(clean_name)

# ------------------------
# 3. Embeddings
# ------------------------
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
name_embeddings = model.encode(df["Name"].tolist(), show_progress_bar=True)

scaler = Pipeline([
    ("imputer", SimpleImputer(strategy="mean")),
    ("scaler", StandardScaler())
])
scaled_weight = scaler.fit_transform(df[["Weight"]])

encoder = Pipeline([
    ("imputer", SimpleImputer(strategy="constant", fill_value=0)),
    ("encoder", OneHotEncoder(sparse_output=False, handle_unknown="ignore"))
])
encoded_unit = encoder.fit_transform(df[["Unit"]])

final_embeddings = np.hstack([name_embeddings, scaled_weight, encoded_unit])

pca = PCA(n_components=50, random_state=42)
reduced_embeddings = pca.fit_transform(final_embeddings)

# ------------------------
# 4. Clustering con HDBSCAN
# ------------------------
clusterer = hdbscan.HDBSCAN(min_cluster_size=10,cluster_selection_epsilon=0.5)
hdb_labels = clusterer.fit_predict(reduced_embeddings)

df["ClusterID"] = hdb_labels

mask_noise = df["ClusterID"] == -1
num_noise = mask_noise.sum()
print(f"Productos en ruido (-1): {num_noise}")

if num_noise > 0:
    # Solo los embeddings de los productos que fueron ruido
    noise_embeddings = reduced_embeddings[mask_noise]

    # Definir número de clusters para el ruido
    k = max(10, num_noise // 500)  # ajusta: 1 cluster cada ~500 productos
    kmeans = KMeans(n_clusters=k, random_state=42)
    noise_labels = kmeans.fit_predict(noise_embeddings)

    # Offset para que no choquen con los de HDBSCAN
    max_cluster = df["ClusterID"].max()
    noise_labels_offset = noise_labels + max_cluster + 1

    # Asignar de vuelta
    df.loc[mask_noise, "ClusterID"] = noise_labels_offset

# ------------------------
# 5. Resultado
# ------------------------
print(df[["ProductID", "Name", "CleanName", "ClusterID"]])

print(df["ClusterID"].value_counts())