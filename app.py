import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
import textwrap
from io import BytesIO

# ====================================================================
# 📝 MENÚ DEL DÍA - EDITA AQUÍ ESTOS DATOS CADA DÍA SEGÚN EL RESTAURANTE 📝
# ====================================================================
TEXTO_CALDO = "Caldo: Menestron de carne"

OPCIONES_SEGUNDO = [
    "Pollo al horno con ensalada de remolacha",
    "Arroz con camaron"
]

# 🔑 CAMBIA ESTA CONTRASEÑA PARA TU ACCESO ADMINISTRADOR
CLAVE_ADMIN = "admin123"
# ====================================================================

ARCV_PEDIDOS = "pedidos_almuerzo.csv"
COLUMNAS = ["Nombre", "Tipo de Almuerzo", "Segundo", "Arroz", "Observaciones"]

# Si el archivo no existe, lo creamos
if not os.path.exists(ARCV_PEDIDOS):
    df_inicial = pd.DataFrame(columns=COLUMNAS)
    df_inicial.to_csv(ARCV_PEDIDOS, index=False, sep=";")

st.title("🍱 Registro de Pedidos de Almuerzo")

# --- MENSAJE DE ADMIN (APARECE ARRIBA DE TODO) ---
if "msg_admin" in st.session_state:
    st.success(st.session_state["msg_admin"])
    del st.session_state["msg_admin"]

# --- SECCIÓN 1: FORMULARIO DE REGISTRO ---
st.header(TEXTO_CALDO)

nombre = st.text_input("Tu nombre:")
completo_segundo = st.radio("¿Completo o solo segundo?:", ["Completo", "Solo segundo"])
seleccion_segundo = st.radio("Selecciona el segundo:", OPCIONES_SEGUNDO)
tipo_arroz = st.radio("Selecciona el arroz:", ["Blanco", "Moro"])
notas = st.text_area("Observaciones (opcional):", placeholder="Ej: MADURO EXTRA")

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
        st.session_state["msg_pedido"] = f"✅ Pedido registrado con éxito para {nombre.strip()}"
        st.rerun()
    else:
        st.warning("Por favor, escribe tu nombre antes de enviar.")

# --- MENSAJE DE PEDIDO REGISTRADO (APARECE ABAJO DEL BOTÓN "GUARDAR PEDIDO") ---
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

        df_mostrar = df_pedidos.copy()
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

        # --- GENERACIÓN DE IMAGEN CON LETRA GRANDE Y FORMATO MULTILÍNEA CORREGIDO ---
        st.subheader("🖼️ Generar imagen para compartir por WhatsApp")

        def generar_imagen_perfecta(df, completo, solo_seg):
            df_fmt = df.copy()
            
            # Renombramos el encabezado para que salga en dos líneas
            df_fmt = df_fmt.rename(columns={"Tipo de Almuerzo": "Tipo de\nAlmuerzo"})

            # Saltos de línea ajustados para no cortar palabras cortas como "Completo"
            df_fmt['Segundo'] = df_fmt['Segundo'].apply(lambda x: textwrap.fill(str(x), width=14))
            df_fmt['Observaciones'] = df_fmt['Observaciones'].apply(lambda x: textwrap.fill(str(x), width=10))
            df_fmt['Nombre'] = df_fmt['Nombre'].apply(lambda x: textwrap.fill(str(x), width=12))
            df_fmt['Tipo de\nAlmuerzo'] = df_fmt['Tipo de\nAlmuerzo'].apply(lambda x: textwrap.fill(str(x), width=10))

            num_filas = len(df_fmt)
            alto_figura = max(5.0, num_filas * 0.95 + 3.0)
            
            fig, ax = plt.subplots(figsize=(11, alto_figura), dpi=250)
            ax.axis('off')
            
            plt.title("REPORTE DE PEDIDOS DE ALMUERZO", fontsize=30, fontweight='bold', pad=20, color='#0F172A')
            
            col_widths = [0.05, 0.10, 0.11, 0.18, 0.09, 0.16]

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

        st.download_button(
            label="📲 Descargar Imagen JPG (Para WhatsApp)",
            data=buf_imagen,
            file_name="pedidos_del_dia.jpg",
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
        
        if os.path.exists(ARCV_PEDIDOS):
            df_pedidos_admin = pd.read_csv(ARCV_PEDIDOS, sep=";")
            
            if not df_pedidos_admin.empty:
                df_admin_show = df_pedidos_admin.copy()
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

        # --- RESETEAR BASE DE DATOS ---
        st.markdown("---")
        st.subheader("⚠️ Resetear base de datos")
        if st.button("Borrar pedidos anteriores"):
            if os.path.exists(ARCV_PEDIDOS):
                os.remove(ARCV_PEDIDOS)
                st.session_state["msg_admin"] = "¡Base de datos reiniciada para un nuevo día!"
                st.rerun()

    elif password_ingresada != "":
        st.error("Clave incorrecta")
