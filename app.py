from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from dotenv import load_dotenv
import os


# Cargar variables de entorno
load_dotenv('connect.env')

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')


#Configuracion de conexión a la base de datos.
def get_db_connection():
    return mysql.connector.connect(
        host = os.getenv('DB_HOST'),
        user = os.getenv('DB_USER'),
        password = os.getenv('DB_PASSWORD'),
        database = os.getenv('DB_NAME')
    )

# Ruta para el inicio de sesión
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        #Consulta para verificar usuario y contraseña:
        query = "SELECT * FROM usuarios WHERE nickname = %s AND contraseña = %s"
        cursor.execute(query, (username,password))
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user:
            session['user'] = user['nickname']
            session['nombre'] = user['nombre']

            if user['rol'] == 'administrador':
                return redirect(url_for('administrador'))
            else:
                return redirect(url_for('usuario'))
        else:
            flash('Credenciales incorrectas. Intenta otra vez', 'error')

    return render_template('index.html')

# Ruta para el módulo del administrador
@app.route('/administrador')
def administrador():
    if 'nombre' in session:
        return render_template('administrador/home.html', nombre = session['nombre'])
    else:
        return redirect(url_for('index'))

# Ruta para el módulo del usuario
@app.route('/usuario')
def usuario():
    if 'user' in session:
        return render_template('usuario/home.html')
    return redirect(url_for('index'))

#Rutas para los modulos de administrador:
#------------------------------------------
#Funciones de usuario
@app.route('/admin/usuarios')
def admin_usuarios():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM usuarios"
    cursor.execute(query)
    usuarios = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('administrador/usuarios.html', nombre = session['nombre'], usuarios = usuarios)

#Funcion de agregar usuario
@app.route('/admin/agregar_usuario', methods=['GET','POST'])
def agregar_usuario():
    if request.method == 'POST':
        nombre = request.form['nombre_user']
        nickname = request.form['nickname_user']
        contraseña = request.form['contraseña_user']
        rol = request.form['rol_user']

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("INSERT INTO usuarios (nombre, nickname, contraseña, rol) VALUES (%s, %s, %s, %s)",
                            (nombre,nickname,contraseña,rol))
            conn.commit()
            flash('Usuario agregado exitosamente','success')
            return redirect(url_for('usuarios'))
        except mysql.connector.Error as err:
            flash(f"Error al agregar el usuario: {err}", 'danger')
            return render_template('/administrador/agregar_usuarios.html')
        finally:
            cursor.close()
            conn.close()
        
    return render_template('/administrador/agregar_usuarios.html', nombre = session['nombre'])

#Funcion para editar el usuario:
@app.route('/editar_usuario/<int:user_id>', methods=['GET'])
def editar_usuario(user_id):
    # Obtener conexión a la base de datos
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Consultar los datos del usuario por ID
    cursor.execute("SELECT * FROM usuarios WHERE id_usuario = %s", (user_id,))
    usuario = cursor.fetchone()
    
    cursor.close()
    conn.close()

    if usuario:
        return render_template('/administrador/modificar_usuarios.html', usuario=usuario)
    else:
        flash("Usuario no encontrado.", "error")
        return redirect(url_for('admin_usuarios'))
    
