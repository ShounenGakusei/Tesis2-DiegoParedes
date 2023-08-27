"""
from datetime import datetime

import pandas as pd

from Utils.ValidarParametros import comprobarDatos

class TestParametros():
    # Reporte
    reporte = {'Campo': [] , 'Valor': [], 'Esperado':[],'Resultado':[],'Aprobado': [], 'Mensaje': []}

    # Parametors iniciales
    good_dato = 0.4
    good_lat = -4.48047
    good_lon = -80.39788
    good_date = '2022-02-01-07-00'

    # Test aprobados / fallados
    passed = 0
    failed = 0

    def test_params(self, list_cases):
        print(f'Cantidad de tests : {len(list_cases)}')
        for i in list_cases.index:
            tipo = list_cases['Campo'][i]
            params = {
                'fecha': self.good_date if tipo != 'fecha' else list_cases['Valor'][i],
                'dato': self.good_dato if tipo != 'dato' else list_cases['Valor'][i],
                'coordLon': self.good_lon if tipo != 'coordLon' else list_cases['Valor'][i],
                'coordLat': self.good_lat if tipo != 'coordLat' else list_cases['Valor'][i]
            }
            result = comprobarDatos(params)
            self.reporte['Campo'].append(list_cases['Campo'][i])
            self.reporte['Valor'].append(list_cases['Valor'][i])
            self.reporte['Esperado'].append(list_cases['Esperado'][i])
            self.reporte['Resultado'].append(result['valido'])
            if result['valido'] == list_cases['Esperado'][i]:
                self.passed = self.passed + 1
                self.reporte['Aprobado'].append('o')
                self.reporte['Mensaje'].append(str(result[tipo]))
            else:
                self.failed = self.failed + 1
                self.reporte['Aprobado'].append('x')
                self.reporte['Mensaje'].append(str(result[tipo]))
        print('DONE')

    def save_reporte(self, path_base):
        tempDF = pd.DataFrame(self.reporte)
        cod = datetime.today().strftime("%Y%m%d")
        tempDF.to_csv(f'{path_base}/Tests/Reportes/UT_reporte_{cod}.csv', index = False)

    def unitTests(self,path_base):
        dfCases = pd.read_csv(f'{path_base}/Tests/UT_casos.csv')

        self.test_params(dfCases)
        self.save_reporte(path_base)
        return {'Fail': self.failed, 'pass': self.passed}
"""
a =5
