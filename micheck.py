import streamlit as st
import pandas as pd
from datetime import datetime, time
import os

# Configuración de la página
st.set_page_config(page_title="App Horas Inteligente", layout="wide")
st.title("⏱️ Registro de Horas (Sábados Automáticos)")

# Nombre del archivo de base de datos
ARCHIVO_DATOS = "mis_horas.csv"

# --- BARRA LATERAL (CONFIGURACIÓN) ---
with st.sidebar:
    st.header("💰 Configuración")
    sueldo = st.number_input("Sueldo Base Mensual", value=500000)
    horas_mes = st.number_input("Horas por mes", value=160)
    valor_hora = sueldo / horas_mes
    st.write(f"Valor hora normal: **${valor_hora:.2f}**")
    
    st.divider()
    # Botón para limpiar los datos de prueba
    if st.button("🗑️ Borrar Datos de Prueba"):
        if os.path.exists(ARCHIVO_DATOS):
            os.remove(ARCHIVO_DATOS)
            st.success("Archivo borrado correctamente.")
            st.rerun()
        else:
            st.info("No hay datos para borrar.")

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
        dia_semana = fecha.weekday() # 0=Lunes, 5=Sábado, 6=Domingo

        # --- LÓGICA AUTOMÁTICA DE CÁLCULO ---
        if es_feriado or dia_semana == 6: # Feriado o Domingo
            h_100 = total_h
        elif dia_semana == 5: # Es SÁBADO
            limite_sabado = datetime.combine(fecha, time(13, 0))
            if h_sal > limite_sabado:
                # Horas antes de las 13:00
                antes_13 = max(0, (limite_sabado - h_ent).total_seconds() / 3600)
                # Horas después de las 13:00
                despues_13 = max(0, (h_sal - limite_sabado).total_seconds() / 3600)
                
                h_100 = despues_13
                if antes_13 > 8:
                    h_50 = antes_13 - 8
            else:
                if total_h > 8: h_50 = total_h - 8
        else: # Lunes a Viernes
            if total_h > 8: h_50 = total_h - 8
        
        monto_extra = (h_50 * valor_hora * 1.5) + (h_100 * valor_hora * 2.0)
        
        nueva_fila = {
            "Fecha": fecha.strftime("%Y-%m-%d"),
            "Día": ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"][dia_semana],
            "Entrada": entrada.strftime("%H:%M"),
            "Salida": salida.strftime("%H:%M"),
            "Total": round(total_h, 2),
            "H_50": round(h_50, 2),
            "H_100": round(h_100, 2),
            "Monto_Extra": round(monto_extra, 2)
        }
        
        df_nuevo = pd.DataFrame([nueva_fila])
        if not os.path.isfile(ARCHIVO_DATOS):
            df_nuevo.to_csv(ARCHIVO_DATOS, index=False)
        else:
            df_nuevo.to_csv(ARCHIVO_DATOS, mode='a', header=False, index=False)
        st.success(f"¡Jornada guardada! Día: {nueva_fila['Día']}")
    else:
        st.error("Error: La salida debe ser posterior a la entrada.")

# --- HISTORIAL Y MÉTRICAS ---
st.divider()
if os.path.isfile(ARCHIVO_DATOS):
    df = pd.read_csv(ARCHIVO_DATOS)
    st.write("### Historial Mensual")
    st.dataframe(df, use_container_width=True)
    
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Total Horas Extras (Dinero)", f"${df['Monto_Extra'].sum():,.2f}")
    with c2:
        # Botón para descargar el archivo y subirlo a Drive
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar CSV para Google Drive", csv, "mis_horas_final.csv", "text/csv")
