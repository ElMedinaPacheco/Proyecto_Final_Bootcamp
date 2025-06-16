
# === IMPORTAR LIBRERIAS===
import pandas as pd
import os
import glob
import re
import matplotlib.pyplot as plt
import numpy as np
import geopandas as gpd
import mapclassify              # Clasificación de color
import seaborn as sns
from sklearn.model_selection import train_test_split
from scipy.stats import chi2_contingency
import streamlit as st
import io
import snowflake.connector
from streamlit_option_menu import option_menu

# === IMPORTAR BASE DE DATOS ===

# === CARGAR BASE DE DATOS ===
ruta_archivo = r"C:\Users\SoyCurie\Desktop\ProyectoBootcamp\datos\df_Total.csv"

# Cargar archivo CSV
df_Total = pd.read_csv(ruta_archivo, encoding="utf-8")

# Mostrar los primeros registros
print(df_Total.head())

# === PREPROCESAMIENTO GLOBAL DE DATOS ===

cols_sumar = ['GRADUADOS', 'ADMITIDOS', 'PRIMER CURSO']

# Agrupar todo el dataset sin los valores a sumar
df_Total_Agrupado = df_Total.groupby(
    [col for col in df_Total.columns if col not in cols_sumar],
    as_index=False
)[cols_sumar].sum()

# Función resumen por género
def resumen_genero(df, etapa):
    resumen = df.groupby(['AÑO', 'SEXO']).agg({etapa: 'sum'}).reset_index()
    pivot = resumen.pivot(index='AÑO', columns='SEXO', values=etapa)
    pivot['TOTAL'] = pivot.sum(axis=1)
    pivot['% MUJERES'] = (pivot.get('Femenino', 0) / pivot['TOTAL']) * 100
    return pivot

# Crear resúmenes globales
resumen_admitidos = resumen_genero(df_Total_Agrupado, 'ADMITIDOS')
resumen_matriculados = resumen_genero(df_Total_Agrupado, 'PRIMER CURSO')
resumen_graduados = resumen_genero(df_Total_Agrupado, 'GRADUADOS')

# Convertir índice a numérico
resumen_admitidos.index = pd.to_numeric(resumen_admitidos.index)
resumen_matriculados.index = pd.to_numeric(resumen_matriculados.index)
resumen_graduados.index = pd.to_numeric(resumen_graduados.index)

# === ESTILOS CSS PERSONALIZADOS CON SIDEBAR EN GRADIENTE ===
st.markdown("""
<style>
body, .stApp {
    background: radial-gradient(circle at left, #063624, #0d0e0e);
    color: white;
}
section[data-testid="stSidebar"] {
    background: radial-gradient(circle at left, #063624, #0d0e0e);
    color: white;
    border-right: 1px solid #1f1f1f;
}

h1, h2, h3 {
    color: #ffffff;
}
div[data-testid="stHorizontalBlock"] > div {
    background-color: #1e1e1e;
    border-radius: 10px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    border: 1px solid #333;
}
.stButton > button {
    background-color: #10b981;
    color: white;
    border: none;
    padding: 0.6rem 1.2rem;
    border-radius: 8px;
    font-weight: bold;
    margin-top: 10px;
}
.stButton > button:hover {
    background-color: #0e9b72;
}
[data-testid="stMarkdownContainer"] > p {
    font-size: 1.1rem;
}
</style>
""", unsafe_allow_html=True)

# === SIDEBAR CON MENÚ DE OPCIONES ===
if "selected_menu" not in st.session_state:
    st.session_state["selected_menu"] = "Inicio"

with st.sidebar:
    selected = option_menu(
        menu_title="Mujeres en TIC",
        options=["Inicio", "Graficos", "Información"],
        icons=["house-fill", "diagram-3-fill", "envelope-fill"],
        menu_icon="menu-button-wide",
        default_index=["Inicio", "Graficos", "Información"].index(st.session_state["selected_menu"]),
        styles={
            "container": {
                "background-color": "#0d0e0e",
                "padding": "5px",
                "border-radius": "0px",
                "border": "none"
            },
            "icon": {
                "color": "white",
                "font-size": "20px"
            },
            "nav-link": {
                "color": "white",
                "font-size": "16px",
                "text-align": "left",
                "--hover-color": "#222222",
            },
            "nav-link-selected": {
                "background-color": "#1dbe82",
                "color": "#0d0e0e",
                "font-weight": "bold",
                "icon-color": "#0d0e0e",
            },
        }
    )

