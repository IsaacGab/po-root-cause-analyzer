# Diccionario de Datos: Analizador de Causa Raíz (Blend)

Este documento describe la estructura, nombres limpios y propósitos de las variables contenidas en el dataset de Órdenes de Compra (`po_root_cause_synthetic.csv`).

---

## 1. Identificadores y Datos de Proveedor
Sección dedicada a la identificación de la transacción y las entidades comerciales involucradas.

| Nombre Original | Nombre Limpio | Descripción |
| :--- | :--- | :--- |
| `PO_NBR` | `Purchase_Order_Number` | Número de identificación único de la Orden de Compra. |
| `PO_DT` | `Purchase_Order_Date` | Fecha en la que se creó u originó la orden de compra. |
| `VENDOR_NBR` | `Vendor_Number` | Identificador único del proveedor que surte la mercancía. |
| `VENDOR_NAME` | `Vendor_Name` | Nombre comercial del proveedor. |
| `PAY_VENDOR_NBR` | `Payment_Vendor_Number` | Identificador de la entidad financiera/legal a la que se le paga (puede diferir del proveedor físico). |
| `PAY_VENDOR_NAME` | `Payment_Vendor_Name` | Nombre de la entidad legal a la que se factura/paga. |

---

## 2. Logística del Centro de Distribución (DC)
Ubicaciones físicas e instalaciones de la red de distribución donde se recibe la mercancía.

| Nombre Original | Nombre Limpio | Descripción |
| :--- | :--- | :--- |
| `DC_ID` | `Distribution_Center_ID` | Identificador numérico del Centro de Distribución de destino. |
| `DC_LOC_NAME` | `Distribution_Center_Location_Name` | Nombre de la ciudad o región del Centro de Distribución. |
| `DC_FACILITY_CD_ABBREV` | `Distribution_Center_Facility_Code` | Código abreviado de la instalación física. |
| `PO_STATUS_CD` | `Purchase_Order_Status_Code` | Estado actual de la orden en el sistema (ej. Cerrada, Recibida). |

---

## 3. Control de Volúmenes y Cantidades
Métricas numéricas de las unidades solicitadas versus las realmente entregadas (esencial para detectar faltantes o *Short Ships*).

| Nombre Original | Nombre Limpio | Descripción |
| :--- | :--- | :--- |
| `TOT_ORG_QTY` | `Total_Original_Quantity` | Cantidad total de piezas solicitadas inicialmente. |
| `TOT_ON_ORD_QTY` | `Total_On_Order_Quantity` | Cantidad de piezas que se mantienen activas en la orden. |
| `TOT_ADJ_QTY` | `Total_Adjusted_Quantity` | Ajustes en las cantidades debidos a modificaciones previas. |
| `TOT_RCVD_QTY` | `Total_Received_Quantity` | Cantidad total de piezas físicas que entraron al inventario. |
| `NUM_CASES_ORDERED` | `Number_of_Cases_Ordered` | Número total de cajas master solicitadas al proveedor. |
| `NUM_CASES_SHIPPED` | `Number_of_Cases_Shipped` | Número total de cajas master que el proveedor embarcó realmente. |

---

## 4. Planificación y Ventanas de Citas (SLA)
Fechas límite acordadas comercialmente y el registro del proceso de reservación de citas en el Centro de Distribución.

| Nombre Original | Nombre Limpio | Descripción |
| :--- | :--- | :--- |
| `STA_DT` | `Scheduled_Time_of_Arrival_Date` | **Fecha Comprometida (SLA):** Fecha límite en la que el proveedor prometió entregar la mercancía. |
| `REQUESTED_DT` | `Appointment_Requested_Date` | Fecha para la cual el transportista solicitó originalmente su cita de descarga. |
| `FIRST_SUBMITTED_DT` | `Appointment_First_Submitted_Date` | Marca de tiempo de la primera vez que se ingresó la solicitud al sistema. |
| `DT_APPT_FIRST_APPROVED` | `Appointment_First_Approved_Date` | Fecha en la que el sistema aprobó por primera vez un espacio de descarga. |
| `APPROVED_DT` | `Appointment_Approval_Date` | Fecha de confirmación/aprobación final de la cita actual. |
| `DT_APPT_CURRENT_APPROVED` | `Current_Approved_Appointment_Date` | Fecha de la ventana de descarga asignada actualmente. |
| `PREVIOUS_REQUEST_DT` | `Previous_Appointment_Request_Date` | Historial de fechas solicitadas en caso de reprogramación. |
| `HOT_PO_FLAG` | `Is_High_Priority_PO` | Indicador binario (Y/N) de si la orden es crítica para el negocio. |
| `HOT_APPT_FL` | `Is_High_Priority_Appointment` | Indicador de prioridad alta para la asignación del espacio en andén. |

---

## 5. Operación en Patio y Tiempos de Terminal
Fechas operativas reales del transportista desde su llegada física al complejo logístico hasta su salida.

| Nombre Original | Nombre Limpio | Descripción |
| :--- | :--- | :--- |
| `TRAILER_ARRIVE_DT` | `Trailer_Arrival_Date` | Fecha y hora real en que el transportista llegó a las inmediaciones/patio del DC. |
| `CHECKIN_DT` | `Trailer_Check_In_Date` | Registro formal de entrada en la caseta de vigilancia. |
| `CHECKOUT_DT` | `Trailer_Check_Out_Date` | Registro formal de salida en la caseta tras concluir la descarga. |
| `TRAILER_DEPART_DT` | `Trailer_Departure_Date` | Fecha y hora en que el camión abandonó físicamente las instalaciones. |
| `RECPT_DT` | `Actual_Receipt_Date` | Fecha en la que los datos de recepción impactaron formalmente el sistema de inventarios. |
| `CARRIER_PARTY_NAME` | `Carrier_Company_Name` | Nombre de la empresa transportista (línea fletera). |
| `TRAILER_NBR` | `Trailer_Number` | Placas o número económico de identificación de la caja del tráiler. |
| `YARD_DROP_FL` | `Is_Yard_Drop` | Bandera que indica si el chofer desenganchó la caja en patio y se retiró (Y) o si esperó la descarga en vivo (N). |

---

## 6. Diagnóstico de Retrasos y Tiempos Muertos
Variables analíticas y campos de clasificación de errores para medir el desempeño logístico y justificar penalizaciones.

| Nombre Original | Nombre Limpio | Descripción |
| :--- | :--- | :--- |
| `IS_LATE` | `Is_Late_Flag` | Indicador lógico si la orden llegó después de su `STA_DT`. |
| `DELAY_DAYS` | `Delay_In_Days` | Número de días transcurridos entre la fecha comprometida y la recepción real. |
| `YARD_WAIT_HRS` | `Yard_Wait_Time_Hours` | Tiempo transcurrido desde el Check-In hasta que se le asigna un andén físico de descarga. |
| `DOCK_HRS` | `Dock_Processing_Time_Hours` | Tiempo total que tomó el personal de recibo en vaciar el tráiler y validar la mercancía. |
| `REASON_CD` | `Delay_Reason_Code` | Código estandarizado de la causa del retraso (ej. VEND, CARR, DC). |
| `REASON_DSC` | `Delay_Reason_Description` | Explicación textual del código de retraso o comentario del operador. |