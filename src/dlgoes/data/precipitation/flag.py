"""
Clasificacion V2
 - NC
 - ND
 - M01
 - D01
 - D02
 - C01 
"""


# Return the new flag based on the thresholds and the value of precipitation
import pandas as pd


def simulate_qc_flags(row, umbrales, max_value=401):
    dato = row['PRECIPITACION']
    
    if pd.isna(dato):
        return 'ND'
    
    # Hard filters
    elif dato<0 or dato>=max_value:
        return 'M01'
    
    codigo = str(row['CODE'])
    mes =  int(row['FECHA'].split('/')[1]) -1
    hora = int(row['HORA'].split(':')[0])
    
    if not codigo in list(umbrales.keys()):
        val1 = -1
        val2 = -1
    else:
        val1 = umbrales[codigo][mes][hora][0]
        val2 = umbrales[codigo][mes][hora][1]
    
    if (val1==-1) and (val2==-1):
        return 'NC'
    if dato > val2:
        return 'D02'
    if dato > val1:
        return 'D01'       
    return 'C01'
    