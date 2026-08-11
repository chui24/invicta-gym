# Invicta Gym - Management and Biometric Control System

![Invicta Gym Logo](static/img/invicta_logo.png)

Invicta Gym is a comprehensive platform designed to modernize access control and membership management for fitness centers. The core feature of this system is its robust facial recognition engine deployed in the backend, which manages physical access to the facilities based on real-time financial statuses (Access Semaphore System).

## Key Features

* **Intelligent Biometric Validation:** Real-time facial detection and validation processed server-side (Python/OpenCV/dlib), ensuring high security standards and allowing low-resource edge devices at reception points.
* **Access Semaphore Engine:** A visual and logical gateway that automatically grants or denies entry based on dynamic grace periods, membership validity, and payment statuses.
* **Membership and Client Management:** Full administrative control over client profiles, subscriptions, renewals, and integrated payment tracking.
* **Dynamic Currency Automation:** Automated daily web scraping of official BCV exchange rates to dynamically calculate Bolivar (Bs) pricing in real time during membership renewals.
* **Premium User Interface:** A modern, responsive design built with Tailwind CSS, featuring a Dark/Neon aesthetic (Glassmorphism) optimized for low-light gym environments.
* **High Availability & Resilience:** Stress-tested architecture designed to tolerate high volumes of simultaneous biometric validations and database transactions without bottlenecks or memory leaks.

## Technology Stack

* **Backend Environment:** Python 3, Django, Django REST Framework
* **Computer Vision:** `face_recognition`, OpenCV (`opencv-python-headless`), NumPy
* **Database Management:** PostgreSQL 15
* **Frontend Technologies:** HTML5, JavaScript (Vanilla ES6+), Tailwind CSS v3
* **Infrastructure & Containerization:** Docker, Docker Compose
* **Quality Assurance:** Grafana k6 (Load Testing)

## Prerequisites

To deploy this project in a local or VPS environment, the host machine only requires the following container orchestration tools:

* [Docker](https://docs.docker.com/get-docker/)
* [Docker Compose](https://docs.docker.com/compose/install/)

*(Python, Node.js, and PostgreSQL do not need to be installed on the host machine as the architecture is fully containerized).*

## Installation and Deployment

1. **Clone the repository**
   ```bash
   git clone https://github.com/chui24/invicta-gym.git
   cd invicta-gym
   ```

2. **Deploy the infrastructure using Docker**
   During the initial build, C++ dependencies required for the computer vision engine will be compiled automatically.
   ```bash
   docker compose up --build -d
   ```

3. **Access the Application**
   Navigate to the following address in your web browser: `http://localhost:8000`

## Project Structure

* `/gym/`: Main Django application containing data models, views, and the core biometric logic.
* `/config/`: Central routing, system settings, and environment configurations.
* `/templates/`: Server-rendered HTML templates.
* `/static/`: Asynchronous logic (JS), compiled stylesheets (Tailwind), and media assets.
* `/media/`: Local storage volume (ignored by version control) for storing baseline facial recognition data.

## Development Notes

* **Frontend Compilation:** The `tailwind` container runs an active `npm run tailwind:watch` process in the background. UI modifications will be compiled and reflected instantaneously without manual intervention.
* **Performance Considerations:** The facial recognition pipeline maintains a latency threshold of ~33ms (P95) on a 1-core / 1GB RAM environment. Client-side JS processing for computer vision is intentionally avoided to bypass hardware limitations on reception devices.

---
*Developed and tested to guarantee industrial stability in high-traffic environments.*
