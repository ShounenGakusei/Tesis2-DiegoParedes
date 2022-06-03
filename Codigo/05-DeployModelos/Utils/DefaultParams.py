def getDefaultParams(path_base):

    params = {
        # Parametros principales
        'fecha': '2022-02-01-07',
        'dato': 0.4,
        'coordLon': -80.39788,
        'coordLat': -4.48047,

        # Parametros fijos
        'dirModelos' : f'{path_base}/Modelos/',
        'domain': [-88.0, -63.0, -25.0, 5.0],  # [-83.5495, -66.4504, -20.2252, 1.3783],
        'canales': ['07', '08', '13'],
        'tiempos': ['00', '50', '40', '30'],
        'margen': 30,

        # Parametros auxiliares
        'dibujar': False,
        'canalDibujar': '13',
        'save': True,
        'hard_save': False,
        "sizeMax": 2000000,
        "saveMax": 10000000,
        'umbral': 0.51,
        'port' : 8080,
    }

    return params