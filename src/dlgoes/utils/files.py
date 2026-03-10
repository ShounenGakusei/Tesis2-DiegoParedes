import os 
import stat

def force_remove(file_path):
    try:
        # Cambiar permisos si es necesario
        os.chmod(file_path, stat.S_IWRITE)
        os.remove(file_path)
        print(f"Archivo eliminado: {file_path}")
    except FileNotFoundError:
        print(f"El archivo no existe: {file_path}")
    except Exception as e:
        print(f"No se pudo eliminar el archivo: {e}")
