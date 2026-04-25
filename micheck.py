import streamlit as st
import pandas as pd
from datetime import datetime, time
import os
import io

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
    
    # Función para eliminar una sola fila
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

        # Lógica de cálculo de horas extra
        if es_feriado or dia_semana == 6:  # Domingo o Feriado
            h_100 = total_h
        elif dia_semana == 5:  # Sábado
            limite_sabado = datetime.combine(fecha, time(13, 0))
            if h_ent >= limite_sabado:
                h_100 = total_h
            elif h_sal > limite_sabado:
                h_100 = (h_sal - limite_sabado).total_seconds() / 3600
                h_50 = (limite_sabado - h_ent).total_seconds() / 3600
            else:
                h_50 = total_h
        else:  # Lunes a Viernes
            if total_h > 9:
                h_50 = total_h - 9
        
        # Guardamos solo las horas, no el monto (para que sea dinámico)
        nueva_fila = {
            "Fecha": fecha.strftime("%Y-%m-%d"),
            "Día": ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"][dia_semana],
            "Entrada": entrada.strftime("%H:%M"),
            "Salida": salida.strftime("%H:%M"),
            "Total_Hs": round(total_h, 2),
            "Extras_50": round(h_50, 2),
            "Extras_100": round(h_100, 2)
        }
        
        df_nuevo = pd.DataFrame([nueva_fila])
        if not os.path.isfile(ARCHIVO_DATOS):
            df_nuevo.to_csv(ARCHIVO_DATOS, index=False)
        else:
            df_nuevo.to_csv(ARCHIVO_DATOS, mode='a', header=False, index=False)
        st.success("Registrado correctamente.")
        st.rerun()
    else:
        st.error("Revisa las horas ingresadas.")

# --- LISTADO Y REPORTES ---
st.divider()
if os.path.isfile(ARCHIVO_DATOS):
    df = pd.read_csv(ARCHIVO_DATOS)
    
    # CÁLCULO DINÁMICO: Se recalculan los montos según el sueldo de la sidebar
    df["Monto_a_Cobrar"] = (df["Extras_50"] * valor_hora * 1.5) + (df["Extras_100"] * valor_hora * 2.0)
    
    st.write("### Listado de Hs. extras")
    # Mostramos con formato de moneda en la vista de la app
    st.dataframe(df.style.format({"Monto_a_Cobrar": "${:,.2f}"}), use_container_width=True)
    
    total_extras = df['Monto_a_Cobrar'].sum()
    st.metric("Total Extras del Mes", f"${total_extras:,.2f}")
    
    # --- GENERACIÓN DE EXCEL (.xlsx) ---
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Horas_Extras')
        
        workbook  = writer.book
        worksheet = writer.sheets['Horas_Extras']
        
        # Formatos para el Excel
        formato_encabezado = workbook.add_format({
            'bold': True, 
            'bg_color': '#D7E4BC', 
            'border': 1,
            'align': 'center'
        })
        formato_moneda = workbook.add_format({'num_format': '$#,##0.00'})
        formato_centro = workbook.add_format({'align': 'center'})

        # Aplicar formatos y anchos
        for col_num, col_name in enumerate(df.columns):
            worksheet.write(0, col_num, col_name, formato_encabezado)
            
            # Si es la columna de dinero, aplicar formato moneda
            if col_name == "Monto_a_Cobrar":
                worksheet.set_column(col_num, col_num, 18, formato_moneda)
            else:
                worksheet.set_column(col_num, col_num, 15, formato_centro)

    # Botón para descargar el Excel
    st.download_button(
        label="📥 Descargar Reporte Excel (.xlsx)",
        data=buffer.getvalue(),
        file_name=f"Reporte_Extras_{datetime.now().strftime('%m_%Y')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