#Funcion para guardar el usuario editado.
@app.route('/guardar_usuario', methods=['POST'])
def guardar_usuario():
    # Obtener los datos del formulario
    user_id = request.form['editar_idUsuario']
    nombre = request.form['editar_nombre_user']
    nickname = request.form['editar_nickname_user']
    contraseña = request.form['editar_contraseña_user']
    rol = request.form['editar_rol_user']
    
    # Actualizar los datos en la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE usuarios 
            SET nombre = %s, nickname = %s, contraseña = %s, rol = %s 
            WHERE id_usuario = %s
        """, (nombre, nickname, contraseña, rol, user_id))
        conn.commit()
        flash("Usuario actualizado correctamente.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error al actualizar el usuario: {str(e)}", "error")
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('admin_usuarios'))

@app.route('/admin/eliminar_usuario/<int:user_id>', methods=['POST'])
def eliminar_usuario(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM usuarios WHERE id_usuario = %s", (user_id,))
        conn.commit()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return '', 204  # Respuesta vacía para AJAX (sin recargar página)
        else:
            flash('Usuario eliminado exitosamente', 'success')
            return redirect(url_for('usuarios'))
        
    except mysql.connector.Error as err:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return str(err), 500
        else:
            flash(f"Error al eliminar el usuario: {err}", 'danger')
            return redirect(url_for('usuarios'))
    finally:
        cursor.close()
        conn.close()

#Funciones de categorias: -----------------------------------------------
@app.route('/admin/categorias')
def admin_categorias():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM categorias"
    cursor.execute(query)
    categorias = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('administrador/categorias.html', nombre = session['nombre'], categorias=categorias)

#Agregar categoria:
@app.route('/admin/agregar_categoria', methods=['GET','POST'])
def agregar_categoria():
    if request.method == 'POST':
        nombre = request.form['nombre_cat']
        descripcion = request.form['descripcion_cat']

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("INSERT INTO categorias (nombre,descripcion) VALUES (%s,%s)",
                            (nombre,descripcion))
            conn.commit()
            flash('Categoria agregada exitosamente')
            return redirect(url_for('categorias'))
        except mysql.connector.Error as err:
            flash(f'Error al agregar el usuario: {err}', 'danger')
            return render_template('/administrador/agregar_categoria.html')
        finally:
            cursor.close()
            conn.close()
    return render_template('/administrador/agregar_categoria.html')

#Editar categoria:
@app.route('/editar_categoria/<int:cat_id>', methods=['GET'])
def editar_categoria(cat_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute('SELECT * FROM categorias WHERE id_categoria = %s', (cat_id,))
    categoria = cursor.fetchone()

    cursor.close()
    conn.close()

    if categoria:
        return render_template('/administrador/modificar_categoria.html', categoria = categoria)
    else:
        flash("Categoria no encontrada.", "error")
        return redirect(url_for('admin_categorias'))

#Guardar los cambios en la categoria
@app.route('/guardar_categoria',methods=['POST'])
def guardar_categoria():
    cat_id = request.form['editar_idCategoria']
    nombre = request.form['editar_nombre_cat']
    descripcion = request.form['editar_descripcion_cat']

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("UPDATE categorias SET nombre = %s, descripcion = %s WHERE id_categoria = %s",
                        (nombre,descripcion,cat_id))
        conn.commit()
        flash("Categoria actualizada correctamente.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error al actualizar la categoria: {str(e)}", "error")
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('admin_categorias'))
#Eliminar categoria:
@app.route('/admin/eliminar_categoria/<int:cat_id>', methods=['POST'])
def eliminar_categoria(cat_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM categorias WHERE id_categoria = %s", (cat_id,))
        conn.commit()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return '', 204
        else:
            flash('Categoria eliminada exitosamente', 'success')
            return redirect(url_for('categorias'))
    except mysql.connector.Error as err:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return str(err), 500
        else:
            flash(f'Error al elimminar la categoria:{err}', 'danger')
            return redirect(url_for('categorias'))
    finally:
        cursor.close()
        conn.close()

#--------------------------------------------------------------------------------------------------------
#(Eduardo picazo)
# Aqui estan las funciones para Productos
@app.route('/admin/productos')
def admin_productos():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = """
        SELECT 
            p.id_producto, 
            p.nombre AS nombre_producto, 
            p.descripcion, 
            p.cantidad, 
            c.nombre AS nombre_categoria, 
            pr.nombre AS nombre_proveedor, 
            p.ubicacion
        FROM Productos p
        JOIN Categorias c ON p.categoria_id = c.id_categoria
        JOIN Proveedores pr ON p.proveedor_id = pr.id_proveedor
    """
    cursor.execute(query)
    productos = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('administrador/productos.html', productos=productos, nombre = session['nombre'])


@app.route('/admin/agregar_producto', methods=['GET', 'POST'])
def agregar_productos():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        cantidad = request.form['cantidad']
        categoria_id = request.form['categoria_id']
        proveedor_id = request.form['proveedor_id']
        ubicacion = request.form['ubicacion']

        conn = get_db_connection()
        try:
            cursor = conn.cursor()

            # Validar existencia de categoria_id
            cursor.execute("SELECT COUNT(*) FROM Categorias WHERE id_categoria = %s", (categoria_id,))
            categoria_existe = cursor.fetchone()[0] > 0

            # Validar existencia de proveedor_id
            cursor.execute("SELECT COUNT(*) FROM Proveedores WHERE id_proveedor = %s", (proveedor_id,))
            proveedor_existe = cursor.fetchone()[0] > 0

            if not categoria_existe or not proveedor_existe:
                flash("La categoría o el proveedor no existen. Por favor, verifica los datos.", "error")
                return redirect(url_for('agregar_productos'))

            # Insertar producto si todo está bien
            cursor.execute("""
                INSERT INTO Productos (nombre, descripcion, cantidad, categoria_id, proveedor_id, ubicacion)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (nombre, descripcion, cantidad, categoria_id, proveedor_id, ubicacion))
            conn.commit()
            flash("Producto agregado exitosamente.", "success")
            return redirect(url_for('admin_productos'))
        finally:
            cursor.close()
            conn.close()
    

    else:
        # Consultar categorías y proveedores para el formulario
        try:
            cursor.execute("SELECT id_categoria, nombre FROM Categorias")
            categorias = cursor.fetchall()

            cursor.execute("SELECT id_proveedor, nombre, contacto FROM Proveedores")
            proveedores = cursor.fetchall()
        finally:
            cursor.close()
            conn.close()
        

        return render_template('/administrador/agregar_productos.html',
                               categorias = categorias,
                               proveedores = proveedores)
    



