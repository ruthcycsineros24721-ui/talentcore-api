import time
import httpx

BASE_URL = "http://127.0.0.1:8000"


def imprimir_paso(titulo, estado, detalle=""):
    color = "\033[92m[EXITO]\033[0m" if estado else "\033[91m[FALLO]\033[0m"
    print(f"{color} {titulo}")
    if detalle:
        print(f"       -> {detalle}")


def ejecutar_auditoria():
    print("=" * 70)
    print("    INICIANDO BATERÍA DE PRUEBAS DINÁMICAS (CLIENTE HTTP)")
    print("=" * 70)

    with httpx.Client(base_url=BASE_URL, timeout=5.0) as client:
        # 1. Health Check
        r = client.get("/health")
        imprimir_paso("1. Verificación de servicio (/health)", r.status_code == 200, r.json())

        # 2. Crear Admin inicial (sin header)
        admin_data = {
            "nombre": "Super Admin",
            "email": f"admin_{int(time.time())}@corp.com",
            "rol": "ADMIN_RRHH",
            "anios_antiguedad": 5,
        }
        r = client.post("/api/v1/empleados", json=admin_data)
        admin_id = r.json().get("id")
        imprimir_paso(
            "2. Registro del primer Administrador",
            r.status_code == 201,
            f"Admin ID asignado: {admin_id}",
        )

        # 3. Crear Manager
        headers_admin = {"X-User-Id": str(admin_id)}
        manager_data = {
            "nombre": "Jefe de Operaciones",
            "email": f"jefe_{int(time.time())}@corp.com",
            "rol": "MANAGER",
            "anios_antiguedad": 4,
        }
        r = client.post("/api/v1/empleados", json=manager_data, headers=headers_admin)
        manager_id = r.json().get("id")
        imprimir_paso(
            "3. Registro de Manager",
            r.status_code == 201,
            f"Manager ID: {manager_id}",
        )

        # 4. Crear Empleado subordinado
        empleado_data = {
            "nombre": "Ana Desarrolladora",
            "email": f"ana_{int(time.time())}@corp.com",
            "rol": "EMPLEADO",
            "anios_antiguedad": 2,  # 12 + 2*(2-1) = 14 días
            "manager_id": manager_id,
        }
        r = client.post("/api/v1/empleados", json=empleado_data, headers=headers_admin)
        empleado_id = r.json().get("id")
        imprimir_paso(
            "4. Registro de Empleado (2 años antigüedad)",
            r.status_code == 201,
            f"Empleado ID: {empleado_id}",
        )

        # 5. Consultar saldo inicial
        r = client.get(f"/api/v1/vacaciones/saldo/{empleado_id}")
        saldo = r.json()
        imprimir_paso(
            "5. Verificación de cálculo legal (14 días)",
            saldo.get("saldo_disponible") == 14,
            saldo,
        )

        # 6. Intento de solicitud con exceso de días (debe fallar con 400)
        solicitud_exceso = {
            "empleado_id": empleado_id,
            "dias_solicitados": 15,
            "motivo": "Exceso",
        }
        r = client.post("/api/v1/vacaciones/solicitar", json=solicitud_exceso)
        imprimir_paso(
            "6. Intento de pedir 15 días (Excede saldo)",
            r.status_code == 400,
            r.json(),
        )

        # 7. Solicitud válida de 4 días
        solicitud_valida = {
            "empleado_id": empleado_id,
            "dias_solicitados": 4,
            "motivo": "Viaje corto",
        }
        r = client.post("/api/v1/vacaciones/solicitar", json=solicitud_valida)
        solicitud_id = r.json().get("id")
        imprimir_paso(
            "7. Solicitud válida de 4 días (PENDING)",
            r.status_code == 201,
            f"Solicitud ID: {solicitud_id}",
        )

        # 8. Intento de aprobación por usurpador (debe fallar con 403)
        headers_usurpador = {"X-User-Id": "999"}
        r = client.post(
            f"/api/v1/vacaciones/{solicitud_id}/revisar",
            json={"accion": "APPROVE"},
            headers=headers_usurpador,
        )
        imprimir_paso(
            "8. Seguridad BOLA: Intento de aprobación por usuario no autorizado",
            r.status_code in (403, 404),
            r.json(),
        )

        # 9. Aprobación oficial por el jefe directo
        headers_manager = {"X-User-Id": str(manager_id)}
        r = client.post(
            f"/api/v1/vacaciones/{solicitud_id}/revisar",
            json={"accion": "APPROVE"},
            headers=headers_manager,
        )
        imprimir_paso(
            "9. Aprobación oficial por su Manager directo",
            r.status_code == 200,
            r.json(),
        )

        # 10. Saldo final descontado
        r = client.get(f"/api/v1/vacaciones/saldo/{empleado_id}")
        saldo_final = r.json()
        imprimir_paso(
            "10. Balance final de vacaciones (14 - 4 = 10 días)",
            saldo_final.get("saldo_disponible") == 10,
            saldo_final,
        )

        print("=" * 70)
        print("    BATERÍA DE PRUEBAS COMPLETADA EXITOSAMENTE")
        print("=" * 70)


if __name__ == "__main__":
    try:
        ejecutar_auditoria()
    except Exception as e:
        print(
            f"\n[ERROR] No se pudo conectar al servidor. ¿Olvidaste levantar Uvicorn? Error: {e}"
        )