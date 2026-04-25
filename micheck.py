import streamlit as st
import pandas as pd
from datetime import datetime, time
import os

# Configuración de la página
st.set_page_config(page_title="Control de Horas - 9 a 18", layout="wide")
st.title("⏱️ Mi Registro de Horas (9 a 18 hs)")

ARCHIVO_DATOS = "mis_horas.csv"

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("💰 Configuración")
    sueldo = st.number_input("Sueldo Base Mensual", value=500000)
    # Si trabajas 9hs de lunes a viernes, son aprox 180hs al mes
    horas_mes = st.number_input("Horas por mes", value=180)
    valor_hora = sueldo / horas_mes
    st.write(f"Valor hora normal: **${valor_hora:.2f}**")
    
    st.divider()
    if st.button("🗑️ Borrar Datos de Prueba"):
        if os.path.exists(ARCHIVO_DATOS):
            os.remove(ARCHIVO_DATOS)
            st.success("Limpieza completa.")
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

if st.button("💾 Guardar Jornada"):
    h_ent = datetime.combine(fecha, entrada)
    h_sal = datetime.combine(fecha, salida)
    total_h = (h_sal - h_ent).total_seconds() / 3600
    
    if total_h > 0:
        h_50 = 0.0
        h_100 = 0.0
        dia_semana = fecha.weekday() # 0=Lunes, 5=Sábado, 6=Domingo

        # --- LÓGICA PERSONALIZADA (Tu horario 9-18) ---
        
        # 1. DOMINGOS O FERIADOS: Todo al 100%
        if es_feriado or dia_semana == 6:
            h_100 = total_h
            h_50 = 0.0
            
        # 2. SÁBADOS: Antes de las 13:00 (50% si pasas tu jornada), Después de las 13:00 (100%)
        elif dia_semana == 5:
            limite_sabado = datetime.combine(fecha, time(13, 0))
            if h_ent >= limite_sabado:
                h_100 = total_h
            elif h_sal > limite_sabado:
                h_100 = (h_sal - limite_sabado).total_seconds() / 3600
                h_50 = (limite_sabado - h_ent).total_seconds() / 3600
            else:
                h_50 = total_h

        # 3. LUNES A VIERNES: Extras después de las 9 horas (después de las 18:00)
        else:
            if total_h > 9:
                h_50 = total_h - 9
            else:
                h_50 = 0.0
        
        monto_extra = (h_50 * valor_hora * 1.5) + (h_100 * valor_hora * 2.0)
        
        nueva_fila = {
            "Fecha": fecha.strftime("%Y-%m-%d"),
            "Día": ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"][dia_semana],
            "Entrada": entrada.strftime("%H:%M"),
            "Salida": salida.strftime("%H:%M"),
            "Total_Hs": round(total_h, 2),
            "Extras_50": round(h_50, 2),
            "Extras_100": round(h_100, 2),
            "Monto_a_Cobrar": round(monto_extra, 2)
        }
        
        df_nuevo = pd.DataFrame([nueva_fila])
        if not os.path.isfile(ARCHIVO_DATOS):
            df_nuevo.to_csv(ARCHIVO_DATOS, index=False)
        else:
            df_nuevo.to_csv(ARCHIVO_DATOS, mode='a', header=False, index=False)
        st.success(f"Registrado: {nueva_fila['Día']} - Extras: {h_50 + h_100} hs")
    else:
        st.error("La hora de salida debe ser mayor a la de entrada.")

# --- TABLA ---
st.divider()
if os.path.isfile(ARCHIVO_DATOS):
    df = pd.read_csv(ARCHIVO_DATOS)
    st.write("### Mi Historial")
    st.dataframe(df, use_container_width=True)
    st.metric("Total Extras del Mes", f"${df['Monto_a_Cobrar'].sum():,.2f}")
    
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Descargar Reporte", csv, "control_horas.csv", "text/csv")
