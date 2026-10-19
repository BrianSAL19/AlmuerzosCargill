import streamlit as st
import pandas as pd
import os
import json
import matplotlib.pyplot as plt
import textwrap
from datetime import datetime, timezone, timedelta
from io import BytesIO

# ====================================================================
# 🔑 CONFIGURACIÓN Y ESTADO DE SESIÓN
# ====================================================================
CLAVE_ADMIN = "admin123"
COLUMNAS = ["Nombre", "Tipo de Almuerzo", "Segundo", "Arroz", "Observaciones"]

st.set_page_config(page_title="Registro de Pedidos de Almuerzo", page_icon="🍱")

SEDES_DISPONIBLES = ["OM Cargill", "OM Oficina"]

# Inicializar la sede en la sesión si aún no existe
if "sede_activa" not in st.session_state:
    st.session_state["sede_activa"] = "OM Cargill"

sede_seleccionada = st.session_state["sede_activa"]

# Mapeo de archivos independientes según la sede configurada por el admin
slug_sede = sede_seleccionada.lower().replace(" ", "_")
ARCV_PEDIDOS = f"pedidos_{slug_sede}.csv"
ARCV_MENU = f"menu_{slug_sede}.json"

# Cargar o inicializar el menú del día por sede
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

# Si el archivo de pedidos de la sede no existe, lo creamos
if not os.path.exists(ARCV_PEDIDOS):
    df_inicial = pd.DataFrame(columns=COLUMNAS)
    df_inicial.to_csv(ARCV_PEDIDOS, index=False, sep=";")

st.title(f"🍱 Registro de Pedidos - {sede_seleccionada}")

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

# --- SECCIÓN 1: FORMULARIO DE REGISTRO ---
st.header(TEXTO_CALDO)

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
        st.session_state["msg_pedido"] = f"✅ Pedido registrado con éxito en {sede_seleccionada} para {nombre.strip()}"
        st.rerun()
    else:
        st.warning("Por favor, escribe tu nombre antes de enviar.")

# --- MENSAJE DE PEDIDO REGISTRADO (APARECE ABAJO DEL BOTÓN "GUARDAR PEDIDO") ---
if "msg_pedido" in st.session_state:
    st.success(st.session_state["msg_pedido"])
    del st.session_state["msg_pedido"]

st.divider()

