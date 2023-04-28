import random

import numpy as np
import tensorflow as tf
from wandb.keras import WandbCallback

"""
DEFINIMOS EL PATH DEL PROYECTO 
"""
with open('../../path_base.txt') as f:
        path_base = f.read()
path_base

# Leemos los projectos a comparar
statsFile = pd.read_csv(f'{path_base}/Archivos/Reportes/Entrenamiento/Clasificacion/Reporte-Clasificacion.csv')

projects = []

# Launch 20 experiments, trying different dropout rates
for run in range(20):
    # Start a run, tracking hyperparameters
    wandb.init(
            project="keras-intro",
            # Set entity to specify your username or team name
            # ex: entity="wandb",
            config={
                    "layer_1": 512,
                    "activation_1": "relu",
                    "dropout": random.uniform(0.01, 0.80),
                    "layer_2": 10,
                    "activation_2": "softmax",
                    "optimizer": "sgd",
                    "loss": "sparse_categorical_crossentropy",
                    "metric": "accuracy",
                    "epoch": 6,
                    "batch_size": 256
            })
    config = wandb.config
    for p in project:
        wandb.init(project=f'{params["Proyect"]}-({params["redTipo"]}-{params["outputs"]}-{len(params["inputs"])})',            
            config=config,
            name= f'Ex_{dsName}_({params["canales"][run]}-{params["tiempos"]w[run]}-{params["margen"][run]})_{idModel}')

        wandb.log({"conf_mat" : wandb.plot.confusion_matrix(probs=None,
            preds=_y_pred, y_true=y_true,
            class_names=[0,1]),                                     
            'val_TN' :TN,'val_FN' :FN,'val_TP' :TP,'val_FP' :FP,
            'val_acc': logs['val_acc'],'loss' : logs['loss'],
            'val_loss': logs['val_loss'],'acc' : logs['acc']                                    
            })

    # Mark the run as finished
    wandb.finish()