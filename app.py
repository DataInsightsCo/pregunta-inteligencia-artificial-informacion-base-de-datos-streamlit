import streamlit as st
import pandas as pd
import io
import b_backend
import seaborn as sns
import matplotlib.pyplot as plt



# Configuración de la página
st.set_page_config(page_icon="rpa.png", page_title="SUI Robotic - DataInsights")

# Inicializar el estado de la sesión
if 'pregs' not in st.session_state:
    st.session_state.pregs = []
if 'resps' not in st.session_state:
    st.session_state.resps = []
if 'csv_data' not in st.session_state:
    st.session_state.csv_data = None
if 'analisis' not in st.session_state:
    st.session_state.analisis = ""
if 'show_main' not in st.session_state:
    st.session_state.show_main = True  # Controlar la visualización del formato principal
if 'reset_flag' not in st.session_state:
    st.session_state.reset_flag = False  # Flag para reiniciar

def reset_app():
    # Reiniciar variables y establecer la bandera de reinicio
    st.session_state.pregs = []
    st.session_state.resps = []
    st.session_state.csv_data = None
    st.session_state.analisis = ""
    st.session_state.show_main = True
    st.session_state.reset_flag = True  # Activar bandera de reinicio

def exportar():
    if st.session_state.csv_data:
        st.download_button(
            label="Exportar",
            data=st.session_state.csv_data,
            file_name="consulta_resultado.csv",
            mime="text/csv"
        )

# Función para generar gráficos dinámicos
def generar_grafica(df):
    columnas_numericas = df.select_dtypes(include=['int64', 'float64']).columns
    columnas_fechas = df.select_dtypes(include=['datetime64']).columns
    columnas_categoricas = df.select_dtypes(include=['object']).columns

    # Si la primera columna es de tipo datetime, la usaremos como eje x
    if len(columnas_fechas) > 0:
        fecha_col = columnas_fechas[0]
        #st.write(f"Gráfico de fecha '{fecha_col}' en el eje X:")
        if len(columnas_numericas) > 0:
            for num_col in columnas_numericas:
                #st.write(f"{num_col} vs {fecha_col}:")
                fig, ax = plt.subplots()
                sns.lineplot(x=fecha_col, y=num_col, data=df)
                plt.xticks(rotation=45)
                st.pyplot(fig)
        else:
            st.write("No hay columnas numéricas para graficar contra la fecha.")
    else:
        # Si no hay columnas de fecha, proceder con el análisis normal
        if len(columnas_numericas) > 1:
            #st.write("Gráfica de pares de variables numéricas:")
            fig, ax = plt.subplots()
            sns.pairplot(df[columnas_numericas])
            st.pyplot(fig)
        elif len(columnas_numericas) == 1 and len(columnas_categoricas) >= 1:
            for cat_col in columnas_categoricas:
                #st.write(f"{columnas_numericas[0]} vs {cat_col}:")
                fig, ax = plt.subplots()
                sns.boxplot(x=cat_col, y=columnas_numericas[0], data=df)
                plt.xticks(rotation=45)
                st.pyplot(fig)
        elif len(columnas_numericas) == 1:
            #st.write(f"Distribución de {columnas_numericas[0]}:")
            fig, ax = plt.subplots()
            sns.histplot(df[columnas_numericas[0]], kde=True)
            st.pyplot(fig)
        elif len(columnas_categoricas) > 0:
            for cat_col in columnas_categoricas:
                #st.write(f"Conteo de {cat_col}:")
                fig, ax = plt.subplots()
                sns.countplot(x=cat_col, data=df)
                plt.xticks(rotation=45)
                st.pyplot(fig)

def click():
    if st.session_state.user != '':
        preg = st.session_state.user
        resultados, analisis = b_backend.consulta(preg)
        
        if resultados:
            st.session_state.pregs.append(preg)
            st.session_state.analisis = analisis  # Guardar el análisis en el estado
            
            # Convertir los resultados en un DataFrame dinámico
            df = pd.DataFrame(resultados)
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            st.session_state.csv_data = csv_buffer.getvalue()

            # Generar el DataFrame, organiza y adopta la primera columna como index.
            df = df.sort_values(by=df.columns[0])
            #df.set_index(df.columns[0], inplace=True)
            st.session_state.chart = df  # Guardar dataframe st.session_state
          
        # Ocultar el formato principal
        st.session_state.show_main = False
        
        # Limpiar el input
        st.session_state.user = ''

# Mostrar el formato principal solo si está en el estado inicial o después de "Haz otra pregunta"
if st.session_state.show_main:
    # Agregar logo
    with open("logo.png", "rb") as file:  
    st.image(file, width=100)                # Ajusta la ruta y el tamaño según sea necesario

    # Título personalizado
    st.markdown(
        """
        <h1 style='text-align: center; color: orange;'>
            Consulta tu información con Lenguaje Natural
        </h1>
        """,
        unsafe_allow_html=True
    )

    st.write("Hazle una pregunta a la **Inteligencia Artificial** y obtén resultados desde la base de datos.")

    # Formulario de interacción
    with st.form('my-form'):
        query = st.text_input('¿En qué te puedo ayudar?:', key='user', help='Pulsa enviar')
        submit_button = st.form_submit_button('Enviar', on_click=click)

# Si hay preguntas previas, mostrar los resultados
if not st.session_state.show_main and st.session_state.pregs:
    # Mostrar la pregunta del cliente
    pregunta = st.session_state.pregs[-1]
    st.markdown(f"**Pregunta dada:** <u>{pregunta}</u>", unsafe_allow_html=True)

    # Mostrar análisis y recomendaciones
    st.write("**Análisis y Recomendaciones** de SUI - Robotic: ")
    st.write(st.session_state.analisis)

    # Mostrar la gráfica dinámica
    #st.write("**Gráfico de Resultados:**")
    #generar_grafica(st.session_state.chart)
    
    # Mostrar la lista desplegable para las opciones
    st.write("**Selecciona una opción:**")
    opcion = st.selectbox(
        "Elige una acción a realizar:",
        ("Exportar a CSV", "Otra Pregunta")
    )

    if opcion == "Exportar a CSV":
        exportar()
    elif opcion == "Otra Pregunta":
        reset_app()  # Llamar a la función de reinicio
        st.success("**Confirma** - Selecciónalo de nuevo.")
            
# Recargar la página si se ha activado el reset_flag
if st.session_state.reset_flag:
    st.session_state.reset_flag = False  # Desactivar bandera de reinicio después de recargar
