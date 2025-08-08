configuracion = {
    "CV0018":{
        "sheet_name": "Page 001",
        "usecols":["SEDE", "CEDULA_ASE","ASESOR","FORMAPAGO","VTAS_ANT_I"],
        "rename_map":{
            "SEDE":"Regional",
            "CEDULA_ASE":"Cedula_Asesor",
            "ASESOR":"Nombre_Asesor",
            "FORMAPAGO":"Forma_Pago",
            "VTAS_ANT_I":"Ventas_Antes_Iva"
        }
    },
    "ASESORES":{
        "usecols":["CC ASESOR","TIPO ASESOR"],
        "rename_map":{ 
            "CC ASESOR":"Cedula_Asesor",
            "TIPO ASESOR":"Tipo_Asesor"
        }
    }
}