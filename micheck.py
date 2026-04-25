import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, time

# Configuración de página
st.set_page_config(page_title="Listado de Hs. extras", layout="wide")
st.title("⏱️ Registro de Horas (Sincronizado con Drive)")

# CONEXIÓN CON GOOGLE SHEETS
conn = st.connection("gsheets", type=GSheetsConnection)

# Leer datos existentes (si la planilla está vacía, creamos un DataFrame)
try:
    df = conn.read()
except:
    df = pd.DataFrame(columns=["Fecha", "Día", "Entrada", "Salida", "Total_Hs", "Extras_50", "Extras_100", "Monto_a_Cobrar"])

with st.sidebar:
    st.header("💰 Configuración")
    sueldo = st.number_input("Sueldo Base Mensual", value=500000)
    horas_mes = st.number_input("Horas por mes", value=180)
    valor_hora = sueldo / horas_mes
    
    st.divider()
    st.subheader("⚙️ Administrar")
    if st.button("❌ Eliminar Último Registro"):
        if not df.empty:
            df = df[:-1]
            # Para el botón de borrar:
if st.button("❌ Eliminar Último Registro"):
    if not df.empty:
        df = df[:-1]
        # Cambiamos update por esta línea:
        conn.update(worksheet="Sheet1", data=df) 
        st.warning("Última fila eliminada.")
        st.rerun()
            st.warning("Última fila eliminada.")
            st.rerun()

# --- ENTRADA DE DATOS ---
st.subheader("Registrar Jornada")
col1, col2, col3, col4 = st.columns(4)

with col1:
    fecha = st.date_input("Fecha", datetime.today())
with col2:
    entrada = st.time_input("Hora de Ingreso", time(9, 0))
with col3:
    salida = st.time_input("Hora de Egreso", time(18, 0))
with col4:
    es_feriado = st.checkbox("¿Es Feriado?")

if st.button("💾 Guardar en Drive"):
    h_ent = datetime.combine(fecha, entrada)
    h_sal = datetime.combine(fecha, salida)
    total_h = (h_sal - h_ent).total_seconds() / 3600
    
    if total_h > 0:
        h_50 = 0.0
        h_100 = 0.0
        dia_semana = fecha.weekday()

        # Lógica 9 a 18
        if es_feriado or dia_semana == 6:
            h_100 = total_h
        elif dia_semana == 5:
            limite_sabado = datetime.combine(fecha, time(13, 0))
            if h_ent >= limite_sabado: h_100 = total_h
            elif h_sal > limite_sabado:
                h_100 = (h_sal - limite_sabado).total_seconds() / 3600
                h_50 = (limite_sabado - h_ent).total_seconds() / 3600
            else: h_50 = total_h
        else:
            if total_h > 9: h_50 = total_h - 9
        
        monto_extra = (h_50 * valor_hora * 1.5) + (h_100 * valor_hora * 2.0)
        
        nueva_fila = pd.DataFrame([{
            "Fecha": fecha.strftime("%Y-%m-%d"),
            "Día": ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"][dia_semana],
            "Entrada": entrada.strftime("%H:%M"),
            "Salida": salida.strftime("%H:%M"),
            "Total_Hs": round(total_h, 2),
            "Extras_50": round(h_50, 2),
            "Extras_100": round(h_100, 2),
            "Monto_a_Cobrar": round(monto_extra, 2)
        }])
        
        df_actualizado = pd.concat([df, nueva_fila], ignore_index=True)
        conn.update(data=df_actualizado)
        st.success("¡Datos guardados en Google Drive!")
        st.rerun()

# --- TABLA ---
st.divider()
st.write("### Listado de Hs. extras")
if not df.empty:
    st.dataframe(df, use_container_width=True)
    st.metric("Total Extras", f"${df['Monto_a_Cobrar'].sum():,.2f}")
else:
    st.info("Aún no hay datos en la nube.")
