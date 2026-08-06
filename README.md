# Invicta Gym - Sistema de Gestión y Control Biométrico 🏋️‍♂️

![Invicta Gym](static/img/invicta_logo.png)

Invicta Gym es una plataforma integral para la administración de gimnasios, desarrollada para modernizar el control de acceso y la gestión de membresías. El sistema destaca por integrar un motor de **reconocimiento facial en el backend** que autoriza o deniega el acceso a las instalaciones basándose en el estado de pago del cliente (Semáforo de Acceso).

## 🚀 Características Principales

*   **Validación Biométrica Inteligente:** Detección y validación facial instantánea procesada en el servidor (Python/OpenCV/dlib) para máxima seguridad y compatibilidad con dispositivos de bajos recursos en la recepción.
*   **Semáforo de Acceso:** Sistema visual y lógico que permite la entrada según los días de gracia, estado de membresía o bloqueos por morosidad.
*   **Control de Clientes y Planes:** Registro completo de perfiles, suscripciones (renovaciones) y métodos de pago integrados.
*   **Interfaz de Usuario Premium:** Diseño moderno y responsivo con estética Dark/Neon (Glassmorphism), construido 100% con Tailwind CSS.
*   **Resiliencia Probada:** Testeado bajo estrés (k6) tolerando altas ráfagas de validación y registros simultáneos sin presentar cuellos de botella ni *memory leaks*.

## 🛠️ Stack Tecnológico

*   **Backend:** Python 3, Django, Django REST Framework
*   **Biometría:** `face_recognition`, OpenCV (`opencv-python-headless`), NumPy
*   **Base de Datos:** PostgreSQL 15
*   **Frontend:** HTML5, JavaScript Vanilla (Fetch API / Async), Tailwind CSS v3
*   **Infraestructura:** Docker & Docker Compose (Arquitectura en contenedores)
*   **QA / Testing:** Grafana k6

## 📋 Requisitos Previos

Para ejecutar este proyecto en cualquier entorno local o VPS, solo necesitas tener instalados:

*   [Docker](https://docs.docker.com/get-docker/)
*   [Docker Compose](https://docs.docker.com/compose/install/)

*(No es necesario instalar Python, Node o Postgres en la máquina host, todo está contenedorizado).*

## ⚙️ Instalación y Despliegue (Local)

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/chui24/invicta-gym.git
   cd invicta-gym
   ```

2. **Levantar la infraestructura con Docker**
   Al levantar los contenedores, se compilarán las dependencias necesarias de C++ para el motor de visión artificial (esto puede tardar un par de minutos la primera vez).
   ```bash
   docker compose up --build -d
   ```

3. **Acceder a la aplicación**
   Abre tu navegador web y visita: `http://localhost:8000`

## 📂 Estructura del Proyecto

*   `/gym/`: Aplicación principal de Django (Modelos, Vistas, Lógica Biométrica).
*   `/config/`: Configuraciones de settings y ruteo central de Django.
*   `/templates/`: Vistas y modales en HTML.
*   `/static/`: Hojas de estilos (Tailwind compilado, base CSS) y lógica asíncrona (JS).
*   `/media/`: Almacenamiento local (ignorado en Git) para fotos de perfil generadas vía webcam.
*   `k6_test*.js`: Scripts de pruebas de carga para stress testing.

## 🔒 Notas de Desarrollo

*   **Compilación del Frontend:** Si modificas el diseño y necesitas recompilar Tailwind, el contenedor `tailwind` ya cuenta con un `npm run tailwind:watch` ejecutándose en segundo plano. Los cambios se verán reflejados al instante.
*   **Performance:** El límite de latencia del escáner facial es de ~33ms (P95) en un entorno de 1 núcleo / 1GB RAM. No se recomienda usar JS puro en el frontend para el reconocimiento por limitantes de memoria y compatibilidad de la cámara del cliente final.

---
*Desarrollado y testeado para garantizar estabilidad industrial en entornos de alto tráfico.*
