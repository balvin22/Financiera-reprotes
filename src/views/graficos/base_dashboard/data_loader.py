# data_loader.py
import streamlit as st
import pandas as pd

@st.cache_data(ttl=3600, show_spinner=False)

def load_and_process_data(uploaded_file):
    """
    Carga y procesa eficientemente los datos desde un archivo Excel.
    
    Las hojas 'Reporte_Llamadas', 'Reporte_Mensajes' y 'FNZ007' son opcionales.
    Las alertas de carga ahora se recolectan y se devuelven en un diccionario.
    La alerta de negocio de "Novedades del Sistema" ha sido eliminada.

    Retorna:
        (df_cartera, df_novedades, df_llamadas, df_mensajeria, df_fnz, alerts)
    """
    
    cols_cartera = [                                                                                                                                       
                'Empresa', 'Credito', 'Fecha_Desembolso', 'Factura_Venta', 'Fecha_Facturada',
                'Nombre_Producto', 'Cantidad_Producto', 'Obsequio', 'Cantidad_Obsequio',
                'Cedula_Cliente', 'Nombre_Cliente', 'Correo','Celular','Direccion', 'Barrio',
                'Nombre_Ciudad','Zona', 'Cobrador','Telefono_Cobrador', 'Zona_Cobro',
                'Call_Center_Apoyo', 'Nombre_Call_Center','Telefono_Call_Center', 'Regional_Cobro',
                'Gestor', 'Telefono_Gestor','Jefe_ventas','Celular_Jefe_Ventas','Codigo_Vendedor','Cedula_Vendedor',
                'Nombre_Vendedor','Celular_Vendedor','Vendedor_Activo','Zona_Venta','Lider_Zona','Celular_Lider_Zona','Codigo_Centro_Costos',
                'Regional_Venta', 'Codeudor1', 'Nombre_Codeudor1', 'Telefono_Codeudor1',
                'Ciudad_Codeudor1', 'Codeudor2', 'Nombre_Codeudor2', 'Telefono_Codeudor2',
                'Ciudad_Codeudor2', 'Valor_Desembolso', 'Total_Cuotas', 'Valor_Cuota',
                'Dias_Atraso', 'Franja_Meta','Franja_Cartera', 'Saldo_Capital', 'Saldo_Interes_Corriente',
                'Saldo_Avales', 'Meta_Intereses', 'Meta_General','Meta_Saldo', 'Meta_%', 'Meta_$',
                'Meta_T.R_%', 'Meta_T.R_$', 'Cuotas_Pagadas', 'Cuota_Vigente',
                'Fecha_Cuota_Vigente', 'Valor_Cuota_Vigente', 'Fecha_Cuota_Atraso',
                'Primera_Cuota_Mora', 'Fecha_Ultimo_Pago_Inicial', 'Rango_Ultimo_pago_Inicial',
                'Valor_Cuota_Atraso', 'Valor_Vencido','Fecha_Ultima_Novedad', 'Cantidad_Novedades','Fecha_Ultimo_pago','Rango_Ultimo_pago', 'Dias_Atraso_Final',
                'Franja_Meta_Final','Franja_Cartera_Final', 'Rodamiento','Rodamiento_Cartera' ,
                'Recaudo_Anticipado', 'Recaudo_Meta','Total_Recaudo','Total_Recaudo_Sin_Anti'
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
        "Fecha_Mensaje", "Numero_Telefono", "Nombre_Saliente", "Estado", "Estado_Mensaje", "Estado_Respuesta_Entrante",
        "Flujo_Truora", "Estado_Proceso", "Fallo_Proceso","Tipo_Respuesta_Agente","Call_Center", "Nombre_Call"
    ]

    # Inicialización de DataFrames opcionales
    df_llamadas = pd.DataFrame()
    df_mensajeria = pd.DataFrame()
    df_fnz = pd.DataFrame() 
    
    df_cartera = None
    df_novedades = None
    
    # INICIALIZACIÓN: Diccionario para recolectar alertas.
    alerts = {
        'llamadas_error': None,
        'mensajeria_error': None,
        'fnz_error': None,  
        'novedades_error': None 
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

        date_cols = ["Fecha_Desembolso", "Fecha_Ultima_Novedad", "Fecha_Cuota_Atraso", ]
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
            
        # 1. Cargar Reporte_Llamadas (Opcional)
        try:
            df_llamadas = pd.read_excel(
                uploaded_file,
                sheet_name="Reporte_Llamadas",
                engine='openpyxl',
                usecols=cols_llamadas
            )
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
            alerts['llamadas_error'] = f"Nota: No se pudo cargar la hoja 'Reporte_Llamadas'. Causa: {e}"

        # 2. Cargar Reporte_Mensajes (Opcional)
        try:
            df_mensajeria = pd.read_excel(
                uploaded_file,
                sheet_name="Reporte_Mensajes",
                engine='openpyxl',
                usecols=cols_mensajeria
            )
            if "Fecha_Llamada" in df_mensajeria.columns: 
                df_mensajeria["Fecha_Llamada"] = pd.to_datetime(
                    df_mensajeria["Fecha_Llamada"], errors="coerce", dayfirst=True
                ).dt.date
            
            str_cols_mensajeria = [
               "Fecha_Mensaje", "Numero_Telefono", "Nombre_Saliente", "Estado", "Estado_Mensaje"
            ]
            for col in str_cols_mensajeria:
                if col in df_mensajeria.columns:
                    df_mensajeria[col] = df_mensajeria[col].astype(str).str.strip()
        except Exception as e:
            alerts['mensajeria_error'] = f"Nota: No se pudo cargar la hoja 'Reporte_Mensajes'. Causa: {e}"

        # 3. Cargar FNZ007
        try:
            #Mapeando las columnas conocidas de FNZ007
            mapa_columnas_fnz = {
                'ESTADO':'Estado',
                'ANALISTA':'Analista_Asociado',
                'FECHA':'Fecha',
                'REGIONAL':'Regional_Venta',
                'DESEMBOLSO':'Credito_Desembolsado',
                'CEDULA':'Cedula_Cliente',
                'FS1NACFEC':'Fecha_Nacimiento',
                'APELLIDOS':'Apellidos',
                'NOMBRES':'Nombres',
                'TELEFONO1':'Celular1',
                'MOVIL':'Celular2',
                'FS1EMAIL':'Correo',
                'CARGO':'Cargo',
                'DIRECCION':'Direccion',
                'CODCIUDAD':'Codigo_Ciudad',
                'CIUDAD':'Ciudad',
                'BARRIO':'Barrio',
                'VENNOMBRE':'Nombre_Vendedor',
                'CCONOMBRE':'Centro_Costo',
                'CUOTAS':'Total_Cuotas',
                'FS0NOTA':'Nota',
                'VALOR_TOTA':'Valor_Total',
                'INGRESOS':'Ingresos',
                'GASTOS':'Gastos'
            }
            
            cols_a_cargar = list(mapa_columnas_fnz.keys())
            # No definimos 'usecols' para que traiga todas las columnas disponibles en FNZ007
            df_fnz = pd.read_excel(
                uploaded_file,
                sheet_name="FNZ007",
                engine='openpyxl',
                usecols=cols_a_cargar
            )
            df_fnz.rename(columns=mapa_columnas_fnz, inplace=True) 
            if "Fecha_Nacimiento" in df_fnz.columns:
                 df_fnz["Fecha_Nacimiento"] = pd.to_datetime(df_fnz["Fecha_Nacimiento"]).dt.date
                            
        except Exception as e:
            # Si falla, simplemente se registra (opcional) y df_fnz sigue vacía
            alerts['fnz_error'] = f"Nota: No se pudo cargar la hoja 'FNZ007'. Causa: {e}"

        return df_cartera, df_novedades, df_llamadas, df_mensajeria, df_fnz, alerts

    except Exception as e:
        st.error(f"Error crítico al leer las hojas principales (Cartera o Novedades). Asegúrate de que existan. Error: {e}")
        return None, None, None, None, None, alerts