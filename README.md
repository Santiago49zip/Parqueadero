# Parqueadero

Aplicación Flask + SQLite para gestión de parqueadero.

## Requisitos
- Python 3.10+ (preferible 3.11)
- Crear y activar un entorno virtual

## Instalación rápida
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

## Ejecutar la aplicación
```powershell
python -m backend.app
# La app quedará en http://127.0.0.1:5000
```

## Endpoints principales
- `GET /` : interfaz web (frontend)
- `GET /resumen` : devuelve JSON con totales: `total_propietarios`, `total_vehiculos`, `deudores`, `aldia`
- `GET /buscar?tipo=placa|persona|deudores|aldia&query=...` : búsqueda
- `GET /propietarios` : lista propietarios
- `GET /vehiculos` : lista vehículos
- `GET /vehiculo/<placa>` : buscar vehículo por placa
- `GET /propietario/<id>` : buscar propietario por id
- `GET /pagos/<id_propietario>` : obtener pagos de un propietario
- `POST /registrar_pago` : registrar un pago (JSON con `id_propietario`, `id_vehiculo`, `monto`, `metodo`, `fecha_pago_esperado`, `pagado`)
- `GET /whatsapp/<id_propietario>` : genera enlace de WhatsApp

## Scripts de base de datos
- `BD/Crear_tablas.py` : crea las tablas en `backend/parqueadero.db`.
- `BD/Cargar_excel.py` : carga datos desde `Data/Parqueadero.xlsx` a `backend/parqueadero.db`.
- `BD/Updates.py` : script de inserciones/actualizaciones de ejemplo.

Usar:
```powershell
python BD/Crear_tablas.py
python BD/Cargar_excel.py
python BD/Updates.py
```

## Notas
- La base de datos central es `backend/parqueadero.db` y es la que usa la aplicación.
- Asegúrate de incluir `Data/Parqueadero.xlsx` si usas `BD/Cargar_excel.py`.

## Desarrollo
- Frontend está en `frontend/` (templates, static). El servidor sirve `index.html`.
- Para probar endpoints rápidamente desde PowerShell:
```powershell
(Invoke-RestMethod -Uri 'http://127.0.0.1:5000/resumen' -Method Get) | ConvertTo-Json -Depth 5
```

## Docker

Este proyecto incluye `Dockerfile` y `docker-compose.yml`.

Para construir y ejecutar localmente:
```bash
docker compose up --build
```

La aplicación quedará disponible en:
http://127.0.0.1:5000

> Si quieres que la base de datos se conserve entre ejecuciones, `docker-compose.yml` ya monta `./backend/parqueadero.db`.

## Inicialización automática

Usa los scripts `init.sh` (Linux/macOS) o `init.ps1` (Windows PowerShell) para crear el entorno, instalar dependencias y generar la base de datos.

Linux/macOS:
```bash
./init.sh
```

Windows PowerShell:
```powershell
.\.\init.ps1
```

## Despliegue continuo con GitHub Actions

Se ha añadido un workflow de GitHub Actions que construye y publica la imagen Docker a GitHub Container Registry cuando se hace push a `master`.

Para que funcione, solo necesitas habilitar GitHub Packages (GHCR) en tu repositorio; `GITHUB_TOKEN` ya está disponible automáticamente.

Si deseas desplegar directamente en un servidor Ubuntu desde el contenedor, te puedo ayudar con los pasos de `docker pull` y `docker compose up -d`.
