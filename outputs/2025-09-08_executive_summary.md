# Reporte Diario de Incidencias de Procesamiento
**Fecha de Análisis:** 2025-09-08

## Resumen del Día
Se analizaron las fuentes de datos y se encontraron **0** fuentes con criticidad **URGENTE** y **9** que **REQUIEREN ATENCIÓN**.

---
## 🟡 REQUIERE ATENCIÓN - Necesita Investigación

### Fuente: `196125` (Total Incidencias: 1)
- **Tipo:** Archivos Faltantes
  - **Detalle:** Se recibieron 0 archivos, pero se esperaban aproximadamente 2 (la media histÃ³rica para los Mon es 2.00).
  - **Recomendación IA:** No se requiere acción, ya que la ausencia de archivos en lunes es consistente con el patrón histórico de la fuente (mediana de 0 archivos y filas).

### Fuente: `207938` (Total Incidencias: 1)
- **Tipo:** VariaciÃ³n de Volumen Inesperada
  - **Detalle:** Se encontraron 3 archivos con un nÃºmero de filas anÃ³malo. La media esperada para los Mon es ~436869 (stdev: 16949).
  - **Recomendación IA:** Verificar con el proveedor los 3 archivos con volumen inesperado recibidos el domingo, día en que no se espera procesamiento de filas.
  - **Archivos Afectados (3):**
    - `3_Soop_CONC_20250907_M___POS_MARKETPLACE_5B25A3F571D6400082B1E5E228A3E401_14380200000121_0000.csv`
    - `3_Soop_CONC_20250907_M___PAGO_688B810A3E464D27B9E8AAE31C02CE91_02599377000134_0000.csv`
    - `3_Soop_CONC_20250907_M__SHOP_MARKETPLACE_046F9EC9F801495790B8182D16D66C6A_14380200000121_0000.csv`

### Fuente: `220504` (Total Incidencias: 2)
- **Tipo:** Archivo VacÃ­o Inesperado
  - **Detalle:** Se recibieron 2 archivos vacÃ­os, superando la media histÃ³rica de ~0.28 para los Mon.
  - **Recomendación IA:** Verificar que los archivos `Wallet` y `safemode` estén vacíos como es habitual, pues estas entidades comúnmente no reportan datos o los tienen mínimos.
  - **Archivos Afectados (2):**
    - `QkRq0GTSCYcEkvA__BR_Anotaai_Wallet_payments_accounting_report_2025_09_07.csv`
    - `QkRqxGJmiYcEnrQ__BR_safemode_payments_accounting_report_2025_09_07.csv`
- **Tipo:** Archivos Faltantes
  - **Detalle:** Se recibieron 4 archivos, pero se esperaban aproximadamente 16 (la media histÃ³rica para los Mon es 16.00).
  - **Recomendación IA:** Contactar al proveedor para investigar la falta de 12 archivos, ya que los lunes son días de volumen constante y predecible de 16 archivos para esta fuente.
  - **Archivos Afectados (12):**
    - `QkRq2GdOiYcED6w__BR_Saipos_payments_accounting_report_2025_09_07.csv`
    - `QkRq0GTSCYcEkvA__BR_Anotaai_Wallet_payments_accounting_report_2025_09_07.csv`
    - `QkRqxGJmiYcEnrQ__BR_safemode_payments_accounting_report_2025_09_07.csv`
    - `QkRqvEzQCYcEmgQ__BR_DataOnly_payments_accounting_report_2025_09_07.csv`

### Fuente: `220505` (Total Incidencias: 1)
- **Tipo:** Archivos Faltantes
  - **Detalle:** Se recibieron 0 archivos, pero se esperaban aproximadamente 2 (la media histÃ³rica para los Mon es 2.00).
  - **Recomendación IA:** Verificar con el proveedor la ausencia total de los 2 archivos esperados para el lunes, un día de alto volumen de filas y con un patrón de carga consistente.

### Fuente: `220506` (Total Incidencias: 1)
- **Tipo:** Archivos Faltantes
  - **Detalle:** Se recibieron 0 archivos, pero se esperaban aproximadamente 1 (la media histÃ³rica para los Mon es 1.00).
  - **Recomendación IA:** Verificar con el proveedor la ausencia del archivo esperado, ya que esta fuente siempre entrega un archivo con volumen significativo cada día, incluyendo los Lunes.

### Fuente: `228036` (Total Incidencias: 1)
- **Tipo:** Archivos Faltantes
  - **Detalle:** Se recibieron 0 archivos, pero se esperaban aproximadamente 2 (la media histÃ³rica para los Mon es 2.00).
  - **Recomendación IA:** Verificar con el proveedor la ausencia de los 2 archivos esperados para el lunes, un día de volumen históricamente alto.

### Fuente: `228038` (Total Incidencias: 1)
- **Tipo:** Archivos Faltantes
  - **Detalle:** Se recibieron 0 archivos, pero se esperaban aproximadamente 2 (la media histÃ³rica para los Mon es 2.00).
  - **Recomendación IA:** Verificar con el proveedor por qué no se recibieron los 2 archivos esperados para el lunes, un día de alto volumen.

### Fuente: `239611` (Total Incidencias: 1)
- **Tipo:** Archivos Faltantes
  - **Detalle:** Se recibieron 0 archivos, pero se esperaban aproximadamente 2 (la media histÃ³rica para los Mon es 2.00).
  - **Recomendación IA:** Verificar con el proveedor la ausencia de los 2 archivos esperados para el lunes, un día que suele tener alto volumen de datos.

### Fuente: `239613` (Total Incidencias: 1)
- **Tipo:** Archivos Faltantes
  - **Detalle:** Se recibieron 0 archivos, pero se esperaban aproximadamente 2 (la media histÃ³rica para los Mon es 2.00).
  - **Recomendación IA:** Verificar con el proveedor la ausencia de los 2 archivos esperados para el lunes, un día que suele alternar entre volúmenes muy bajos y puntualmente altos.