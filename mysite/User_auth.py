from controladores import usuarios as cu

class User(object):
    def __init__(self, id, correo, password):
        self.id = id
        self.correo = correo
        self.password = password

    def __str__(self):
        return "User(id='%s')" % self.id

def authenticate(correo, password):
    usuario = cu.obtener_por_correo_auth(correo)
    
    if not usuario:
        return None
    
    user = User(usuario['id_usuario'], usuario['correo'], usuario['contraseña'])
    
    # Comparar contraseñas
    if user.password == password:
        return user
    
    return None

def identity(payload):
    user_id = payload['identity']
    
    usuario = cu.obtener_por_id_auth(user_id)
    
    if not usuario:
        return None
    
    user = User(usuario['id_usuario'], usuario['correo'], usuario['contraseña'])
    return user