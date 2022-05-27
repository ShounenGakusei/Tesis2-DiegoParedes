import traceback

from flask import Flask, request
from flask_restful import Api

from Tests.unit_tests import TestParametros
from Utils.DefaultParams import getDefaultParams
from Utils.Model import Model
from Utils.PredecirClase import evaluarDato, usarModelos
import tensorflow as tf
import json
app = Flask(__name__)
api = Api(app)


path_base = app.root_path

try:
    with open(f'{path_base}/config.json') as json_file:
        params = json.load(json_file)
        print('Se leyó correctamente el archivo config.json')

    # Agregamos parametros adicionales
    params['dirModelos'] = f'{path_base}/Modelos/'
    params['fecha'] = '2022-02-01-07-00'
    params['dato'] =  0.4
    params['coordLon'] = -80.39788
    params['coordLat'] = -4.48047
    params['canales'] = ['07', '08', '13']
    params['tiempos'] =  ['00', '50', '40', '30']
    params['margen'] = 30
    params['dibujar'] = False
    params['canalDibujar'] = '13'

except Exception:
    traceback.print_exc()
    print('No se pudo leer el archivo de config, se procedera a cargar config predeterminada...')
    params = getDefaultParams(path_base)

print(params)
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