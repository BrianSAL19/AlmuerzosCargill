import streamlit as st
import pandas as pd
import os
import json
import matplotlib.pyplot as plt
import textwrap
from datetime import datetime, timezone, timedelta
from io import BytesIO

# ====================================================================
# 🔑 CONFIGURACIÓN, COSTOS Y ARCHIVOS DE DATOS
# ====================================================================
CLAVE_ADMIN = "admin123"
ARCV_PEDIDOS = "pedidos_almuerzo.csv"
ARCV_SEMANA = "resumen_semanal.json"
ARCV_MENU = "menu_dia.json"

COLUMNAS = ["Nombre", "Tipo de Almuerzo", "Segundo", "Arroz", "Observaciones"]

PRECIO_COMPLETO = 3.00
PRECIO_SEGUNDO = 2.25

# Zona Horaria Guayaquil / Ecuador (UTC-5)
ZONA_ECUADOR = timezone(timedelta(hours=-5))

# Cargar o inicializar el menú del día
MENU_DEFAULT = {
    "caldo": "Caldo: Menestron de carne",
    "segundos": [
        "Pollo al horno con ensalada de remolacha",
        "Arroz con camaron"
    ]
}

def cargar_menu():
    if os.path.exists(ARCV_MENU):
        try:
            with open(ARCV_MENU, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return MENU_DEFAULT
    return MENU_DEFAULT

def guardar_menu(data):
    with open(ARCV_MENU, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

menu_actual = cargar_menu()
TEXTO_CALDO = menu_actual.get("caldo", MENU_DEFAULT["caldo"])
OPCIONES_SEGUNDO = menu_actual.get("segundos", MENU_DEFAULT["segundos"])

# --- CARGAR Y GUARDAR ESTRUCTURA SEMANAL MANUAL ---
def cargar_datos_semana():
    if os.path.exists(ARCV_SEMANA):
        try:
            with open(ARCV_SEMANA, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "dias" in data:
                    return data
        except Exception:
            pass
    
    return {
        "texto_semana": "Del 26 al 30 de octubre",
        "dias": {
            "Lunes": {"Completos": 0, "Segundos": 0},
            "Martes": {"Completos": 0, "Segundos": 0},
            "Miércoles": {"Completos": 0, "Segundos": 0},
            "Jueves": {"Completos": 0, "Segundos": 0},
            "Viernes": {"Completos": 0, "Segundos": 0}
        },
        "dia_ficticio_prueba": 0
    }

def guardar_datos_semana(data):
    with open(ARCV_SEMANA, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

semana_data = cargar_datos_semana()

# Si el archivo de pedidos del día no existe, lo creamos
if not os.path.exists(ARCV_PEDIDOS):
    df_inicial = pd.DataFrame(columns=COLUMNAS)
    df_inicial.to_csv(ARCV_PEDIDOS, index=False, sep=";")

st.title("🍱 Registro de Pedidos de Almuerzo")

# ====================================================================
# 🎨 ESTILOS CSS INTENSIVOS PARA MÓVILES (OPCIONES Y ENTRADAS GRANDES)
# ====================================================================
st.markdown("""
    <style>
    /* Forzar tamaño gigante en radio buttons y sus opciones */
    div[data-baseweb="radio"] label, 
    div[data-testid="stRadio"] label,
    div[data-testid="stRadio"] label p,
    .stRadio label p {
        font-size: 22px !important;
        line-height: 1.4 !important;
        font-weight: 500 !important;
    }

    /* Agrandar círculos de los radio buttons en táctil */
    div[data-baseweb="radio"] div {
        transform: scale(1.25);
        margin-right: 8px !important;
    }

    /* Entradas de texto y cuadro de observaciones */
    .stTextInput input, .stTextArea textarea {
        font-size: 20px !important;
        padding: 12px !important;
    }

    /* Etiquetas/preguntas de los inputs */
    div[data-testid="stWidgetLabel"] p, label p {
        font-size: 22px !important;
        font-weight: bold !important;
        color: #0F172A !important;
    }

    /* Botón Guardar Pedido */
    .stButton button {
        padding: 12px 24px !important;
    }
    .stButton button p {
        font-size: 22px !important;
        font-weight: bold !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- MENSAJE DE ADMIN (APARECE ARRIBA DE TODO) ---
if "msg_admin" in st.session_state:
    st.success(st.session_state["msg_admin"])
    del st.session_state["msg_admin"]

# --- VERIFICACIÓN DE HORARIO DE ATENCIÓN (4:00 AM - 5:00 PM) ---
ahora_ec = datetime.now(ZONA_ECUADOR)
hora_actual = ahora_ec.hour

fuera_de_horario_auto = hora_actual >= 17 or hora_actual < 4

if "estado_manual_pedidos" not in st.session_state:
    st.session_state["estado_manual_pedidos"] = None

if st.session_state["estado_manual_pedidos"] is not None:
    pedidos_cerrados = not st.session_state["estado_manual_pedidos"]
else:
    pedidos_cerrados = fuera_de_horario_auto

# --- SECCIÓN 1: FORMULARIO DE REGISTRO ---
st.header(TEXTO_CALDO)

if pedidos_cerrados:
    st.warning("⏰ **Los pedidos de hoy se encuentran CERRADOS.** (Atención de 4:00 AM a 5:00 PM)")
else:
    st.markdown("#### **Tu nombre:**")
    nombre = st.text_input("Tu nombre:", label_visibility="collapsed")

    st.markdown("#### **¿Completo o solo segundo?:**")
    completo_segundo = st.radio("¿Completo o solo segundo?:", ["Completo", "Solo segundo"], label_visibility="collapsed")

    st.markdown("#### **Selecciona el segundo:**")
    seleccion_segundo = st.radio("Selecciona el segundo:", OPCIONES_SEGUNDO, label_visibility="collapsed")

    st.markdown("#### **Selecciona el arroz:**")
    tipo_arroz = st.radio("Selecciona el arroz:", ["Blanco", "Moro"], label_visibility="collapsed")

    st.markdown("#### **Observaciones (opcional):**")
    notas = st.text_area("Observaciones (opcional):", placeholder="Ej: MADURO EXTRA", label_visibility="collapsed")

    if st.button("Guardar Pedido"):
        if nombre.strip():
            observaciones_texto = notas.strip() if notas.strip() else "----"

            nuevo_pedido = pd.DataFrame([{
                "Nombre": nombre.strip(),
                "Tipo de Almuerzo": completo_segundo,
                "Segundo": seleccion_segundo,
                "Arroz": tipo_arroz,
                "Observaciones": observaciones_texto
            }])
            
            nuevo_pedido.to_csv(ARCV_PEDIDOS, mode='a', header=False, index=False, sep=";")
            st.balloons()
            st.session_state["msg_pedido"] = f"✅ Pedido registrado con éxito para {nombre.strip()}"
            st.rerun()
        else:
            st.warning("Por favor, escribe tu nombre antes de enviar.")

# --- MENSAJE DE PEDIDO REGISTRADO ---
if "msg_pedido" in st.session_state:
    st.success(st.session_state["msg_pedido"])
    del st.session_state["msg_pedido"]

st.divider()

# --- SECCIÓN 2: LISTA Y GESTIÓN DE PEDIDOS ---
st.header("📋 Lista Consolidada de Pedidos")

if os.path.exists(ARCV_PEDIDOS):
    df_pedidos = pd.read_csv(ARCV_PEDIDOS, sep=";")
    
    if not df_pedidos.empty:
        if "Observaciones" in df_pedidos.columns:
            df_pedidos["Observaciones"] = df_pedidos["Observaciones"].fillna("----").replace("", "----")

        # 🔄 ORDENAR: Primero "Completo" y después "Solo segundo"
        df_mostrar = df_pedidos.sort_values(by="Tipo de Almuerzo", ascending=True).reset_index(drop=True)
        df_mostrar.insert(0, "#", range(1, len(df_mostrar) + 1))
        
        st.dataframe(df_mostrar, use_container_width=True, hide_index=True)

        st.divider()
        
        # --- RESUMEN DE CONTEO EN PANTALLA ---
        st.subheader("📊 Resumen para el restaurante")
        
        cant_completo = (df_pedidos["Tipo de Almuerzo"] == "Completo").sum()
        cant_solo_segundo = (df_pedidos["Tipo de Almuerzo"] == "Solo segundo").sum()

        if all(col in df_pedidos.columns for col in ["Tipo de Almuerzo", "Segundo", "Arroz"]):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write("**Por tipo:**")
                st.write(f"• Completo: {cant_completo}")
                st.write(f"• Solo segundo: {cant_solo_segundo}")
                
            with col2:
                st.write("**Por plato segundo:**")
                for plato, cantidad in df_pedidos["Segundo"].value_counts().items():
                    st.write(f"• {plato}: {cantidad}")
                    
            with col3:
                st.write("**Por tipo de arroz:**")
                for arroz, cantidad in df_pedidos["Arroz"].value_counts().items():
                    st.write(f"• {arroz}: {cantidad}")

        st.divider()

        # --- GENERACIÓN DE IMAGEN CON ZONA HORARIA ECUADOR (UTC-5) ---
        st.subheader("🖼️ Generar imagen para compartir por WhatsApp")

        def generar_imagen_perfecta(df, completo, solo_seg):
            df_fmt = df.copy()
            df_fmt = df_fmt.rename(columns={"Tipo de Almuerzo": "Tipo de\nAlmuerzo"})

            df_fmt['Segundo'] = df_fmt['Segundo'].apply(lambda x: textwrap.fill(str(x), width=14))
            df_fmt['Observaciones'] = df_fmt['Observaciones'].apply(lambda x: textwrap.fill(str(x), width=10))
            df_fmt['Nombre'] = df_fmt['Nombre'].apply(lambda x: textwrap.fill(str(x), width=12))
            df_fmt['Tipo de\nAlmuerzo'] = df_fmt['Tipo de\nAlmuerzo'].apply(lambda x: textwrap.fill(str(x), width=10))

            num_filas = len(df_fmt)
            alto_figura = max(5.0, num_filas * 0.95 + 3.0)
            
            fig, ax = plt.subplots(figsize=(11, alto_figura), dpi=250)
            ax.axis('off')
            
            fecha_hoy = datetime.now(ZONA_ECUADOR).strftime("%d/%m/%Y")
            titulo_con_fecha = f"REPORTE DE PEDIDOS DE ALMUERZO ({fecha_hoy})"
            
            plt.title(titulo_con_fecha, fontsize=26, fontweight='bold', pad=20, color='#0F172A')
            
            col_widths = [0.05, 0.13, 0.11, 0.18, 0.09, 0.16]

            tabla = ax.table(
                cellText=df_fmt.values,
                colLabels=df_fmt.columns,
                colWidths=col_widths,
                cellLoc='center',
                loc='top',
                bbox=[0, 0.20, 1, 0.72]
            )
            
            tabla.auto_set_font_size(False)
            tabla.set_fontsize(17)
            
            for (r, c), cell in tabla.get_celld().items():
                if r == 0:
                    cell.set_facecolor('#1D4ED8')
                    cell.set_text_props(color='white', weight='bold', fontsize=18)
                else:
                    color_fondo = '#F8FAFC' if r % 2 == 0 else '#FFFFFF'
                    cell.set_facecolor(color_fondo)
                    cell.set_text_props(color='#1E293B', weight='bold')
                
                cell.set_edgecolor('#CBD5E1')
                cell.set_linewidth(1.0)

            texto_resumen = (
                f"RESUMEN DE TOTALES:\n"
                f"• Almuerzos Completos: {completo}   |   • Solo Segundo: {solo_seg}   |   • Total Pedidos: {len(df_fmt)}"
            )
            
            plt.text(
                0.5, 0.04, texto_resumen, 
                ha='center', va='center', fontsize=15, fontweight='bold',
                color='#0F172A',
                bbox=dict(boxstyle='round,pad=0.8', facecolor='#E2E8F0', edgecolor='#94A3B8', linewidth=1.2)
            )
            
            plt.tight_layout()
            
            buffer = BytesIO()
            plt.savefig(buffer, format='jpeg', bbox_inches='tight', facecolor='white')
            buffer.seek(0)
            plt.close(fig)
            return buffer

        buf_imagen = generar_imagen_perfecta(df_mostrar, cant_completo, cant_solo_segundo)

        st.image(buf_imagen, caption="Vista previa de la imagen a enviar", use_container_width=True)

        fecha_archivo = datetime.now(ZONA_ECUADOR).strftime('%Y_%m_%d')

        st.download_button(
            label="📲 Descargar Imagen JPG (Para WhatsApp)",
            data=buf_imagen,
            file_name=f"pedidos_{fecha_archivo}.jpg",
            mime="image/jpeg",
        )

    else:
        st.info("Aún no hay pedidos registrados hoy.")

# ====================================================================
# 🔒 PANEL DE ADMINISTRACIÓN PROTEGIDO (BARRA LATERAL)
# ====================================================================
with st.sidebar:
    st.title("⚙️ Administración")
    password_ingresada = st.text_input("Clave de Admin:", type="password")

    if password_ingresada == CLAVE_ADMIN:
        st.success("Acceso concedido")
        
        # --- CONFIGURACIÓN MANUAL DE LA SEMANA ---
        st.markdown("---")
        st.subheader("🗓️ Nombre de la Semana (Manual)")
        nuevo_texto_semana = st.text_input(
            "Rango de la Semana:", 
            value=semana_data.get("texto_semana", "Del 26 al 30 de octubre")
        )
        if st.button("💾 Guardar Texto de Semana"):
            semana_data["texto_semana"] = nuevo_texto_semana.strip()
            guardar_datos_semana(semana_data)
            st.session_state["msg_admin"] = "¡Rango de la semana actualizado!"
            st.rerun()

        # --- CONTROL DE CIERRE MANUAL Y DÍA ACTUAL ---
        st.markdown("---")
        st.subheader("🔒 Control y Acumulación")
        
        nombres_dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
        
        # Inicializar índice en session_state si no existe
        if "dia_ficticio_prueba" not in st.session_state:
            st.session_state["dia_ficticio_prueba"] = semana_data.get("dia_ficticio_prueba", 0)

        dia_activo_idx = st.session_state["dia_ficticio_prueba"]
        if dia_activo_idx > 4:
            dia_activo_idx = 0

        dia_seleccionado_manual = st.selectbox(
            "Acumular pedidos al día:", 
            nombres_dias, 
            index=dia_activo_idx,
            key="dia_seleccionado_admin"
        )

        if pedidos_cerrados:
            if st.button("🔓 Reabrir Pedidos Manualmente"):
                st.session_state["estado_manual_pedidos"] = True
                st.session_state["msg_admin"] = "¡Pedidos reabiertos manualmente!"
                st.rerun()
        else:
            if st.button("🔒 Cerrar Pedidos del Día Manualmente"):
                st.session_state["estado_manual_pedidos"] = False
                st.session_state["msg_admin"] = "¡Pedidos cerrados manualmente para hoy!"
                st.rerun()

        # --- BOTÓN DE PROCESAR Y ACUMULAR DÍA ---
        if st.button(f"📥 Guardar y Acumular Pedidos a {dia_seleccionado_manual}"):
            if os.path.exists(ARCV_PEDIDOS):
                df_pedidos_cierre = pd.read_csv(ARCV_PEDIDOS, sep=";")
                if not df_pedidos_cierre.empty:
                    completos_dia = int((df_pedidos_cierre["Tipo de Almuerzo"] == "Completo").sum())
                    segundos_dia = int((df_pedidos_cierre["Tipo de Almuerzo"] == "Solo segundo").sum())

                    # Cargar última versión del archivo semanal
                    semana_data_fresca = cargar_datos_semana()
                    semana_data_fresca["dias"][dia_seleccionado_manual]["Completos"] = completos_dia
                    semana_data_fresca["dias"][dia_seleccionado_manual]["Segundos"] = segundos_dia

                    # Calcular el siguiente día para avanzar el selector automáticamente
                    idx_actual = nombres_dias.index(dia_seleccionado_manual)
                    idx_siguiente = (idx_actual + 1) % 5
                    
                    semana_data_fresca["dia_ficticio_prueba"] = idx_siguiente
                    st.session_state["dia_ficticio_prueba"] = idx_siguiente

                    guardar_datos_semana(semana_data_fresca)
                    
                    # Limpiar lista diaria
                    pd.DataFrame(columns=COLUMNAS).to_csv(ARCV_PEDIDOS, index=False, sep=";")
                    st.session_state["estado_manual_pedidos"] = None
                    
                    st.session_state["msg_admin"] = f"¡Se acumularon {completos_dia} completos y {segundos_dia} segundos en {dia_seleccionado_manual}! (Próximo día preparado: {nombres_dias[idx_siguiente]})"
                    st.rerun()
                else:
                    st.warning("No hay pedidos registrados hoy para acumular.")

        # --- CONTROLES DE LIMPIEZA / PRUEBAS ---
        st.markdown("---")
        st.subheader("🧹 Gestión de Pruebas")
        
        dia_a_borrar = st.selectbox("Limpiar acumulado de un día:", nombres_dias, key="select_borrar_dia")
        if st.button(f"🗑️ Borrar registro de {dia_a_borrar}"):
            semana_data["dias"][dia_a_borrar] = {"Completos": 0, "Segundos": 0}
            guardar_datos_semana(semana_data)
            st.session_state["msg_admin"] = f"¡Registro de {dia_a_borrar} reiniciado a 0!"
            st.rerun()

        if st.button("🔄 Renovar Toda la Semana (Reiniciar a $0)"):
            semana_data["dias"] = {
                "Lunes": {"Completos": 0, "Segundos": 0},
                "Martes": {"Completos": 0, "Segundos": 0},
                "Miércoles": {"Completos": 0, "Segundos": 0},
                "Jueves": {"Completos": 0, "Segundos": 0},
                "Viernes": {"Completos": 0, "Segundos": 0}
            }
            semana_data["dia_ficticio_prueba"] = 0
            st.session_state["dia_ficticio_prueba"] = 0
            guardar_datos_semana(semana_data)
            st.session_state["msg_admin"] = "¡Tabla semanal reiniciada por completo!"
            st.rerun()

        # --- CAMBIAR MENÚ DEL DÍA ---
        st.markdown("---")
        st.subheader("🍱 Actualizar Menú del Día")
        
        nuevo_caldo_input = st.text_input("Nombre del Caldo:", value=TEXTO_CALDO.replace("Caldo: ", ""))
        
        segundos_texto_def = "\n".join(OPCIONES_SEGUNDO)
        nuevos_segundos_input = st.text_area(
            "Opciones de Segundo (un plato por línea):",
            value=segundos_texto_def,
            height=120
        )

        if st.button("💾 Guardar Menú"):
            lista_segundos = [s.strip() for s in nuevos_segundos_input.split("\n") if s.strip()]
            if lista_segundos and nuevo_caldo_input.strip():
                nuevo_menu = {
                    "caldo": f"Caldo: {nuevo_caldo_input.strip()}",
                    "segundos": lista_segundos
                }
                guardar_menu(nuevo_menu)
                st.session_state["msg_admin"] = "¡Menú del día actualizado con éxito!"
                st.rerun()
            else:
                st.error("Por favor completa el caldo y al menos una opción de segundo.")

        # --- DESCARGA DEL REPORTE EXACTO A TU IMAGEN EXCEL/CSV ---
        st.markdown("---")
        st.subheader("📊 Generar Reporte Semanal (Formato Exacto)")
        
        semana_actual_export = cargar_datos_semana()
        d = semana_actual_export["dias"]
        
        comp_l = d["Lunes"]["Completos"]
        comp_m = d["Martes"]["Completos"]
        comp_mi = d["Miércoles"]["Completos"]
        comp_j = d["Jueves"]["Completos"]
        comp_v = d["Viernes"]["Completos"]
        tot_comp = comp_l + comp_m + comp_mi + comp_j + comp_v
        tot_comp_val = tot_comp * PRECIO_COMPLETO

        seg_l = d["Lunes"]["Segundos"]
        seg_m = d["Martes"]["Segundos"]
        seg_mi = d["Miércoles"]["Segundos"]
        seg_j = d["Jueves"]["Segundos"]
        seg_v = d["Viernes"]["Segundos"]
        tot_seg = seg_l + seg_m + seg_mi + seg_j + seg_v
        tot_seg_val = tot_seg * PRECIO_SEGUNDO

        gran_total_semana = tot_comp_val + tot_seg_val

        texto_sem = semana_actual_export.get('texto_semana', 'Del 26 al 30 de octubre')
        if not texto_sem.lower().startswith("del"):
            texto_sem = f"Del {texto_sem}"

        filas_csv = [
            ["Precio por almuerzo completo:", "", "", "", f"${PRECIO_COMPLETO:.2f}".replace(".", ",")],
            ["Precio por solo segundo:", "", "", "", f"${PRECIO_SEGUNDO:.2f}".replace(".", ",")],
            [""],
            ["Semana:", texto_sem],
            ["Dia / Almuerzo", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Total"],
            ["Completos", comp_l, comp_m, comp_mi, comp_j, comp_v, f"${tot_comp_val:.2f}".replace(".", ",")],
            ["Segundos", seg_l, seg_m, seg_mi, seg_j, seg_v, f"${tot_seg_val:.2f}".replace(".", ",")],
            ["", "", "Total a pagar en la semana:", "", "", "", f"${gran_total_semana:.2f}".replace(".", ",")]
        ]

        df_export = pd.DataFrame(filas_csv)
        csv_bytes = df_export.to_csv(index=False, header=False, sep=";").encode("utf-8-sig")

        st.download_button(
            label="📥 Descargar CSV Semanal (Formato Exacto)",
            data=csv_bytes,
            file_name=f"reporte_semanal.csv",
            mime="text/csv"
        )

        if os.path.exists(ARCV_PEDIDOS):
            df_pedidos_admin = pd.read_csv(ARCV_PEDIDOS, sep=";")
            
            if not df_pedidos_admin.empty:
                df_admin_show = df_pedidos_admin.sort_values(by="Tipo de Almuerzo", ascending=True).reset_index(drop=True)
                df_admin_show.insert(0, "#", range(1, len(df_admin_show) + 1))
                
                # --- ELIMINAR PEDIDO INDIVIDUAL ---
                st.markdown("---")
                st.subheader("🗑️ Eliminar un pedido erróneo")
                fila_a_borrar = st.selectbox("Selecciona el número de persona (#) a eliminar:", df_admin_show["#"])
                
                if st.button("Eliminar pedido seleccionado"):
                    idx_a_borrar = fila_a_borrar - 1
                    df_pedidos_admin = df_pedidos_admin.drop(df_pedidos_admin.index[idx_a_borrar])
                    df_pedidos_admin.to_csv(ARCV_PEDIDOS, index=False, sep=";")
                    st.session_state["msg_admin"] = f"¡Pedido #{fila_a_borrar} eliminado!"
                    st.rerun()

        # --- RESETEAR BASE DE DATOS DEL DÍA ---
        st.markdown("---")
        st.subheader("⚠️ Resetear base de datos del día")
        if st.button("Borrar pedidos de hoy"):
            if os.path.exists(ARCV_PEDIDOS):
                os.remove(ARCV_PEDIDOS)
                st.session_state["msg_admin"] = "¡Base de datos del día reiniciada!"
                st.rerun()

    elif password_ingresada != "":
        st.error("Clave incorrecta")
