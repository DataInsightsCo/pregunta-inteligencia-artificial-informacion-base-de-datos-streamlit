import re
import mysql.connector
import openai
import os
import streamlit as st



# Configuración del cliente de OpenAI usando st.secrets
client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Configuración de la base de datos usando st.secrets
db_config = {
    'host': st.secrets["DB_HOST"],
    'database': st.secrets["DB_DATABASE"],
    'user': st.secrets["DB_USER"],
    'password': st.secrets["DB_PASSWORD"],
    'port': int(st.secrets["DB_PORT"])
}

# Verificar si la clave está presente
print("API Key cargada:", os.getenv('OPENAI_API_KEY'))

# Función para obtener SQL de OpenAI
def obtener_sql_de_openai(pregunta):
    estructura_bd = """
    Aquí está la tabla con los atributos de nuestra base de datos:
    - Tabla dbsui: Empresa(empresas del sector energético de Colombia), DEPARTAMENTO(los departamentos de Colombia),
      Usuario(tipo de usuario "regulado" o "No regulado"), USO("residencial" o "No Residdencial"), ESTRATO(Alumbrado publico, comercial, industrial, oficial, provisional, residencial),
      TENSION(nivel de tensión de energía), Tipo_Lectura(real, estimada, sin madidor), Fecha(registro mensual en formato año y  mes), 
      Facturacion_Total($ COP), Facturacion_Consumo($ COP), Consumo_Total(kWh), Suscriptores(cantidad de ususarios), Subsidios($ COP), 
      Contribuciones($ COP), Fact_Suscriptores(Facturacion_Total dividido entre Subscritores), Fact_cons_Suscriptores(Facturacion_Consumo dividido entre Subscritores),
      Cons_Suscriptores(Consumo_Total dividido entre Subscritores), Valor_Consumido(Facturacion_Consumo dividido entre Consumo_Total)
    """

    prompt = f"{estructura_bd}\nConvierte la siguiente pregunta en una consulta SQL válida para MySQL:\n{pregunta}"
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Eres un asistente experto en bases de datos SQL."},
            {"role": "user", "content": prompt}
        ]
    )
    
    # Extraer la consulta SQL utilizando una expresión regular
    match = re.search(r"```sql\s*(SELECT .*?);?\s*```", response.choices[0].message.content, re.IGNORECASE | re.DOTALL)
    if match:
        sql_query = match.group(1).strip()
    else:
        sql_query = None
    
    return sql_query

# Función para ejecutar la consulta SQL
def ejecutar_sql(query):
    if query is None:
        return []
    
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    connection.close()
    return result

# Función para enviar el resultado a OpenAI para análisis
def analizar_resultados(resultados):
    # Convertir el resultado de la consulta en un formato legible para OpenAI
    formatted_result = "\n".join([str(r) for r in resultados])

    prompt = f"""
    No des explicaciones al ususario de como se desarrolló la tarea, aquí tienes los datos de una consulta SQL:
    {formatted_result}

    1. Organiza los resultados en una tabla con justificación a la derecha y en las cabeceras escribe el título más adecuado,
       sí el tipo de dato es fecha organizar del más antiguo al más reciente (año-mes),
       sí el dato es número (escribe Cantidad y no pongas $) ó sí el dato es moneda en ($ COP) usa separador de miles sin decimales.
    2. Siendo amable proporciona un análisis experto de los datos.
    3. Ofrece una recomendación puntual y aplicable basada en los datos,
       tener en cuenta que el contexto son los datos de la consulta pero te puedes apoyar en los atributos Suscriptor(mismo clientes) ó Facturación de la tabla.
    """

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Eres un experto en análisis de datos y visualización."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content

# Función para manejar la consulta completa
def consulta(pregunta):
    sql_query = obtener_sql_de_openai(pregunta)
    if sql_query:
        resultados = ejecutar_sql(sql_query)
        analisis = analizar_resultados(resultados)
        return resultados, analisis
    else:
        return None, "No se pudo generar una consulta SQL válida."