# === CONTENIDO SEGÚN SECCIÓN ===
if selected == "Inicio":
    st.title("📊 Análisis de Participación de Mujeres en Carreras TIC en Colombia 2015 - 2023")
    st.markdown("Bienvenido al Dashboard para el análisis de datos usando 24 bases de datos obtenidas del Sistema Nacional de Información de la Educación Superior (SNIES) entre los años 2015 y 2023 de estudiantes admitidos, matriculados en primer curso y graduados.")

    with st.container():
        st.markdown("📌A pesar del crecimiento en la oferta académica y la demanda de carreras TIC y STEM en Colombia, la representación femenina en estos programas sigue siendo baja. Los datos reflejan diferencias significativas desde la inscripción hasta la graduación, con altas tasas de deserción femenina.")
    
    with st.container():
        st.markdown(""" ✅ Realizado por:
        <ul style='font-weight: bold;'>
            <li>Maria Andrea Jiménez</li>
            <li>Santiago Medina</li>
            <li>Valentina Nieves</li>
        </ul>
        """, unsafe_allow_html=True)
        
    # CENTRAR BOTÓN SIN COLUMNAS


    # Cambiar sección en sesión de Streamlit al hacer clic
    if st.button("Ver Graficos", use_container_width=True):
        st.session_state["selected_menu"] = "Graficos"
        st.rerun()




