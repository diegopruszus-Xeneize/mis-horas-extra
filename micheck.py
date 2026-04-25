import streamlit as st
import pandas as pd
from datetime import datetime, time
import os
import io  # Necesario para manejar el archivo en memoria

# Configuración de la página
st.set_page_config(page_title="Control de Horas", layout="wide")
st.title("⏱️ Registro de Horas (9 a 18 hs)")

ARCHIVO_DATOS = "mis_horas.csv"

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("💰 Configuración")
    sueldo = st.number_input("Sueldo Base Mensual", value=500000)
    horas_mes = st.number_input("Horas por mes", value=180)
    valor_hora = sueldo / horas_mes
    st.write(f"Valor hora normal: **${valor_hora:.2f}**")
    
    st.divider()
    st.subheader("⚙️ Administrar Datos")
    
    if os.path.isfile(ARCHIVO_DATOS):
        df_admin = pd.read_csv(ARCHIVO_DATOS)
        if not df_admin.empty:
            fecha_a_borrar = st.selectbox("Seleccionar fecha para eliminar:", df_admin["Fecha"].unique())
            if st.button("❌ Eliminar esta Fila"):
                df_admin = df_admin[df_admin["Fecha"] != fecha_a_borrar]
                df_admin.to_csv(ARCHIVO_DATOS, index=False)
                st.warning(f"Se eliminó el registro del {fecha_a_borrar}")
                st.rerun()

    if st.button("🗑️ BORRAR TODO EL MES"):
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
        dia_semana = fecha.weekday()

        if es_feriado or dia_semana == 6:
            h_100 = total_h
        elif dia_semana == 5:
            limite_sabado = datetime.combine(fecha, time(13, 0))
            if h_ent >= limite_sabado:
                h_100 = total_h
            elif h_sal > limite_sabado:
                h_100 = (h_sal - limite_sabado).total_seconds() / 3600
                h_50 = (limite_sabado - h_ent).total_seconds() / 3600
            else:
                h_50 = total_h
        else:
            if total_h > 9:
                h_50 = total_h - 9
        
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
        st.success(f"Registrado correctamente.")
        st.rerun()
    else:
        st.error("Revisa las horas ingresadas.")

# --- LISTADO Y DESCARGA EN EXCEL ---
st.divider()
if os.path.isfile(ARCHIVO_DATOS):
    df = pd.read_csv(ARCHIVO_DATOS)
    st.write("### Listado de Hs. extras")
    st.dataframe(df, use_container_width=True)
    
    st.metric("Total Extras del Mes", f"${df['Monto_a_Cobrar'].sum():,.2f}")
    
    # --- CREACIÓN DEL EXCEL EN MEMORIA ---
    buffer = io.BytesIO()
    
    # Usamos XlsxWriter como motor para poder dar formato
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Horas_Extras')
        
        # Acceder a los objetos de xlsxwriter
        workbook  = writer.book
        worksheet = writer.sheets['Horas_Extras']
        
        # Formatos
        header_format = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1})
        money_format = workbook.add_format({'num_format': '$#,##0.00'})
        
        # Aplicar formato a los encabezados
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            # Ajustar ancho de columna automáticamente
            worksheet.set_column(col_num, col_num, 15)
            
        # Aplicar formato moneda a la última columna (Monto_a_Cobrar)
        worksheet.set_column(len(df.columns)-1, len(df.columns)-1, 18, money_format)

    # Botón de descarga
    st.download_button(
        label="📥 Descargar Reporte en Excel (.xlsx)",
        data=buffer.getvalue(),
        file_name=f"Reporte_Horas_{datetime.now().strftime('%m_%Y')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
