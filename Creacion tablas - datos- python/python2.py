import getpass
import oracledb
import pandas as pd
import pandasql as ps
import csv
pw = getpass.getpass("Ingresa la contraseña de administrador: ")

connection = oracledb.connect(
    user="sebastian",
    password=pw,
    dsn="localhost:1521/xe")
print("Conexión Exitosa")

reader = csv.reader(open("csv/usuariorolpermisos.csv", "r"))
next(reader)
columna = []
for line in reader:
    columna.append(line)
    print(line)

cur = connection.cursor()
for linea in columna:
    print("Se insertó el dato")
    query = """insert into "TblUsuarioRolPermisos" values (:1, :2, :3)"""
    cur.execute(query, linea)
    connection.commit()


#:1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11, :12





connection.commit()