elif selected == "Graficos":
    st.title("Gráficas")

    st.markdown("### 📈 Evolución de estudiantes TIC por género")
    options = ["Femenino", "Masculino"]
    selection = st.segmented_control("Selecciona género a visualizar", options, selection_mode="single")

    if not selection:
        st.warning("Por favor selecciona un género.")
    else:
        genero = selection
        colores = {
            #"Femenino": "#1dbe82",
            #"Masculino": "#167753",
        }

        # === GRAFICA DE LÍNEAS ===
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(10, 6))

        if genero in resumen_admitidos.columns:
            ax.plot(resumen_admitidos.index, resumen_admitidos[genero], label=f'Admitidos - {genero}', color=colores.get(genero, '#ffffff'))
        if genero in resumen_matriculados.columns:
            ax.plot(resumen_matriculados.index, resumen_matriculados[genero], label=f'Matriculados - {genero}', linestyle='--', color=colores.get(genero,'#167753'))
        if genero in resumen_graduados.columns:
            ax.plot(resumen_graduados.index, resumen_graduados[genero], label=f'Graduados - {genero}', linestyle='-.', color=colores.get(genero,'#1dbe82'))

        ax.set_title('Evolución por género y etapa educativa')
        ax.set_xlabel('Año')
        ax.set_ylabel('Cantidad de personas')
        ax.grid(True, linestyle='--', linewidth=0.5, color='lightgray', alpha=0.4)
        ax.legend()
        st.pyplot(fig)

        # === GRÁFICAS DE BARRAS INDIVIDUALES POR ETAPA ===
        def graficar_barras_resumen(resumen_df, titulo, color):
            valores = resumen_df.get(genero)
            if valores is not None:
                fig_bar, ax_bar = plt.subplots(figsize=(8, 5))
                ax_bar.bar(valores.index.astype(str), valores.values, color=color)
                ax_bar.set_title(titulo)
                ax_bar.set_xlabel("Año")
                ax_bar.set_ylabel("Cantidad")
                ax_bar.grid(axis='y', linestyle='--', linewidth=0.5, color='gray', alpha=0.4)
                st.pyplot(fig_bar)

        
        graficar_barras_resumen(resumen_admitidos, "Admitidos por año", colores.get(genero, '#ffffff'))
        graficar_barras_resumen(resumen_matriculados, "Matriculados (Primer curso) por año", colores.get(genero, '#167753'))
        graficar_barras_resumen(resumen_graduados, "Graduados por año", colores.get(genero, '#1dbe82'))


    ##--------------------------------------------------------------
    # === GRADUADOS TIC POR NIVEL DE FORMACIÓN Y GÉNERO ===
    st.markdown("### 📈 Graduados TIC por nivel de formación y género")

    # Crear df_graduados a partir del total agrupado
    df_graduados = df_Total_Agrupado[df_Total_Agrupado['GRADUADOS'] > 0]

    # Segmentador de años
    opciones_anios = ["2019", "2020", "2021", "2022", "2023"]
    seleccion_anios = st.segmented_control("Selecciona años a visualizar", opciones_anios, selection_mode="multi")

    if not seleccion_anios:
        st.warning("Por favor selecciona al menos un año.")
    else:
        anios_int = list(map(int, seleccion_anios))  # convertir a int
        df_filtrado = df_graduados[df_graduados['AÑO'].isin(anios_int)]

        # Agrupar por nivel y sexo
        resumen_niveles = df_filtrado.groupby(['NIVEL DE FORMACIÓN', 'SEXO'])['GRADUADOS'].sum().unstack().fillna(0)

        # Plot con estilo oscuro
        plt.style.use('dark_background')
        fig_niveles, ax_niveles = plt.subplots(figsize=(10, 6))
        resumen_niveles.plot(kind='bar', ax=ax_niveles, color=['#1dbe82', '#167753'])

        ax_niveles.set_title('Graduados TIC por nivel de formación y género', fontsize=14)
        ax_niveles.set_xlabel('Nivel de formación', color='white')
        ax_niveles.set_ylabel('Número de graduados', color='white')
        ax_niveles.tick_params(axis='x', rotation=45, colors='white')
        ax_niveles.tick_params(axis='y', colors='white')
        ax_niveles.legend(title='Género', facecolor='black', edgecolor='white', labelcolor='white')

        plt.tight_layout()
        st.pyplot(fig_niveles)
    

    # === TOP 10 IES CON MÁS MUJERES ADMITIDAS EN TIC ===
    st.markdown("###  Top 10 IES con más mujeres admitidas en TIC")

    if not seleccion_anios:
        st.warning("Por favor selecciona al menos un año para visualizar los datos.")
    else:
        df_admitidas = df_Total_Agrupado[
            (df_Total_Agrupado['AÑO'].isin(anios_int)) & 
            (df_Total_Agrupado['SEXO'] == 'Femenino') &
            (df_Total_Agrupado['ADMITIDOS'] > 0)
        ]

        top_ies = (
            df_admitidas.groupby('INSTITUCIÓN DE EDUCACIÓN SUPERIOR (IES)')['ADMITIDOS']
            .sum()
            .sort_values(ascending=False)
            .head(10)
        )

        # Plot horizontal
        plt.style.use('dark_background')
        fig_top, ax_top = plt.subplots(figsize=(9, 5))
        top_ies.plot(kind='barh', ax=ax_top, color='#1dbe82')

        ax_top.set_title(f"Top 10 IES con más mujeres admitidas en TIC ({', '.join(seleccion_anios)})")
        ax_top.set_xlabel("Número de admitidas", color='white')
        ax_top.set_ylabel("IES", color='white')
        ax_top.tick_params(axis='x', colors='white')
        ax_top.tick_params(axis='y', colors='white')
        ax_top.invert_yaxis()

        plt.tight_layout()
        st.pyplot(fig_top)

    
    # === SEGMENTADOR EXCLUSIVO PARA MAPA ===
    st.markdown("### 🗺️ Mapa de mujeres en TIC por departamento")
    año_mapa = st.selectbox("Selecciona el año para visualizar en el mapa:", sorted(df_Total['AÑO'].unique(), reverse=True))

    # === CARGAR GEOJSON LOCAL (asegúrate que la ruta es correcta) ===
    try:
        gdf = gpd.read_file(r"C:\Users\SoyCurie\Desktop\ProyectoBootcamp\datos\colombia.geo.json")
        gdf['DPTO'] = gdf['DPTO'].astype(int)
    except Exception as e:
        st.error(f"Error al cargar el archivo GeoJSON: {e}")

    # === FILTRAR Y PROCESAR DATOS DE df_Total PARA MUJERES TIC EN ESE AÑO ===
    df_filtrado = df_Total[
        (df_Total['AÑO'] == año_mapa) &
        (df_Total['SEXO'].str.lower().str.strip() == 'femenino') &
        (df_Total['ID CINE CAMPO AMPLIO'] == 6)
    ]

    # === AGRUPAR POR DEPARTAMENTO ===
    admitidas = df_filtrado.groupby('CÓDIGO DEL DEPARTAMENTO (PROGRAMA)')['ADMITIDOS'].sum().reset_index()
    matriculadas = df_filtrado.groupby('CÓDIGO DEL DEPARTAMENTO (PROGRAMA)')['PRIMER CURSO'].sum().reset_index()
    graduadas = df_filtrado.groupby('CÓDIGO DEL DEPARTAMENTO (PROGRAMA)')['GRADUADOS'].sum().reset_index()

    # === UNIFICAR DATOS EN UN SOLO DF PARA MAPEO ===
    df_mapa = admitidas.merge(matriculadas, on='CÓDIGO DEL DEPARTAMENTO (PROGRAMA)', how='outer') \
                    .merge(graduadas, on='CÓDIGO DEL DEPARTAMENTO (PROGRAMA)', how='outer') \
                    .fillna(0)

    df_mapa.rename(columns={
        'CÓDIGO DEL DEPARTAMENTO (PROGRAMA)': 'DPTO',
        'ADMITIDOS': 'Admitidas',
        'PRIMER CURSO': 'Matriculadas',
        'GRADUADOS': 'Graduadas'
    }, inplace=True)
    df_mapa['DPTO'] = df_mapa['DPTO'].astype(int)

    # === UNIR CON GEODATAFRAME ===
    mapa = gdf.merge(df_mapa, on='DPTO', how='left').fillna(0)

    # === CREAR MAPAS ===
    fig, axes = plt.subplots(1, 3, figsize=(24, 9))

    bins_ad = [12, 55, 163, 386, 530, 20620]
    bins_mat = [10, 49, 129, 292, 428, 16786]
    bins_grad = [2, 14, 52, 121, 166, 3238]

    # Admitidas
    mapa.plot(column='Admitidas', cmap='YlGn', scheme='user_defined',
            classification_kwds={'bins': bins_ad}, legend=True, ax=axes[0], edgecolor='black')
    axes[0].set_title(f'Admitidas en TIC – {año_mapa}')
    axes[0].axis('off')

    # Matriculadas
    mapa.plot(column='Matriculadas', cmap='BuGn', scheme='user_defined',
            classification_kwds={'bins': bins_mat}, legend=True, ax=axes[1], edgecolor='black')
    axes[1].set_title(f'Matriculadas 1er curso en TIC – {año_mapa}')
    axes[1].axis('off')

    # Graduadas
    mapa.plot(column='Graduadas', cmap='PuBuGn', scheme='user_defined',
            classification_kwds={'bins': bins_grad}, legend=True, ax=axes[2], edgecolor='black')
    axes[2].set_title(f'Graduadas en TIC – {año_mapa}')
    axes[2].axis('off')

    plt.tight_layout()
    st.pyplot(fig)
    


    # === Cargar datos ===
    st.markdown("## 📊 Análisis por Departamento, Año y Género")
    departamentos = df_Total['DEPARTAMENTO DE OFERTA DEL PROGRAMA'].dropna().unique()
    anios = df_Total['AÑO'].dropna().unique()
    generos = df_Total['SEXO'].dropna().unique()

    departamento_sel = st.selectbox("Selecciona un Departamento", sorted(departamentos))
    anios_sel = st.multiselect("Selecciona uno o varios años", sorted(anios), default=[2023])
    generos_sel = st.multiselect("Selecciona géneros", sorted(generos), default=['Femenino', 'Masculino'])

    # === Filtrar DataFrame ===
    df_filtrado = df_Total[
        (df_Total['DEPARTAMENTO DE OFERTA DEL PROGRAMA'] == departamento_sel) &
        (df_Total['AÑO'].isin(anios_sel)) &
        (df_Total['SEXO'].isin(generos_sel))
    ]

    # === Función para graficar cada etapa con su propia figura ===
    def graficar_etapa(columna, titulo, color):
        df_etapa = df_filtrado.groupby(['AÑO', 'SEXO'])[columna].sum().unstack().fillna(0)

        if df_etapa.empty or not df_etapa.select_dtypes(include='number').any().any():
            st.warning(f"⚠️ No hay datos disponibles para: **{titulo}**.")
            return

        fig, ax = plt.subplots(figsize=(10, 5))
        df_etapa.plot(kind='bar', ax=ax, title=titulo, color=color)
        ax.set_xlabel("Año")
        ax.set_ylabel("Cantidad")
        ax.set_xticks(range(len(df_etapa)))
        ax.set_xticklabels(df_etapa.index, rotation=0)
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        st.pyplot(fig)

    # === Graficar Admitidos ===
    graficar_etapa('ADMITIDOS', f'Admitidos en TIC en {departamento_sel}', ['#1dbe82', '#167753', 'white', '#09b9d2'])

    # === Graficar Matriculados Primer Curso ===
    graficar_etapa('PRIMER CURSO', f'Matriculados en 1er curso TIC en {departamento_sel}', ['#1dbe82', '#167753', 'white', '#09b9d2'])

    # === Graficar Graduados ===
    graficar_etapa('GRADUADOS', f'Graduados TIC en {departamento_sel}', ['#1dbe82', '#167753', 'white', '#09b9d2'])




