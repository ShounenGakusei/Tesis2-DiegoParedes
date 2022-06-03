import os
import time
import traceback
import GOES

import pyproj as pyproj
from pyresample import utils
from pyresample.geometry import SwathDefinition
from pyresample import bilinear

from netCDF4 import Dataset
import numpy as np

from Utils.ValidarParametros import converGoesDate


def reproject(CMI, LonCen, LatCen, LonCenCyl, LatCenCyl):
    Prj = pyproj.Proj('+proj=eqc +lat_ts=0 +lat_0=0 +lon_0=0 +x_0=0 +y_0=0 +a=6378.137 +b=6378.137 +units=km')
    AreaID = 'cyl'
    AreaName = 'cyl'
    ProjID = 'cyl'
    Proj4Args = '+proj=eqc +lat_ts=0 +lat_0=0 +lon_0=0 +x_0=0 +y_0=0 +a=6378.137 +b=6378.137 +units=km'

    ny, nx = LonCenCyl.shape
    SW = Prj(LonCenCyl.min(), LatCenCyl.min())
    NE = Prj(LonCenCyl.max(), LatCenCyl.max())
    area_extent = [SW[0], SW[1], NE[0], NE[1]]

    AreaDef = utils.get_area_def(AreaID, AreaName, ProjID, Proj4Args, nx, ny, area_extent)

    SwathDef = SwathDefinition(lons=LonCen, lats=LatCen)
    #CMICyl = resample_nearest(SwathDef, CMI, AreaDef, radius_of_influence=6000, fill_value=np.nan, epsilon=0, reduce_data=False)
    CMICyl = bilinear.resample_bilinear(CMI, SwathDef, AreaDef, radius=6000, fill_value=np.nan, reduce_data=False, segments=None, epsilon=0) # nprocs=1, neighbours=32

    return CMICyl

def saveCoordenadas(filename, LonCen, LatCen):
    try:
        f = Dataset(filename,'a', format='NETCDF4')
        tmpGroup = f.createGroup('coordenadas')
        tmpGroup.createDimension('longitude', LonCen.shape[1])
        tmpGroup.createDimension('latitude', LatCen.shape[0])

        lats_file = tmpGroup.createVariable('latitude', LatCen.dtype.type, ('latitude',))
        lons_file = tmpGroup.createVariable('longitude', LonCen.dtype.type, ('longitude',))

        lats_file[:] = LatCen[:,0]
        lons_file[:] = LonCen[0,:]
        f.close()
    except Exception:
        print('No se pudo agregar las coordendas')
        traceback.print_exc()
        f.close()


def saveNCFile(filename, i, c, CMI, LonsCen, LatsCen):
    try:
        f = Dataset(filename, 'a', format='NETCDF4')
        tmpGroup = f.createGroup(f'{c}-{i}')

        tmpGroup.createDimension('longitude', LonsCen.shape[1])
        tmpGroup.createDimension('latitude', LatsCen.shape[0])

        # lats_file = tmpGroup.createVariable('latitude', LatsCen.dtype.type, ('latitude',))
        # lons_file = tmpGroup.createVariable('longitude', LonsCen.dtype.type, ('longitude',))
        parameter01 = tmpGroup.createVariable('CMI', CMI.dtype.type, ('latitude', 'longitude'),
                                              zlib=True)  # , least_significant_digit=2)

        # lats_file[:] = LatsCen[:,0]
        # lons_file[:] = LonsCen[0,:]
        parameter01[:, :] = CMI

        f.close()

        return ''
    except Exception:
        traceback.print_exc()
        f.close()
        return f'Error: {c}-{i}'


# domain =  [-88.0,-63.0,-25.0,5.0] # [-90.0,-30.0,-60.0,15.0]
def downloadImageGOES(path_base, p):
    start_time = time.time()
    errors = []
    data = {}

    """
    Parametros para el procesamiento
    """
    domain = p['domain']  # [-83.5495, -66.4504, -20.2252, 1.3783]

    # this parameters are used to create a GLM navigation of 2D, then navigation is changed to 1 km
    pixresol = 2.0
    xmin, xmax = 80, 1030  # -83.54954954954955 -66.45045045045045
    ymin, ymax = 700, 1900  # -20.225225225225227 1.3783783783783794

    # here define the corners of pixels where will accumulate the lightnings

    lat_cor = 14.0 + np.arange(3665) * (-pixresol / 111.0)  # np.arange(14.0,-52.01,-pixresol/111.0)
    lon_cor = -85.0 + np.arange(2945) * (
                pixresol / 111.0)  # -84.0+np.arange(2897)*(pixresol/111.0) #-84.0+np.arange(2889)*(pixresol/111.0) #np.arange(-84.0,-31.98,pixresol/111.0)
    lat_cen = lat_cor[:-1] - (pixresol / 2.0) / 111.0
    lon_cen = lon_cor[:-1] + (pixresol / 2.0) / 111.0
    lon_cor, lat_cor = np.meshgrid(lon_cor, lat_cor)
    lon_cen, lat_cen = np.meshgrid(lon_cen, lat_cen)

    lon_cor, lat_cor = lon_cor[ymin:ymax + 1, xmin:xmax + 1], lat_cor[ymin:ymax + 1, xmin:xmax + 1]
    lon_cen, lat_cen = lon_cen[ymin:ymax, xmin:xmax], lat_cen[ymin:ymax, xmin:xmax]

    """
    Inicio
    """



    # Inicializamos variables de descarga
    filename = f'{path_base}/Imagenes/{p["fecha"]}.nc'
    try:
        os.remove(filename)
    except FileNotFoundError:
        pass
    except:
        errors.append('No se puede descargar: No se permite borrar archivo existente')
        return -1, errors

    f = Dataset(filename, 'w', format='NETCDF4')
    f.close()

    fechaIni = converGoesDate(p['fecha'], mm=-(10 * len(p['tiempos'])))
    fechaFin = converGoesDate(p['fecha'], mm=10)

    LonCen = None
    for c in p['canales']:
        filesT = GOES.download('goes16', 'ABI-L2-CMIPF',
                               DateTimeIni=fechaIni, DateTimeFin=fechaFin,
                               channel=[c], rename_fmt='%Y%m%d%H%M%S', path_out=f'{path_base}/Temp/')

        if len(filesT) < len(p['tiempos']):
            errors.append(f'No se pudo encontrar suficientes imagenes para el canal {c}')
            return -1, errors

        for i in range(len(filesT)):
            ds = GOES.open_dataset(filesT[len(filesT) - i - 1])

            # Primer archivo, se  guardara las coordenadas y se fijara el dominio (1200x950)
            if i == 0 and c == p['canales'][0] and p['save']:
                CMI, LonCen, LatCen = ds.image('CMI', lonlat='center', domain=domain)
                domain_in_pixels = CMI.pixels_limits
                mask = np.where(np.isnan(CMI.data) == True, True, False)
                print(' Se guardaran las cordenadas')
                saveCoordenadas(filename, lon_cen, lat_cen)

            else:
                CMI, _, _ = ds.image('CMI', lonlat='none', domain_in_pixels=domain_in_pixels, nan_mask=mask)

            # Se procesa la imagen
            CMICyl = reproject(CMI.data, LonCen.data, LatCen.data, lon_cen, lat_cen)
            data[f'{c}-{i}'] = CMICyl

            # Guardamos las imagenes
            errorSave = saveNCFile(filename, i, c, (CMICyl * 100).astype(np.int16), lon_cen, lat_cen)
            if errorSave:
                errors.append(errorSave)
                return -1, errors

    print("Time taken: %.2fs" % (time.time() - start_time))
    return filename, errors