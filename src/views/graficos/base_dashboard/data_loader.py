import streamlit as st
import pandas as pd
import os

# Carpeta local en tu proyecto de escritorio
DATA_DIR = "data_bin"

def get_local_path(name):
    return os.path.join(DATA_DIR, f"{name}.parquet")

def save_to_disk(df_cartera, df_novedades, df_llamadas, df_mensajeria, df_fnz):
    """Guarda los DataFrames en formato Parquet (binario rápido)"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    data_map = {
        "cartera": df_cartera,
        "novedades": df_novedades,
        "llamadas": df_llamadas,
        "mensajeria": df_mensajeria,
        "fnz": df_fnz
    }
    
    for name, df in data_map.items():
        if df is not None and not df.empty:
            df.to_parquet(get_local_path(name), index=False, engine='pyarrow')

@st.cache_data(show_spinner="Leyendo datos desde disco...")
def load_from_local_disk():
    """Carga los datos previamente procesados del disco duro"""
    try:
        if not os.path.exists(get_local_path("cartera")):
            return None, None, None, None, None
            
        df_cartera = pd.read_parquet(get_local_path("cartera"))
        df_novedades = pd.read_parquet(get_local_path("novedades"))
        
        # Cargas opcionales con validación de existencia
        df_llamadas = pd.read_parquet(get_local_path("llamadas")) if os.path.exists(get_local_path("llamadas")) else pd.DataFrame()
        df_mensajeria = pd.read_parquet(get_local_path("mensajeria")) if os.path.exists(get_local_path("mensajeria")) else pd.DataFrame()
        df_fnz = pd.read_parquet(get_local_path("fnz")) if os.path.exists(get_local_path("fnz")) else pd.DataFrame()
        
        return df_cartera, df_novedades, df_llamadas, df_mensajeria, df_fnz
    except Exception as e:
        st.warning(f"No se pudieron cargar datos previos: {e}")
        return None, None, None, None, None

def load_and_process_data(uploaded_file):
    """
    PROCESAMIENTO COMPLETO CON BLINDAJE ANTI-ERRORES.
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

    alerts = {'llamadas_error': None, 'mensajeria_error': None, 'fnz_error': None, 'novedades_error': None}

    # Inicialización
    df_llamadas = pd.DataFrame()
    df_mensajeria = pd.DataFrame()
    df_fnz = pd.DataFrame()

    try: 
        # 1. CARGA PRINCIPAL
        df_cartera = pd.read_excel(uploaded_file, sheet_name="Analisis_de_Cartera", engine='openpyxl', usecols=cols_cartera)
        df_novedades = pd.read_excel(uploaded_file, sheet_name="Detalle_Novedades", engine='openpyxl', usecols=cols_novedades)

        # 2. BLINDAJE DE FECHAS (EXCLUIMOS Fecha_Cuota_Vigente PARA SALVAR "VIGENCIA EXPIRADA")
        cols_fechas = [
            "Fecha_Desembolso", "Fecha_Facturada", 
            "Fecha_Cuota_Atraso", "Primera_Cuota_Mora", "Fecha_Ultimo_Pago_Inicial", 
            "Fecha_Ultima_Novedad", "Fecha_Ultimo_pago"
        ]
        for col in cols_fechas:
            if col in df_cartera.columns:
                df_cartera[col] = pd.to_datetime(df_cartera[col], errors="coerce").dt.date
                
        for col in ["Fecha_Novedad", "Fecha_Compromiso"]:
            if col in df_novedades.columns:
                df_novedades[col] = pd.to_datetime(df_novedades[col], errors="coerce").dt.date

        # 3. LIMPIEZA DE STRINGS Y CÉDULAS
        str_cols = ["Empresa", "Regional_Venta", "Nombre_Ciudad", "Nombre_Vendedor", "Franja_Meta", "Rodamiento", "Gestor", "Regional_Cobro", "Zona_Cobro", "Zona"]
        for col in str_cols:
            if col in df_cartera.columns:
                df_cartera[col] = df_cartera[col].astype(str).str.strip()

        if "Cantidad_Novedades" in df_cartera.columns:
            df_cartera['Cantidad_Novedades'] = pd.to_numeric(df_cartera['Cantidad_Novedades'], errors='coerce').fillna(0)

        df_cartera['Cedula_Cliente'] = df_cartera['Cedula_Cliente'].astype(str).str.strip()
        df_novedades['Cedula_Cliente'] = df_novedades['Cedula_Cliente'].astype(str).str.strip()
        
        # 4. CARGAS OPCIONALES
        try:
            df_llamadas = pd.read_excel(uploaded_file, sheet_name="Reporte_Llamadas", engine='openpyxl', usecols=cols_llamadas)
            if "Fecha_Llamada" in df_llamadas.columns:
                df_llamadas["Fecha_Llamada"] = pd.to_datetime(df_llamadas["Fecha_Llamada"], errors="coerce")
            
            for col in ["Extension_Llamada", "Destino_Llamada", "Estado_Llamada", "Codigo_Llamada", "Grabacion_Llamada", "Call_Center", "Nombre_Call"]:
                if col in df_llamadas.columns:
                    df_llamadas[col] = df_llamadas[col].astype(str).str.strip()
        except Exception as e:
            alerts['llamadas_error'] = f"Nota: No se pudo cargar la hoja 'Reporte_Llamadas'. Causa: {e}"

        try:
            df_mensajeria = pd.read_excel(uploaded_file, sheet_name="Reporte_Mensajes", engine='openpyxl', usecols=cols_mensajeria)
            if "Fecha_Llamada" in df_mensajeria.columns: 
                df_mensajeria["Fecha_Llamada"] = pd.to_datetime(df_mensajeria["Fecha_Llamada"], errors="coerce", dayfirst=True).dt.date
            
            for col in ["Fecha_Mensaje", "Numero_Telefono", "Nombre_Saliente", "Estado", "Estado_Mensaje"]:
                if col in df_mensajeria.columns:
                    df_mensajeria[col] = df_mensajeria[col].astype(str).str.strip()
        except Exception as e:
            alerts['mensajeria_error'] = f"Nota: No se pudo cargar la hoja 'Reporte_Mensajes'. Causa: {e}"

        try:
            mapa_columnas_fnz = {
                'ESTADO':'Estado', 'ANALISTA':'Analista_Asociado', 'FECHA':'Fecha',
                'REGIONAL':'Regional_Venta', 'DESEMBOLSO':'Credito_Desembolsado',
                'CEDULA':'Cedula_Cliente', 'FS1NACFEC':'Fecha_Nacimiento',
                'APELLIDOS':'Apellidos', 'NOMBRES':'Nombres', 'TELEFONO1':'Celular1',
                'MOVIL':'Celular2', 'FS1EMAIL':'Correo', 'CARGO':'Cargo',
                'DIRECCION':'Direccion', 'CODCIUDAD':'Codigo_Ciudad', 'CIUDAD':'Ciudad',
                'BARRIO':'Barrio', 'VENNOMBRE':'Nombre_Vendedor', 'CCONOMBRE':'Centro_Costo',
                'CUOTAS':'Total_Cuotas', 'FS0NOTA':'Nota', 'VALOR_TOTA':'Valor_Total',
                'INGRESOS':'Ingresos', 'GASTOS':'Gastos'
            }
            cols_a_cargar = list(mapa_columnas_fnz.keys())
            
            df_fnz = pd.read_excel(uploaded_file, sheet_name="FNZ007", engine='openpyxl', usecols=cols_a_cargar)
            df_fnz.rename(columns=mapa_columnas_fnz, inplace=True) 
            
            if "Fecha_Nacimiento" in df_fnz.columns:
                 df_fnz["Fecha_Nacimiento"] = pd.to_datetime(df_fnz["Fecha_Nacimiento"], errors="coerce").dt.date
        except Exception as e:
            alerts['fnz_error'] = f"Nota: No se pudo cargar la hoja 'FNZ007'. Causa: {e}"

        # 5. BLINDAJE DE TIPOS PARA PARQUET
        # A. Identificadores, Teléfonos y Textos Mixtos (Añadimos Valor y Fecha Cuota Vigente)
        cols_a_texto = [
            'Telefono_Call_Center', 'Telefono_Cobrador', 'Celular_Jefe_Ventas', 
            'Telefono_Codeudor1', 'Telefono_Codeudor2', 'Celular_Vendedor',
            'Cedula_Cliente', 'Credito', 'Celular', 'Codigo_Vendedor', 
            'Cedula_Vendedor', 'Codigo_Centro_Costos', 'Factura_Venta',
            'Fecha_Cuota_Vigente', 'Valor_Cuota_Vigente' # <--- SE SALVAN LOS TEXTOS AQUÍ
        ]
        for col in cols_a_texto:
            if col in df_cartera.columns:
                df_cartera[col] = df_cartera[col].astype(str).replace(['None', 'nan', 'NaN', 'nan.0'], '').str.replace(r'\.0$', '', regex=True)

        # B. Dinero y Cantidades (Quitamos Valor_Cuota_Vigente de aquí)
        cols_a_numero = [
            'Saldo_Interes_Corriente', 'Saldo_Capital', 'Saldo_Avales', 
            'Valor_Desembolso', 'Total_Cuotas', 'Valor_Cuota', 
            'Dias_Atraso', 'Meta_Intereses', 'Meta_General', 'Meta_Saldo', 
            'Meta_%', 'Meta_$', 'Meta_T.R_%', 'Meta_T.R_$', 
            'Cuotas_Pagadas', 'Cuota_Vigente', 
            'Valor_Cuota_Atraso', 'Valor_Vencido', 'Cantidad_Novedades', 
            'Dias_Atraso_Final', 'Recaudo_Anticipado', 'Recaudo_Meta', 
            'Total_Recaudo', 'Total_Recaudo_Sin_Anti'
        ]
        for col in cols_a_numero:
            if col in df_cartera.columns:
                df_cartera[col] = pd.to_numeric(df_cartera[col], errors='coerce').fillna(0)

        # C. Llamadas y Mensajería (Signo +)
        if not df_llamadas.empty:
            for col in ['Destino_Llamada', 'Extension_Llamada', 'Codigo_Llamada']:
                if col in df_llamadas.columns:
                    df_llamadas[col] = df_llamadas[col].astype(str).replace(['None', 'nan', 'NaN'], '')
                    
        if not df_mensajeria.empty:
            if 'Numero_Telefono' in df_mensajeria.columns:
                df_mensajeria['Numero_Telefono'] = df_mensajeria['Numero_Telefono'].astype(str).replace(['None', 'nan', 'NaN'], '')

        # D. Nombre de Call Center
        if 'Nombre_Call_Center' in df_cartera.columns:
            df_cartera['Nombre_Call_Center'] = df_cartera['Nombre_Call_Center'].fillna('SIN CALL').astype(str)

        # 6. GUARDADO Y RETORNO
        save_to_disk(df_cartera, df_novedades, df_llamadas, df_mensajeria, df_fnz)
        st.cache_data.clear()
        
        return df_cartera, df_novedades, df_llamadas, df_mensajeria, df_fnz, alerts

    except Exception as e:
        st.error(f"Error crítico en el proceso principal: {e}")
        return None, None, None, None, None, alerts