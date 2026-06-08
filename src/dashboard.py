import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="GastroAstur — Gastronomía en Asturias",
    layout="wide",
    initial_sidebar_state="expanded",
)

#Paleta de colores 
COLORES = ["#2c7bb6", "#e07b39", "#27ae60", "#d62728", "#9467bd", "#8c564b"]

#Carga y normalización de datos
@st.cache_data
def cargar_datos():
    df = pd.read_json("data/processed/restaurantes_clean.json")

    #Normalizar variantes de nombres de ciudad (bilinguismo asturiano)
    variantes = {
        "gijón/xixón": "gijón",
        "oviedo/uviéu": "oviedo",
        "avilés/avilés": "avilés",
    }
    df["ciudad"] = df["ciudad"].replace(variantes)

    cruce = pd.read_json("data/processed/locales_por_habitante.json")

    with open("data/raw/wikidata_gastronomia.json", encoding="utf-8") as f:
        wiki = json.load(f)

    if wiki:
        df_wiki = pd.DataFrame(wiki)
        df_wiki = df_wiki[
            df_wiki["nombre"].notna()
            & (df_wiki["nombre"].str.len() > 2)
            & ~df_wiki["nombre"].str.startswith("Q")
        ].reset_index(drop=True)
    else:
        df_wiki = pd.DataFrame(columns=["id", "nombre", "descripcion"])

    return df, cruce, df_wiki


df, df_cruce, df_wiki = cargar_datos()

#Métricas de calidad del dato
pct_nombre = 100 * df["nombre"].notna().mean()
pct_cocina = 100 * df["cocina"].notna().mean()
pct_geo = 100 * (df["lat"].notna() & df["lon"].notna()).mean()

#Sidebar
with st.sidebar:
    st.title("GastroAstur")
    st.caption("Gastronomía asturiana con datos abiertos")
    st.divider()

    st.markdown("**Resumen del dataset**")
    st.metric("Locales totales", f"{len(df):,}")
    st.metric("Concejos analizados", df["ciudad"].nunique())
    st.metric("Tipos de cocina únicos", df["cocina"].nunique())

    st.divider()
    st.markdown("**Completitud de datos**")
    st.progress(pct_nombre / 100, text=f"Con nombre: {pct_nombre:.0f}%")
    st.progress(pct_cocina / 100, text=f"Con cocina: {pct_cocina:.0f}%")
    st.progress(pct_geo / 100, text=f"Geolocalizados: {pct_geo:.0f}%")

    st.divider()
    st.caption("Fuentes: OSM · INE · Nominatim · Wikidata")

