import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="GastroAstur",
    page_icon="🍽️",
    layout="wide"
)

# --- Carga de datos ---
@st.cache_data
@st.cache_data
def cargar_datos():
    df = pd.read_json("data/processed/restaurantes_clean.json")
    cruce = pd.read_json("data/processed/locales_por_habitante.json")
    
    # Wikidata — maneja lista vacía o columnas distintas
    with open("data/raw/wikidata_gastronomia.json", encoding="utf-8") as f:
        wiki = json.load(f)
    
    if wiki:
        df_wiki = pd.DataFrame(wiki)
        # Filtra filas sin nombre o con ID como nombre
        df_wiki = df_wiki[
            df_wiki["nombre"].notna() &
            (df_wiki["nombre"].str.len() > 2) &
            ~df_wiki["nombre"].str.startswith("Q")
        ].reset_index(drop=True)
    else:
        df_wiki = pd.DataFrame(columns=["id", "nombre", "descripcion"])

    return df, cruce, df_wiki
df, df_cruce, df_wiki = cargar_datos()


# --- Header ---
st.title("🍽️ GastroAstur")
st.markdown("Análisis exploratorio de la gastronomía asturiana con datos abiertos.")
st.divider()


# --- KPIs ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total locales", f"{len(df):,}")
col2.metric("Concejos con datos", df["ciudad"].nunique())
col3.metric("Tipos de cocina", df["cocina"].nunique())
col4.metric("Concejo más denso", df_cruce.iloc[0]["concejo"].capitalize())
st.divider()


# --- Sección 1: Distribución por tipo ---
st.subheader("Distribución por tipo de local")
col1, col2 = st.columns(2)

with col1:
    conteo_tipo = df["amenity"].value_counts().reset_index()
    conteo_tipo.columns = ["tipo", "cantidad"]
    fig1 = px.bar(conteo_tipo, x="tipo", y="cantidad",
                  color="tipo",
                  color_discrete_sequence=px.colors.qualitative.Set2,
                  labels={"tipo": "Tipo", "cantidad": "Nº locales"})
    fig1.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    fig2 = px.pie(conteo_tipo, names="tipo", values="cantidad",
                  color_discrete_sequence=px.colors.qualitative.Set2,
                  hole=0.4)
    fig2.update_layout(showlegend=True)
    st.plotly_chart(fig2, use_container_width=True)


# --- Sección 2: Top cocinas ---
st.subheader("Top 10 tipos de cocina")
top_cocinas = df["cocina"].value_counts().head(10).reset_index()
top_cocinas.columns = ["cocina", "cantidad"]
fig3 = px.bar(top_cocinas, x="cantidad", y="cocina",
              orientation="h",
              color="cantidad",
              color_continuous_scale="Teal",
              labels={"cocina": "", "cantidad": "Nº locales"})
fig3.update_layout(plot_bgcolor="rgba(0,0,0,0)", yaxis={"categoryorder": "total ascending"})
st.plotly_chart(fig3, use_container_width=True)


# --- Sección 3: Densidad por concejo ---
st.subheader("Densidad gastronómica por concejo")
st.caption("Locales por cada 1000 habitantes")
fig4 = px.bar(
    df_cruce.sort_values("locales_por_1000hab", ascending=True),
    x="locales_por_1000hab",
    y="concejo",
    orientation="h",
    color="locales_por_1000hab",
    color_continuous_scale="RdYlGn",
    labels={"concejo": "", "locales_por_1000hab": "Locales / 1000 hab"},
    hover_data=["num_locales", "poblacion"]
)
fig4.update_layout(plot_bgcolor="rgba(0,0,0,0)", yaxis={"categoryorder": "total ascending"})
st.plotly_chart(fig4, use_container_width=True)


# --- Sección 4: Mapa ---
st.subheader("Mapa de locales")

col_filtro1, col_filtro2 = st.columns(2)
with col_filtro1:
    tipos = ["Todos"] + sorted(df["amenity"].dropna().unique().tolist())
    tipo_sel = st.selectbox("Filtrar por tipo", tipos)

with col_filtro2:
    cocinas = ["Todas"] + sorted(df["cocina"].dropna().unique().tolist())
    cocina_sel = st.selectbox("Filtrar por cocina", cocinas)

