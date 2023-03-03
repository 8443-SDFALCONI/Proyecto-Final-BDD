"""
Importamos los módulos necesarios
"""
from __future__ import print_function
from flask import Flask, jsonify, abort, request
from flask_cors import CORS, cross_origin
import logging
import os
import oracledb
from waitress import serve
from flask import render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

"""
Configuramos las variables de entorno
"""
os.environ["PYTHON_USERNAME"] = "sebastian"
os.environ["PYTHON_PASSWORD"] = "123123Oracle"
os.environ["PYTHON_CONNECTSTRING"] = "localhost:1521/xe"

"""
Creamos una instancia de la aplicación Flask
"""
app = Flask(__name__)
app.secret_key = '123123Flask'

"""
Configuramos el manejador de login
"""
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

CORS(app)
cors = CORS(app, resources={
            r"/api/*": {"origins": "*", "methods": "POST,DELETE,PUT,GET,OPTIONS"}})


def start_pool():
    """
    Se establece una conexión a Oracle mediante la creación de un pool de conexiones con los valores proporcionados en las variables de entorno.

    Retorna:
    pool: objeto de tipo oracledb.Pool que  permite representar el pool de conexiones
    """
    pool_min = 4
    pool_max = 4
    pool_inc = 0

    print("Conectando a", os.environ.get("PYTHON_CONNECTSTRING"))

    pool = oracledb.create_pool(
        user=os.environ.get("PYTHON_USERNAME"),
        password=os.environ.get("PYTHON_PASSWORD"),
        dsn=os.environ.get("PYTHON_CONNECTSTRING"),
        min=pool_min,
        max=pool_max,
        increment=pool_inc
    )

    return pool


def create_schema():
    """
    Crea un cursor y ejecuta una consulta en la base de datos Oracle para verificar la conexión.
    """
    with pool.acquire() as connection:
        with connection.cursor() as cursor:

            try:
                cursor.execute(
                    """
                    select * from "TblRol"
                    """
                )
            except oracledb.Error as err:
                error_obj, = err.args
                print(f"Conexión no extiosa: {error_obj.message}")


pool = start_pool()

create_schema()


@app.route('/login')
def index():
    """Muestra la página de inicio de sesión."""
    if current_user.is_authenticated:
        return redirect(url_for("/"))
    return render_template('sistema.html')


@app.route('/', methods=['GET', 'POST'])
def login():
    """Maneja la lógica de inicio de sesión.

    Si el usuario envía sus credenciales, verifica que los datos sean correctos y si lo son,
    redirige al usuario a la página del sistema.

    Si los datos no son correctos, se muestra un mensaje de error.
    """
    with pool.acquire() as connection:
        with connection.cursor() as cursor:
            try:
                msg = ''
                if request.method == 'POST' and 'usuario' in request.form and 'contrasenia' in request.form:
                    usuario = request.form['usuario']
                    contrasenia = request.form['contrasenia']
                    cursor.execute(
                        """ SELECT * FROM "TblUsuario" WHERE "VarCorreoUsuario" = :usuario AND "VarContraseniaUsuario" = :contra """, usuario=usuario, contra=contrasenia)
                    account = cursor.fetchone()

                    if account:
                        session['loggedin'] = True
                        return redirect(url_for("sistema"))
                    else:
                        msg = 'Usuario o contraseña incorrecta!'
            except oracledb.Error as err:
                error_obj, = err.args
                print(f"Conexión no extiosa: {error_obj.message}")
    return render_template('web.html', msg=msg)


@app.route('/sistema/')
def sistema():
    """Muestra la página principal del sistema si el usuario está autenticado,
    de lo contrario redirige al usuario a la página de inicio de sesión."""
    if 'loggedin' in session:
        return render_template('/sistema.html')
    return redirect(url_for('login'))


@app.route('/logout')
def logout():
    """Cierra la sesión del usuario y redirige al usuario a la página de inicio de sesión."""
    session.pop('loggedin', None)
    return redirect(url_for('login'))


