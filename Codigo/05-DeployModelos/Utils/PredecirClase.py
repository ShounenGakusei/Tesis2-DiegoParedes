import traceback

import numpy as np
import os, shutil

from Utils.ObtenerImagen import getImages
from Utils.ObtenerModelo import crearModelo
from Utils.ValidarParametros import comprobarDatos

import tensorflow as tf


def evaluarDato(path_base, params, modelo):
    # Comprueba los parametros
    advertencias = {}
    errors = comprobarDatos(params)
    if not errors['valido']:
        print('Sucedio error al comprobar datos')
        return 0, errors

    # Borramos los archivos de la carpeta dlImages (temporal)
    folder = f'{path_base}/dlImages'
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('No se pudo borrar el % archivos. Razon: %s' % (file_path, e))

    # Obtenemos la matriz de la imagen procesada
    imagenMatriz, erroresImagen = getImages(path_base, params)

    # Revisamos errores de obtencion
    if erroresImagen:
        errors['imagen'] = erroresImagen
        errors['valido'] = False
        print('Error al leer las iamgenes')
        return 0, errors

    # TODO  Cmbiar shape fijo a parametros ...
    # Revisamos erroers de recorte
    if imagenMatriz.shape != (3,10,10,3):
        errors['imagen'] = [f'La imagen (canal-tiempo-largo-ancho) tiene la forma ({imagenMatriz.shape}) cuando se espera (6,24,24,3)']
        errors['valido'] = False
        print('Error al recortar las iamgenes')
        return 0, errors


    return imagenMatriz, errors #predicciones, nc, malo, conforme, errors


def usarModelos(imagenMatriz, dato, modelo, extras={}):
    with tf.device("cpu:0"):
        predicciones, nc, malo, conforme, errores = modelo.predecirValor(imagenMatriz, dato, extras=extras)


    return predicciones, nc, malo, conforme, errores