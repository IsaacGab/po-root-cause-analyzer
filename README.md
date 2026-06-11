# Analizador de Causas Raíz en Retrasos de Órdenes de Compra

> **Proyecto MAS Mentor — IA en Cadena de Suministro**
> Herramienta basada en Inteligencia Artificial que analiza Órdenes de Compra (POs) retrasadas, identifica la etapa exacta del ciclo de vida donde ocurrió la demora, y genera explicaciones automatizadas junto con acciones recomendadas utilizando un Modelo de Lenguaje Grande (LLM).

---

## 1. Justificación del Proyecto

Los equipos de cadena de suministro (*supply chain*) revisan **cientos de Órdenes de Compra** de forma manual para identificar retrasos y sus causas. Este proceso actual es lento, inconsistente y propenso a errores humanos por las siguientes razones:

* Un solo PO puede retrasarse por **más de 5 causas distintas** (proveedor, transportista, centro de distribución o problemas de agenda).
* La causa real se encuentra oculta entre **múltiples marcas de tiempo (*timestamps*) del ciclo de vida**.
* El personal del Centro de Distribución (DC) registra los **códigos de motivo de forma manual**, lo que genera inconsistencias con los datos reales del sistema.
* No se generan **explicaciones claras y accionables** para mitigar cada caso.
* El equipo operativo carece de un criterio claro de **priorización** para resolver los casos más críticos primero.

Este proyecto desarrolla una solución que combina **reglas lógicas determinísticas con un LLM** para automatizar el análisis, validar las anotaciones del personal operativo y entregar recomendaciones específicas por cada orden de compra.

---

## 2. El Ciclo de Vida de una Orden de Compra (PO)

Cada Orden de Compra pasa por una serie de etapas secuenciales, registrando una marca de tiempo (*timestamp*) en cada evento:

```text
 Pedido     Fecha Límite    Cita en DC     Llegada de    Inicio de     Fin de       Recibo en
 Emitido     de Entrega Aprobada     Transporte    Andén (Check)  Andén (Out)    Inventario
 ───────     ────────────   ───────────     ──────────   ────────────  ───────────   ──────────
  PO_DT         STA_DT      APPROVED_DT   TRAILER_ARRIVE   CHECKIN       CHECKOUT     RECPT_DT
```

### Responsabilidades y Tipos de Retraso por Etapa

| Etapa | Rango de Timestamps | Responsable | Tipo de Retraso Típico |
| :--- | :--- | :--- | :--- |
| **PROVEEDOR** | `PO_DT → STA_DT` | Proveedor (*Vendor*) | Tiempo de entrega excedido, envío tardío. |
| **TRANSPORTISTA** | `APPROVED_DT → TRAILER_ARRIVE_DT` | Transportista (*Carrier*) | Arribo tardío del contenedor, incumplimiento del transportista. |
| **OPERACIÓN DC** | `TRAILER_ARRIVE → CHECKOUT` | Operaciones del DC | Saturación del patio (*yard congestion*), procesamiento lento en andenes. |
| **RECEPCIÓN** | `RECPT_DT` vs `STA_DT` | — | Veredicto analítico final: A tiempo / Retrasado. |

> **KPI Principal:** Si `RECPT_DT > STA_DT` $\rightarrow$ La Orden de Compra se considera oficialmente **retrasada**.

---

## 3. Estructura del Dataset

* **Archivo origen:** [`po_root_cause_synthetic.csv`](po_root_cause_synthetic.csv)
* **Contenido:** Tabla plana (pre-consolidada mediante *joins*) con **400 registros sintéticos de Órdenes de Compra** y **38 columnas** que abarcan datos del proveedor, centro de distribución, transportista, marcas de tiempo del ciclo de vida, cantidades, banderas de control (*flags*) y códigos de motivo.

### Distribución Estimada de Escenarios

| Escenario Operativo | Porcentaje Aprox. |
| :--- | :--- |
| A tiempo (Sin retraso) | ~30% |
| Retraso del Proveedor (Carga/envío tardío) | ~20% |
| Incumplimiento del Transportista (Llegada tardía del tráiler) | ~15% |
| Saturación en patio del Centro de Distribución | ~12% |
| Procesamiento lento en andén del Centro de Distribución | ~8% |
| Reprogramación de cita de entrega | ~15% |

### Problemas de Calidad de Datos Incluidos (Intencionales)
Como el primer paso de cualquier flujo de datos (*pipeline*) es la **limpieza de datos**, el dataset incorpora las siguientes anomalías para su resolución:
* ~10% de valores nulos en la columna `TRAILER_ARRIVE_DT`.
* ~5% de marcas de tiempo fuera de orden cronológico.
* ~20% de códigos de motivo erróneos (discrepancias entre el reporte manual del personal y lo registrado en los *timestamps*).

---

## 4. Lógica de Clasificación Basada en Reglas

### Etapa 1 — Pre-Arribo (Proveedor / Transportista)
* **STA Push (Retraso de Cita):** `APPROVED_DT > STA_DT`
* **Late Shipment (Envío Tardío):** `VENDOR_SHIP_DT > STA_DT`
* **Carrier Miss (Falla del Transportista):** `TRAILER_ARRIVE > APPROVED_DT + umbral_tolerancia`
* **Rescheduled (Reprogramado):** `DT_APPT_CURRENT_APPROVED != DT_APPT_FIRST_APPROVED`

### Etapa 2 — Operación en el Centro de Distribución (DC)
* **Saturación de Patio (Yard Congestion):** `CHECKIN_DT - TRAILER_ARRIVE > 4 horas`
* **Procesamiento Lento en Andén (Long Dock):** `CHECKOUT_DT - CHECKIN_DT > 6 horas`

