# Documentación Técnica y Arquitectura - Invicta Gym

Este documento proporciona una visión general y técnica del proyecto **Invicta Gym**, diseñada para servir como punto de partida y contexto para desarrolladores, administradores de sistemas y asistentes de inteligencia artificial que interactúen con el código fuente.

---

## 1. Resumen del Proyecto

**Invicta Gym** es un sistema integral de gestión para un centro de entrenamiento. Su objetivo principal es administrar la cartera de clientes, monitorear el estado de las membresías/suscripciones en tiempo real, procesar pagos y, en fases posteriores, gestionar rutinas de entrenamiento y planes nutricionales.

El sistema prioriza una interfaz de usuario (UI) moderna y premium basada en el diseño **Dark Neon** y **Glassmorphism**, buscando que la experiencia de administración sea altamente visual, intuitiva y estéticamente atractiva.

---

## 2. Stack Tecnológico

El proyecto está construido sobre una arquitectura moderna y robusta:

*   **Backend:** Python 3.10 con el framework **Django 5.2.16**.
*   **Base de Datos:** **PostgreSQL 15** para almacenamiento relacional seguro.
*   **Frontend:** HTML5 semántico, **Tailwind CSS 3.4.1** para estilos utilitarios y Vanilla JavaScript para interacciones del DOM (ej. integración de cámara web).
*   **Infraestructura/Orquestación:** **Docker y Docker Compose** para aislamiento de entornos y despliegue unificado.

---

## 3. Infraestructura y Contenedores (Docker Compose)

El proyecto está completamente contenedorizado para evitar conflictos de dependencias y simplificar el desarrollo. El archivo `docker-compose.yml` define tres servicios principales:

1.  **`db` (PostgreSQL):**
    *   **Imagen:** `postgres:15-alpine`.
    *   **Lógica:** Almacena toda la data relacional. Utiliza un volumen local (`postgres_data`) para garantizar la persistencia de datos incluso si el contenedor se destruye.
    *   **Inicialización:** Utiliza un mecanismo de auto-arranque `restart: unless-stopped`. La base de datos inicia completamente limpia (se eliminó el `init.sql` de legado).
2.  **`web` (Django Application):**
    *   **Imagen:** Construida a partir de un `Dockerfile` (`python:3.10-slim`).
    *   **Lógica:** Aplica las migraciones automáticamente en el arranque (`python manage.py migrate`) asegurando que la base de datos se estructure sin intervención humana, y luego ejecuta el servidor de desarrollo de Django (`runserver`) exponiendo el puerto 8000.
    *   **Conectividad:** Se conecta a `db` a través de la red interna de Docker usando variables de entorno (`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`).
3.  **`tailwind` (Compilador CSS):**
    *   **Imagen:** `node:20-alpine`.
    *   **Lógica:** Ejecuta el script `npm run tailwind:watch`. Observa los cambios en los archivos HTML y recompila el CSS (`tailwind_output.css`) en tiempo real. Al montar el volumen del código fuente, los cambios se reflejan instantáneamente en el contenedor `web`.

---

## 4. Lógica de Negocio y Base de Datos

La aplicación principal se llama `gym` y su núcleo reside en sus modelos (`gym/models.py`), diseñados para mantener el backend inteligente y el frontend ligero:

### Modelos Principales
*   **`Plan`:** Define los tipos de membresías disponibles (Ej: Plan Regular, Trimestral, Pase Diario). Define duración y precios.
*   **`Cliente`:** Almacena la información personal de los usuarios, su fotografía, y el **`descriptor_facial` (JSONField)**, que es un vector numérico extraído por inteligencia artificial para la identificación biométrica.
*   **`Suscripcion`:** Es el puente transaccional entre un Cliente y un Plan.
    *   **Lógica de Fechas Inteligente:** El modelo `Suscripcion` incluye propiedades (`@property`) que calculan en tiempo real el estado de la cuenta. 
    *   `dias_restantes`: Calcula la diferencia entre hoy y la fecha de vencimiento.
    *   `porcentaje_tiempo`: Devuelve un valor del 0 al 100 indicando qué proporción del plan ha transcurrido. (Este valor alimenta directamente las barras de progreso en el Frontend).
*   **`Asistencia`:** Registra las entradas diarias de los clientes activos.