elif selected == "Información":

    # Mostrar info del DataFrame
    buffer = io.StringIO()
    df_Total.info(buf=buffer)
    info_text = buffer.getvalue()
    st.subheader("📄 Información del DataFrame df_Total")
    st.text(info_text)

    st.markdown("## 📊 Prueba Chi²: Asociación entre sexo y nivel de formación")

    # Filtrar solo Femenino y Masculino
    df_chi = df_Total[df_Total['SEXO'].isin(['Femenino', 'Masculino'])]

    # Crear tabla de contingencia
    tabla = pd.crosstab(df_chi['SEXO'], df_chi['NIVEL DE FORMACIÓN'])

    # Aplicar prueba chi-cuadrado
    chi2, p, dof, expected = chi2_contingency(tabla)

    # Mostrar resultados
    st.markdown("### 📌 Resultados de la prueba Chi²")
    st.write(f"**Estadístico Chi²:** {chi2:.2f}")
    st.write(f"**p-valor:** {p:.4f}")
    st.write(f"**Grados de libertad:** {dof}")

    if p < 0.05:
        st.success("✅ Existe una asociación significativa entre el sexo y el nivel de formación.")
    else:
        st.info("🔎 No se encontró una asociación significativa entre el sexo y el nivel de formación.")


    st.markdown("## 📊 Chi²: Asociación entre sexo e institución educativa")

    # Filtrar solo Femenino y Masculino
    df_chi2_ies = df_Total[df_Total['SEXO'].isin(['Femenino', 'Masculino'])]

    # Crear tabla de contingencia: SEXO vs IES
    tabla2 = pd.crosstab(df_chi2_ies['SEXO'], df_chi2_ies['INSTITUCIÓN DE EDUCACIÓN SUPERIOR (IES)'])

    # Aplicar prueba chi-cuadrado
    chi2, p, dof, expected = chi2_contingency(tabla2)

    # Mostrar resultados
    st.markdown("### 📌 Resultados de la prueba Chi²")
    st.write(f"**Estadístico Chi²:** {chi2:.2f}")
    st.write(f"**p-valor:** {p:.4f}")
    st.write(f"**Grados de libertad:** {dof}")

    if p < 0.05:
        st.success("✅ Existe una asociación significativa entre el sexo y la institución educativa.")
    else:
        st.info("🔎 No se encontró una asociación significativa entre el sexo y la institución educativa.")