df_mapa = df.dropna(subset=["lat", "lon"]).copy()
if tipo_sel != "Todos":
    df_mapa = df_mapa[df_mapa["amenity"] == tipo_sel]
if cocina_sel != "Todas":
    df_mapa = df_mapa[df_mapa["cocina"] == cocina_sel]

st.caption(f"Mostrando {len(df_mapa)} locales")

fig5 = px.scatter_mapbox(
    df_mapa,
    lat="lat", lon="lon",
    color="amenity",
    hover_name="nombre",
    hover_data={"cocina": True, "ciudad": True, "lat": False, "lon": False},
    color_discrete_sequence=px.colors.qualitative.Set2,
    zoom=7,
    height=500
)
fig5.update_layout(mapbox_style="carto-positron",
                   margin={"r": 0, "t": 0, "l": 0, "b": 0})
st.plotly_chart(fig5, use_container_width=True)


# --- Sección 5: Wikidata ---
st.subheader("🧀 Gastronomía asturiana en Wikidata")
st.dataframe(
    df_wiki[["nombre", "descripcion"]].reset_index(drop=True),
    use_container_width=True,
    height=300
)

# --- Sección 6: Comparativa Oviedo vs Gijón vs Avilés ---
st.divider()
st.subheader("🏙️ Comparativa Oviedo vs Gijón vs Avilés")

ciudades_cmp = ["oviedo", "gijón", "avilés"]
df_cmp = df[df["ciudad"].isin(ciudades_cmp)].copy()

col1, col2 = st.columns(2)

with col1:
    # Distribución por tipo
    tipo_ciudad = df_cmp.groupby(["ciudad", "amenity"]).size().reset_index(name="cantidad")
    fig6 = px.bar(
        tipo_ciudad,
        x="ciudad", y="cantidad", color="amenity",
        barmode="group",
        color_discrete_sequence=px.colors.qualitative.Set2,
        labels={"ciudad": "Ciudad", "cantidad": "Nº locales", "amenity": "Tipo"},
        title="Tipos de local por ciudad"
    )
    fig6.update_layout(plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig6, use_container_width=True)

with col2:
    # Top 5 cocinas por ciudad
    cocina_ciudad = (
        df_cmp.dropna(subset=["cocina"])
        .groupby(["ciudad", "cocina"])
        .size()
        .reset_index(name="cantidad")
    )
    top_por_ciudad = (
        cocina_ciudad.sort_values("cantidad", ascending=False)
        .groupby("ciudad").head(5)
    )
    fig7 = px.bar(
        top_por_ciudad,
        x="cantidad", y="cocina", color="ciudad",
        orientation="h",
        barmode="group",
        color_discrete_sequence=["#e07b39", "#2196a6", "#27ae60"],
        labels={"cocina": "", "cantidad": "Nº locales", "ciudad": "Ciudad"},
        title="Top 5 cocinas por ciudad"
    )
    fig7.update_layout(plot_bgcolor="rgba(0,0,0,0)",
                       yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig7, use_container_width=True)

# Métricas comparativas
col1, col2, col3 = st.columns(3)
for col, ciudad in zip([col1, col2, col3], ciudades_cmp):
    d = df_cmp[df_cmp["ciudad"] == ciudad]
    col.metric(
        ciudad.capitalize(),
        f"{len(d)} locales",
        f"{d['cocina'].nunique()} tipos de cocina"
    )


# --- Sección 7: Cocinas por zona geográfica ---
st.divider()
st.subheader("🗺️ Cocinas por zona geográfica")
st.caption("Zona oeste: Navia, Luarca, Cangas del Narcea · Zona centro: Oviedo, Avilés, Siero · Zona este: Gijón, Llanes, Ribadesella")

zonas = {
    "oeste":  ["navia", "luarca", "cangas del narcea", "castropol", "vegadeo"],
    "centro": ["oviedo", "avilés", "siero", "mieres", "langreo"],
    "este":   ["gijón", "llanes", "ribadesella", "villaviciosa", "colunga"],
}

def asignar_zona(ciudad):
    if pd.isna(ciudad):
        return None
    for zona, ciudades in zonas.items():
        if ciudad in ciudades:
            return zona
    return None

