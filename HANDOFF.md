# Memoria de Proyecto (Antigravity Handoff)

**Proyecto:** Invicta Gym
**Estado Actual:** Fase Técnica 1 Completa (Demo de Biometría validada)

## 🧠 Contexto para Antigravity (IA)
Si estás leyendo esto, acabas de ser inicializado en una nueva computadora para continuar el desarrollo de "Invicta Gym". Aquí tienes el resumen de lo que el "yo" anterior hizo junto al usuario:

### 1. ¿Qué se ha construido hasta ahora?
*   **Arquitectura Base:** Django web app + PostgreSQL + Tailwind CSS compilado por Node.
*   **Reconocimiento Facial:** Inicialmente se intentó hacer en el frontend con JavaScript (`face-api.js`), pero fallaba y crasheaba la memoria. Lo **migramos al backend (Python)** usando `face_recognition`, `OpenCV` y `dlib`.
*   **Flujo Biométrico (Lectura):** En el `/dashboard`, un escáner captura la webcam (usando un canvas oculto y *polling* asíncrono) y envía un fotograma en Base64 al endpoint `/api/validar_rostro/`. El backend extrae el descriptor facial, usa la distancia euclidiana para compararlo contra los descriptores guardados en la BD, e indica el estado del pago del cliente (Semáforo).
*   **Flujo de Registro:** En `/cliente/crear/`, se toma la foto de perfil del usuario. El servidor genera el vector biométrico (`descriptor_facial` guardado como JSON) en el mismo momento de su inscripción y crea la Suscripción y su Pago inicial.

### 2. Infraestructura y Testing
*   El proyecto está **Dockerizado**.
*   Se realizaron **Pruebas de Estrés con k6** (`k6_test.js` y `k6_test_registro.js`).
*   Los resultados fueron impecables: el sistema aguanta **50 inserciones por segundo** consumiendo apenas un 57% de CPU y demostrando 0% de fallos.
*   Se comprobó que el sistema opera de manera perfecta aún restringiendo el contenedor web a **512MB RAM y 0.5 CPU**, habilitándolo para ser alojado en VPS muy económicos.

### 3. Siguientes Pasos (Roadmap de Desarrollo)
Una vez que la dueña del gimnasio apruebe la demo del Semáforo Biométrico, los próximos módulos a implementar son:
1.  **Pagos y Renovaciones:** Lógica profunda de cobros, recibos, extensión de las fechas de vencimiento de los planes.
2.  **Gestión Dinámica de Planes:** Crear/Editar/Eliminar las distintas membresías desde una vista de administración (VIP, Mensual, etc.).
3.  **Módulo de Reportes:** Gráficos estadísticos sobre asistencias (quizás con Chart.js), ingresos del mes, control de morosidad.

### 4. Instrucciones para la IA:
*   El código fuente está limpio y funcionando. Revisa `gym/views.py` para entender la lógica central.
*   **NO alteres el Dockerfile** a menos que sea estrictamente necesario. Ya contiene instrucciones críticas (`cmake`, `libgl1`, etc.) que costó mucho compilar para que funcionara la biometría.
*   Antes de hacer grandes cambios, pregunta siempre al usuario en qué módulo desea enfocarse hoy.
