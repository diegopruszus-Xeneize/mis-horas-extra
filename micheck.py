import streamlit as st
import requests
import pandas as pd
from datetime import datetime, time

# --- CONFIGURACIÓN DE LA APP ---
st.set_page_config(page_title="App Horas Persistente", layout="wide")

# URL de tu Apps Script (Configurada con tu link)
URL_SCRIPT = "https://script.google.com/macros/s/AKfycbyrCnDx4UlHjaxFTreMkPiksTn_UaBP45hHZ_FmXVXaXBkvZ0AWHWTJ_AMUKVAGMsNT4w/exec"

st.title("⏱️ Registro de Horas (Sincronizado con Drive)")
st.markdown("Los datos se guardan directamente en tu Google Sheets. Ya no se borrarán al reiniciar la app.")

# --- BARRA LATERAL (CONFIGURACIÓN) ---
with st.sidebar:
    st.header("💰 Configuración")
    sueldo = st.number_input("Sueldo Base Mensual", value=500000)
    horas_mes = st.number_input("Horas por mes", value=160)
    valor_hora = sueldo / horas_mes
    st.write(f"Valor hora normal: **${valor_hora:.2f}**")
    
    st.divider()
    st.info("Para ver el historial completo o borrar filas, accede directamente a tu planilla de Google Sheets.")

# --- ENTRADA DE DATOS ---
st.subheader("Registrar Nueva Jornada")
col1, col2, col3, col4 = st.columns(4)

with col1:
    fecha = st.date_input("Fecha", datetime.today())
with col2:
    entrada = st.time_input("Hora de Ingreso", time(9, 0))
with col3:
    salida = st.time_input("Hora de Egreso", time(18, 0))
with col4:
    es_feriado = st.checkbox("¿Es Feriado?")

if st.button("💾 Guardar Jornada"):
    h_ent = datetime.combine(fecha, entrada)
    h_sal = datetime.combine(fecha, salida)
    total_h = (h_sal - h_ent).total_seconds() / 3600
    
    if total_h > 0:
        h_50 = 0.0
        h_100 = 0.0
        dia_semana = fecha.weekday() # 0=Lunes, 6=Domingo
        nombre_dia = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"][dia_semana]

        # --- LÓGICA DE CÁLCULO ---
        if es_feriado or dia_semana == 6: 
            h_100 = total_h
        elif dia_semana == 5: # Sábado
            limite_sabado = datetime.combine(fecha, time(13, 0))
            if h_sal > limite_sabado:
                antes_13 = max(0, (limite_sabado - h_ent).total_seconds() / 3600)
                despues_13 = max(0, (h_sal - limite_sabado).total_seconds() / 3600)
                h_100 = despues_13
                if antes_13 > 8: h_50 = antes_13 - 8
            else:
                if total_h > 8: h_50 = total_h - 8
        else: # Lunes a Viernes
            if total_h > 9: 
                h_50 = total_h - 9
        
        monto_extra = (h_50 * valor_hora * 1.5) + (h_100 * valor_hora * 2.0)

        # --- PREPARAR DATOS PARA ENVÍO ---
        payload = {
            "Fecha": fecha.strftime("%d/%m/%Y"),
            "Día": nombre_dia,
            "Entrada": entrada.strftime("%H:%M"),
            "Salida": salida.strftime("%H:%M"),
            "Total_Hs": round(total_h, 2),
            "Extras_50": round(h_50, 2),
            "Extras_100": round(h_100, 2),
            "Monto_a_Cobrar": round(monto_extra, 2)
        }

        # --- ENVÍO A GOOGLE SHEETS ---
        try:
            with st.spinner("Guardando en la nube..."):
                response = requests.post(URL_SCRIPT, json=payload)
                if response.status_code == 200:
                    st.success(f"✅ ¡Jornada del {nombre_dia} guardada con éxito!")
                    st.balloons()
                else:
                    st.error("❌ Error al guardar. Verifica la URL de Apps Script.")
        except Exception as e:
            st.error(f"❌ Error de conexión: {e}")
    else:
        st.warning("⚠️ La hora de salida debe ser posterior a la de entrada.")