df_zonas = df.copy()
df_zonas["zona"] = df_zonas["ciudad"].apply(asignar_zona)
df_zonas = df_zonas.dropna(subset=["zona", "cocina"])

zona_sel = st.radio("Selecciona zona", ["oeste", "centro", "este"], horizontal=True)

df_zona_fil = df_zonas[df_zonas["zona"] == zona_sel]
top_cocinas_zona = df_zona_fil["cocina"].value_counts().head(10).reset_index()
top_cocinas_zona.columns = ["cocina", "cantidad"]

fig8 = px.bar(
    top_cocinas_zona,
    x="cantidad", y="cocina",
    orientation="h",
    color="cantidad",
    color_continuous_scale="Teal",
    labels={"cocina": "", "cantidad": "Nº locales"},
    title=f"Top 10 cocinas — zona {zona_sel}"
)
fig8.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    yaxis={"categoryorder": "total ascending"}
)
st.plotly_chart(fig8, use_container_width=True)

col1, col2, col3 = st.columns(3)
col1.metric("Locales en zona", len(df_zona_fil))
col2.metric("Tipos de cocina", df_zona_fil["cocina"].nunique())
col3.metric("Cocina más frecuente", df_zona_fil["cocina"].value_counts().index[0] if len(df_zona_fil) > 0 else "—")


# --- Sección 8: Predicción interactiva ---
st.divider()
st.subheader("🤖 Predicción interactiva")
st.caption("Introduce una cocina y una ciudad para predecir el tipo de local.")

import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

@st.cache_resource
def cargar_modelo():
    df_m = pd.read_json("data/processed/restaurantes_clean.json").fillna("desconocido")
    conteo = df_m["amenity"].value_counts()
    clases_validas = conteo[conteo >= 10].index
    df_m = df_m[df_m["amenity"].isin(clases_validas)]

    le_c = LabelEncoder()
    le_ci = LabelEncoder()
    le_a = LabelEncoder()

    df_m["cocina_enc"]  = le_c.fit_transform(df_m["cocina"])
    df_m["ciudad_enc"]  = le_ci.fit_transform(df_m["ciudad"])
    df_m["amenity_enc"] = le_a.fit_transform(df_m["amenity"])

    X = df_m[["cocina_enc", "ciudad_enc"]].values
    y = df_m["amenity_enc"].values

    clf = RandomForestClassifier(n_estimators=200, class_weight="balanced", random_state=42)
    clf.fit(X, y)
    return clf, le_c, le_ci, le_a

clf, le_cocina, le_ciudad, le_amenity = cargar_modelo()

col1, col2 = st.columns(2)
with col1:
    cocinas_disponibles = sorted(df["cocina"].dropna().unique().tolist())
    cocina_input = st.selectbox("Tipo de cocina", cocinas_disponibles)
with col2:
    ciudades_disponibles = sorted(df["ciudad"].dropna().unique().tolist())
    ciudad_input = st.selectbox("Ciudad", ciudades_disponibles)

if st.button("Predecir tipo de local", type="primary"):
    cocina_enc = le_cocina.transform([cocina_input])[0]
    ciudad_enc = le_ciudad.transform([ciudad_input])[0]
    pred = clf.predict([[cocina_enc, ciudad_enc]])[0]
    proba = clf.predict_proba([[cocina_enc, ciudad_enc]])[0]
    clase = le_amenity.inverse_transform([pred])[0]

    st.success(f"**Tipo predicho: {clase.upper()}**")

    # Gráfico de probabilidades
    prob_df = pd.DataFrame({
        "tipo": le_amenity.classes_,
        "probabilidad": proba
    }).sort_values("probabilidad", ascending=True)

    fig9 = px.bar(
        prob_df,
        x="probabilidad", y="tipo",
        orientation="h",
        color="probabilidad",
        color_continuous_scale="Blues",
        labels={"tipo": "", "probabilidad": "Probabilidad"},
        range_x=[0, 1]
    )
    fig9.update_layout(plot_bgcolor="rgba(0,0,0,0)", showlegend=False)
    st.plotly_chart(fig9, use_container_width=True)

# --- Footer ---
st.divider()
st.caption("Datos: OpenStreetMap · INE · Nominatim · Wikidata | Proyecto GastroAstur 2025")