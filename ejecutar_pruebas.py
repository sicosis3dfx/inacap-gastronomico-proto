"""
Script interactivo para ejecutar la batería de pruebas de la Evaluación 4.
Uso directo en terminal:
    python ejecutar_pruebas.py
"""

import os
import sys
import time

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_proyecto.test_settings')
    
    import django
    django.setup()
    
    from django.core.management import call_command
    
    print("\n" + "=" * 76)
    print(" SISTEMA GASTRONOMICO INACAP RENCA — SUITE DE TESTING EVALUACION 4")
    print(" Verificando: Funcionalidad, OWASP Top 10, RBAC y Latencia ISO 25010 (<200ms)")
    print("=" * 76 + "\n")
    
    inicio = time.time()
    call_command('test', 'gastronomia', verbosity=2, settings='mi_proyecto.test_settings')
    duracion = time.time() - inicio
    
    print("\n" + "=" * 76)
    print(f" [OK] Bateria de pruebas finalizada exitosamente en {duracion:.2f} segundos.")
    print("=" * 76 + "\n")
