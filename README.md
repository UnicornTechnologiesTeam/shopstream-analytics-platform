     ___        ______     ____ _                 _  ___  
    / \ \      / / ___|   / ___| | ___  _   _  __| |/ _ \ 
   / _ \ \ /\ / /\___ \  | |   | |/ _ \| | | |/ _` | (_) |
  / ___ \ V  V /  ___) | | |___| | (_) | |_| | (_| |\__, |
 /_/   \_\_/\_/  |____/   \____|_|\___/ \__,_|\__,_|  /_/ 



# 📊 ShopStream Analytics Platform

### Pipeline de Analítica de Comportamiento de Usuario en AWS

Plataforma de ingeniería de datos construida sobre AWS que procesa logs de comportamiento de usuarios de un e-commerce ficticio (ShopStream), calcula métricas de experiencia de usuario con PySpark, y expone indicadores clave a través de una API REST serverless.

---

## 🏗️ Arquitectura

```
S3 (raw/)
    │
    ▼ [S3 PutObject Event]
Lambda (validación de esquema)
    │
    ├── ✅ Válidos → permanecen en raw/
    └── ❌ Inválidos → quarantine/
    
    [Glue Workflow — 2:00 AM UTC]
    │
    ▼
EMR + PySpark (transformación)
    │
    ▼
S3 (processed/ — Parquet)
    │
    ▼
Glue ETL Visual (S3 → RDS)
    │
    ▼
RDS PostgreSQL (Data Warehouse)
    │
    ▼
API REST Lambda + Zappa + API Gateway
```

---

## ☁️ Infraestructura AWS

| Recurso | Servicio | Detalle |
|---|---|---|
| Almacenamiento raw | S3 | `shopstream-raw-data-dg` — particionado por year/month/day |
| Validación | Lambda | `shopstream-validate-ingesta` — trigger S3 PutObject |
| Monitoreo | CloudWatch | Namespace `ShopStream/Ingesta` |
| Transformación | EMR + PySpark | Spark 3.3.0 — cluster m5.xlarge |
| Orquestación | Glue Workflows | Schedule diario 2:00 AM UTC |
| ETL Visual | Glue Studio | S3 → Change Schema → Data Quality → PostgreSQL |
| Data Warehouse | RDS PostgreSQL | `shopstream-dw` — base de datos `shopstream_dw` |
| API | Lambda + Zappa | `environment-dev` — API Gateway REST |
| Alertas | SNS + CloudWatch Events | Notificación por email si ETL falla |

---

## 🗂️ Modelo de Datos

### Eventos (S3 — JSON gzip)

| Evento | Campos principales |
|---|---|
| `page_view` | user_id, session_id, page_url, page_type, timestamp, time_on_page_seconds, device_type, country |
| `click` | user_id, session_id, element_id, element_type, page_url, timestamp, x_position, y_position |
| `search` | user_id, session_id, query, results_count, timestamp |
| `product_view` | user_id, session_id, product_id, category, price, timestamp, time_on_page_seconds |
| `cart_event` | user_id, session_id, product_id, action (add/remove), timestamp |

### Data Warehouse (RDS PostgreSQL)

| Tabla | Descripción |
|---|---|
| `top_pages` | Top 20 páginas por tiempo de permanencia promedio |
| `bounce_rate` | Tasa de rebote por tipo de página |
| `funnel` | Embudo de conversión page_view → product_view → cart_event |
| `product_conversion` | Productos con alta vista pero baja conversión al carrito |
| `device_country` | Tiempo promedio por dispositivo y país |
| `anomalies` | Sesiones anómalas detectadas por Z-score > 3 |

---

## 📈 Métricas Calculadas con PySpark

- **Top 20 páginas** con mayor tiempo de permanencia promedio
- **Tasa de rebote** por tipo de página (home, categoría, producto, carrito)
- **Embudo de conversión**: page_view → product_view → cart_event
- **Productos** con alta vista pero baja conversión al carrito
- **Top 10 rutas de navegación** más frecuentes por sesión
- **Tiempo promedio** por tipo de dispositivo (mobile/desktop/tablet) y país
- **Detección de anomalías** usando Z-score con umbral > 3 (14,535 detectadas)

---

## 🔌 API REST

**URL Base:** `https://k0fio5jyub.execute-api.us-east-1.amazonaws.com/dev`

