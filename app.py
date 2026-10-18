import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
import textwrap
from io import BytesIO

# ====================================================================
# 📝 MENÚ DEL DÍA - EDITA AQUí ESTOS DATOS CADA DÍA SEGÚN EL RESTAURANTE 📝
# ====================================================================
TEXTO_CALDO = "Caldo: AGUADO DE POLLO"

OPCIONES_SEGUNDO = [
    "SUDADO DE CAMARON",
    "POLLO FRITO Y MENESTRA DE FREJOL"
]
# ====================================================================

ARCV_PEDIDOS = "pedidos_almuerzo.csv"
COLUMNAS = ["Nombre", "Tipo de Almuerzo", "Segundo", "Arroz", "Observaciones"]

# Si el archivo no existe, lo creamos
if not os.path.exists(ARCV_PEDIDOS):
    df_inicial = pd.DataFrame(columns=COLUMNAS)
    df_inicial.to_csv(ARCV_PEDIDOS, index=False, sep=";")

st.title("🍱 Registro de Pedidos de Almuerzo")

# --- SECCIÓN 1: FORMULARIO DE REGISTRO ---
# Aquí se muestra automáticamente el caldo configurado arriba
st.header(TEXTO_CALDO)

nombre = st.text_input("Tu nombre:")
completo_segundo = st.radio("¿Completo o solo segundo?:", ["Completo", "Solo segundo"])

# Aquí se cargan automáticamente las opciones de segundo configuradas arriba
seleccion_segundo = st.radio("Selecciona el segundo:", OPCIONES_SEGUNDO)

# El arroz se mantiene fijo como pediste
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
        st.success(f"¡Pedido registrado con éxito para {nombre}!")
        st.rerun()
    else:
        st.warning("Por favor, escribe tu nombre antes de enviar.")

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
        
        # --- ELIMINAR UN PEDIDO ---
        st.subheader("🗑️ Eliminar un pedido erróneo")
        fila_a_borrar = st.selectbox("Selecciona el número de persona (#) a eliminar:", df_mostrar["#"])
        
        if st.button("Eliminar pedido seleccionado"):
            idx_a_borrar = fila_a_borrar - 1
            df_pedidos = df_pedidos.drop(df_pedidos.index[idx_a_borrar])
            df_pedidos.to_csv(ARCV_PEDIDOS, index=False, sep=";")
            st.success(f"¡Pedido #{fila_a_borrar} eliminado!")
            st.rerun()

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

        # --- GENERACIÓN DE IMAGEN PERFECTA PARA WHATSAPP ---
        st.subheader("🖼️ Generar imagen para compartir por WhatsApp")

        def generar_imagen_perfecta(df, completo, solo_seg):
            df_fmt = df.copy()
            df_fmt['Segundo'] = df_fmt['Segundo'].apply(lambda x: textwrap.fill(str(x), width=22))
            df_fmt['Observaciones'] = df_fmt['Observaciones'].apply(lambda x: textwrap.fill(str(x), width=18))
            df_fmt['Nombre'] = df_fmt['Nombre'].apply(lambda x: textwrap.fill(str(x), width=15))

            num_filas = len(df_fmt)
            alto_figura = max(4.5, num_filas * 0.75 + 2.5)
            
            fig, ax = plt.subplots(figsize=(11, alto_figura), dpi=250)
            ax.axis('off')
            
            plt.title("REPORTE DE PEDIDOS DE ALMUERZO", fontsize=15, fontweight='bold', pad=15, color='#0F172A')
            
            col_widths = [0.06, 0.20, 0.18, 0.28, 0.12, 0.16]

            tabla = ax.table(
                cellText=df_fmt.values,
                colLabels=df_fmt.columns,
                colWidths=col_widths,
                cellLoc='center',
                loc='top',
                bbox=[0, 0.22, 1, 0.70]
            )
            
            tabla.auto_set_font_size(False)
            tabla.set_fontsize(9)
            
            for (r, c), cell in tabla.get_celld().items():
                if r == 0:
                    cell.set_facecolor('#1D4ED8')
                    cell.set_text_props(color='white', weight='bold', fontsize=9.5)
                    cell.set_height(0.08)
                else:
                    color_fondo = '#F8FAFC' if r % 2 == 0 else '#FFFFFF'
                    cell.set_facecolor(color_fondo)
                    cell.set_text_props(color='#1E293B')
                
                cell.set_edgecolor('#CBD5E1')
                cell.set_linewidth(0.8)

            texto_resumen = (
                f"RESUMEN DE TOTALES:\n"
                f"• Almuerzos Completos: {completo}   |   • Solo Segundo: {solo_seg}   |   • Total Pedidos: {len(df_fmt)}"
            )
            
            plt.text(
                0.5, 0.06, texto_resumen, 
                ha='center', va='center', fontsize=10, fontweight='bold',
                color='#0F172A',
                bbox=dict(boxstyle='round,pad=0.7', facecolor='#E2E8F0', edgecolor='#94A3B8', linewidth=1)
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

# --- BOTÓN PARA REINICIAR LA TABLA (Nuevo día / Nuevo menú) ---
st.divider()
if st.button("⚠️ Resetear base de datos (Borrar pedidos anteriores)"):
    if os.path.exists(ARCV_PEDIDOS):
        os.remove(ARCV_PEDIDOS)
        st.success("¡Base de datos reiniciada para un nuevo día!")
        st.rerun()
