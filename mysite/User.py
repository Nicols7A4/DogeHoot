from controladores import usuarios

class User(object):
    def __init__(self, id, correo, password):
        self.id = id
        self.correo = correo
        self.password = password

    def __str__(self):
        return "User(id='%s')" % self.id

def authenticate(username, password):
    usuario = usuarios.obtener_por_correo(username)
    user = None
    if usuario:
        user = User(usuario[0], usuario[1], usuario[2])
    if user and user.password.encode('utf-8') == password.encode('utf-8'):
        return user

def identity(payload):
    user_id = payload['identity']
    usuario = usuarios.obtener_por_id(user_id)
    user = None
    if usuario:
        user = User(usuario[0], usuario[3], usuario[4])
    return user