#Header
st.title("GastroAstur")
st.markdown(
    "Análisis exploratorio de la gastronomía asturiana combinando datos de "
    "**OpenStreetMap**, **INE**, **Nominatim** y **Wikidata**."
)

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Visión General", "Mapa", "Análisis Territorial", "Gastronomía Asturiana", "Predicción ML"]
)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — Visión General
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    st.subheader("Indicadores clave")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total locales", f"{len(df):,}")
    c2.metric("Concejos con datos", df["ciudad"].nunique())
    c3.metric("Tipos de cocina", df["cocina"].nunique())
    c4.metric("Concejo más denso", df_cruce.iloc[0]["concejo"].capitalize())

    c5, c6, c7 = st.columns(3)
    c5.metric("Con nombre", f"{pct_nombre:.0f}%")
    c6.metric("Con tipo de cocina", f"{pct_cocina:.0f}%")
    c7.metric("Geolocalizados", f"{pct_geo:.0f}%")

    st.divider()

    # Distribución por tipo
    st.subheader("Distribución por tipo de local")
    conteo_tipo = df["amenity"].value_counts().reset_index()
    conteo_tipo.columns = ["tipo", "cantidad"]

    col1, col2 = st.columns(2)
    with col1:
        fig1 = px.bar(
            conteo_tipo, x="tipo", y="cantidad",
            color="tipo",
            color_discrete_sequence=COLORES,
            labels={"tipo": "Tipo", "cantidad": "Nº locales"},
            text_auto=True,
        )
        fig1.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)")
        fig1.update_traces(textposition="outside")
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        fig2 = px.pie(
            conteo_tipo, names="tipo", values="cantidad",
            color_discrete_sequence=COLORES,
            hole=0.4,
        )
        fig2.update_traces(textinfo="percent+label")
        st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # Top cocinas
    st.subheader("Top 10 tipos de cocina")
    top_cocinas = df["cocina"].value_counts().head(10).reset_index()
    top_cocinas.columns = ["cocina", "cantidad"]
    fig3 = px.bar(
        top_cocinas, x="cantidad", y="cocina",
        orientation="h",
        color="cantidad",
        color_continuous_scale="Teal",
        labels={"cocina": "", "cantidad": "Nº locales"},
        text_auto=True,
    )
    fig3.update_layout(plot_bgcolor="rgba(0,0,0,0)", yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig3, use_container_width=True)

    st.divider()

    # Densidad por concejo
    st.subheader("Densidad gastronómica por concejo")
    st.caption("Locales por cada 1.000 habitantes")
    df_cruce_sorted = df_cruce.sort_values("locales_por_1000hab", ascending=True)
    fig4 = px.bar(
        df_cruce_sorted,
        x="locales_por_1000hab", y="concejo",
        orientation="h",
        color="locales_por_1000hab",
        color_continuous_scale="RdYlGn",
        labels={"concejo": "", "locales_por_1000hab": "Locales / 1.000 hab"},
        hover_data=["num_locales", "poblacion"],
        text=df_cruce_sorted["locales_por_1000hab"].round(2),
    )
    fig4.update_layout(plot_bgcolor="rgba(0,0,0,0)", yaxis={"categoryorder": "total ascending"})
    fig4.update_traces(textposition="outside")
    st.plotly_chart(fig4, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — Mapa
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    st.subheader("Mapa de locales")

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        tipos = ["Todos"] + sorted(df["amenity"].dropna().unique().tolist())
        tipo_sel = st.selectbox("Tipo de local", tipos, key="mapa_tipo")
    with col_f2:
        cocinas = ["Todas"] + sorted(df["cocina"].dropna().unique().tolist())
        cocina_sel = st.selectbox("Tipo de cocina", cocinas, key="mapa_cocina")
    with col_f3:
        municipios = ["Todos"] + sorted(df["ciudad"].dropna().unique().tolist())
        municipio_sel = st.selectbox("Municipio", municipios, key="mapa_municipio")

    df_mapa = df.dropna(subset=["lat", "lon"]).copy()
    if tipo_sel != "Todos":
        df_mapa = df_mapa[df_mapa["amenity"] == tipo_sel]
    if cocina_sel != "Todas":
        df_mapa = df_mapa[df_mapa["cocina"] == cocina_sel]
    if municipio_sel != "Todos":
        df_mapa = df_mapa[df_mapa["ciudad"] == municipio_sel]

    zoom_inicial = 9 if municipio_sel != "Todos" else 7
    st.caption(f"Mostrando **{len(df_mapa)}** locales")

    fig5 = px.scatter_mapbox(
        df_mapa,
        lat="lat", lon="lon",
        color="amenity",
        hover_name="nombre",
        hover_data={"cocina": True, "ciudad": True, "lat": False, "lon": False},
        color_discrete_sequence=COLORES,
        zoom=zoom_inicial,
        height=560,
    )
    fig5.update_layout(
        mapbox_style="carto-positron",
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
    )
    st.plotly_chart(fig5, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — Análisis Territorial
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    st.subheader("Comparativa Oviedo · Gijón · Avilés")

    ciudades_cmp = ["oviedo", "gijón", "avilés"]
    df_cmp = df[df["ciudad"].isin(ciudades_cmp)].copy()

    c1, c2, c3 = st.columns(3)
    for col, ciudad in zip([c1, c2, c3], ciudades_cmp):
        d = df_cmp[df_cmp["ciudad"] == ciudad]
        col.metric(ciudad.capitalize(), f"{len(d)} locales", f"{d['cocina'].nunique()} tipos de cocina")

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        tipo_ciudad = df_cmp.groupby(["ciudad", "amenity"]).size().reset_index(name="cantidad")
        fig6 = px.bar(
            tipo_ciudad,
            x="ciudad", y="cantidad", color="amenity",
            barmode="group",
            color_discrete_sequence=COLORES,
            labels={"ciudad": "Ciudad", "cantidad": "Nº locales", "amenity": "Tipo"},
            title="Tipos de local por ciudad",
        )
        fig6.update_layout(plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig6, use_container_width=True)

    with col2:
        cocina_ciudad = (
            df_cmp.dropna(subset=["cocina"])
            .groupby(["ciudad", "cocina"])
            .size()
            .reset_index(name="cantidad")
        )
        top_por_ciudad = (
            cocina_ciudad.sort_values("cantidad", ascending=False).groupby("ciudad").head(5)
        )
        fig7 = px.bar(
            top_por_ciudad,
            x="cantidad", y="cocina", color="ciudad",
            orientation="h", barmode="group",
            color_discrete_sequence=["#2c7bb6", "#e07b39", "#27ae60"],
            labels={"cocina": "", "cantidad": "Nº locales", "ciudad": "Ciudad"},
            title="Top 5 cocinas por ciudad",
        )
        fig7.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", yaxis={"categoryorder": "total ascending"}
        )
        st.plotly_chart(fig7, use_container_width=True)

    # Radar: composición porcentual de tipos por ciudad
    amenity_pivot = df_cmp.groupby(["ciudad", "amenity"]).size().reset_index(name="n")
    totales = amenity_pivot.groupby("ciudad")["n"].transform("sum")
    amenity_pivot["pct"] = amenity_pivot["n"] / totales * 100
    categorias = sorted(amenity_pivot["amenity"].unique().tolist())

    fig_radar = go.Figure()
    colores_radar = ["#2c7bb6", "#e07b39", "#27ae60"]
    for ciudad, color in zip(ciudades_cmp, colores_radar):
        subset = amenity_pivot[amenity_pivot["ciudad"] == ciudad]
        valores = [
            float(subset[subset["amenity"] == c]["pct"].values[0])
            if c in subset["amenity"].values
            else 0.0
            for c in categorias
        ]
        valores_cerrados = valores + valores[:1]
        cats_cerradas = categorias + [categorias[0]]
        fig_radar.add_trace(
            go.Scatterpolar(
                r=valores_cerrados,
                theta=cats_cerradas,
                fill="toself",
                name=ciudad.capitalize(),
                line_color=color,
            )
        )
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, ticksuffix="%")),
        title="Composición de tipos de local (% por ciudad)",
        showlegend=True,
    )
    st.plotly_chart(fig_radar, use_container_width=True)

    st.divider()

    # Cocinas por zona geográfica
    st.subheader("Cocinas por zona geográfica")
    st.caption(
        "Zona oeste: Navia, Luarca, Cangas del Narcea · "
        "Zona centro: Oviedo, Avilés, Siero · "
        "Zona este: Gijón, Llanes, Ribadesella"
    )

    zonas = {
        "oeste":  [  "castropol", "vegadeo", "taramundi", "san tirso de abres",
    "san martín de oscos", "santa eulalia de oscos", "villanueva de oscos",
    "navia", "coaña", "el franco", "tapia de casariego", "boal",
    "illano", "pesoz", "grandas de salime", "villayón",
    "valdés", "cudillero", "salas", "tineo", "allande",
    "cangas del narcea", "degaña", "ibias", "Boal", "vegadeo", "tapia de casariego"],
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

    col_z1, col_z2 = st.columns([3, 1])
    with col_z1:
        fig8 = px.bar(
            top_cocinas_zona, x="cantidad", y="cocina",
            orientation="h", color="cantidad",
            color_continuous_scale="Teal",
            labels={"cocina": "", "cantidad": "Nº locales"},
            title=f"Top 10 cocinas — zona {zona_sel}",
            text_auto=True,
        )
        fig8.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", yaxis={"categoryorder": "total ascending"}
        )
        st.plotly_chart(fig8, use_container_width=True)

    with col_z2:
        st.metric("Locales en zona", len(df_zona_fil))
        st.metric("Tipos de cocina", df_zona_fil["cocina"].nunique())
        cocina_top = (
            df_zona_fil["cocina"].value_counts().index[0] if len(df_zona_fil) > 0 else "—"
        )
        st.metric("Cocina más frecuente", cocina_top)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — Gastronomía Asturiana (Wikidata)
