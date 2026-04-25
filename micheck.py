import streamlit as st
from google.oauth2 import service_account
from google.cloud import storage  # Cambia esto por el servicio que uses (firestore, bigquery, etc.)
import json

# Función para obtener las credenciales
def get_gcp_credentials():
    # 1. Intentar leer desde Streamlit Secrets (Para GitHub/Cloud)
    if "gcp_service_account" in st.secrets:
        return service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"]
        )
    
    # 2. Intentar leer desde archivo local (Para desarrollo en tu PC)
    else:
        try:
            return service_account.Credentials.from_service_account_file('keyfile.json')
        except Exception as e:
            st.error("No se encontraron credenciales de Google Cloud.")
            return None

# Inicializar las credenciales
credentials = get_gcp_credentials()

if credentials:
    # Ejemplo de uso: Conectar a Storage
    # Cambia 'nombre-de-tu-proyecto' por tu ID real de GCP
    client = storage.Client(credentials=credentials, project=credentials.project_id)
    
    st.title("✅ Conexión Exitosa")
    st.write("El código está usando la cuenta de servicio directamente (sin Google Sheets).")
    
    # Tu código anterior aquí...
    # ejemplo: buckets = list(client.list_buckets())
