import glob
import datetime
from os.path import join

def create_get_actual_log_dir(path_base):
    temp = datetime.datetime.today().strftime("%Y%m%d") + '_LOG.txt'
    file_log = join(join(path_base, 'logs'), temp)

    # Verificamos si existe el archivo log
    files = [x for x in glob.glob(f"{path_base}/logs/*.txt") if temp in file_log]
    if len(files) == 0:
        # En caso no exista, lo creamos
        f = open(file_log, "w")
        f.close()

    return file_log

def find_log_file(path_base, fecha = ''):
    file_log = join(join(path_base, 'logs'), f'{fecha}_LOG.txt')
    files = [x for x in glob.glob(f"{path_base}/logs/*.txt") if fecha in file_log]
    if files:
        return files[0]
    return ''

def write_on_file(file_name, data, changeline = True):
    f = open(file_name, "a")
    data = f'[{datetime.datetime.today().strftime("%Y/%m/%d %H:%M:%S")}] : {data}'
    if changeline:
        f.write(data + '\n')
    else:
        f.write(data)
    f.close()