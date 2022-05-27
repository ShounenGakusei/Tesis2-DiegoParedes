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

    # Borramos los archivos de la carpeta Temp (temporal)
    folder = f'{path_base}/Temp'
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

    if erroresImagen:
        errors['imagen'] = erroresImagen
        print('Error al leer las iamgenes')
        return 0, errors


    return imagenMatriz, errors #predicciones, nc, malo, conforme, errors


def usarModelos(imagenMatriz, dato, modelo):
    """
    dirModelos = params['dirModelos']

    errors = []
    predicciones = []
    totalModelos = 0

    modelos_file = [f'{dirModelos}{e}' for e in os.listdir(dirModelos)]
    modelos_file = [e for e in modelos_file if '.hdf5' in e]
    if len(modelos_file) == 0:
        errors.append('No se encontraron modelos')
        return 0,0, errors
    modelo = crearModelo(params)
    for mWeigts in modelos_file:
        try:
            modelo.load_weights(mWeigts)
            config = modelo.get_config()

            inputsLayers = []
            for layer in config['layers']:
                if layer['class_name'] == 'InputLayer':
                    inputsLayers.append(layer['name'])

            with tf.device("cpu:0"):
                prediction = modelo.predict({inputsLayers[0]: np.full((1, imagenMatriz.shape[0], imagenMatriz.shape[1],
                                                                          imagenMatriz.shape[2], imagenMatriz.shape[3]),
                                                                         imagenMatriz),
                                             inputsLayers[1]: np.full((1,), dato)})

            predicciones.append(prediction[0,0])
            totalModelos = totalModelos + 1
            confianza = 0

        except Exception:
            traceback.print_exc()
            errors.append(f'Error al predecir con el modelo {modelo}')
            pass

    conforme = 0
    for p in predicciones:
        if p > 0.5:
            conforme = conforme + 1
    """
    with tf.device("cpu:0"):
        predicciones, nc, malo, conforme, errores = modelo.predecirValor(imagenMatriz, dato)


    return predicciones, nc, malo, conforme, errores