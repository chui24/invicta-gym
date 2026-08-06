import http from 'k6/http';
import { check, sleep } from 'k6';

// Configuración de la prueba de carga
export const options = {
    stages: [
        { duration: '30s', target: 10 },  // Ramp-up a 10 usuarios concurrentes
        { duration: '1m', target: 50 },   // Pico de 50 usuarios concurrentes
        { duration: '30s', target: 0 },   // Ramp-down a 0 usuarios
    ],
    thresholds: {
        http_req_duration: ['p(95)<3000'], // El 95% de las peticiones debe completarse en menos de 3s
        http_req_failed: ['rate<0.05'],    // Tasa de error menor al 5%
    },
};

// Pequeña imagen base64 de prueba (1x1 pixel negro) para simular la captura de la webcam
const dummyBase64Image = 'data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////wgALCAABAAEBAREA/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxA=';

export default function () {
    // 1. Obtener la página para extraer el token CSRF
    const resGet = http.get('http://localhost:8000/cliente/crear/');
    
    check(resGet, {
        'GET /cliente/crear/ responde 200': (r) => r.status === 200,
    });

    // Extraer el csrfmiddlewaretoken de la respuesta (usando regex simple)
    const csrfMatch = resGet.body.match(/name="csrfmiddlewaretoken" value="([^"]*)"/);
    const csrfToken = csrfMatch ? csrfMatch[1] : '';

    if (!csrfToken) {
        console.error('No se pudo obtener el token CSRF');
        return;
    }

    // 2. Preparar los datos del formulario (como form-urlencoded)
    const payload = {
        csrfmiddlewaretoken: csrfToken,
        cedula: `V${Math.floor(Math.random() * 100000000)}`,
        nombre: `K6 Load Test User ${__VU}-${__ITER}`,
        correo: `test${__VU}_${__ITER}_${Math.floor(Math.random() * 10000)}@invictagym.com`,
        telefono: '04120000000',
        plan: '1', // Asumimos que el plan con ID 1 existe
        fecha_inscripcion: '2026-08-01',
        metodo_pago: 'Efectivo',
        foto_base64: dummyBase64Image
    };

    // 3. Enviar la petición POST
    const resPost = http.post('http://localhost:8000/cliente/crear/', payload, {
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': 'http://localhost:8000/cliente/crear/'
        }
    });

    // La redirección al dashboard (status 302) o status 200 indica éxito en Django
    check(resPost, {
        'POST /cliente/crear/ redirige o responde 200': (r) => r.status === 200 || r.status === 302,
    });

    sleep(1); // Simular el tiempo que le toma a un usuario (1 segundo de pausa entre interacciones)
}