### Reglas Transversales y Priorización
* **Recibo Tardío (Late Receipt):** `RECPT_DT > STA_DT` (Indicador clave).
* **Faltante de Mercancía (Short Ship):** `CASES_SHIPPED / CASES_ORDERED < 0.9`.
* **Prioridad Alta Retrasada (Hot PO Delayed):** `HOT_PO_FLAG = 1` asociado a cualquier tipo de retraso.
* **Tiempo de Espera Corto (Short Lead Time):** `STA_DT - PO_DT < 3 días`.

> **Nota de arquitectura:** Estas condiciones pueden superponerse; un PO puede presentar **múltiples causas de retraso de forma simultánea**.

---

## 5. Plantilla de Referencia para el Prompt del LLM

```text
### System
Eres un analista experto en cadena de suministro especializado en investigar retrasos de Órdenes de Compra.
Tu objetivo es explicar las causas raíz de forma clara y recomendar acciones operativas específicas.

### User
Analiza la siguiente Orden de Compra retrasada:

PO: {PO_NBR} | Proveedor: {VENDOR_NAME}
DC Destino: {DC_ID} | Transportista: {CARRIER_NAME}

Línea de Tiempo Registrada:
  Pedido Emitido:             {PO_DT}
  Fecha Límite (STA):         {STA_DT}
  Cita Aprobada:              {APPROVED_DT}
  Llegada del Transporte:     {TRAILER_ARRIVE_DT}
  Inicio de Andén (Check-In): {CHECKIN_DT}
  Fin de Andén (Check-Out):   {CHECKOUT_DT}
  Recibo en Inventario:       {RECPT_DT}

Métricas de Retraso Calculadas:
  Días de retraso al arribo:  {days_late} días
  Tiempo de espera en patio:  {yard_hours} horas
  Tiempo de procesamiento:     {dock_hours} horas
  Etapa crítica identificada: {STAGE}

Código de Motivo Manual (Personal del DC): {REASON_DSC}
Indicador de Urgencia (Hot PO): {HOT_PO_FLAG}
Porcentaje de Envío Incompleto: {short_ship_pct}%

Genera un output estructurado con:
  (1) Explicación de la causa raíz en 2-3 oraciones.
  (2) Acción recomendada específica para mitigar el problema.
  (3) Nivel de severidad: HIGH / MEDIUM / LOW.
```

### Directrices para la Salida del LLM
El modelo debe fundamentarse en los datos duros (*timestamps*) como única fuente de verdad:
1. Cuantificar el impacto temporal exacto (días u horas).
2. Contrastar y señalar si el código manual (`REASON_DSC`) fue acertado o erróneo.
3. Evaluar agravantes como alertas de urgencia (*Hot PO*) o faltantes de mercancía.
4. Asignar severidad **HIGH** si el PO es urgente y presenta retrasos considerables, **MEDIUM** para incidencias estándar y **LOW** para variaciones limítrofes.

---

## 6. Criterios de Evaluación del Proyecto

| Dimensión Analítica | Método de Medición | Umbral de Éxito | Tipo |
| :--- | :--- | :--- | :--- |
| **Clasificación de Etapas** | Porcentaje de POs retrasados donde la etapa asignada coincide con el mayor desfase temporal en los datos. | > 80% de precisión | Requerido |
| **Consistencia de Códigos** | Porcentaje de registros donde la clasificación algorítmica coincide con el factor humano (`REASON_DSC`). | Reportar métrica final | Requerido |
| **Calidad de Explicación LLM** | Auditoría manual de 20 casos: consistencia en la etapa, métricas correctas y viabilidad de la acción recomendada. | 4 / 5 puntos mínimo | Requerido |
| **Jerarquía de Severidad** | Órdenes urgentes (`HOT_PO_FLAG=Y`) con retrasos > 3 días deben clasificarse estrictamente con severidad **HIGH**. | > 95% de cumplimiento | Requerido |
| **Análisis de Discrepancias** | Documentación analítica de casos donde la clasificación matemática corrigió con éxito el error del registro manual. | 5+ casos detallados | Avanzado (*Stretch*) |

---

## 7. Cronograma General de Desarrollo

* **Semana 1 — Pipeline de Datos y Limpieza:** Carga del CSV, estandarización y corrección de cronologías inversas y manejo de nulos. Análisis Exploratorio de Datos (EDA) inicial.
* **Semana 2 — Motor de Reglas Lógicas:** Programación de los umbrales determinísticos por etapa. Análisis comparativo inicial contra el factor humano e identificación de registros erróneos.
* **Semana 3 — Integración de Capa de IA:** Diseño conceptual y refinamiento de prompts. Orquestación del procesamiento por lotes mediante el LLM y cálculo automatizado de severidad.
* **Semana 4 — Evaluación e Interfaz:** Desarrollo del aplicativo interactivo de consulta, consolidación de métricas finales de rendimiento y presentación ejecutiva.

---

## 8. Stack Tecnológico Sugerido

* **Pandas & NumPy:** Manipulación matemática de matrices, limpieza de series de tiempo y unificación de datos.
* **Anthropic Python SDK (`claude-sonnet-4-6`):** Procesamiento de lenguaje natural avanzado para diagnóstico de causas raíz.
* **Datetime / Timedelta:** Operaciones nativas de deltas y ventanas temporales de logística.
* **Streamlit / Jupyter Notebook:** Entorno analítico visual y demo de cara al usuario final.
* **Git / GitHub:** Control de versiones, ramas de trabajo y resguardo del repositorio.
