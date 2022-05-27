import os
import traceback

import numpy as np
import tensorflow as tf

from Utils.ObtenerModelo import crearModelo


class Model():
    modelos = []
    params = {}
    errors = []
    valido = True
    def __init__(self, params):
        self.params = params

    def iniciarModelos(self):
        # Reseteamos las variables
        self.modelos = []
        self.inputLayers = []
        self.errors = []
        self.valido = True

        modelos_file = [f'{self.params["dirModelos"]}{e}' for e in os.listdir(self.params["dirModelos"])]
        modelos_file = [e for e in modelos_file if '.hdf5' in e]
        if len(modelos_file) == 0:
            self.errors.append('No se encontraron los modelos')
            self.valido = False

        print(f'Cantidad de modelos leidos: {len(modelos_file)}')


        init = True
        for mWeigts in modelos_file:
            try:
                modelo = crearModelo(self.params)
                modelo.load_weights(mWeigts)
                self.modelos.append(modelo)

            except:
                self.errors.append(f'No se pudo agregar el modelo {mWeigts}')
                pass

            if len(self.modelos) == 0:
                self.errors.append(f'No se logro agregar ningun modelo')
                self.valido = False

    def predecirValor(self, imagen, dato):
        errores = []
        predicciones = []

        conforme = 0
        malo = 0
        nc = 0

        # Verificamos si se inicio correctamente los modelos
        if not self.valido:
            # Si no es asi, intentamos incializar nuevamente
            self.iniciarModelos()

        # En caso no se pueda inicializar, se retorna error
        if not self.valido:
            return [0],0,0,0, self.errors


        for modelo in self.modelos:
            inputLayers = []
            config = modelo.get_config()
            for layer in config['layers']:
                if layer['class_name'] == 'InputLayer':
                    inputLayers.append(layer['name'])
            try:
                with tf.device("cpu:0"):
                    prediction = modelo.predict({inputLayers[0]: np.full((1, imagen.shape[0], imagen.shape[1],
                                                                              imagen.shape[2], imagen.shape[3]),
                                                                             imagen),
                                                 inputLayers[1]: np.full((1,), dato)}, verbose=0)
                    predicciones.append(prediction[0,0])

            except Exception:
                traceback.print_exc()
                pass

        if len(predicciones) == 0:
            errores.append(f'Error al predecir con el modelo')

        for p in predicciones:
            if p > self.params['umbral']:
                conforme = conforme + 1
            elif p < (1-self.params['umbral']):
                malo = malo + 1
            else:
                nc = nc +1

        return predicciones, nc, malo, conforme, errores
