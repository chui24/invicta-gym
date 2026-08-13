# Memoria de Proyecto (Antigravity Handoff)

**Proyecto:** Invicta Gym
**Estado Actual:** Fase Técnica 1 y 2 Completas (Biometría, Finanzas y Automatización Auditiva validadas en Producción).
**Próximo Objetivo:** Fase 3 (Rutinas y Dietas).

## 🧠 Contexto para Antigravity (IA)
Si estás leyendo esto, acabas de ser inicializado en una nueva computadora para continuar el desarrollo de "Invicta Gym". Aquí tienes el resumen exacto de cómo quedó el proyecto en la última iteración:

### 1. Funcionalidades Desarrolladas (Fase 1 y 2)
*   **Arquitectura Base:** Django web app + PostgreSQL + Tailwind CSS compilado localmente.
*   **Reconocimiento Facial (Backend):** Usando `face_recognition` y `dlib`. Se captura desde la webcam mediante polling asíncrono y se procesa en el endpoint `/api/validar_rostro/`.
*   **Roles y Polimorfismo:** El sistema diferencia entre "Clientes" y "Personal" (Staff). La tarjeta del dashboard se adapta dinámicamente ocultando fechas para el staff y mostrando menús extra para clientes.
*   **Semáforo Biométrico e Inteligencia UX:**
    *   **Activo (Verde):** Pago al día.
    *   **Por vencer (Amarillo):** Se activa cuando quedan 3 días o menos, o si el cliente está en los días de gracia tras expirar su plan.
    *   **Inactivo (Rojo):** Mensualidad vencida y gracia expirada.
*   **Módulo Auditivo:** Precarga en JavaScript (`dashboard.js`) de archivos mp3 locales (`bienvenida_al_gym.mp3`, `(recordatorio de pago).mp3`, `(pago vencido).mp3`). La UI narra el estatus al validar el rostro del cliente (el staff está excluido del audio).
*   **Automatización de Pagos (Tasa BCV):** Sistema integrado que raspa diariamente el sitio oficial del Banco Central de Venezuela (`gym/utils/bcv_scraper.py`) y actualiza una variable global (`tasa_bcv`) en la BD. La interfaz de renovación calcula automáticamente el equivalente en Bs mediante JS en vivo.

### 2. Infraestructura y Estado del Repositorio
*   **Entorno Dockerizado:** Totalmente configurado (`docker compose up --build -d`). 
*   **Repositorio Limpio:** Todo el código se migró a estándares profesionales para su presentación en GitHub (README técnico sin íconos, limpieza de caché, imágenes huérfanas de pruebas de estrés removidas, archivos JIT de Tailwind configurados).
*   **Comandos Personalizados:**
    *   `python manage.py actualizar_bcv`: Para actualizar la tasa de divisa en tiempo real (listo para cron job).
    *   `python manage.py limpiar_media`: Limpia de forma autónoma fotos viejas y archivos residuales del servidor que no estén mapeados en la BD.

### 3. Siguientes Pasos (Roadmap de Desarrollo)
Nos estamos preparando para entrar de lleno a la **Fase 3**. Una vez aprobada la fase anterior por la dueña, avanzaremos con:
1.  **Rutinas Semanales:** Interfaz de asignación y visualización de entrenamientos para clientes.
2.  **Dietas / Planes Alimenticios:** Módulo de seguimiento de nutrición básica.
3.  **Reportes y Métricas:** Panel administrativo final con gráficas (asistencias, ingresos, etc.).

### 4. Instrucciones para la IA:
*   El código fuente está limpio y profesionalizado. Revisa `gym/views.py` para entender la lógica central.
*   Los comandos JS ahora son tomados en cuenta por Tailwind (`tailwind.config.js` escanea `./static/js/**/*.js`).
*   **NO alteres el Dockerfile** a menos que sea estrictamente necesario. Las dependencias biométricas son delicadas.
*   El usuario pide calidad premium, sin placeholders, y con diseños estéticos (Dark/Neon - Glassmorphism).
*   Antes de hacer grandes cambios, pregunta siempre al usuario en qué módulo desea enfocarse.
