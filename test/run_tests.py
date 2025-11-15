"""
Script para ejecutar todas las pruebas del sistema
"""
import pytest
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_all_tests():
    """Ejecuta todos los tests con configuración detallada"""
    print("=" * 80)
    print("EJECUTANDO SUITE COMPLETA DE PRUEBAS - SISTEMA DE INVENTARIO")
    print("=" * 80)
    print()
    
    # Configuración de pytest
    args = [
        "test/",  # Directorio de tests
        "-v",  # Verbose
        "--tb=short",  # Traceback corto
        "--color=yes",  # Colores
        "-s",  # Mostrar prints
        "--maxfail=5",  # Detener después de 5 fallos
    ]
    
    # Ejecutar pytest
    exit_code = pytest.main(args)
    
    print()
    print("=" * 80)
    if exit_code == 0:
        print("✅ TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
    else:
        print("❌ ALGUNAS PRUEBAS FALLARON")
    print("=" * 80)
    
    return exit_code


def run_auth_tests():
    """Ejecuta solo los tests de autenticación"""
    print("Ejecutando tests de autenticación...")
    return pytest.main([
        "test/test_auth.py",
        "-v",
        "--tb=short",
        "-s"
    ])


def run_database_tests():
    """Ejecuta solo los tests de base de datos"""
    print("Ejecutando tests de base de datos...")
    return pytest.main([
        "test/test_database.py",
        "-v",
        "--tb=short",
        "-s"
    ])


def run_endpoint_tests():
    """Ejecuta solo los tests de endpoints"""
    print("Ejecutando tests de endpoints...")
    return pytest.main([
        "test/test_endpoints.py",
        "-v",
        "--tb=short",
        "-s"
    ])


def run_with_coverage():
    """Ejecuta tests con reporte de cobertura"""
    print("Ejecutando tests con reporte de cobertura...")
    return pytest.main([
        "test/",
        "-v",
        "--tb=short",
        "--cov=app",
        "--cov-report=html",
        "--cov-report=term"
    ])


if __name__ == "__main__":
    # Si se pasa un argumento, ejecutar ese grupo específico
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
        
        if test_type == "auth":
            sys.exit(run_auth_tests())
        elif test_type == "database" or test_type == "db":
            sys.exit(run_database_tests())
        elif test_type == "endpoints" or test_type == "api":
            sys.exit(run_endpoint_tests())
        elif test_type == "coverage" or test_type == "cov":
            sys.exit(run_with_coverage())
        else:
            print(f"Tipo de test desconocido: {test_type}")
            print("Opciones: auth, database, endpoints, coverage")
            sys.exit(1)
    else:
        # Ejecutar todos los tests
        sys.exit(run_all_tests())
