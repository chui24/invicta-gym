# Memoria de Proyecto (Antigravity Handoff)

**Proyecto:** Invicta Gym
**Estado Actual:** Fase Técnica 1 y 2 Completas, Fase 3 en Desarrollo Activo (Rutinas implementadas).
**Próximo Objetivo:** Continuar con asignación de rutinas y Fase 3 (Dietas).

## 🧠 Contexto para Antigravity (IA)
Si estás leyendo esto, acabas de ser inicializado en una nueva computadora para continuar el desarrollo de "Invicta Gym". Aquí tienes el resumen exacto de cómo quedó el proyecto en la última iteración:

### 1. Funcionalidades Desarrolladas (Fase 1 y 2)
*   **Arquitectura Base:** Django web app + PostgreSQL + Tailwind CSS compilado localmente.
*   **Reconocimiento Facial (Backend):** Usando `face_recognition` y `dlib`. Se procesa en el endpoint `/api/validar_rostro/`.
*   **Roles y Polimorfismo:** Diferenciación entre "Clientes" y "Personal". Menús adaptados dinámicamente según el rol.
*   **Semáforo Biométrico e Inteligencia UX:** Activo (Verde), Por vencer (Amarillo) e Inactivo (Rojo) basado en pagos.
*   **Módulo Auditivo:** Narración de estatus de membresía cargado en JS.
*   **Automatización de Pagos (Tasa BCV):** Raspado diario automático y corrección de un bug de recursión infinita en el scraper. La interfaz calcula automáticamente las renovaciones en Bs.

### 2. Fase 3: Rutinas (Nuevo)
*   **Constructor de Rutinas (Routine Builder):** Interfaz asíncrona en `rutina_crear.html` para diseñar mesociclos completos, asignar a entrenadores (Personal), configurar días (`DiaRutina`) y ejercicios (`EjercicioRutina`) atómicamente con JSON y AJAX sin recargar la página.
*   **Lógica de Renderizado:** La vista del perfil de cliente identifica si tiene una rutina activa y adapta el diseño para mostrar la rutina cargada o un botón/estado vacío en caso de que no.
*   **Importación de Excel (Validado):** Se estructuró y corrió satisfactoriamente un script interno de migración que extrae rutinas pre-hechas desde la plantilla Excel de la dueña del gimnasio ("mesociclo yuli.xlsx") y la guarda en BD (Este script se removió posteriormente del entorno local para mantener el proyecto limpio en Git).

### 3. Infraestructura y Estado del Repositorio
*   **Entorno Dockerizado:** Totalmente configurado (`docker compose up --build -d`). 
*   **Repositorio Limpio:** Listo para Git. Archivos residuales, scripts temporales, DB local SQLite o data local de PostgreSQL están debidamente omitidos en `.gitignore` para no ensuciar un entorno de producción o de otro desarrollador.
*   **Comandos Personalizados:** `actualizar_bcv` y `limpiar_media`.

### 4. Siguientes Pasos (Roadmap de Desarrollo)
Nos encontramos a la mitad de la **Fase 3**:
1.  **Rutinas Semanales (Faltantes):** Implementar visualizaciones adicionales o rotaciones automáticas.
2.  **Dietas / Planes Alimenticios:** Módulo de seguimiento de nutrición básica.
3.  **Reportes y Métricas:** Panel administrativo final con gráficas (asistencias, ingresos, etc.).

### 5. Instrucciones para la IA:
*   Revisa `gym/views.py` y `rutina_crear.html` para entender la lógica central de la fase de rutinas.
*   El usuario pide calidad premium, sin placeholders, y con diseños estéticos (Dark/Neon - Glassmorphism).
*   Se resolvió el conflicto con los tags de Django en `base.html` -> el tag para JS es `extra_js`.
*   Antes de hacer grandes cambios, pregunta siempre al usuario en qué módulo desea enfocarse.
