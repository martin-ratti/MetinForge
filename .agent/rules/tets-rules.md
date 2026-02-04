---
trigger: always_on
---

## PROTOCOLO DE INTEGRIDAD DE CÓDIGO (Regla Antigravity)

**DISPARADOR:** Cada vez que generes código, modifiques archivos existentes o crees nuevos archivos.

**ACCIONES OBLIGATORIAS (Ejecutar en orden):**

1.  **Cobertura de Tests:**
    * Analiza si el código modificado/creado tiene tests asociados.
    * *Si NO tiene o es nuevo:* Genera inmediatamente un archivo de test unitario correspondiente.
    * *Si YA tiene:* Actualiza el test para reflejar los nuevos cambios.

2.  **Ciclo de Compilación y Depuración:**
    * Ejecuta `npm run dev` o `npm run build`.
    * **CRÍTICO:** Si aparecen errores en la terminal o en la pestaña "Problems", corrígelos y repite este paso. No avances hasta que la compilación sea exitosa (0 errores).

3.  **Verificación Final (Safety Check):**
    * Ejecuta la suite completa de pruebas: Unitarias, Integración y E2E.
    * *Objetivo:* Asegurar "Regresión Cero" (que nada previo se haya roto).

**RESTRICCIÓN:** No des por finalizada la tarea ni entregues el código al usuario hasta que los pasos 2 y 3 se completen sin errores.