Desplegada con **Zappa** en AWS Lambda + API Gateway.

### Endpoints

#### `GET /pages/top`
Retorna las páginas con mayor tasa de rebote o tiempo de permanencia.

```bash
# Por tiempo de permanencia
curl "https://k0fio5jyub.execute-api.us-east-1.amazonaws.com/dev/pages/top?metric=time_on_page&limit=5"

# Por tasa de rebote
curl "https://k0fio5jyub.execute-api.us-east-1.amazonaws.com/dev/pages/top?metric=bounce_rate&limit=5"
```

| Parámetro | Tipo | Descripción |
|---|---|---|
| `metric` | string | `time_on_page` o `bounce_rate` |
| `limit` | int | Número de resultados (default: 10) |

---

#### `GET /sessions/summary`
Resumen de sesiones filtrado por país y dispositivo.

```bash
curl "https://k0fio5jyub.execute-api.us-east-1.amazonaws.com/dev/sessions/summary?country=CO&device=mobile"
```

| Parámetro | Tipo | Descripción |
|---|---|---|
| `country` | string | Código de país (US, CO, BR, MX...) |
| `device` | string | `mobile`, `desktop` o `tablet` |

---

#### `GET /anomalies`
Lista de sesiones anómalas detectadas con su Z-score.

```bash
curl "https://k0fio5jyub.execute-api.us-east-1.amazonaws.com/dev/anomalies?date=2026-05-21"
```

| Parámetro | Tipo | Descripción |
|---|---|---|
| `date` | string | Fecha en formato YYYY-MM-DD |

---

## 🗃️ Estructura del Proyecto

```
shopstream-analytics-platform/
├── generate_data.py          # Generador de datos sintéticos (500,000 eventos/día)
├── lambda_function.py        # Validación de esquema — desplegada en Lambda
├── app.py                    # API REST Flask — desplegada con Zappa
├── etl_anomalies.py          # ETL de anomalías — job de Glue
├── zappa_settings.json       # Configuración de Zappa
├── tests/
│   ├── test_lambda.py        # 7 pruebas unitarias de validación
│   └── test_api.py           # 5 pruebas unitarias de API
└── .github/
    └── workflows/
        └── ci-cd.yml         # Pipeline CI/CD — test + deploy
```

---

## 🚀 Stack Tecnológico

**Ingesta y Validación**
- Python 3.9 + boto3
- AWS Lambda + S3 Events
- Amazon CloudWatch

**Transformación**
- Apache Spark 3.3.0 (PySpark)
- AWS EMR
- AWS Glue Studio (ETL Visual)

**Almacenamiento**
- Amazon S3 (datos raw y procesados en Parquet)
- Amazon RDS PostgreSQL 18 (data warehouse)

**API**
- Flask + Zappa
- AWS Lambda + API Gateway
- psycopg2

**CI/CD y Pruebas**
- GitHub Actions
- pytest (12 pruebas unitarias)

---

## ⚙️ Pipeline Automatizado

```
[2:00 AM UTC]
     │
     ▼
trigger-schedule-2am
     │
     ▼
shopstream-etl-top-pages  ──── FAILED ──→ SNS Alert (email)
     │
   SUCCEEDED
     │
     ▼
trigger-etl-succeeded
     │
     ▼
shopstream-etl-anomalies
```

---

## 🧪 Pruebas Unitarias

```bash
pytest tests/ -v
```

```
tests/test_api.py::test_pages_top_time        PASSED
tests/test_api.py::test_pages_top_bounce      PASSED
tests/test_api.py::test_sessions_summary      PASSED
tests/test_api.py::test_anomalies             PASSED
tests/test_api.py::test_anomalies_sin_fecha   PASSED
tests/test_lambda.py::test_page_view_valido   PASSED
tests/test_lambda.py::test_page_view_falta_campo PASSED
tests/test_lambda.py::test_event_type_desconocido PASSED
tests/test_lambda.py::test_timestamp_invalido PASSED
tests/test_lambda.py::test_cart_event_valido  PASSED
tests/test_lambda.py::test_product_view_valido PASSED
tests/test_lambda.py::test_click_valido       PASSED

12 passed in 0.79s
```

---

## 👥 Equipo

**UnicornTechnologiesTeam**
- Diego Alejandro Guevara Rodriguez
- unicorntechnologies.team@gmail.com

*Big Data e Ingeniería de Datos — 2026*
