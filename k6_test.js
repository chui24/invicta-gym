import http from 'k6/http';
import { check, sleep } from 'k6';

// Configuración de la prueba de carga
export const options = {
    stages: [
        { duration: '30s', target: 5 },   // Ramp-up: subir a 5 usuarios concurrentes en 30s
        { duration: '1m', target: 5 },    // Mantener 5 usuarios durante 1 minuto
        { duration: '30s', target: 10 },  // Pico de carga: subir a 10 usuarios
        { duration: '30s', target: 0 },   // Ramp-down: bajar a 0 usuarios
    ],
    thresholds: {
        http_req_duration: ['p(95)<2000'], // El 95% de las peticiones debe tardar menos de 2s
        http_req_failed: ['rate<0.01'],    // Menos del 1% de errores permitidos
    },
};

// Se simula una imagen en base64 muy pequeña para no saturar la red local con el payload,
// sino para estresar el procesamiento del CPU en el backend (OpenCV/dlib).
const dummyBase64Image = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////wgALCAABAAEBAREA/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAQDAQACEQMRBAAAEA//xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oACAECEQE/EBP/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oACAEDAQE/EBP/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oACAEBAAE/EBP/2Q==";

export default function () {
    const baseUrl = 'http://localhost:8000'; // Usaremos red de host

    // 1. Prueba: Cargar el Dashboard principal (GET)
    const resDashboard = http.get(`${baseUrl}/`);
    check(resDashboard, {
        'Dashboard responde 200': (r) => r.status === 200,
    });
    
    sleep(1); // Simular tiempo de lectura del usuario

    // 2. Prueba: Enviar frame al escáner facial (POST)
    // El frontend envía un frame cada 1.5s, simularemos algo similar.
    const payload = JSON.stringify({
        image: dummyBase64Image,
    });

    const params = {
        headers: {
            'Content-Type': 'application/json',
        },
    };

    const resRostro = http.post(`${baseUrl}/api/validar_rostro/`, payload, params);
    
    check(resRostro, {
        'API Rostro responde 200': (r) => r.status === 200,
        'API procesa el JSON sin crashear': (r) => {
            try {
                const body = JSON.parse(r.body);
                // Puede retornar not_found porque la imagen falsa no tiene cara, 
                // pero eso significa que el backend operó bien matemáticamente.
                return body.status === 'not_found' || body.status === 'unknown_face' || body.status === 'success';
            } catch(e) {
                return false;
            }
        }
    });

    sleep(1.5); // Intervalo de 1.5s real del frontend
}
