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

### 2. Fase 3: Rutinas (Flexibilidad y Motor Biométrico)
*   **Flexibilidad de Días Asíncronos:** El sistema permite ahora seleccionar días específicos de la semana para el entrenamiento del cliente (ej. Lunes, Miércoles, Viernes), almacenándolos en un `JSONField` llamado `dias_activos` en `AsignacionCliente`.
*   **Constructor Multi-Semanal Avanzado:** Interfaz asíncrona en `rutina_crear.html` para diseñar planes de hasta 12 semanas. Permite estructurar días y ejercicios (con campos desglosados para Series, Repeticiones y Peso Sugerido) utilizando Vanilla JS para persistencia temporal (estado `routineData`) antes del guardado.
*   **Edición Bidireccional y Componentes UI:** El constructor carga el JSON preconfigurado. Se integraron reglas CSS puras para evadir fallos de Tailwind en tiempo real para la selección de días (botones Neón en Hover y Active).
*   **Motor Biométrico de Inasistencias (Lookback Algorithm):** El endpoint `/api/validar_rostro/` determina exactamente qué "Día de Rutina" le corresponde al cliente cruzando fechas. Además, busca hasta 7 días atrás si el cliente se ausentó en una fecha agendada, disparando un **Badge de Alarma Naranja** instantáneo en el Dashboard de Recepción.
*   **Lógica de Renderizado por Semana:** La vista del perfil de cliente (`rutina_cliente.html`) identifica la rutina, filtra dinámicamente los días según la semana seleccionada (por query parameter o default cronológico) y renderiza los ejercicios asignados con placeholders inteligentes de peso prescrito.

### 2.5 Rediseño de UI y Navegación (Mobile-First y UX Premium)
*   **Menú Lateral Colapsable Global:** Se implementó una lógica de expansión de contenido en escritorio. Al colapsar el menú lateral, el área principal (`flex-grow`) ocupa fluidamente todo el espacio restante.
*   **Encabezado Dinámico Global:** Unificación de la jerarquía visual con la frase de marca ("NO SEAS GUAPA, SÉ ICÓNICA") y el reloj/fecha local incrustado en una pastilla oscura, todo alineado a la derecha en `base.html` y totalmente responsive (tipografía y layouts adaptables a móvil).
*   **Dashboard Estadístico:** Se refactorizó el contenedor de tarjetas para mantener proporciones horizontales nativas (`flex-nowrap`), pero con alturas y márgenes optimizados sin uso de grillas molestas para el usuario.
*   **Optimización de Interfaz de Creación de Rutinas:** Se organizaron los inputs ("Series", "Reps" y "Peso Sugerido") optimizando el espacio horizontal para móviles sin perder el soporte *Drag & Drop* nativo de SortableJS.

### 3. Infraestructura y Estado del Repositorio (Fase 4 - Pruebas Cloud)
*   **Entorno Dockerizado Local:** Totalmente configurado (`docker compose up --build -d`) para la rama de desarrollo.
*   **Entorno Producción/VPS:** Se configuró Nginx como proxy inverso (con red externa `instances`). 
    *   **Unificación de Docker:** En la rama `test`, se fusionó `docker-compose.prod.yml` en un único `docker-compose.yml` maestro que elimina los volúmenes (`volumes: []`), obliga a reconstruir la imagen para aplicar cambios (`--build`), e inyecta explícitamente variables desde `.env`.
    *   **Seguridad y Variables:** Las credenciales seguras se leen mediante `.env`. Se mejoró la robustez de `settings.py` para ignorar espacios en blanco en `ALLOWED_HOSTS` y `CSRF_TRUSTED_ORIGINS`.
    *   **Certificados y Cámara:** Se aplicó SSL oficial vía Certbot para habilitar el uso seguro y nativo de `navigator.mediaDevices.getUserMedia` (Cámara Web) sin errores `NotAllowedError`.
    *   **Cache Busting:** Se añadieron parámetros de versión (`?v=1.1`) a `base.js` y `tailwind_output.css` en `base.html` para evadir el caché rancio de los navegadores móviles sin requerir "Hard Refresh".
*   **Git Flow & Repositorio Limpio:** Estrategia de 3 ramas (`main` para Septiembre, `test` activa en VPS, y `develop` para código local). El archivo `.dockerignore` aísla los artefactos y notas de este repositorio.
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