# --- SECCIÓN 2: LISTA Y GESTIÓN DE PEDIDOS ---
st.header(f"📋 Lista Consolidada - {sede_seleccionada}")

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

        def generar_imagen_perfecta(df, completo, solo_seg, sede):
            df_fmt = df.copy()
            
            df_fmt = df_fmt.rename(columns={"Tipo de Almuerzo": "Tipo de\nAlmuerzo"})

            df_fmt['Segundo'] = df_fmt['Segundo'].apply(lambda x: textwrap.fill(str(x), width=13))
            df_fmt['Observaciones'] = df_fmt['Observaciones'].apply(lambda x: textwrap.fill(str(x), width=8))
            df_fmt['Nombre'] = df_fmt['Nombre'].apply(lambda x: textwrap.fill(str(x), width=11))
            df_fmt['Tipo de\nAlmuerzo'] = df_fmt['Tipo de\nAlmuerzo'].apply(lambda x: textwrap.fill(str(x), width=10))

            num_filas = len(df_fmt)
            alto_figura = max(5.0, num_filas * 1.1 + 3.0)
            
            fig, ax = plt.subplots(figsize=(11, alto_figura), dpi=250)
            ax.axis('off')
            
            # 📅 FECHA EXACTA DE ECUADOR (UTC-5)
            zona_ecuador = timezone(timedelta(hours=-5))
            fecha_hoy = datetime.now(zona_ecuador).strftime("%d/%m/%Y")
            titulo_con_fecha = f"REPORTE PEDIDOS - {sede.upper()}\n({fecha_hoy})"
            
            plt.title(titulo_con_fecha, fontsize=24, fontweight='bold', pad=20, color='#0F172A')
            
            col_widths = [0.05, 0.12, 0.13, 0.22, 0.10, 0.18]

            tabla = ax.table(
                cellText=df_fmt.values,
                colLabels=df_fmt.columns,
                colWidths=col_widths,
                cellLoc='center',
                loc='top',
                bbox=[0, 0.20, 1, 0.72]
            )
            
            tabla.auto_set_font_size(False)
            tabla.set_fontsize(15)
            
            for (r, c), cell in tabla.get_celld().items():
                if r == 0:
                    cell.set_facecolor('#1D4ED8')
                    cell.set_text_props(color='white', weight='bold', fontsize=17)
                else:
                    color_fondo = '#F8FAFC' if r % 2 == 0 else '#FFFFFF'
                    cell.set_facecolor(color_fondo)
                    cell.set_text_props(color='#1E293B', weight='bold')
                
                cell.set_edgecolor('#CBD5E1')
                cell.set_linewidth(1.0)

            texto_resumen = (
                f"RESUMEN DE TOTALES ({sede}):\n"
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

        buf_imagen = generar_imagen_perfecta(df_mostrar, cant_completo, cant_solo_segundo, sede_seleccionada)

        st.image(buf_imagen, caption=f"Vista previa de la imagen - {sede_seleccionada}", use_container_width=True)

        zona_ecuador = timezone(timedelta(hours=-5))
        fecha_archivo = datetime.now(zona_ecuador).strftime('%Y_%m_%d')

        st.download_button(
            label="📲 Descargar Imagen JPG (Para WhatsApp)",
            data=buf_imagen,
            file_name=f"pedidos_{slug_sede}_{fecha_archivo}.jpg",
            mime="image/jpeg",
        )

    else:
        st.info(f"Aún no hay pedidos registrados hoy para {sede_seleccionada}.")

# ====================================================================
# 🔒 PANEL DE ADMINISTRACIÓN PROTEGIDO (BARRA LATERAL)
# ====================================================================
with st.sidebar:
    st.title("⚙️ Administración")
    
    password_ingresada = st.text_input("Clave de Admin:", type="password")

    if password_ingresada == CLAVE_ADMIN:
        st.success("Acceso concedido")
        
        # --- SELECTOR DE SEDE / EMPRESA DENTRO DEL MODO ADMIN ---
        st.markdown("---")
        st.subheader("🏢 Seleccionar Sede/Lugar")
        
        idx_actual = SEDES_DISPONIBLES.index(sede_seleccionada) if sede_seleccionada in SEDES_DISPONIBLES else 0
        nueva_sede = st.selectbox(
            "Selecciona la Sede activa:",
            SEDES_DISPONIBLES,
            index=idx_actual
        )
        
        if nueva_sede != st.session_state["sede_activa"]:
            st.session_state["sede_activa"] = nueva_sede
            st.session_state["msg_admin"] = f"Sede cambiada a: {nueva_sede}"
            st.rerun()

        # --- CAMBIAR MENÚ DEL DÍA ---
        st.markdown("---")
        st.subheader(f"🍱 Menú del Día ({sede_seleccionada})")
        
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
                st.session_state["msg_admin"] = f"¡Menú de {sede_seleccionada} actualizado con éxito!"
                st.rerun()
            else:
                st.error("Por favor completa el caldo y al menos una opción de segundo.")

        if os.path.exists(ARCV_PEDIDOS):
            df_pedidos_admin = pd.read_csv(ARCV_PEDIDOS, sep=";")
            
            if not df_pedidos_admin.empty:
                df_admin_show = df_pedidos_admin.sort_values(by="Tipo de Almuerzo", ascending=True).reset_index(drop=True)
                df_admin_show.insert(0, "#", range(1, len(df_admin_show) + 1))
                
                # --- ELIMINAR PEDIDO INDIVIDUAL ---
                st.markdown("---")
                st.subheader("🗑️ Eliminar un pedido erróneo")
                fila_a_borrar = st.selectbox("Selecciona el número (#) a eliminar:", df_admin_show["#"])
                
                if st.button("Eliminar pedido seleccionado"):
                    idx_a_borrar = fila_a_borrar - 1
                    df_pedidos_admin = df_pedidos_admin.drop(df_pedidos_admin.index[idx_a_borrar])
                    df_pedidos_admin.to_csv(ARCV_PEDIDOS, index=False, sep=";")
                    st.session_state["msg_admin"] = f"¡Pedido #{fila_a_borrar} de {sede_seleccionada} eliminado!"
                    st.rerun()

        # --- RESETEAR BASE DE DATOS ---
        st.markdown("---")
        st.subheader("⚠️ Resetear base de datos")
        if st.button(f"Borrar pedidos de {sede_seleccionada}"):
            if os.path.exists(ARCV_PEDIDOS):
                os.remove(ARCV_PEDIDOS)
                st.session_state["msg_admin"] = f"¡Base de datos de {sede_seleccionada} reiniciada para un nuevo día!"
                st.rerun()

    elif password_ingresada != "":
        st.error("Clave incorrecta")
