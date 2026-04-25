import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, time

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Listado de Hs. extras", layout="wide")
st.title("⏱️ Registro de Horas (Sincronizado con Drive)")

# 2. CONEXIÓN CON GOOGLE SHEETS
# Se conecta usando el link que pusiste en "Secrets"
conn = st.connection("gsheets", type=GSheetsConnection)

# Leer datos actuales
try:
    df = conn.read()
    # Si la planilla tiene filas vacías al final, las limpiamos
    df = df.dropna(how="all")
except:
    # Si falla la lectura, creamos un molde vacío
    df = pd.DataFrame(columns=["Fecha", "Día", "Entrada", "Salida", "Total_Hs", "Extras_50", "Extras_100", "Monto_a_Cobrar"])

# 3. BARRA LATERAL
with st.sidebar:
    st.header("💰 Configuración")
    sueldo = st.number_input("Sueldo Base Mensual", value=500000)
    horas_mes = st.number_input("Horas por mes", value=180)
    valor_hora = sueldo / horas_mes
    st.write(f"Valor hora normal: **${valor_hora:.2f}**")
    
    st.divider()
    st.subheader("⚙️ Administrar")
    
    if st.button("❌ Eliminar Último Registro"):
        if not df.empty:
            df_limpio = df.iloc[:-1]
            conn.update(data=df_limpio)
            st.warning("Última fila eliminada de Drive.")
            st.rerun()
        else:
            st.info("No hay datos para borrar.")

# 4. ENTRADA DE DATOS
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
        dia_semana = fecha.weekday() # 0=Lunes, 5=Sábado, 6=Domingo

        # LÓGICA DE CÁLCULO (Jornada 9 a 18)
        if es_feriado or dia_semana == 6: # Domingo o Feriado
            h_100 = total_h
        elif dia_semana == 5: # Sábado
            limite_sabado = datetime.combine(fecha, time(13, 0))
            if h_ent >= limite_sabado:
                h_100 = total_h
            elif h_sal > limite_sabado:
                h_100 = (h_sal - limite_sabado).total_seconds() / 3600
                h_50 = (limite_sabado - h_ent).total_seconds() / 3600
            else:
                h_50 = total_h
        else: # Lunes a Viernes
            if total_h > 9:
                h_50 = total_h - 9
        
        monto_extra = (h_50 * valor_hora * 1.5) + (h_100 * valor_hora * 2.0)
        
        # Crear la nueva fila
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
        
        # Unir con los datos existentes y subir
        df_actualizado = pd.concat([df, nueva_fila], ignore_index=True)
        conn.update(data=df_actualizado)
        st.success("¡Guardado exitosamente en Google Drive!")
        st.rerun()
    else:
        st.error("La hora de salida debe ser después de la entrada.")

# 5. VISUALIZACIÓN
st.divider()
st.write("### Listado de Hs. extras")
if not df.empty:
    st.dataframe(df, use_container_width=True)
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.metric("Total Acumulado", f"${df['Monto_a_Cobrar'].sum():,.2f}")
    with col_m2:
        st.write("Datos sincronizados con Google Sheets.")
else:
    st.info("Todavía no hay registros cargados.")
