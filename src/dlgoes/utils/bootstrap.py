import zipfile

with zipfile.ZipFile("data/raw/Inicial.zip", "r") as zip_ref:
    zip_ref.extractall("data/raw/")