# controladores/foto_perfil.py
import os
from datetime import datetime
from flask import Blueprint, request, redirect, url_for, flash, session, current_app
from PIL import Image
from bd import obtener_conexion
import pymysql

perfil_bp = Blueprint("perfil", __name__)

def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'webp'}

def _unique_name(user_id, ext):
    ts = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    return f"user_{user_id}_{ts}.{ext}"

@perfil_bp.post("/usuario/perfil/foto")
def actualizar_foto_perfil():
    if 'user_id' not in session:
        flash("Inicia sesión para cambiar tu foto.", "error")
        return redirect(url_for('auth_page'))

    file = request.files.get('foto')
    if not file or file.filename == '':
        flash("No seleccionaste ninguna imagen.", "error")
        return redirect(url_for('usuario_perfil'))

    if not _allowed_file(file.filename):
        flash("Formato no permitido. Usa JPG, JPEG, PNG o WEBP.", "error")
        return redirect(url_for('usuario_perfil'))

    # 1) Procesar/guardar imagen normalizada a JPG 256x256
    try:
        img = Image.open(file.stream); img.verify()
        file.stream.seek(0)
        img = Image.open(file.stream).convert("RGB")
        w, h = img.size; s = min(w, h)
        left, top = (w - s)//2, (h - s)//2
        img = img.crop((left, top, left + s, top + s)).resize((256, 256))

        filename = _unique_name(session['user_id'], "jpg")
        upload_folder = os.path.join(current_app.root_path, 'static', 'img', 'usuario')
        os.makedirs(upload_folder, exist_ok=True)
        img.save(os.path.join(upload_folder, filename), format="JPEG", quality=88)
    except Exception:
        flash("La imagen está corrupta o no es válida.", "error")
        return redirect(url_for('usuario_perfil'))

    # 2) BD: borrar anterior (si existe) y actualizar ruta
    try:
        conn = obtener_conexion()
        cur  = conn.cursor(pymysql.cursors.DictCursor)

        cur.execute("SELECT foto FROM USUARIO WHERE id_usuario=%s", (session['user_id'],))
        row = cur.fetchone()
        old_rel = row.get('foto') if row else None

        if old_rel:
            try:
                old_path = os.path.join(current_app.root_path, 'static', old_rel.lstrip('/'))
                if os.path.isfile(old_path):
                    os.remove(old_path)
            except Exception:
                pass

        rel_path = f"img/usuario/{filename}"
        cur.execute("UPDATE USUARIO SET foto=%s WHERE id_usuario=%s", (rel_path, session['user_id']))
        conn.commit()
        cur.close(); conn.close()
    except Exception:
        flash("No se pudo actualizar la foto en la base de datos.", "error")
        return redirect(url_for('usuario_perfil'))

    flash("¡Tu foto de perfil fue actualizada!", "success")
    return redirect(url_for('usuario_perfil'))
