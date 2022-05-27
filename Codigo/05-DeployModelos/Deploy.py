from flask import Flask, request
from flask_restful import reqparse, Api, Resource

from Tests.unit_tests import TestParametros
from Utils.Model import Model
from Utils.PredecirClase import evaluarDato, usarModelos
import tensorflow as tf
app = Flask(__name__)
api = Api(app)


# argument parsing
#parser = reqparse.RequestParser()
#parser.add_argument('query')

path_base = app.root_path#f'C:/Users/Shounen/Desktop/Ciclo XI/Tesis 2/NewTesis/Codigo/05-DeployModelos'
params = {
    # Parametros principales
    'fecha': '2022-02-01-07-00',
    'dato': 0.4,
    'coordLon': -80.39788,
    'coordLat': -4.48047,

    # Parametros fijos
    'dirModelos' : f'{path_base}/Modelos/',
    'domain': [-88.0, -63.0, -25.0, 5.0],  # [-83.5495, -66.4504, -20.2252, 1.3783],
    'canales': ['07', '08', '13'],
    'tiempos': ['00', '50', '40', '30'],
    'margen': 30,
    'umbral' : 0.51,

    # Parametros auxiliares
    'dibujar': False,
    'canalDibujar': '13',
    'save': True,
    'hard_save': False
}
with tf.device("cpu:0"):
    modelosBase = Model(params)
    modelosBase.iniciarModelos()
blocked = False

@app.route("/unit_tests")
def unitTest():
    nuevoTest = TestParametros()
    resultados = nuevoTest.unitTests(path_base)
    return resultados



@app.route("/predecir")
def get():

    dato = request.args.get('dato', default='*', type=str)
    fecha = request.args.get('fecha', default='2022-02-01-07-00', type=str)
    coordlon = request.args.get('lon', default='-80.39788', type=str)
    coordLat = request.args.get('lat', default='-4.48047', type=str)

    print(f'Nueva peticion: {dato}')

    params['dato'] = dato
    params['fecha'] = fecha
    params['coordlon'] = coordlon
    params['coordLat'] = coordLat


    imagenMatriz, errors = evaluarDato(path_base, params, modelosBase)


    malos = conformes = nc = 0
    if errors['valido']:
        predicciones, nc, malos, conformes, errorModel = usarModelos(imagenMatriz, params['dato'], modelosBase)


        if errorModel:
            errors['modelo'] = errorModel
            print('Error al leer el modelo')


    if (malos + conformes + nc) == 0:
        pred_text = 'NC'
        mensaje = {}
        for k,v in errors.items():
            if v:
                mensaje[k] = v

    elif conformes > (malos+nc):
        pred_text = 'C'
        mensaje = f'Precision: {conformes/(nc+conformes+malos)}'#Umbral:{params["umbral"]} - NC:{nc} - C:{conformes} - M:{malos}'
    elif malos > (conformes+nc):
        pred_text = 'M'
        mensaje = f'Precision: {malos/(nc+conformes+malos)}'#f'Umbral:{params["umbral"]} - NC:{nc} - C:{conformes} - M:{malos}'
    else:
        pred_text = 'NC'
        mensaje = f'Umbral: {params["umbral"]}'#f'Umbral:{params["umbral"]} - NC:{nc} - C:{conformes} - M:{malos}'


    output = {'prediction': pred_text, 'mensaje': mensaje, 'parametros': {'Dato': params['dato'],
                                                                         'Fecha': params['fecha'],
                                                                         'Longitud': params['coordLon'],
                                                                         'Latitud': params['coordLat']}
              }


    return output

if __name__ == '__main__':
    app.run(debug=True, port=8080, threaded=False)