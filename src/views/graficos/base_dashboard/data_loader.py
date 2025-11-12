# data_loader.py
import streamlit as st
import pandas as pd

@st.cache_data(ttl=3600, show_spinner=False)
def load_and_process_data(uploaded_file):
    """
    Carga y procesa eficientemente los datos desde un archivo Excel.
    
    Las hojas 'Reporte_Llamadas' y 'Reporte_Mensajes' son opcionales.
    Las alertas de carga ahora se recolectan y se devuelven en un diccionario.
    La alerta de negocio de "Novedades del Sistema" ha sido eliminada.

    Retorna:
        (df_cartera, df_novedades, df_llamadas, df_mensajeria, alerts)
    """
    
    cols_cartera = [
        "Fecha_Desembolso", "Fecha_Ultima_Novedad", "Empresa", "Regional_Venta",
        "Nombre_Ciudad", "Nombre_Vendedor", "Franja_Meta", "Rodamiento", "Gestor",
        "Regional_Cobro", "Zona_Cobro", "Zona",
        "Cantidad_Novedades", "Cedula_Cliente", "Credito", "Nombre_Producto",
        "Obsequio", "Nombre_Cliente", "Correo", "Celular", "Direccion", "Barrio",
        "Nombre_Codeudor2", "Cobrador", "Telefono_Cobrador", "Call_Center_Apoyo",
        "Codigo_Vendedor", "Nombre_Call_Center", "Telefono_Call_Center",
        "Telefono_Gestor", "Valor_Desembolso", "Movil_Vendedor", "Vendedor_Activo",
        "Lider_Zona", "Codeudor1", "Total_Cuotas", "Nombre_Codeudor1",
        "Telefono_Codeudor1", "Ciudad_Codeudor1", "Codeudor2", "Nombre_Codeudor2",
        "Telefono_Codeudor2", "Ciudad_Codeudor2", "Valor_Cuota", "Dias_Atraso", "Franja_Cartera",
        "Meta_Intereses", "Meta_Saldo", "Meta_%", "Meta_$", "Meta_T.R_%","Meta_General",
        "Meta_T.R_$", "Cuotas_Pagadas", "Fecha_Cuota_Atraso", "Primera_Cuota_Mora",
        "Valor_Cuota_Atraso", "Valor_Vencido", "Dias_Atraso_Final","Fecha_Ultimo_pago","Rango_Ultimo_pago",
        "Franja_Meta_Final", "Franja_Cartera_Final", "Rodamiento_Cartera","Valor_Cuota_Vigente",
        "Recaudo_Anticipado", "Recaudo_Meta", "Total_Recaudo", "Fecha_Cuota_Vigente","Total_Recaudo_Sin_Anti"
    ]
    
    cols_novedades = [
        "Fecha_Novedad", "Cedula_Cliente", "Nombre_Cliente", "Usuario_Novedad",
        "Nombre_Usuario", "Cargo_Usuario", "Celular_Corporativo", "Tipo_Novedad",
        "Novedad", "Fecha_Compromiso", "Valor","Empresa","Celular_Cliente","Telefono_Cliente"
    ]
    
    cols_llamadas = [
        "Fecha_Llamada", "Extension_Llamada", "Destino_Llamada", "Estado_Llamada", "Duracion_Llamada",
        "Codigo_Llamada", "Grabacion_Llamada", "Call_Center", "Nombre_Call"
    ]
    
    cols_mensajeria = [
        "Codigo_Pais", "Numero_Telefono", "Nombre_Saliente", "Estado", "Estado_Mensaje", "Estado_Respuesta_Saliente",
        "Respuesta_Saliente", "Flujo_Truora", "Primer_Mensaje_Agente", "Fecha_Llamada", "Call_Center", "Nombre_Call"
    ]

    df_llamadas = pd.DataFrame()
    df_mensajeria = pd.DataFrame()
    df_cartera = None
    df_novedades = None
    
    # INICIALIZACIÓN: Diccionario para recolectar alertas.
    # ELIMINAMOS la alerta de 'novedades_error' para que no se muestre por defecto.
    alerts = {
        'llamadas_error': None,
        'mensajeria_error': None,
        'novedades_error': None # Ahora es None por defecto
    }

    try: 
        df_cartera = pd.read_excel(
            uploaded_file, 
            sheet_name="Analisis_de_Cartera",
            engine='openpyxl',
            usecols=cols_cartera
        )
        
        df_novedades = pd.read_excel(
            uploaded_file,
            sheet_name="Detalle_Novedades",
            engine='openpyxl',
            usecols=cols_novedades
        )

        date_cols = ["Fecha_Desembolso", "Fecha_Ultima_Novedad", "Fecha_Cuota_Atraso", 
                     "Primera_Cuota_Mora",]
        for col in date_cols:
            if col in df_cartera.columns:
                df_cartera[col] = pd.to_datetime(df_cartera[col], errors="coerce").dt.date

        date_cols_novedades = ["Fecha_Novedad", "Fecha_Compromiso"]
        for col in date_cols_novedades:
            if col in df_novedades.columns:
                df_novedades[col] = pd.to_datetime(df_novedades[col], errors="coerce").dt.date

        str_cols = ["Empresa", "Regional_Venta", "Nombre_Ciudad", "Nombre_Vendedor", 
                     "Franja_Meta", "Rodamiento", "Gestor", "Regional_Cobro", 
                     "Zona_Cobro", "Zona"]
        for col in str_cols:
            if col in df_cartera.columns:
                df_cartera[col] = df_cartera[col].astype(str).str.strip()

        if "Cantidad_Novedades" in df_cartera.columns:
            df_cartera['Cantidad_Novedades'] = pd.to_numeric(df_cartera['Cantidad_Novedades'], errors='coerce').fillna(0)

        if 'Cedula_Cliente' in df_cartera.columns:
            df_cartera['Cedula_Cliente'] = df_cartera['Cedula_Cliente'].astype(str).str.strip()

        if 'Cedula_Cliente' in df_novedades.columns:
            df_novedades['Cedula_Cliente'] = df_novedades['Cedula_Cliente'].astype(str).str.strip()
            
        # 1. Cargar Reporte_Llamadas
        try:
            df_llamadas = pd.read_excel(
                uploaded_file,
                sheet_name="Reporte_Llamadas",
                engine='openpyxl',
                usecols=cols_llamadas
            )
            # Limpieza básica de llamadas
            if "Fecha_Llamada" in df_llamadas.columns:
                df_llamadas["Fecha_Llamada"] = pd.to_datetime(df_llamadas["Fecha_Llamada"], errors="coerce")
            
            str_cols_llamadas = [
                "Extension_Llamada", "Destino_Llamada", "Estado_Llamada", 
                "Codigo_Llamada", "Grabacion_Llamada", "Call_Center", "Nombre_Call"
            ]
            for col in str_cols_llamadas:
                if col in df_llamadas.columns:
                    df_llamadas[col] = df_llamadas[col].astype(str).str.strip()

        except Exception as e:
            # Recolectar la alerta en lugar de mostrarla
            alerts['llamadas_error'] = f"Nota: No se pudo cargar la hoja 'Reporte_Llamadas'. Causa: {e}"

        # 2. Cargar Reporte_Mensajes
        try:
            df_mensajeria = pd.read_excel(
                uploaded_file,
                sheet_name="Reporte_Mensajes",
                engine='openpyxl',
                usecols=cols_mensajeria
            )
            # Limpieza básica de mensajería
            if "Fecha_Llamada" in df_mensajeria.columns: # Basado en tu lista de columnas
                df_mensajeria["Fecha_Llamada"] = pd.to_datetime(
                    df_mensajeria["Fecha_Llamada"], errors="coerce", dayfirst=True
                ).dt.date
            
            str_cols_mensajeria = [
                "Codigo_Pais", "Numero_Telefono", "Nombre_Saliente", "Estado", 
                "Estado_Menasaje", "Estado_Respuesta_Saliemte", "Respuesta_Saliente", 
                "Flujo_Truora", "Primer_Mensaje_Agente", "Call_Center", "Nombre_Call"
            ]
            for col in str_cols_mensajeria:
                if col in df_mensajeria.columns:
                    df_mensajeria[col] = df_mensajeria[col].astype(str).str.strip()
        except Exception as e:
            # Recolectar la alerta en lugar de mostrarla
            alerts['mensajeria_error'] = f"Nota: No se pudo cargar la hoja 'Reporte_Mensajes'. Causa: {e}"
            
        # Lógica de la alerta de negocio de Novedades del Sistema ha sido ELIMINADA
        # No se inicializa ni se sobreescribe, por lo que queda como None y no se muestra.
            
        # Devolver el diccionario de alertas como quinto valor
        return df_cartera, df_novedades, df_llamadas, df_mensajeria, alerts

    except Exception as e:
        # Alerta crítica: las hojas principales (Cartera o Novedades) no se cargaron.
        st.error(f"Error crítico al leer las hojas principales (Cartera o Novedades). Asegúrate de que existan. Error: {e}")
        return None, None, None, None, alerts