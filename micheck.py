import streamlit as st
import pandas as pd
from datetime import datetime, time
import os
import io

# Configuración de la página
st.set_page_config(page_title="Control de Horas", layout="wide")
st.title("⏱️ Registro de Horas y Reportes Históricos")

# --- CONFIGURACIÓN DE ARCHIVOS ---
ARCHIVO_DATOS = "mis_horas.csv"
CARPETA_REPORTES = "reportes_guardados"

# Crear carpeta de reportes si no existe
if not os.path.exists(CARPETA_REPORTES):
    os.makedirs(CARPETA_REPORTES)

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
    df["Monto_a_Cobrar"] = (df["Extras_50"] * valor_hora * 1.5) + (df["Extras_100"] * valor_hora * 2.0)
    
    st.write("### Listado de Hs. extras")
    st.dataframe(df.style.format({"Monto_a_Cobrar": "${:,.2f}"}), use_container_width=True)
    
    total_extras = df['Monto_a_Cobrar'].sum()
    st.metric("Total Extras del Mes", f"${total_extras:,.2f}")
    
    # --- GENERACIÓN DE EXCEL ---
    nombre_archivo = f"Reporte_Extras_{datetime.now().strftime('%m_%Y_%H%M%S')}.xlsx"
    ruta_guardado = os.path.join(CARPETA_REPORTES, nombre_archivo)
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Horas_Extras')
        workbook  = writer.book
        worksheet = writer.sheets['Horas_Extras']
        
        formato_encabezado = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1, 'align': 'center'})
        formato_moneda = workbook.add_format({'num_format': '$#,##0.00'})
        formato_centro = workbook.add_format({'align': 'center'})

        for col_num, col_name in enumerate(df.columns):
            worksheet.write(0, col_num, col_name, formato_encabezado)
            if col_name == "Monto_a_Cobrar":
                worksheet.set_column(col_num, col_num, 18, formato_moneda)
            else:
                worksheet.set_column(col_num, col_num, 15, formato_centro)

    # Guardar copia automática en servidor
    with open(ruta_guardado, "wb") as f:
        f.write(buffer.getvalue())

    st.download_button(
        label="📥 Descargar y Guardar Reporte en Historial",
        data=buffer.getvalue(),
        file_name=nombre_archivo,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# --- BUSCADOR HISTÓRICO ---
st.divider()
st.subheader("📂 Historial de Reportes Guardados")

archivos_guardados = sorted(os.listdir(CARPETA_REPORTES), reverse=True)

if archivos_guardados:
    archivo_selec = st.selectbox("Seleccione un reporte anterior para descargar o borrar:", archivos_guardados)
    ruta_completa = os.path.join(CARPETA_REPORTES, archivo_selec)
    
    with open(ruta_completa, "rb") as f:
        bytes_archivo = f.read()
        
    c1, c2 = st.columns([1, 4])
    with c1:
        st.download_button(
            label="💾 Descargar de nuevo",
            data=bytes_archivo,
            file_name=archivo_selec,
            key=f"dl_{archivo_selec}"
        )
    with c2:
        if st.button("🗑️ Eliminar permanentemente este archivo"):
            os.remove(ruta_completa)
            st.rerun()
else:
    st.info("Aún no hay reportes guardados en el historial.")
