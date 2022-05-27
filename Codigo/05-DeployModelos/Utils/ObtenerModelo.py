import tensorflow as tf

def crearModelo3D(p, run):
    # Imagen
    input_1 = tf.keras.layers.Input(shape=(p['tiempos'][run], p['margen'][run], p['margen'][run], p['canales'][run]))

    # Convulutional layers
    rescaling = tf.keras.layers.Rescaling(1. / 65536)(input_1)
    conv3d_1 = tf.keras.layers.Conv3D(128, kernel_size=3, padding='same', activation=tf.keras.activations.relu)(
        rescaling)
    # mxPool_1 = tf.keras.layers.MaxPooling3D()(conv3d_1)
    dropout_1 = tf.keras.layers.Dropout(0.2)(conv3d_1)

    conv3d_2 = tf.keras.layers.Conv3D(64, kernel_size=3, padding='same', activation=tf.keras.activations.relu)(
        dropout_1)
    mxPool_2 = tf.keras.layers.MaxPooling3D()(conv3d_2)
    dropout_2 = tf.keras.layers.Dropout(0.1)(mxPool_2)

    # conv2d_3 = tf.keras.layers.Conv3D(32, kernel_size=3,padding='same',activation=tf.keras.activations.relu)(dropout_1)
    # mxPool_3 = tf.keras.layers.MaxPooling3D()(conv2d_3)
    # dropout_3  = tf.keras.layers.Dropout(0.2)(mxPool_3)

    # conv2d_4 = tf.keras.layers.Conv3D(64, kernel_size=3,padding='same',activation=tf.keras.activations.relu)(dropout_3)
    # mxPool_4 = tf.keras.layers.MaxPooling3D()(conv2d_4)
    # dropout_4  = tf.keras.layers.Dropout(0.2)(mxPool_4)

    conv3d_5 = tf.keras.layers.Conv3D(32, kernel_size=3, padding='same', activation=tf.keras.activations.relu)(
        dropout_2)

    # Flatten layer :
    flatten = tf.keras.layers.Flatten()(conv3d_5)

    final = flatten
    listConcat = [flatten]
    listInputs = [input_1]

    if len(p['inputs']) > 1:
        # Agregamos los otros atrbutos
        for attr in p['inputs'][1:]:
            # The other input
            input_x = tf.keras.layers.Input(shape=(1,))
            listConcat.append(input_x)
            listInputs.append(input_x)

        # Concatenate
        final = tf.keras.layers.Concatenate()(listConcat)

    dense_1 = tf.keras.layers.Dense(units=32, activation=tf.keras.activations.relu)(final)
    # dense_2 = tf.keras.layers.Dense(units=16, activation=tf.keras.activations.relu)(dense_1)
    dense_3 = tf.keras.layers.Dense(units=32, activation=tf.keras.activations.relu)(dense_1)

    # output
    if p['redTipo'] == 'Regresion':
        output = tf.keras.layers.Dense(units=1)(dense_3)
        dimOutput = 1
    elif p['redTipo'] == 'Clasificacion':
        output = tf.keras.layers.Dense(units=1, activation=tf.keras.activations.sigmoid)(
            dense_3)  # units=1, activation=tf.keras.activations.relu)(dense_3)
        dimOutput = 2
    else:
        print(f"No se pudo crear el modelo outputs no esta bien definido {p['redTipo']}")
        return -1

    full_model = tf.keras.Model(inputs=listInputs, outputs=[output])

    # print(full_model.summary())
    return full_model

def crearModelo(params):
    p = {
        'redTipo': 'Clasificacion',
        'inputs': ['imagen', 'dato'],
        'outputs': 'clase',
        #'lr': 0.001,
        #'batch': 32,
        #'dataset': 1,
        #'epocas': 10,
        #'paciencia': 4,
        'canales': [len(params['canales'])],
        'tiempos': [len(params['tiempos'])],
        'margen': [params['margen']],
        'runs': 1
    }
    run = 0

    return crearModelo3D(p, run)
