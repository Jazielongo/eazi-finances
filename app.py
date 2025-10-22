from flask import Flask, render_template, request, jsonify, session, redirect
import re
import pymysql
pymysql.install_as_MySQLdb()
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'eazi_secret_key'  # cámbiala por algo aleatorio/seguro

# Config MySQL (ajusta con tus credenciales)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '12345'             # tu pass
app.config['MYSQL_DB'] = 'eazi_finances'      # tu BDD
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

EMAIL_RE = re.compile(r'^\S+@\S+\.\S+$')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    if 'usuario_id' not in session:
        return redirect('/')
        
    try:
        cur = mysql.connection.cursor()
        
        # Calcular balance general sumando ingresos y restando egresos
        cur.execute("""
            SELECT 
                COALESCE(SUM(CASE 
                    WHEN tipo_movimiento = 'ingreso' THEN total 
                    WHEN tipo_movimiento = 'egreso' THEN -total 
                    ELSE 0 
                END), 0) as balance
            FROM movimiento 
            WHERE id_negocio = 1
        """)
        result = cur.fetchone()
        balance = float(result['balance']) if result and result['balance'] else 0.00
        
        cur.close()
        
        # Renderizar dashboard pasando el balance calculado
        return render_template('dashboard.html', balance=balance)
                             
    except Exception as e:
        print(f"Error en dashboard: {str(e)}")
        return redirect('/')

# ---------- Rutas para botones de acción ----------
@app.route('/realizar-registro')
def realizar_registro():
    if 'usuario_id' not in session:
        return redirect('/login')
        
    cur = mysql.connection.cursor()
    
    # Obtener categorías
    cur.execute("SELECT categoria_id, nombre FROM categoria")
    categorias = cur.fetchall()
    
    # Obtener proveedores
    cur.execute("SELECT proveedor_id, nombre FROM proveedor")
    proveedores = cur.fetchall()
    
    cur.close()
    
    return render_template('registro.html', 
                         categorias=categorias,
                         proveedores=proveedores)

@app.route('/reportes')
def reportes():
    # Verificar si el usuario está logueado
    if 'usuario_id' not in session:
        return redirect('/')
    # Por ahora redirigir al dashboard hasta que se cree el HTML
    return redirect('/dashboard')

@app.route('/escanear-tickets')
def escanear_tickets():
    # Verificar si el usuario está logueado
    if 'usuario_id' not in session:
        return redirect('/')
    return render_template('escanear-ticket.html')


@app.route('/mis-negocios')
def mis_negocios():
    # Verificar si el usuario está logueado
    if 'usuario_id' not in session:
        return redirect('/')
    # Por ahora redirigir al dashboard hasta que se cree el HTML
    return redirect('/dashboard')

# ---------- Registro ----------
@app.route('/register', methods=['POST'])
def register():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    phone = request.form.get('phone', '').strip()

    # Validaciones backend
    if not name or not email or not password:
        return jsonify(success=False, message='Faltan datos obligatorios.'), 400
    if not EMAIL_RE.match(email):
        return jsonify(success=False, message='Correo inválido.'), 400
    if phone and not phone.isdigit():
        return jsonify(success=False, message='El teléfono debe contener solo números.'), 400
    if len(password) < 6:
        return jsonify(success=False, message='La contraseña debe tener al menos 6 caracteres.'), 400

    cur = mysql.connection.cursor()
    cur.execute("SELECT usuario_id FROM usuario WHERE email = %s", [email])
    if cur.fetchone():
        cur.close()
        return jsonify(success=False, message='El correo ya está registrado.'), 409

    hashed = generate_password_hash(password)  # se guarda en hash_password
    cur.execute("""
        INSERT INTO usuario (nombre, email, hash_password, telefono, estado)
        VALUES (%s, %s, %s, %s, 'activo')
    """, (name, email, hashed, phone if phone else None))
    mysql.connection.commit()
    cur.close()

    return jsonify(success=True, message='Cuenta creada correctamente.'), 200

