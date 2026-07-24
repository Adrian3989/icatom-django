# 🍅 ICATOM — Sistema de Diagnóstico Fitosanitario Inteligente

Sistema web que utiliza Inteligencia Artificial para el diagnóstico automatizado de enfermedades en cultivos de tomate, desarrollado para la empresa agroindustrial **ICATOM S.A.** (Ica, Perú).

🌐 **Demo en vivo:** [icatom-diagnostico.onrender.com](https://icatom-diagnostico.onrender.com)
📄 **Documentación de la API:** `/api/docs/`

---

## 📖 Descripción

El proceso tradicional de detección de enfermedades en cultivos depende del criterio visual y la disponibilidad de un ingeniero agrónomo, lo que puede demorar hasta **24 horas** entre la detección de síntomas y la obtención de un diagnóstico. Este sistema reduce ese tiempo a **segundos**, permitiendo que cualquier trabajador de campo fotografíe una planta afectada desde su celular y obtenga un diagnóstico automatizado impulsado por IA, junto con recomendaciones de tratamiento.

---

## ✨ Características principales

- 🔐 **Autenticación por roles** — Trabajador de campo, Ingeniero agrónomo y Administrador
- 📸 **Diagnóstico con IA** — Análisis de imágenes mediante la API de **Google Gemini**
- 📊 **Historial centralizado** — Consulta con filtros por fecha, sector y enfermedad
- 📈 **Panel de reportes** — Estadísticas e indicadores por sector y periodo
- 📄 **Exportación de datos** — Descarga de reportes en PDF y Excel
- 🌐 **API REST documentada** — Especificación OpenAPI/Swagger autogenerada

---

## 🏗️ Arquitectura

El sistema está diseñado bajo principios **SOA**, organizado en cuatro servicios independientes con responsabilidades bien definidas:

| Servicio | Responsabilidad |
|---|---|
| 🔑 **Autenticación** | Validación de credenciales y control de acceso por rol |
| 🩺 **Diagnóstico** | Recepción de imágenes, orquestación con la API de IA y generación del resultado |
| 🗂️ **Historial** | Registro y consulta de diagnósticos realizados |
| 📊 **Reportes** | Generación de estadísticas e indicadores agregados |

```
Navegador ──HTTP──> Django (Servicios internos) ──HTTPS/JSON──> API de Gemini (Google)
                          │
                          └──> PostgreSQL (persistencia)
```

La arquitectura sigue un patrón de **capas** (Presentación → Servicios → Integración → Datos), con bajo acoplamiento entre componentes: el servicio de Diagnóstico podría cambiar de proveedor de IA sin afectar al resto del sistema.

---

## 🛠️ Stack tecnológico

**Backend**
- 🐍 Python 3.13
- 🎯 Django 4.2 + Django REST Framework
- 🤖 Google Gemini API (`google-genai`)
- 🐘 PostgreSQL (producción) / SQLite (desarrollo)

**Documentación de API**
- 📘 drf-spectacular (OpenAPI / Swagger)

**Utilidades**
- 🖼️ Pillow — procesamiento de imágenes
- 📄 ReportLab — generación de PDF
- 📊 openpyxl — generación de Excel

**Despliegue**
- ☁️ Render (hosting)
- 🦄 Gunicorn — servidor WSGI de producción
- ⚡ WhiteNoise — servido de archivos estáticos

**Frontend**
- 🎨 Bootstrap 5

---

## 🚀 Instalación local

```bash
# 1. Clonar el repositorio
git clone https://github.com/Adrian3989/icatom-django.git
cd icatom-django

# 2. Crear y activar entorno virtual
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux / macOS

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno (crear archivo .env)
SECRET_KEY=tu-clave-secreta
DEBUG=True
GEMINI_API_KEY=tu-api-key-de-gemini

# 5. Aplicar migraciones
python manage.py migrate

# 6. Crear superusuario
python manage.py createsuperuser

# 7. Ejecutar servidor de desarrollo
python manage.py runserver
```

El sistema quedará disponible en `http://127.0.0.1:8000` 🎉

---

## 📁 Estructura del proyecto

```
icatom/
├── icatom/              # Configuración del proyecto (settings, urls)
├── diagnostico/         # App principal
│   ├── models.py        # Usuario, Sector, Enfermedad, Diagnostico
│   ├── views.py         # Lógica de los 4 servicios
│   ├── gemini_service.py # Integración con la API de IA
│   ├── pdf_service.py
│   └── excel_service.py
├── templates/            # Interfaz web (HTML + Bootstrap)
├── static/
├── media/                # Imágenes subidas por los usuarios
└── requirements.txt
```

---

## 🔌 Endpoints principales

| Método | Endpoint | Descripción |
|---|---|---|
| `POST` | `/api/diagnostico/` | Envía una imagen y recibe el diagnóstico generado por IA |
| `GET` | `/api/historial/` | Lista los diagnósticos registrados, con filtros opcionales |
| `GET` | `/api/docs/` | Documentación interactiva Swagger UI |

📘 La especificación completa (OpenAPI 3.0) puede consultarse en `/api/docs/`.

---

## 👥 Roles del sistema

| Rol | Permisos |
|---|---|
| 🧑‍🌾 **Trabajador de campo** | Registrar diagnósticos y ver su propio historial |
| 👨‍🔬 **Ingeniero agrónomo** | Registrar diagnósticos, consultar historial completo |
| 🛠️ **Administrador** | Gestión de usuarios, acceso a reportes y estadísticas |

---

## ⚠️ Limitaciones conocidas

- El almacenamiento de imágenes en el entorno de despliegue gratuito es **efímero** — se recomienda migrar a un servicio externo (ej. Cloudinary) para persistencia real en producción.
- El diagnóstico se apoya en un modelo de IA de propósito general (Gemini), no entrenado específicamente para fitopatología del tomate — se recomienda como validación adicional el criterio de un ingeniero agrónomo certificado.


## 📝 Licencia

Proyecto desarrollado con fines académicos.
