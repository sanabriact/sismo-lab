# SismoLab AVL

Sistema interactivo para simular y analizar eventos sísmicos con árboles AVL y BST. Permite cargar escenarios, visualizar eventos en un mapa, recibir reportes por cola, corregir eventos por revisiones, explorar asociaciones, archivar eventos, auditar la estructura y operar en modo normal o estrés.

## Funcionalidades principales

- Gestión de escenarios, estaciones, zonas y eventos sísmicos.
- Árbol AVL como estructura principal y BST para comparación visual.
- Priorización de eventos a partir de magnitud, profundidad y zona poblada.
- Procesamiento de reportes por una cola FIFO, con revisiones, confirmaciones, conflictos y reportes antiguos.
- Asociaciones entre eventos según tiempo, distancia y política de selección.
- Modo estrés sin balanceo inmediato y recuperación posterior del AVL.
- Auditoría estructural, métricas, histórico, archivo de ramas y deshacer acciones.
- Importación y exportación de escenarios JSON.

## Requisitos

- Python 3.10 o posterior.
- Node.js 20 o posterior y npm (o pnpm).
- Git para clonar el repositorio.

## Instalación

### Backend

Desde la raíz del repositorio, crea y activa un entorno virtual e instala las dependencias:

**Windows PowerShell**
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r backend/requirements.txt
```

**macOS / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
```

La generación asistida por Groq es opcional. Para habilitarla, crea `backend/.env` con las claves que usan los dos clientes:

```dotenv
GROQ_API_KEY_SCENARIO=tu_clave_para_escenarios
GROQ_API_KEY_REPORTS=tu_clave_para_reportes
GROQ_MODEL=nombre_del_modelo
```

Las funciones principales de carga, edición y visualización no requieren configurar esa integración.

### Frontend

En una segunda terminal, desde la raíz del proyecto:

```bash
cd frontend
npm install
```

El repositorio incluye `package-lock.json`; también puede usarse `npm ci` para instalar las versiones fijadas en ese archivo. Alternativamente, el proyecto incluye un lockfile de pnpm.

## Ejecución

Inicia el backend desde la raíz del repositorio con el entorno virtual activo:

```bash
python -m backend.app
```

Inicia el frontend en otra terminal:

```bash
cd frontend
npm run dev
```

Abre en el navegador la dirección que Vite muestra en la terminal (normalmente <http://localhost:5173>). El backend Flask-SocketIO se inicia en el puerto 5000. Mantén ambos procesos en ejecución mientras uses la aplicación.


## Estructura del proyecto

- `backend/models`: modelos de eventos, escenarios, reloj, métricas e histórico.
- `backend/structures`: implementaciones de AVL, BST, cola, pila y nodos.
- `backend/managers`: carga de escenarios, asociaciones, parámetros y modo estrés.
- `backend/services`: reglas de negocio, auditoría, reportes, persistencia y consultas.
- `backend/repositories`: acceso a datos JSON.
- `backend/tests`: pruebas automatizadas del backend.
- `frontend/src`: interfaz React y TypeScript.

## Persistencia de datos

El estado operativo se guarda en `backend/data/seismic_observatory.json`. Conserva una copia antes de reemplazarlo si necesitas mantener datos locales. Los escenarios que se carguen o exporten se gestionan como archivos JSON desde la aplicación.

## Notas de desarrollo

- Ejecuta los comandos de Python desde la raíz para que los imports del paquete `backend` se resuelvan correctamente.
- La cola procesa un reporte por paso o de forma continua; las acciones disponibles dependen del escenario cargado.
- Usa la vista de auditoría para revisar orden global, alturas, factores de balance y consistencia del índice.