@app.route('/admin/modificar_producto/<int:id>', methods=['GET', 'POST'])
def modificar_producto(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Obtener el producto actual
    cursor.execute("SELECT * FROM Productos WHERE id_producto=%s", (id,))
    producto = cursor.fetchone()
    if not producto:
        return "Producto no encontrado", 404

    # Obtener categorías y proveedores para los menús desplegables
    cursor.execute("SELECT id_categoria, nombre FROM Categorias")
    categorias = cursor.fetchall()

    cursor.execute("SELECT id_proveedor, nombre, contacto FROM Proveedores")
    proveedores = cursor.fetchall()

    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        cantidad = request.form['cantidad']
        categoria_id = request.form['categoria_id']
        proveedor_id = request.form['proveedor_id']
        ubicacion = request.form['ubicacion']
        
        # Validar existencia de categoría y proveedor
        cursor.execute("SELECT COUNT(*) FROM Categorias WHERE id_categoria = %s", (categoria_id,))
        categoria_existe = cursor.fetchone()['COUNT(*)'] > 0

        cursor.execute("SELECT COUNT(*) FROM Proveedores WHERE id_proveedor = %s", (proveedor_id,))
        proveedor_existe = cursor.fetchone()['COUNT(*)'] > 0

        if not categoria_existe or not proveedor_existe:
            # Mostrar mensaje de error si alguno no existe
            flash("La categoría o el proveedor especificados no existen.", "error")
            return render_template(
                '/administrador/modificar_productos.html',
                producto=producto,
                categorias=categorias,
                proveedores=proveedores
            )

        # Actualizar el producto si todo es válido
        cursor.execute("""
            UPDATE Productos 
            SET nombre=%s, descripcion=%s, cantidad=%s, categoria_id=%s, proveedor_id=%s, ubicacion=%s 
            WHERE id_producto=%s
        """, (nombre, descripcion, cantidad, categoria_id, proveedor_id, ubicacion, id))
        conn.commit()
        flash("Producto actualizado con éxito.", "success")
        return redirect(url_for('admin_productos'))

    # Renderizar el formulario con los datos actuales
    return render_template(
        '/administrador/modificar_productos.html',
        producto=producto,
        categorias=categorias,
        proveedores=proveedores
    )


@app.route('/admin/eliminar_producto/<int:id>',methods=['POST'])
def eliminar_producto(id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Productos WHERE id_producto=%s", (id,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('admin_productos'))



#----------------------------------------------------------------------------------------------------
#aqui estan las funciones de proveedores
#funcion agregada para mostrar los proveedores en la tabla
@app.route('/admin/proveedores')
def admin_proveedores():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT id_proveedor, nombre, contacto, telefono, direccion FROM Proveedores"
    cursor.execute(query)
    proveedores = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('administrador/proveedores.html', nombre = session['nombre'], proveedores=proveedores)

@app.route('/admin/agregar_proveedor', methods=['GET', 'POST'])
def agregar_proveedor():
    if request.method == 'POST':
        nombre = request.form['nombre']
        contacto = request.form['contacto']
        telefono = request.form['telefono']
        direccion = request.form['direccion']
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Proveedores (nombre, contacto, telefono, direccion) VALUES (%s, %s, %s, %s)",
                           (nombre, contacto, telefono, direccion))
            conn.commit()
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('admin_proveedores'))
    return render_template('/administrador/agregar_proveedor.html')

@app.route('/admin/modificar_proveedor/<int:id>', methods=['GET', 'POST'])
def modificar_proveedor(id):
    print(f"Modificando proveedor con ID: {id}")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Proveedores WHERE id_proveedor=%s", (id,))
    proveedor = cursor.fetchone()
    print(f"Proveedor encontrado: {proveedor}")
    if not proveedor:
        return "Proveedor no encontrado", 404
    if request.method == 'POST':
        nombre = request.form['nombre']
        contacto = request.form['contacto']
        telefono = request.form['telefono']
        direccion = request.form['direccion']
        cursor.execute("UPDATE Proveedores SET nombre=%s, contacto=%s, telefono=%s, direccion=%s WHERE id_proveedor=%s",
                       (nombre, contacto, telefono, direccion, id))
        conn.commit()
        return redirect(url_for('admin_proveedores'))
    return render_template('/administrador/modificar_proveedor.html', proveedor=proveedor)

