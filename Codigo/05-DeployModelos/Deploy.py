import time
import traceback

from flask import Flask, request, render_template, jsonify
# from flask_restful import Api

# from Tests.unit_tests import TestParametros
from Utils.DefaultParams import getDefaultParams
from Utils.GestinarLogs import create_get_actual_log_dir, write_on_file, find_log_file
from Utils.Model import Model
from Utils.ObtenerAuxiliares import getElevation, getAuxiliarParams
from Utils.ObtenerImagen import get_dir_size, deleteFilesDir
from Utils.PredecirClase import evaluarDato, usarModelos
from Utils.ValidarParametros import comprobarDatos
import tensorflow as tf
import json
import numpy as np

import plotly.express as px
from skimage import io

app = Flask(__name__)
# api = Api(app)


path_base = app.root_path

try:
    with open(f'{path_base}/config.json') as json_file:
        params = json.load(json_file)
        print('Se leyó correctamente el archivo config.json')

    # Agregamos parametros adicionales
    params['dirModelos'] = f'{path_base}/Modelos/'
    params['fecha'] = '2022-02-01-07-00'
    params['dato'] = 0.4
    # params['coordLon'] = -80.39788
    # params['coordLat'] = -4.48047
    params['canales'] = ['07', '08', '13']
    params['tiempos'] = ['00', '30', '10']  # ['00', '50', '40', '30', '20', '10']
    params['margen'] = 10  # 24
    params['dibujar'] = False
    params['canalDibujar'] = '13'
    # params['sizeMax'] = 300 # en MB
    params["hard_save"] = False

except Exception:
    traceback.print_exc()
    print('No se pudo leer el archivo de config, se procedera a cargar config predeterminada...')
    params = getDefaultParams(path_base)

# print(params)
with tf.device("cpu:0"):
    modelosBase = Model(params)
    modelosBase.iniciarModelos()
blocked = False

"""
@app.route("/unit_tests")
def unitTest():
    nuevoTest = TestParametros()
    resultados = nuevoTest.unitTests(path_base)
    return resultados
"""


def predecirQCPrecipitation(params_prediction):
    params_prediction['ID'] = int(time.time())

    log_file = create_get_actual_log_dir(path_base)
    write_on_file(log_file, f'({params_prediction["ID"]}) Iniciando nueva prediccion ...')
    write_on_file(log_file, f'({params_prediction["ID"]}) Params:  {str(params_prediction)}')

    deleteFilesDir(path=f'{path_base}/dlImages/')
    # Verificamos el tamaño de la carpeta
    sizeDir = get_dir_size(path=f'{path_base}/Imagenes/')
    print(f'Tamaño en dir Imagenes: {sizeDir}')
    if sizeDir > (float(params_prediction['sizeMax']) * 1024 * 1024):
        print('Procediendo a vaciar dir Imagenes...')
        deleteFilesDir(path=f'{path_base}/Imagenes/')

    imagenMatriz, errors = evaluarDato(path_base, params_prediction, modelosBase)

    extras = {}
    # extras['alt'] = getElevation(path_base,params['coordlon'],params['coordLat'], errors)
    axuiliarValid = getAuxiliarParams(path_base, float(params_prediction['coordLon']),
                                      float(params_prediction['coordLat']), extras, errors)
    extras['umbral'] = params_prediction['umbral']

    malos = conformes = nc = 0
    predicciones = [0]

    if errors['valido'] and axuiliarValid:
        predicciones, nc, malos, conformes, errorModel = usarModelos(imagenMatriz, params_prediction['dato'],
                                                                     modelosBase,
                                                                     extras=extras)

        if errorModel:
            errors['modelo'] = errorModel
            errors['valido'] = False
            print('Error al leer el modelo')

    errores_output = {}
    mensaje = ''

    if (malos + conformes + nc) == 0:
        pred_text = 'NC'
        for k, v in errors.items():
            if v:
                errores_output[k] = v

    elif conformes != 0:
        pred_text = 'C'
        mensaje = f'Precision: {predicciones[0] * 100:.3f}%'  # {conformes/(nc+conformes+malos)}'#Umbral:{params["umbral"]} - NC:{nc} - C:{conformes} - M:{malos}'
    elif malos > (conformes + nc):
        pred_text = 'M'
        mensaje = f'Precision: {(1 - predicciones[0]) * 100:.3f}%'  # {malos/(nc+conformes+malos)}'#f'Umbral:{params["umbral"]} - NC:{nc} - C:{conformes} - M:{malos}'
    else:
        pred_text = 'NC'
        mensaje = f'Precision: {(predicciones[0]) * 100:.3f}% - Umbral: {params_prediction["umbral"]}'  # f'Umbral:{params["umbral"]} - NC:{nc} - C:{conformes} - M:{malos}'

    output = {'prediction': pred_text, 'errores': errores_output, 'parametros': {'Dato': params_prediction['dato'],
                                                                                 'Fecha': params_prediction['fecha'],
                                                                                 'Longitud': params_prediction[
                                                                                     'coordLon'],
                                                                                 'Latitud': params_prediction[
                                                                                     'coordLat'],
                                                                                 'altitud': extras['alt'],
                                                                                 'per90': extras['umb1']},
              'mensaje': mensaje, 'valido': errors['valido'], 'confianza': round(predicciones[0] * 100, 2)
              }

    if not errors['valido']:
        write_on_file(log_file, f'({params_prediction["ID"]})  Errores: {str(errors)}')

    write_on_file(log_file, f'({params_prediction["ID"]})  Prediccion finalizada con exito')
    return output, imagenMatriz


