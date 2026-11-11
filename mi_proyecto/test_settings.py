"""
Configuración optimizada para ejecución de pruebas automatizadas (Testing CI/CD).
Utiliza SQLite en memoria para máxima velocidad de ejecución y aislamiento
de base de datos según estándares ISO/IEC 25010 y buenas prácticas de testing.
"""

from .settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

ALLOWED_HOSTS = ['*']

# Hashers acelerados para testing rápido de contraseñas
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]
