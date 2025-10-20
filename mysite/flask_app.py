
# Exponer el `app` principal para que `flask run` lo cargue.
# Evita que el CLI cree un segundo app que no tiene las rutas definidas en `main.py`.
from main import app  # importa y expone la instancia de Flask creada en main.py

__all__ = ["app"]

