import hashlib

def encriptar_sha256(texto):
    texto = texto.encode('utf-8')
    objHash = hashlib.sha256(texto)
    textenc = objHash.hexdigest()
    return textenc

print(encriptar_sha256('abcDEF$123'))