# ---------- Login ----------
@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')

    if not email or not password:
        return jsonify(success=False, message='Faltan datos.'), 400
    if not EMAIL_RE.match(email):
        return jsonify(success=False, message='Correo inválido.'), 400

    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT usuario_id, nombre, email, hash_password, estado
        FROM usuario
        WHERE email = %s
        LIMIT 1
    """, [email])
    user = cur.fetchone()
    cur.close()

    if not user:
        return jsonify(success=False, message='Correo no encontrado.'), 404
    if user['estado'] != 'activo':
        return jsonify(success=False, message='Tu cuenta está inactiva.'), 403
    if not check_password_hash(user['hash_password'], password):
        return jsonify(success=False, message='Contraseña incorrecta.'), 401

    # Guarda algo de sesión por si luego lo usas
    session['usuario_id'] = user['usuario_id']
    session['nombre'] = user['nombre']
    session['email'] = user['email']

    return jsonify(success=True, message='Inicio de sesión exitoso.', user=user['nombre'], redirect='/dashboard'), 200

# ---------- Logout ----------
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify(success=True, message='Sesión cerrada correctamente.', redirect='/'), 200

# ---------- Movimientos ----------
@app.route('/guardar_movimiento', methods=['POST'])
def guardar_movimiento():
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autorizado (inicia sesión)'}), 401

    try:
        cur = mysql.connection.cursor()
        
        # 1. Verificar/crear negocio por defecto
        cur.execute("SELECT negocio_id FROM negocio WHERE negocio_id = 1")
        if not cur.fetchone():
            # Crear negocio por defecto
            cur.execute("""
                INSERT INTO negocio (negocio_id, nombre, giro, moneda_base) 
                VALUES (1, 'Mi Negocio', 'General', 'MXN')
            """)
            # Asociar usuario al negocio
            cur.execute("""
                INSERT INTO usuario_negocio (id_usuario, id_negocio, rol)
                VALUES (%s, 1, 'owner')
            """, (session['usuario_id'],))
            mysql.connection.commit()

        # 2. Obtener datos del form
        f = request.form
        tipo = f.get('tipo_movimiento') or 'ingreso'
        monto_total = f.get('monto_total') or f.get('montoTotal')
        subtotal = f.get('subtotal')
        iva = f.get('iva')
        descripcion = f.get('descripcion') or ''
        fecha_str = f.get('fecha_registro') or ''
        
        # 3. Parsear fecha
        try:
            fecha_obj = datetime.strptime(fecha_str, '%d/%m/%y')
        except:
            fecha_obj = datetime.now()

        # 4. Parsear números
        try:
            total_n = float(monto_total) if monto_total else 0
            subtotal_n = float(subtotal) if subtotal else None
            iva_n = float(iva) if iva else None
        except:
            return jsonify({'error': 'Valores numéricos inválidos'}), 400

        # 5. Insertar movimiento
        cur.execute("""
            INSERT INTO movimiento (
                id_negocio, tipo_movimiento, descripcion, 
                fecha_operacion, moneda, metodo_pago,
                subtotal, iva, total, creado_por
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            1,  # id_negocio fijo = 1
            tipo,
            descripcion,
            fecha_obj,
            'MXN',
            'efectivo',
            subtotal_n,
            iva_n,
            total_n,
            session['usuario_id']
        ))
        mysql.connection.commit()
        movimiento_id = cur.lastrowid
        cur.close()

        return jsonify({
            'mensaje': 'Movimiento guardado correctamente',
            'movimiento_id': movimiento_id
        }), 201

    except Exception as e:
        print(f"Error: {str(e)}")  # Log del error
        return jsonify({'error': str(e)}), 500

@app.route('/edicion')
def edicion():
    if 'usuario_id' not in session:
        return redirect('/')
        
    try:
        cur = mysql.connection.cursor()
        # Obtener todos los movimientos ordenados por fecha
        cur.execute("""
            SELECT 
                movimiento_id,
                tipo_movimiento,
                descripcion,
                DATE_FORMAT(fecha_operacion, '%d/%m/%y') as fecha,
                total
            FROM movimiento 
            WHERE id_negocio = 1
            ORDER BY fecha_operacion DESC, movimiento_id DESC
        """)
        movimientos = cur.fetchall()
        cur.close()
        
        return render_template('edicion.html', movimientos=movimientos)
    except Exception as e:
        print(f"Error en edición: {str(e)}")
        return redirect('/')

@app.route('/actualizar_movimiento/<int:movimiento_id>', methods=['POST'])
def actualizar_movimiento(movimiento_id):
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
        
    try:
        data = request.get_json()
        descripcion = data.get('descripcion', '').strip()
        total = float(data.get('total', 0))
        
        if total <= 0:
            return jsonify({'error': 'El monto debe ser mayor a 0'}), 400
            
        cur = mysql.connection.cursor()
        # Actualizar movimiento
        cur.execute("""
            UPDATE movimiento 
            SET descripcion = %s,
                total = %s,
                actualizado_en = CURRENT_TIMESTAMP
            WHERE movimiento_id = %s AND id_negocio = 1
        """, (descripcion, total, movimiento_id))
        mysql.connection.commit()
        cur.close()
        
        return jsonify({'mensaje': 'Movimiento actualizado correctamente'}), 200
    except Exception as e:
        print(f"Error actualizando movimiento: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/eliminar_movimiento/<int:movimiento_id>', methods=['POST'])
def eliminar_movimiento(movimiento_id):
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
        
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            DELETE FROM movimiento 
            WHERE movimiento_id = %s AND id_negocio = 1
        """, (movimiento_id,))
        mysql.connection.commit()
        cur.close()
        
        return jsonify({'mensaje': 'Movimiento eliminado correctamente'}), 200
    except Exception as e:
        print(f"Error eliminando movimiento: {str(e)}")
        return jsonify({'error': str(e)}), 500



if __name__ == '__main__':
    app.run(debug=True)