@app.route('/administracion/')
def administracion():
    """Muestra la página de administración del sistema si el usuario está autenticado,
    de lo contrario redirige al usuario a la página de inicio de sesión."""
    id = current_user.get_id()
    return render_template('/administracion.html')


@app.route("/form_agregar_usuario")
def form_agregar_usuario():
    """Función para cargar el formulario de agregar usuario"""
    return render_template('/sistema/form_agregar_usuario.html')


@app.route("/agregar_usuario", methods=['POST'])
def agregar_usuario():
    """Función para agregar usuario"""
    with pool.acquire() as connection:
        with connection.cursor() as cursor:

            if request.method == 'POST':
                nombres = request.form['nombres']
                apellidos = request.form['apellidos']
                email = request.form['email']
                nombreusuario = request.form['nombreusuario']
                contrasenia = request.form['contrasenia']
                genero = request.form['genero']
                idusuario = request.form['idusuario']
                estado = request.form['estado']
                telefono = request.form['telefono']
                try:
                    # Ejecuta una consulta a la base de datos
                    cursor.execute(
                        '''
                                INSERT INTO "TblUsuario" VALUES(:idusuario,:nombres, :apellidos, :email, :estado,  :contrasenia, :nombreusuario, :genero ,:telefono)
                            ''', [idusuario, nombres, apellidos, email, estado,  contrasenia, nombreusuario, genero, telefono])
                    connection.commit()

                except oracledb.Error as err:
                    # En caso de error, muestra un mensaje de error en la consola
                    error_obj, = err.args
                    print(f"Conexión no exitosa: {error_obj.message}")

        with pool.acquire() as connection:
            with connection.cursor() as cursor:
                try:
                    cursor.execute(
                        '''
                                    Select * from "TblUsuario" where "VarIdentificadorUsuario" = :idusuario
                                ''', [idusuario])
                    resultado = cursor.fetchall()
                    aceptado = "Se agregó correctamente el usuario"
                except oracledb.Error as err:
            # En caso de error, muestra un mensaje de error en la consola
                    error_obj, = err.args
                    print(f"Conexión no exitosa: {error_obj.message}")
                return render_template('/sistema/agregar_usuario.html', resultado=resultado, aceptado=aceptado)
    # Renderiza la plantilla y pasa el resultado de la consulta
    return render_template('/sistema')

@app.route("/ver_usuarios")
def ver_usuarios():
    with pool.acquire() as connection:
        with connection.cursor() as cursor:
            try:
                cursor.execute(
                    '''
                    SELECT * from "TblUsuario"
                    ''')
                resultado = cursor.fetchall()
            except oracledb.Error as err:
                error_obj, = err.args
                print(f"Conexión no exitosa: {error_obj.message}")
        return render_template('/sistema/ver_usuarios.html', resultado=resultado)

@app.route("/ver_vistas")
def ver_vistas():
    with pool.acquire() as connection:
        with connection.cursor() as cursor:
            try:
                cursor.execute(
                    '''
                    SELECT DISTINCT * from PARROQUIAS Natural Join (SELECT * FROM PROVINCIAS Natural Join (SELECT * FROM CANTONES Natural Join (SELECT * FROM PERMISOS))) FETCH NEXT 10 ROWS ONLY
                    ''')
                resultado = cursor.fetchall()
            except oracledb.Error as err:
                error_obj, = err.args
                print(f"Conexión no exitosa: {error_obj.message}")
        return render_template('/sistema/ver_vistas.html', resultado=resultado)


@login_manager.user_loader
def load_user(user_id):
    return model.usuarios.objects.get(usuario_id=user_id)


'''
Esta parte del código indica que si se está ejecutando directamente este archivo
 (en lugar de ser importado por otro), entonces se iniciará la aplicación Flask en el servidor local en el puerto especificado o en el puerto 8080 si no se especifica ninguno.
'''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.environ.get('PORT', '8080'), debug=True)
