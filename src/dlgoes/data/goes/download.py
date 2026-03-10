import traceback
import numpy as np
import os
import time
from netCDF4 import Dataset
from dlgoes.utils.files import force_remove
from dlgoes.utils.logging import setup_logging
import logging
import GOES
from datetime import datetime, timedelta
import pyproj
from pyresample import utils
from pyresample.geometry import SwathDefinition
from pyresample import bilinear
import re
import gc
import os

logger_qc = logging.getLogger(__name__)
    
class GOESImageProcessor:
    def __init__(self, cfg , channels = [], times = []):
        
        logger_qc.debug("Iniciando GOES class")
        self.errors = []  # Lista para almacenar errores
        self.success = True  # Indicador de éxito
        self.config_params = cfg

        if channels:
            self.channels = channels
        else:
            self.channels = cfg.goes.channels
    
        if times:
            self.times = times
        else:
            self.times = cfg.goes.times


    def validate_images_goes(self, filename):
        logger_qc.debug(f'Validando archivo de imagen : {filename}')
        if not filename.is_file():
            logger_qc.info("Validacion Imagen (False): No existe el archivo")
            return False
        
        valido = True
        file_size = filename.stat().st_size

        creation_time = datetime.fromtimestamp(filename.stat().st_mtime)
        logger_qc.debug(f'Fecha de creacion del archivo {creation_time}')
        logger_qc.debug(f'Tamañ del archvo {file_size}')
        if (datetime.now() - creation_time) > timedelta(minutes=10):
            if file_size < self.config_params.goes.limits.min_image_size_bytes:
                logger_qc.info("Validacion Imagen (False): El archivo es menor a 20mb y ya paso 10min desde su creacion")
                valido = False
        if not valido:
            force_remove(filename)
        return valido

    def save_nc_file(self, filename, i, c, CMI, LonsCen, LatsCen):
        # Crear el archivo si no existe
        if not filename.is_file():
            with Dataset(filename, 'w', format='NETCDF4') as f:
                f.setncattr('file_description', 'Archivo generado por el procesamiento GOES')
                logger_qc.info(f"Archivo {filename} creado.")

        try:
            logger_qc.info(f"Guardando datos en {filename}, grupo {c}-{i}")
            
            with Dataset(filename, 'a', format='NETCDF4') as f:
                # Crear un grupo para el canal y tiempo
                tmpGroup = f.createGroup(f'{c}-{i}')

                # Dimensiones del grupo
                tmpGroup.createDimension('longitude', LonsCen.shape[1])
                tmpGroup.createDimension('latitude', LatsCen.shape[0])

                # Crear variable y asignar los datos
                parameter01 = tmpGroup.createVariable('CMI', CMI.dtype.type, ('latitude', 'longitude'), zlib=True)
                parameter01[:, :] = CMI

                # Agregar atributos al archivo
                creation_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.setncattr('creation_date', creation_date)
                logger_qc.info(f"Datos guardados exitosamente en el grupo {c}-{i}.")

        except Exception as e:
            # Registrar el error y asegurar que no quede el archivo en un estado inconsistente
            self.errors.append(f"Error en save_nc_file ({c}-{i}): {e}")
            self.success = False
            logger_qc.error(f"Error al guardar archivo NetCDF en {filename}: {e}")
            return True  # Indicar que hubo un error

        return False  # Todo se guardó correctamente


    def _reproject(self, CMI, LonCen, LatCen, LonCenCyl, LatCenCyl):
        try:
           

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

            CMICyl = bilinear.resample_bilinear(CMI, SwathDef, AreaDef, radius=self.config_params.goes.reprojection.radius, 
                                                fill_value=np.nan, reduce_data=False)

            # Liberar memoria innecesaria
            del LonCen, LatCen
            gc.collect()

            return CMICyl
        except Exception as e:
            print(str(e))
            return None
        
    def reproject(self, CMI, LonCen, LatCen, LonCenCyl, LatCenCyl):
        try:
            logger_qc.info("Reproyectando datos")
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

            CMICyl = bilinear.resample_bilinear(CMI, SwathDef, AreaDef, radius=6000, fill_value=np.nan, reduce_data=False)
            return CMICyl
        except Exception as e:
            self.errors.append(f"Error en reprojection: {e}")
            self.success = False
            logger_qc.error(f"Error al reproyectar: {e}")
            return None

    def conver_goes_date(self, fecha, hh=5, mm=0, reversa=False):
        if reversa:
            return fecha[0:4] + '-' + fecha[4:6] + '-' + fecha[6:8] + '-' + fecha[8:10] + '-' + fecha[10:12]
        else:
            f = datetime.strptime(fecha, "%Y-%m-%d-%H-%M") + timedelta(hours=hh, minutes=mm)
            return f'{f.year:04}{f.month:02}{f.day:02}-{f.hour:02}{f.minute:02}00'

    def save_coordinates(self, filename, LonCen, LatCen):
        try:
            logger_qc.info(f"Guardando coordenadas en {filename}")
            f = Dataset(filename, 'a', format='NETCDF4')
            tmpGroup = f.createGroup('coordenadas')
            tmpGroup.createDimension('longitude', LonCen.shape[1])
            tmpGroup.createDimension('latitude', LatCen.shape[0])

            lats_file = tmpGroup.createVariable('latitude', LatCen.dtype.type, ('latitude',))
            lons_file = tmpGroup.createVariable('longitude', LonCen.dtype.type, ('longitude',))

            lats_file[:] = LatCen[:, 0]
            lons_file[:] = LonCen[0, :]
            f.close()
        except Exception as e:
            self.errors.append(f"Error en save_coordinates: {e}")
            self.success = False
            logger_qc.error(f"No se pudo agregar las coordenadas: {e}")


    def clean_folder_if_exceeds_limit(self, folder_path,max_size, files_to_remove=1):
        """
        Limpia la carpeta si su tamaño total supera el límite especificado.
        
        Args:
            folder_path (str): Ruta de la carpeta a verificar.
            max_size (int): Tamaño máximo permitido en bytes.
            files_to_remove (int): Número de archivos más antiguos a eliminar si se excede el límite.
        """

        if max_size == -1:
            logger_qc.info(f"Parametro -1 en {folder_path.name}: NO SE BORRARÁ NADA")
            return 
        
        # Calcular el tamaño total de la carpeta
        total_size = 0
        files = []
        for filename in os.listdir(folder_path):
            file_path = folder_path / filename
            if file_path.is_file() and file_path.suffix == ".nc":
                stat = file_path.stat()
                files.append((file_path, stat.st_mtime))
                total_size += stat.st_size

        # Si el tamaño total excede el límite
        logger_qc.info(f"Espacio actual ocupado {len(files)} :  {total_size} de {max_size} en {folder_path}")

        if total_size > max_size:
            # Ordenar los archivos por fecha de modificación (antiguos primero)
            files.sort(key=lambda x: x[1])  # Ordenar por timestamp (getmtime)
            
            # Eliminar los archivos más antiguos
            for i in range(min(files_to_remove, len(files))):
                try:
                    force_remove(files[i][0])
                    #print(f"Archivo temporal eliminado por exceso de capacidad: {files[i][0]}")
                except Exception as e:
                    print(f"Error al eliminar el archivo temporal {files[i][0]}: {e}")


    def download_image_goes(self, fecha, download=True):
        logger_qc.debug(f'Iniciando meotdo download_image_goes')
        pattern = r'^\d{4}-\d{2}-\d{2}-\d{2}-\d{2}$'  # Formato: YYYY-MM-DD-HH-MM

        ## Caso de prueba
        if fecha in  ['2024-11-27-15-00','2024-11-26-15-00']:
            return self.config_params.paths.project_root /  self.config_params.goes.goes_test_images / f'{fecha}.nc'
        
        if not re.match(pattern, fecha):
            logger_qc.debug(f'No se ingreso el foromato adecuado de fecha: {fecha}')
            self.errors.append("Formato de fecha inválido. Use YYYY-MM-DD-HH-MM.")
            self.success = False
            return ''
            
        try:
            start_time = time.time()
            logger_qc.info(f"--------Iniciando descarga de imagen GOES para {fecha}")
            domain = self.config_params.goes.domain

            logger_qc.debug(f'Buscando arhcivo de imagen: {self.config_params.goes.goes_data}')
            filename = self.config_params.paths.project_root / self.config_params.goes.goes_data / f'{fecha}.nc'
            logger_qc.debug(f'Buscando arhcivo de imagen: {filename}')
            if self.validate_images_goes(filename):               
                return filename
            
            if not download:
                logger_qc.debug(f'Aun no se ha descargado la fecha: {fecha}')
                self.errors.append(f'Aun no se ha descargado la fecha: {fecha}')
                self.success = False
                return ''
            
            # Coordenadas iniciales
            pixresol = self.config_params.goes.reprojection.pixres_km
            xmin, xmax = self.config_params.goes.reprojection.xmin, self.config_params.goes.reprojection.xmax
            ymin, ymax = self.config_params.goes.reprojection.ymin, self.config_params.goes.reprojection.ymax

            lat_cor = 14.0 + np.arange(ymin, ymax + 1) * (-pixresol / 111.0)
            lon_cor = -85.0 + np.arange(xmin, xmax + 1) * (pixresol / 111.0)

            lat_cen = lat_cor[:-1] - (pixresol / 2.0) / 111.0
            lon_cen = lon_cor[:-1] + (pixresol / 2.0) / 111.0

            lon_cor, lat_cor = np.meshgrid(lon_cor, lat_cor)
            lon_cen, lat_cen = np.meshgrid(lon_cen, lat_cen)
       

            logger_qc.debug(f'Leyendo archivo dataset en : {filename}')
            
            logger_qc.debug(f'Convirtiendo fecha del goes')
            fecha_ini = self.conver_goes_date(fecha, mm=-(10 * len(self.times))) # TODO - len(p['tiempos'])
            fecha_fin = self.conver_goes_date(fecha, mm=10)

            temp_path = self.config_params.paths.project_root / self.config_params.goes.goes_data / 'temp'

            logger_qc.debug(f'Carpeta temporal de imagenes: {temp_path}')

            logger_qc.debug(f'Limpiando limites de carpetas: {temp_path} - {self.config_params.goes.goes_data}')
            self.clean_folder_if_exceeds_limit(temp_path,self.config_params.goes.limits.max_temp_folder_bytes, files_to_remove=len(self.times)*len(self.channels))
            self.clean_folder_if_exceeds_limit(self.config_params.paths.project_root / self.config_params.goes.goes_data,
                                               self.config_params.goes.limits.max_image_folder_bytes, files_to_remove=1)
            LonCen = None
            for c in self.channels:
                logger_qc.debug(f'buscando imagenes de GOES canal: {c}')
                filesT = GOES.download('goes16', 'ABI-L2-CMIPF',
                                       DateTimeIni=fecha_ini, DateTimeFin=fecha_fin,
                                       channel=[c], rename_fmt='%Y%m%d%H%M%S', path_out=temp_path.as_posix() + "/")

                if len(filesT) < len(self.times):
                    logger_qc.debug(f'No se encontro suficientes imagenes para el canal')
                    self.errors.append(f"No se encontraron suficientes imágenes para el canal {c}")
                    self.success = False
                    force_remove(filename)                    
                    return ''

                for i in range(len(filesT)):
                    logger_qc.debug(f'Procesando tiempo {i} en canal {c}')
                    ds = GOES.open_dataset(filesT[len(filesT) - i - 1])

                    logger_qc.debug(f'Verificando tiempo y canales correctos')
                    if i == 0 and c == self.channels[0] and self.config_params.goes.save_images:
                        CMI, LonCen, LatCen = ds.image('CMI', lonlat='center', domain=domain)
                        domain_in_pixels = CMI.pixels_limits
                        mask = np.where(np.isnan(CMI.data) == True, True, False)
                        logger_qc.debug(f'Procesando cordenadas {i}-{c}')
                        self.save_coordinates(filename, lon_cen, lat_cen)
                    else:
                        CMI, _, _ = ds.image('CMI', lonlat='none', domain_in_pixels=domain_in_pixels, nan_mask=mask)

                    logger_qc.debug(f'reproyectando!')
                    CMI = self.reproject(CMI.data, LonCen.data, LatCen.data, lon_cen, lat_cen)
                    logger_qc.debug(f'Gaurdando en archov NC')
                    error_save = self.save_nc_file(filename, i, c, (CMI * 100).astype(np.int16), lon_cen, lat_cen)
                    if error_save:
                        force_remove(filename)
                        
                        return ''

            logger_qc.info(f"Tiempo de procesamiento: {time.time() - start_time:.2f}s")
            return filename
        except Exception as e:
            traceback.print_exc()
            self.errors.append(f"Error en download_image_goes: {e}")
            self.success = False
            force_remove(filename)
            