@app.route("/")
def getHome():
    return render_template('index.html', params=params)


@app.route("/downloadImages/<period>")
def getPeriodImagen(period):
    logs = {}
    global params
    p = params.copy()
    p['dato'] = '1.0'
    p['coordLon'] = '-80.39788'
    p['coordLat'] = '-4.48047'
    p['umbral'] = '0.51'
    p['sizeMax'] = '10000'

    for j in range(13,30,1):
        for i in range(24):
            p['fecha'] = f'{period}-{j:02d}-{i:02d}-00'
            output, _ = predecirQCPrecipitation(p)
            logs[p['fecha']] = output
    return logs


@app.route("/logs")
def getLogs():
    file_name = find_log_file(path_base, '20230502')
    if file_name:
        with open(file_name) as f:
            lines = f.readlines()
    else:
        lines = []

    return render_template('view_logs.html', lines=lines)


@app.route('/validar-UI-data', methods=['POST'])
def validarDatosUI():
    data = request.get_json()

    err = {'valido': True}
    err['dato'] = data['dato']
    err['fecha'] = data['fecha'] + '-00'
    err['coordLon'] = data['longitud']
    err['coordLat'] = data['latitud']

    err['umbral'] = data['umbral']
    err['sizeMax'] = data['sizeMax']

    err = comprobarDatos(err)
    if err['valido']:
        return jsonify({'success': True, 'prediccion': 85.5})
    else:
        return jsonify({'success': False, 'errors': err})


@app.route('/predecir-UI-data')
def predecirDatosUI():
    global params
    p = params.copy()

    p['dato'] = request.args.get('dato', type=str)
    p['fecha'] = request.args.get('fecha', type=str) + '-00'
    p['coordLon'] = request.args.get('lon', type=str)
    p['coordLat'] = request.args.get('lat', type=str)

    p['umbral'] = request.args.get('umbral', type=str)
    p['sizeMax'] = request.args.get('sizeMax', type=str)

    output, imagenArr = predecirQCPrecipitation(p)

    plot_div = None

    if output['valido']:
        if type(imagenArr) == np.ndarray:
            imagenArr = np.transpose(imagenArr, (0, 3, 1, 2))

        fig = px.imshow(imagenArr, animation_frame=0, facet_col=1, binary_string=True, labels={'facet_col': 'CANAL'})
        # fig.update_layout(title='Imagenes satelitales (C13 - C07 - C08)', height=600)

        plot_div = fig.to_html(full_html=False)

    colores = {'NC': 'grey', 'C': 'green', 'M': 'yellow'}
    if output['valido']:
        output['color'] = colores[output['prediction']]
    return render_template('prediccion-resumen.html', plot_div=plot_div, output=output)


@app.route("/predecir")
def get():
    dato = request.args.get('dato', default='*', type=str)
    fecha = request.args.get('fecha', default='2022-02-01-07', type=str)
    coordlon = request.args.get('lon', default='-80.39788', type=str)
    coordLat = request.args.get('lat', default='-4.48047', type=str)

    umbral = request.args.get('umbral', default='0.51', type=str)
    sizeMax = request.args.get('sizeMax', default='300', type=str)

    if len(fecha) == 13:
        fecha = fecha + '-00'

    print(f'Nueva peticion: {dato}', coordlon, coordLat)

    global params
    p = params.copy()
    p['dato'] = dato
    p['fecha'] = fecha
    p['coordLon'] = coordlon
    p['coordLat'] = coordLat

    p['umbral'] = umbral
    p['sizeMax'] = sizeMax
    print('bef', p)

    output, _ = predecirQCPrecipitation(p)

    return output


if __name__ == '__main__':
    app.run(debug=False, port=params['port'], threaded=False, host='0.0.0.0')