### Flujo de Registro de Cliente
1. El administrador ingresa los datos personales.
2. Se solicita una fotografía (opcional). Mediante la API del navegador (`navigator.mediaDevices`), Vanilla JS captura el frame de la cámara, lo dibuja en un `<canvas>` y lo inyecta como `base64` en un input oculto del formulario.
3. Django recibe el `base64`, lo decodifica, lo guarda como archivo de imagen. Posteriormente, a través de la librería `face_recognition` (Python + OpenCV), extrae la matriz matemática del rostro y la guarda en el campo `descriptor_facial`.
4. Automáticamente, genera el registro de `Pago` y la `Suscripcion`, calculando la `fecha_vencimiento` basado en los días del `Plan` seleccionado.

### El Semáforo Biométrico de Acceso
El corazón operativo del sistema es el **Semáforo Biométrico** (`/api/validar_rostro/`). 
*   **Captura Asíncrona:** El frontend realiza *polling* de la cámara web, enviando fotogramas al backend en Base64 de manera invisible para el usuario.
*   **Distancia Euclidiana:** El servidor compara el rostro recibido contra la base de datos de descriptores de clientes. Si encuentra coincidencia, identifica al usuario.
*   **Reglas de Acceso:** Una vez identificado, verifica el estado de su `Suscripcion`. Si está al día (o dentro de los *días de gracia*), marca una `Asistencia` y responde al frontend para que el Semáforo se ponga en Verde y muestre la tarjeta del cliente. Si está vencido, arroja Rojo (acceso denegado).

### Testing y Performance Industrial (k6)
La arquitectura biométrica basada en el servidor demostró ser inmensamente robusta y estable.
Bajo pruebas de estrés ejecutadas con **Grafana k6**, el sistema logró procesar **2,364 registros biométricos en 2 minutos** (concurrencia de 50 usuarios), sin memory leaks y manteniendo un percentil 95 de latencia en **~101 ms**. Además, se comprobó que el flujo biométrico rinde perfectamente en VPS económicos limitados a 512MB RAM y 0.5 CPU.

---

## 5. Arquitectura Frontend y Diseño UI/UX

La interfaz rompe con los diseños administrativos tradicionales "planos".

*   **Glassmorphism:** Las tarjetas (Cards) y formularios utilizan fondos con opacidad (`bg-black/30`), desenfoque (`backdrop-blur-2xl`) y bordes luminosos.
*   **Glow & Neon:** Se hace uso extensivo de utilidades personalizadas de Tailwind (sombras desplegables de colores intensos `shadow-[0_0_20px_rgba(...)]`) para dar feedback visual (hover states, inputs activos).
*   **Formularios Centralizados:** Las clases CSS de los inputs (`TW_INPUT_CLASS`) están definidas en el backend (`gym/forms.py`). Esto asegura que cualquier nuevo formulario renderizado por Django herede instantáneamente la estética Dark Neon sin duplicar código en los HTML.
*   **Componentes Clave:**
    *   *Dashboard Carrusel:* Un slider horizontal responsivo para visualizar métricas (Asistencias, Vencidos, Pases Diarios) sin abrumar la vista.
    *   *Tarjetas de Clientes:* En lugar de tablas, se usan tarjetas que incluyen barras de progreso dinámicas inyectadas desde el backend.

---

## 6. Flujo de Trabajo para Desarrolladores

Para integrarse al desarrollo o levantar el proyecto desde cero:

### 1. Requisitos Previos
*   Docker y Docker Compose instalados.

### 2. Levantar el Entorno
Ejecutar en la raíz del proyecto:
```bash
docker compose up --build -d
```
Esto inicializará la base de datos, compilará las dependencias de Python/Node.js, y levantará el servidor web en `http://localhost:8000`.

### 3. Ejecución de Comandos Django
Debido a que el proyecto está en Docker, los comandos administrativos de Django deben correrse dentro del contenedor `web`.
*   **Migraciones:** `docker compose exec web python manage.py makemigrations` y `docker compose exec web python manage.py migrate`
*   **Crear Superusuario:** `docker compose exec web python manage.py createsuperuser`
*   **Logs:** `docker compose logs -f web` (Para ver errores de backend) o `docker compose logs -f tailwind` (Para ver la compilación de CSS).

### 4. Próximos Pasos (Roadmap)
*   **Fase de Módulos:** Implementar los modelos y vistas para "Rutinas" y "Nutrición".
*   **Control de Accesos:** Robustecer la lógica de autenticación y vistas protegidas.
*   **Optimización de Producción:** Cambiar el servidor de desarrollo (`runserver`) por `Gunicorn` u otro servidor WSGI/ASGI de producción cuando se decida desplegar.
