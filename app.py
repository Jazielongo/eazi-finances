from flask import Flask, render_template, request, jsonify, session, redirect
import re
import os
import pymysql
from PIL import Image
import pytesseract
import numpy as np
from dateutil import parser
from werkzeug.utils import secure_filename
import traceback
pymysql.install_as_MySQLdb()
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import json

# Configuración para subida de archivos
UPLOAD_FOLDER = 'static/uploads'
TICKETS_FOLDER = os.path.join(UPLOAD_FOLDER, 'tickets')
METADATA_FILE = os.path.join(TICKETS_FOLDER, 'metadata.json')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.secret_key = 'eazi_secret_key'  # cámbiala por algo aleatorio/seguro
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Crear directorio de uploads si no existe
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TICKETS_FOLDER, exist_ok=True)

def load_metadata():
    try:
        if os.path.exists(METADATA_FILE):
            with open(METADATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print('Error leyendo metadata:', str(e))
    return {}

def save_metadata(meta):
    try:
        with open(METADATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print('Error guardando metadata:', str(e))

# Intentar detectar tesseract en Windows (ruta por defecto de instalador UB-Mannheim)
if os.name == 'nt':
    possible = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(possible):
        pytesseract.pytesseract.tesseract_cmd = possible
        print(f"Usando tesseract en: {possible}")
    else:
        print("Aviso: no se detectó tesseract.exe en la ruta por defecto. Asegúrate de instalar Tesseract y añadir su ruta a PATH o configurar pytesseract.pytesseract.tesseract_cmd.")

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

        # Obtener últimos 5 ingresos
        cur.execute("""
            SELECT 
                descripcion,
                DATE_FORMAT(fecha_operacion, '%d/%m/%y') as fecha,
                total
            FROM movimiento 
            WHERE id_negocio = 1 
            AND tipo_movimiento = 'ingreso'
            ORDER BY fecha_operacion DESC, movimiento_id DESC
            LIMIT 5
        """)
        ingresos = cur.fetchall()

        # Obtener últimos 5 egresos
        cur.execute("""
            SELECT 
                descripcion,
                DATE_FORMAT(fecha_operacion, '%d/%m/%y') as fecha,
                total
            FROM movimiento 
            WHERE id_negocio = 1 
            AND tipo_movimiento = 'egreso'
            ORDER BY fecha_operacion DESC, movimiento_id DESC
            LIMIT 5
        """)
        egresos = cur.fetchall()
        
        cur.close()
        
        # Renderizar dashboard pasando todos los datos
        return render_template('dashboard.html', 
                             balance=balance,
                             ingresos=ingresos,
                             egresos=egresos)
                             
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

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extraer_fecha(texto):
    lines = texto.split('\n')
    fecha_candidatos = []

    # Patrones de fecha comunes en tickets
    patrones_fecha = [
        (r"\b(?:FECHA|DATE|EXPEDIDO|EMITIDO)\b.*?(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})", 10),  # Alta prioridad para fechas junto a "FECHA"
        (r"\b(?:FECHA|DATE|EXPEDIDO|EMITIDO)\b.*?(\d{2,4}[-/]\d{1,2}[-/]\d{1,2})", 10),  # Formato año primero
        (r"\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b", 5),  # Formato común dd/mm/yy[yy]
        (r"\b(\d{2,4}[-/]\d{1,2}[-/]\d{1,2})\b", 5),  # Formato yyyy/mm/dd
        (r"\b(\d{1,2}\s+(?:ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC)[A-Z]*\.?\s+\d{2,4})\b", 8)  # Formato texto
    ]

    # Mapa de meses cortos en español a inglés (para ayudar al parser si es necesario)
    meses_map = {
        'ENE': 'JAN', 'FEB': 'FEB', 'MAR': 'MAR', 'ABR': 'APR', 'MAY': 'MAY', 'JUN': 'JUN',
        'JUL': 'JUL', 'AGO': 'AUG', 'SEP': 'SEP', 'OCT': 'OCT', 'NOV': 'NOV', 'DIC': 'DEC'
    }

    for idx, raw_line in enumerate(lines):
        line = raw_line.strip()
        up_line = line.upper()

        # Buscar fechas según los patrones definidos (usar la versión en mayúsculas para matching)
        for patron, prioridad in patrones_fecha:
            matches = re.finditer(patron, up_line)
            for match in matches:
                fecha_str = match.group(1)
                try:
                    # Reemplazar abreviaturas de mes en español por inglés si aparecen
                    fs = fecha_str
                    for es_m, en_m in meses_map.items():
                        fs = re.sub(r'\b' + re.escape(es_m) + r'\b', en_m, fs, flags=re.IGNORECASE)

                    fecha_obj = None
                    # Intentar parse flexible. Primero dayfirst=True, luego fallback.
                    try:
                        fecha_obj = parser.parse(fs, dayfirst=True, fuzzy=True)
                    except Exception:
                        try:
                            fecha_obj = parser.parse(fs, dayfirst=False, fuzzy=True)
                        except Exception:
                            fecha_obj = None

                    if fecha_obj:
                        now = datetime.now()
                        # Aceptar fechas razonables entre 2000 y año actual+1
                        if 2000 <= fecha_obj.year <= (now.year + 1) and fecha_obj <= (now + timedelta(days=365)):
                            score = prioridad
                            if 'FECHA' in up_line:
                                score += 5
                            # Si está en el primer tercio del ticket
                            if idx < len(lines) // 3:
                                score += 3
                            fecha_candidatos.append((fecha_obj, score))
                except Exception:
                    # No detener la extracción por errores puntuales
                    continue

    # Si encontramos candidatos, retornar el de mayor score
    if fecha_candidatos:
        fecha_candidatos.sort(key=lambda x: x[1], reverse=True)
        return fecha_candidatos[0][0]

    return None

def extraer_total(texto):
    lines = texto.split('\n')
    candidatos = []
    
    # Patrones para encontrar el total
    patrones_total = [
        # Patrones con alta prioridad (explícitamente marcados como total)
        (r'TOTAL\s*(?:A\s*PAGAR)?[\s:]*[$/]*\s*(\d+[.,]\d{2})', 10),
        (r'TOTAL\s*(?:A\s*PAGAR)?[\s:]*[$/]*\s*(\d+)(?:[.,]00)?', 9),  # Totales sin decimales
        (r'(?:IMPORTE|MONTO)\s*TOTAL[\s:]*[$/]*\s*(\d+[.,]\d{2})', 8),
        
        # Patrones con prioridad media (posibles totales)
        (r'(?:VENTA|CARGO)\s*TOTAL[\s:]*[$/]*\s*(\d+[.,]\d{2})', 7),
        (r'\bTOTAL[\s:]*[$/]*\s*(\d+[.,]\d{2})', 6),
        
        # Patrones con baja prioridad (números que podrían ser totales)
        (r'[$/]?\s*(\d+[.,]\d{2})\s*(?:MXN|MN|PESOS)?$', 3),
        (r'[$/]?\s*(\d+)(?:[.,]00)?\s*(?:MXN|MN|PESOS)?$', 2)
    ]
    
    for i, line in enumerate(lines):
        line = line.upper().strip()
        
        for patron, prioridad in patrones_total:
            matches = re.finditer(patron, line)
            for match in matches:
                try:
                    # Extraer el número y limpiar
                    numero_str = match.group(1).strip()
                    
                    # Manejar diferentes formatos de números
                    if ',' in numero_str and '.' in numero_str:
                        # Formato 1.234,56
                        numero_str = numero_str.replace('.', '').replace(',', '.')
                    else:
                        # Formato 1234.56 o 1234,56
                        numero_str = numero_str.replace(',', '.')
                    
                    numero = float(numero_str)
                    
                    # Ajustar score basado en varios factores
                    score = prioridad
                    
                    # Bonus por posición (preferir números cerca del final del ticket)
                    if i > len(lines) * 0.7:  # En el último tercio
                        score += 2
                        
                    # Bonus por palabras clave cercanas
                    contexto = ' '.join(lines[max(0, i-2):min(len(lines), i+3)])
                    if 'TOTAL' in contexto:
                        score += 3
                    if 'PAGAR' in contexto or 'VENTA' in contexto:
                        score += 2
                        
                    # Penalización por números muy pequeños
                    if numero < 1:
                        score -= 5
                    
                    candidatos.append((numero, score))
                except:
                    continue
    
    # Si encontramos candidatos, retornar el de mayor score
    if candidatos:
        # Ordenar por score y seleccionar el mejor candidato
        candidatos.sort(key=lambda x: x[1], reverse=True)
        return candidatos[0][0]
    
    return None

def extraer_proveedor(texto):
    lines = texto.split('\n')
    proveedor = None
    
    # Lista de palabras clave que suelen aparecer en los nombres de negocios
    keywords = ['S.A.', 'S.A. DE C.V.', 'SA DE CV', 'NUEVA', 'RESTAURANTES', 'MATERIAS']
    
    # Buscar en las primeras líneas (normalmente el nombre está al principio)
    for i in range(min(5, len(lines))):
        line = lines[i].strip()
        if any(keyword in line.upper() for keyword in keywords):
            proveedor = line
            break
        # Si la línea parece un nombre de negocio (más de 3 palabras)
        elif len(line.split()) >= 3 and line.isupper():
            proveedor = line
            break
    
    return proveedor

def procesar_imagen_ticket(image_path):
    try:
        # Abrir y procesar la imagen
        img = Image.open(image_path)
        # Convertir a escala de grises
        img = img.convert('L')
        # Usar pytesseract para extraer el texto
        texto = pytesseract.image_to_string(img)
        
        # Extraer información relevante
        fecha = extraer_fecha(texto)
        total = extraer_total(texto)
        proveedor = extraer_proveedor(texto)
        
        return {
            'success': True,
            'fecha': fecha.strftime('%d/%m/%Y') if fecha else None,
            'total': total,
            'proveedor': proveedor,
            'texto_completo': texto
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


@app.route('/procesar-ticket', methods=['POST'])
def procesar_ticket():
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401

    if 'ticket' not in request.files:
        return jsonify({'error': 'No se proporcionó ningún archivo'}), 400

    file = request.files['ticket']
    if file.filename == '':
        return jsonify({'error': 'No se seleccionó ningún archivo'}), 400

    if file and allowed_file(file.filename):
        try:
            orig_name = secure_filename(file.filename)
            base, ext = os.path.splitext(orig_name)
            filename = f"{base}_{int(datetime.now().timestamp())}{ext}"
            save_path = os.path.join(TICKETS_FOLDER, filename)
            file.save(save_path)

            # Procesar la imagen y crear metadata provisional (no guardado hasta confirmar)
            resultado = procesar_imagen_ticket(save_path)
            meta = load_metadata()
            meta_entry = {
                'fecha': resultado.get('fecha'),
                'total': resultado.get('total'),
                'proveedor': resultado.get('proveedor'),
                'texto_completo': resultado.get('texto_completo'),
                'created_at': datetime.now().isoformat(),
                'saved': False
            }
            meta[filename] = meta_entry
            save_metadata(meta)

            if resultado.get('success'):
                return jsonify({
                    'success': True,
                    'fecha': resultado.get('fecha'),
                    'total': resultado.get('total'),
                    'proveedor': resultado.get('proveedor'),
                    'texto_completo': resultado.get('texto_completo'),
                    'filename': filename
                }), 200
            else:
                print('Error al procesar imagen:', resultado.get('error'))
                return jsonify({'error': 'Error al procesar el ticket: ' + (resultado.get('error') or 'error desconocido')}), 500

        except Exception as e:
            print('Excepción en /procesar-ticket:', str(e))
            traceback.print_exc()
            return jsonify({'error': 'Error interno del servidor al procesar el ticket.'}), 500

    return jsonify({'error': 'Tipo de archivo no permitido'}), 400

@app.route('/escanear-tickets')
def escanear_tickets():
    # Verificar si el usuario está logueado
    if 'usuario_id' not in session:
        return redirect('/')
    return render_template('escanear-ticket.html')
@app.route('/mis-tickets')
def mis_tickets():
    # Página de galería: solo listar tickets que hayan sido confirmados (saved=True)
    if 'usuario_id' not in session:
        return redirect('/')

    items = []
    meta = load_metadata()
    try:
        entries = []
        for fname, m in meta.items():
            if not allowed_file(fname):
                continue
            if m.get('saved'):
                created = m.get('created_at') or ''
                entries.append((created, fname))
        entries.sort(reverse=True)
        for _created, fname in entries:
            m = meta.get(fname, {})
            items.append({
                'filename': fname,
                'fecha': m.get('fecha'),
                'total': m.get('total'),
                'proveedor': m.get('proveedor')
            })
    except Exception as e:
        print('Error listando tickets:', str(e))

    return render_template('mis-tickets.html', items=items)


@app.route('/mis-negocios')
def mis_negocios():
    # Verificar si el usuario está logueado
    if 'usuario_id' not in session:
        return redirect('/')
    # Por ahora redirigir al dashboard hasta que se cree el HTML
    return redirect('/dashboard')




@app.route('/mis-tickets/update', methods=['POST'])
def mis_tickets_update():
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
        
    data = request.get_json() or {}
    filename = data.get('filename')
    if not filename:
        return jsonify({'error': 'Falta filename'}), 400
        
    # Validar fecha (debe ser DD/MM/YYYY)
    fecha = data.get('fecha', '').strip()
    if fecha:
        try:
            fecha_obj = parser.parse(fecha, dayfirst=True)
            fecha = fecha_obj.strftime('%d/%m/%Y')
        except:
            return jsonify({'error': 'Formato de fecha inválido. Use DD/MM/YYYY'}), 400
            
    # Validar total (debe ser un número)
    total = data.get('total', '').strip()
    if total:
        try:
            total = float(total.replace('$', '').replace(',', '').strip())
        except:
            return jsonify({'error': 'Total debe ser un número válido'}), 400
    else:
        total = None

    # Actualizar metadata
    try:
        meta = load_metadata()
        safe_name = secure_filename(filename)
        
        if safe_name not in meta:
            return jsonify({'error': 'Ticket no encontrado'}), 404
            
        # Actualizar campos
        entry = meta[safe_name]
        if fecha:
            entry['fecha'] = fecha
        if total is not None:
            entry['total'] = total
        if 'proveedor' in data:
            entry['proveedor'] = data['proveedor'].strip() if data['proveedor'] else None
            
        # Guardar cambios
        save_metadata(meta)
        
        return jsonify({'mensaje': 'Ticket actualizado correctamente'}), 200
    except Exception as e:
        print('Error actualizando metadata:', str(e))
        return jsonify({'error': 'Error interno al actualizar'}), 500

@app.route('/mis-tickets/delete', methods=['POST'])
def mis_tickets_delete():
    if 'usuario_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401

    data = request.get_json() or {}
    filename = data.get('filename')
    if not filename:
        return jsonify({'error': 'Falta filename'}), 400

    # Normalizar y validar path
    safe_name = secure_filename(filename)
    file_path = os.path.join(TICKETS_FOLDER, safe_name)
    # Evitar romper fuera del directorio
    if not os.path.commonpath([os.path.abspath(file_path), os.path.abspath(TICKETS_FOLDER)]) == os.path.abspath(TICKETS_FOLDER):
        return jsonify({'error': 'Nombre de archivo inválido'}), 400

    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            # eliminar metadata si existe
            meta = load_metadata()
            if safe_name in meta:
                meta.pop(safe_name, None)
                save_metadata(meta)
            return jsonify({'mensaje': 'Archivo eliminado'}), 200
        except Exception as e:
            print('Error eliminando archivo:', str(e))
            return jsonify({'error': 'No se pudo eliminar el archivo'}), 500

    return jsonify({'error': 'Archivo no encontrado'}), 404

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
        # intentar parse flexible de fecha (acepta dd/mm/yyyy o dd/mm/yy etc.)
        try:
            if fecha_str:
                fecha_obj = parser.parse(fecha_str, dayfirst=True)
            else:
                fecha_obj = datetime.now()
        except Exception:
            fecha_obj = datetime.now()

        # 4. Parsear números
        def parse_number(s):
            if s is None:
                return None
            s = str(s).strip()
            if s == '':
                return None
            # eliminar símbolos de moneda y espacios
            s = s.replace('$', '').replace(' ', '')
            # Si tiene punto y coma o múltiples comas, normalizar
            # Caso: '1.250,50' (coma decimal) -> convertir a '1250.50'
            if s.count(',') > 0 and s.count('.') > 0:
                # asumir '.' separador de miles, ',' decimal
                s = s.replace('.', '').replace(',', '.')
            elif s.count(',') > 0 and s.count('.') == 0:
                # '1234,56' -> '1234.56'
                s = s.replace(',', '.')
            else:
                # quitar separadores de miles si existen
                s = s.replace(',', '')
            try:
                return float(s)
            except:
                return None

        total_n = parse_number(monto_total) or 0
        subtotal_n = parse_number(subtotal)
        iva_n = parse_number(iva)

        if total_n is None:
            return jsonify({'error': 'Valores numéricos inválidos (monto)'}), 400

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

        # Si se proporcionó un ticket_filename, actualizar metadata y marcar guardado
        ticket_filename = f.get('ticket_filename')
        if ticket_filename:
            try:
                meta = load_metadata()
                safe = secure_filename(ticket_filename)
                entry = meta.get(safe, {})
                # Actualizar con valores confirmados por el usuario
                entry['fecha'] = fecha_obj.strftime('%d/%m/%Y') if fecha_obj else entry.get('fecha')
                entry['total'] = total_n
                entry['proveedor'] = descripcion or entry.get('proveedor')
                entry['saved'] = True
                entry['linked_movimiento_id'] = movimiento_id
                meta[safe] = entry
                save_metadata(meta)
            except Exception as e:
                print('Error actualizando metadata en guardar_movimiento:', str(e))

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
