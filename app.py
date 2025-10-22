from flask import Flask, render_template, request, jsonify, session, redirect
import pymysql
pymysql.install_as_MySQLdb()
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import re

app = Flask(__name__)
app.secret_key = 'eazi_secret_key'  # cámbiala por algo aleatorio/seguro

# Config MySQL (ajusta con tus credenciales)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'JazielSQL'             # tu pass
app.config['MYSQL_DB'] = 'eazi_finances'      # tu BDD
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

EMAIL_RE = re.compile(r'^\S+@\S+\.\S+$')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    # Verificar si el usuario está logueado
    if 'usuario_id' not in session:
        return redirect('/')
    return render_template('dashboard.html')

# ---------- Rutas para botones de acción ----------
@app.route('/realizar-registro')
def realizar_registro():
    # Verificar si el usuario está logueado
    if 'usuario_id' not in session:
        return redirect('/')
    # Por ahora redirigir al dashboard hasta que se cree el HTML
    return render_template('registro.html')

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


if __name__ == '__main__':
    app.run(debug=True)
