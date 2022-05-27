Autor: Diego Paredes Chilon
Proyecto de Tesis (PUCP) 2022 - 1
EL proyecto se ejecuto en JupyterNoteBooks, con version de Python: 3.9
A continuacion se muestra las librerias necesarias a instalar:

# LIBRERIAS ESTANDARES
!pip install numpy                    # Manejo de arreglos
!pip install pandas                   # Manejo de df y uso de excel/csv
!pip install matplotlib                # Para graficar

# 01 PROCESAMIENTO DE DATOS
!pip install Cython                    # Para instalar cartopy
conda install -c conda-forge cartopy   # Para visualizar las estaciones
!pip install scikit-learn              # Para mezclar los datos y dividirlos

# 02 PROCESAMIENTO DE IMAGENES
!pip install netcdf4                   # Para leer los archivos binarios .nc
!pip install PNG					   # Formato que se usa para guardar las imagenes satelitales procesadas

# 03 ENTRENAMIENTO DE MODELOS
!pip install scipy                     # Otra forma de uniformizar los datos
!pip install tensorflow                # Libreria para definir los modelos y entrenarlos
!pip install wandb                     # Para guardar los resultados
conda list cudnn					   # Para usar GPU en el entrenamiento (Opcional)
conda list cudatoolkit			       # Para usar GPU en el entrenamiento (Opcional)

# 04 GENERAR REPORTES
!pip install seaborn                   # Generar graficos mas "avanzados"