@app.route('/admin/eliminar_proveedor/<int:id>',methods=['POST'])
def eliminar_proveedor(id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Proveedores WHERE id_proveedor=%s", (id,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('admin_proveedores'))
#---------------------------------------------------------------------------------------------------

#Funciones de movimiento:
@app.route('/admin/movimientos')
def admin_movimientos():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    
    cursor.execute('''SELECT
                        M.id_movimiento, 
                        M.fecha, M.tipo,
                        P.nombre AS nombre_producto,
                        M.cantidad,
                        U.nombre AS nombre_usuario,
                        M.comentarios
                    FROM movimientosinventario M 
                    JOIN productos P ON M.producto_id = P.id_producto
                    JOIN usuarios U ON M.usuario_id = U.id_usuario''')
    movimientos = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('administrador/movimientos.html', nombre = session['nombre'], movimientos = movimientos)

#Funcion para agregar un movimiento:
@app.route('/admin/agregar_movimiento', methods=['GET', 'POST'])
def agregar_movimiento():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        fecha = request.form['fecha_mov']
        tipo = request.form['tipo_mov']
        id_producto = request.form['producto_mov']
        cantidad = request.form['cantidad_mov']
        id_usuario = request.form['usuario_mov']
        comentario = request.form['comentario_mov']
        #conn = get_db_connection()
        #cursor = conn.cursor()

        try:
            #Insertar los datos a la tabla
            cursor.execute(''' INSERT INTO movimientosinventario (fecha, tipo, producto_id, cantidad, usuario_id, comentarios)
                            VALUES (%s, %s, %s, %s, %s, %s)''', (fecha, tipo, id_producto, cantidad, id_usuario, comentario))
            conn.commit()
            flash('Movimiento de mercancia agregado exitosamente.', 'success')
            return redirect(url_for('/admin/movimientos'))
        except mysql.connector.Error as err:
            flash(f'Error al agregar el movimiento: {err}', 'danger')
            return render_template('/administrador/agregar_movimiento.html')
        finally:
            cursor.close()
            conn.close()

    else:
        #Consultar productos y usuarios:
        try:
            cursor.execute('SELECT id_producto, nombre FROM productos')
            productos = cursor.fetchall()

            cursor.execute('SELECT id_usuario, nombre FROM usuarios')
            usuarios = cursor.fetchall()
        finally:
            cursor.close()
            conn.close()
        return render_template('/administrador/agregar_movimiento.html', productos=productos, usuarios=usuarios)

#Funcion editar movimiento
@app.route('/editar_movimiento/<int:mov_id>', methods=['GET'])
def editar_movimiento(mov_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    #Consultar los datos del movimiento.
    cursor.execute('SELECT * FROM movimientosinventario WHERE id_movimiento = %s', (mov_id,))
    movimiento = cursor.fetchone()
    print(movimiento)

    #Traer los productos
    cursor.execute('SELECT id_producto, nombre FROM productos')
    productos = cursor.fetchall()

    #Traer los usuarios
    cursor.execute('SELECT id_usuario, nombre FROM usuarios')
    usuarios = cursor.fetchall()

    cursor.close()
    conn.close()

    if movimiento:
        return render_template('/administrador/modificar_movimiento.html', movimiento=movimiento, productos=productos, usuarios=usuarios)
    else:
        flash('Movimiento no encontrado.', 'error')
        return redirect(url_for('admin_movimientos'))

#Funcion para guardar movimiento editado:
@app.route('/guardar_movimiento', methods=['POST'])
def guardar_movimiento():
    movimiento_id = request.form['editar_idMov']
    fecha = request.form['editar_fechaMov']
    tipo = request.form['editar_tipoMov']
    producto_id = request.form['editar_productoMov']
    cantidad = request.form['editar_cantidadMov']
    usuario_id = request.form['editar_usuarioMov']
    comentario = request.form['editar_comentarioMov']

    print(tipo)

    #Conexion a la BD
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''UPDATE movimientosinventario
                        SET fecha = %s, tipo = %s, producto_id = %s, cantidad = %s, usuario_id = %s, comentarios = %s
                        WHERE id_movimiento = %s''',
                        (fecha,tipo,producto_id,cantidad,usuario_id,comentario,movimiento_id))
        conn.commit()
        flash('Movimiento modificado correctamente.', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error al actualizar el movimiento: {str(e)}', 'error')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('admin_movimientos'))

#Funcion eliminar movimiento
@app.route('/admin/eliminar_movimiento/<int:id>', methods=['POST'])
def eliminar_movimiento(id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM movimientosinventario WHERE id_movimiento = %s', (id,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('admin_movimientos'))
#--------------------------------------------------------------------------------------------------
#Ruta para cerrar sesion
@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Sesión cerrada exitosamente.')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)