# ─────────────────────────────────────────────────────────────────────────────
with tab4:
    st.subheader("Gastronomía asturiana en Wikidata")
    st.markdown(
        "Platos y productos típicos documentados en Wikidata "
        "para la gastronomía asturiana."
    )
    st.divider()

    for _, row in df_wiki.iterrows():
        with st.container(border=True):
            st.markdown(f"### {row['nombre']}")
            if pd.notna(row.get("descripcion")):
                st.caption(row["descripcion"])
            wiki_id = row.get("id")
            if pd.notna(wiki_id):
                st.markdown(f"[Ver en Wikidata →](https://www.wikidata.org/wiki/{wiki_id})")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 5 — Predicción ML
# ─────────────────────────────────────────────────────────────────────────────
with tab5:
    st.subheader("Predicción interactiva")
    st.caption("Introduce una cocina y una ciudad para predecir el tipo de local más probable.")

    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import LabelEncoder

    @st.cache_resource
    def cargar_modelo():
        df_m = pd.read_json("data/processed/restaurantes_clean.json").fillna("desconocido")
        conteo = df_m["amenity"].value_counts()
        clases_validas = conteo[conteo >= 10].index
        df_m = df_m[df_m["amenity"].isin(clases_validas)]

        le_c  = LabelEncoder()
        le_ci = LabelEncoder()
        le_a  = LabelEncoder()

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
        cocina_input = st.selectbox("Tipo de cocina", cocinas_disponibles, key="pred_cocina")
    with col2:
        ciudades_disponibles = sorted(df["ciudad"].dropna().unique().tolist())
        ciudad_input = st.selectbox("Ciudad", ciudades_disponibles, key="pred_ciudad")

    if st.button("Predecir tipo de local", type="primary"):
        try:
            cocina_enc = le_cocina.transform([cocina_input])[0]
            ciudad_enc = le_ciudad.transform([ciudad_input])[0]
            pred  = clf.predict([[cocina_enc, ciudad_enc]])[0]
            proba = clf.predict_proba([[cocina_enc, ciudad_enc]])[0]
            clase = le_amenity.inverse_transform([pred])[0]
            confianza = proba.max() * 100

            st.success(f"**Tipo predicho: {clase.upper()}** — confianza: {confianza:.0f}%")

            prob_df = pd.DataFrame(
                {"tipo": le_amenity.classes_, "probabilidad": proba}
            ).sort_values("probabilidad", ascending=True)

            fig9 = px.bar(
                prob_df, x="probabilidad", y="tipo",
                orientation="h",
                color="probabilidad",
                color_continuous_scale="Blues",
                labels={"tipo": "", "probabilidad": "Probabilidad"},
                range_x=[0, 1],
                text=prob_df["probabilidad"].map("{:.0%}".format),
            )
            fig9.update_layout(plot_bgcolor="rgba(0,0,0,0)", showlegend=False)
            fig9.update_traces(textposition="outside")
            st.plotly_chart(fig9, use_container_width=True)

        except ValueError as e:
            st.warning(f"No se encontraron datos para esta combinación: {e}")

    with st.expander("Importancia de variables del modelo"):
        clf_loaded, *_ = cargar_modelo()
        feat_imp = pd.DataFrame(
            {
                "variable": ["Tipo de cocina", "Ciudad"],
                "importancia": clf_loaded.feature_importances_,
            }
        ).sort_values("importancia", ascending=True)
        fig10 = px.bar(
            feat_imp, x="importancia", y="variable",
            orientation="h",
            color="importancia",
            color_continuous_scale="Blues",
            labels={"variable": "", "importancia": "Importancia"},
            range_x=[0, 1],
            text_auto=":.2f",
        )
        fig10.update_layout(plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig10, use_container_width=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "Datos: [OpenStreetMap](https://www.openstreetmap.org) · "
    "[INE](https://www.ine.es) · "
    "[Nominatim](https://nominatim.org) · "
    "[Wikidata](https://www.wikidata.org) | "
    "Proyecto GastroAstur 2025"
)
