# Busca el valor X en el array, devuelve su posicion
import os
import traceback
from netCDF4 import Dataset
import numpy as np

from Utils.DescargarImagen import downloadImageGOES
from Utils.GraficarImagen import dibujarMapa
from Utils.ValidarParametros import findImagesFiles


def getPosMap(x, array):
    pos = -1
    for i in range(len(array)):
        if abs(array[i] - x) <= 0.01:
            pos = i

    return pos


def findStationCoords(lons, lats, cordX, cordY):
    x = getPosMap(cordX, lons)
    y = getPosMap(cordY, lats)
    return x, y


# Con el nombre del archivo, regresa las las imagenes necesarias pero unidas
# Si en parametros se indica dibujar, se graficara el mapa y el punto a evaluar
def mergeImagesFile(fileName, p):
    data = []
    errors = []
    try:
        ds = Dataset(fileName)
        coord = ds.groups['coordenadas']
        lats = coord['latitude'][:].data
        lons = coord['longitude'][:].data

        x, y = findStationCoords(lons, lats, p['coordLon'], p['coordLat'])

        margen = int(p['margen'] / 2)
        for i in range(len(p['tiempos'])):
            canalImages = []
            for c in p['canales']:
                cmis = ds.groups[f'{c}-{i}']
                cmi = cmis.variables['CMI'][:].data.astype(np.float32) / 100.0

                if p['dibujar'] and p['canalDibujar'] == c and i == 0:
                    try:
                        dibujarMapa(lons, lats, cmi, mersh=0, point=[p['coordLon'], p['coordLat']])
                    except:
                        errors.append('No se pudo dibujar la imagen')
                        pass

                cropedImg = cmi[y - margen:y + margen, x - margen:x + margen]
                canalImages.append(cropedImg)

            data.append(np.dstack(canalImages))

        data = np.stack(data, axis=0)

        ds.close()


    except Exception:
        ds.close()
        traceback.print_exc()
        return [0], errors.append(f'No se pudo unir las imagenes: Tiempo: {i}- Canal: {c}')

    return data, errors


# Busca las imagenes, las descarga y las une
def getImages(path_base, params):
    fileName = f'{path_base}/Imagenes/{params["fecha"]}.nc'
    downLoad = False
    errors = []

    # Se borrara el archivo de imagenes, y se descargara nuevamente
    if params['hard_save']:
        try:
            os.remove(fileName)
            print('Se borro el archivo de imagen encontrado correctamente')
        except FileNotFoundError:
            pass
        except Exception:
            traceback.print_exc()
            errors.append('Error al intentar borrar el archivo de imagenes')
            return -1, errors

        downLoad =  True
        fileName, errorDownload = downloadImageGOES(path_base, params)
        if errorDownload:
            errors.append(errorDownload)
            return -1, errors

    # Se verificara si existe el archivo, caso contrario se borrara
    else:
        fileName, errorFindFile = findImagesFiles(fileName)
        # En caso no lo encuentre, o este corrupto, se descargara nuevamente
        if errorFindFile:
            errors.append(errorFindFile)

            downLoad = True
            fileName, errorDownload = downloadImageGOES(path_base, params)
            if errorDownload:
                errors.append(errorDownload)
                return -1, errors


    # Recortamos las imagenes y las combinamos
    if not errors:
        mergedImages, errorMerge = mergeImagesFile(fileName, params)
        if not errorMerge:
            return mergedImages, errors
        # Si no se ha ocurrido error y no se ha intentado descargar las iamgenes, se intentara descargarlos
        elif not downLoad:
            fileName, errorDownload = downloadImageGOES(path_base, params)
            if errorDownload:
                errors.append(errorDownload)
                return -1, errors
        else:
            return -1, errors


    else:
        return -1,errors