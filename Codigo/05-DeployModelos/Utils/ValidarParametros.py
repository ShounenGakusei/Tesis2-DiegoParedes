# Busca si existe las iamgenes sateliltes en la PC, yen caso este corrupto lo borra
from datetime import datetime, timedelta
import os

from netCDF4 import Dataset


def findImagesFiles(filename):
    try:
        file_size = os.path.getsize(filename)
        if file_size > 4000:
            return filename, ''
        else:
            print(f"Se encontro archivo corrupto de imagen, procedera a descargarse denuevo ...")
            test_ds = Dataset(filename, 'r', format='NETCDF4')
            test_ds.close()
            os.remove(filename)
            print('Archivo Corrupto encontrado...se volvera a descargar')
            return None, ''
    except FileNotFoundError:
        print('Archivo no descargado aun..se descargara')
        return None, ''


# Convierte la fecha a un formato para poder descargar las imagenes
# Si es reversa, convierte del formato para descargar a un formato basico
# ADEMAS, Comprueba que la fecha sea correcta
def converGoesDate(fecha, hh=0, mm=0, reversa=False):
    if reversa:
        return fecha[0:4] + '-' + fecha[4:6] + '-' + fecha[6:8] + '-' + fecha[8:10] + '-' + fecha[10:12]
    else:
        f = datetime.strptime(fecha, "%Y-%m-%d-%H-%M") + timedelta(hours=hh, minutes=mm)
        return f'{f.year:04}{f.month:02}{f.day:02}-{f.hour:02}{f.minute:02}00'


# Verifica que todos lso datos sean validos, devuelve la lsita de errores
def comprobarDatos(p):
    errors = {'valido': True, 'dato': [], 'coordLon': [], 'coordLat': [], 'fecha': [], 'imagen': [] , 'sizeMax' : [], 'umbral' : []}

    # Pruebas de dato
    if not p['dato']:
        errors['dato'].append('El dato no puede ser vacio')
        errors['valido'] = False
    try:
        p['dato'] = float(p['dato'])
        if p['dato'] < 0:
            errors['dato'].append('El dato debe ser positivo')
            errors['valido'] = False
    except:
        errors['dato'].append('El dato no se pudo transformar a numero real')
        errors['valido'] = False
        pass

    # Pruebas de Longitud
    if not p['coordLon']:
        errors['coordLon'].append('La longitud no puede ser nula')
        errors['valido'] = False
    try:
        p['coordLon'] = float(p['coordLon'])
        if (p['coordLon'] > 66.45) or (p['coordLon'] < -83.54):
            errors['coordLon'].append('La longitud debe estar entre 66.45 y -83.54 (Territorio Peruano)')
            errors['valido'] = False
    except:
        errors['coordLon'].append('No se pudo convertir la longitud a numero real')
        errors['valido'] = False
        pass
    # Pruebas de latitud
    if not p['coordLat']:
        errors['coordLat'].append('La latitud no puede ser nula')
        errors['valido'] = False
    try:
        p['coordLat'] = float(p['coordLat'])
        if (p['coordLat'] > 1.38) or (p['coordLat'] < -20.25):
            errors['coordLat'].append('La latitud debe estar entre 1.38 y -20.25 (Territorio Peruano)')
            errors['valido'] = False
    except:
        errors['coordLat'].append('No se pudo convertir la latitud a numero real')
        errors['valido'] = False

    # Pruebas de fecha
    if not p['fecha']:
        errors['fecha'].append('La fecha no puede ser vacio')
        errors['valido'] = False

    try:
        f = datetime.strptime(p['fecha'], "%Y-%m-%d-%H-%M")

        dMax = datetime.now() - timedelta(hours=1)
        dMin = datetime(2020, 1, 1, 0, 0)
        if f < dMin:
            errors['fecha'].append('La fecha debe ser mayor a dMin')
            errors['valido'] = False

        if f > dMax:
            errors['fecha'].append(f'La fecha debe ser menor a la fecha actual ({dMax})')
            errors['valido'] = False
    except:
        errors['fecha'].append('No se pudo convertir fecha a formato Year-month-day-hour')
        errors['valido'] = False

    # Pruebas de Umbral
    if not p['umbral']:
        errors['umbral'].append('El umbral no puede ser vacio')
        errors['valido'] = False
    try:
        p['umbral'] = float(p['umbral'])
        if (p['umbral'] > 1) or (p['umbral'] < 0):
            errors['umbral'].append('El umbral debe ser un valor entre 0 y 1')
            errors['valido'] = False
    except:
        errors['umbral'].append('El umbral no se pudo transformar a numero real')
        errors['valido'] = False
        pass

    # Pruebas de sizeMax
    if not p['sizeMax']:
        errors['sizeMax'].append('El tamaño maximo de memoria no puede ser nulo')
        errors['valido'] = False
    try:
        p['sizeMax'] = float(p['sizeMax'])
        if (p['sizeMax'] < 300):
            errors['sizeMax'].append('El tamaño maximo de memoria debe ser mayor a 100 MB')
            errors['valido'] = False
    except:
        errors['sizeMax'].append('El tamaño maximo no se pudo transformar a numero real')
        errors['valido'] = False
        pass

    return errors
