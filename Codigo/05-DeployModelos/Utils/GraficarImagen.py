from netCDF4 import Dataset, num2date
"""

# Como input recibe un string que es el directoeio de una imagen satelital (.nc),
# devuelve la matriz que representa esta imagen numpy.array(1200,950)
def getMapFile(imagenFile, mersh=0, imprimir=0, point=[]):
    try:
        ds = Dataset(imagenFile)
    except:
        print("No se pudo leer los archivos de imagen")
        print(imagenFile)
        return -1, -1

    # convierte el formato de la variable de Int16 a Float32 y guarda el resultado
    field = ds.variables['CMI'][:].data.astype(np.float32) / 100.0

    # obtiene las coordenadas de los pixeles
    lons = ds.variables['longitude'][:].data
    lats = ds.variables['latitude'][:].data
    date = num2date(ds.variables['time'][:], ds.variables['time'].units, only_use_cftime_datetimes=False,
                    only_use_python_datetimes=True)
    print(date[0])
    if imprimir:
        dibujarMapa(lons, lats, field, mersh, point)

    return lons, lats, field


def dibujarMapa(lons, lats, field, mersh=0, point=[]):
    if mersh:
        # field=  np.resize(f,(len(lats),len(lons)))
        lons, lats = np.meshgrid(lons, lats)
    else:
        field = field

    # realiza el grafico
    fig = plt.figure('ABI', figsize=(4, 4), dpi=150)
    ax = fig.add_axes([0.1, 0.1, 0.8, 0.8], projection=ccrs.PlateCarree())

    ax.add_feature(cf.COASTLINE)
    ax.add_feature(cf.BORDERS)
    # img = ax.pcolormesh(lons, lats, field, cmap=plt.cm.Greys, transform=ccrs.PlateCarree())
    img = ax.pcolormesh(lons, lats, field, vmin=200, vmax=300, transform=ccrs.PlateCarree())

    plt.colorbar(img)
    if point:
        plt.plot(point[0], point[1], 'ro')

    plt.show()

    return
"""
def dibujarMapa(lons, lats, field, mersh=0, point=[]):
    return 0
