const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const fotoPreview = document.getElementById('foto_preview');
// Django rendered input id is usually id_foto_base64
const inputBase64 = document.getElementById('id_foto_base64'); 

const btnIniciar = document.getElementById('btn_iniciar_camara');
const btnCapturar = document.getElementById('btn_capturar');
const btnRetomar = document.getElementById('btn_retomar');
const camContainer = document.getElementById('cam_container');

let streamActivo = null;

// Encender cámara
btnIniciar.addEventListener('click', async () => {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' } });
        video.srcObject = stream;
        streamActivo = stream;
        
        btnIniciar.style.display = 'none';
        camContainer.style.display = 'block';
        fotoPreview.style.display = 'none';
        btnRetomar.style.display = 'none';
        
        const placeholder = document.getElementById('foto_placeholder');
        if (placeholder) placeholder.style.display = 'none';
    } catch (err) {
        console.error("Error accediendo a la cámara: ", err);
        alert("No se pudo acceder a la cámara. Asegúrese de dar permisos.");
    }
});

// Capturar foto
btnCapturar.addEventListener('click', () => {
    const context = canvas.getContext('2d');
    // Dibujar frame del video en canvas
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // Obtener base64
    const dataUrl = canvas.toDataURL('image/jpeg', 0.8);
    if (inputBase64) {
        inputBase64.value = dataUrl;
    }
    
    // Mostrar preview
    fotoPreview.src = dataUrl;
    fotoPreview.style.display = 'block';
    
    // Ocultar video
    camContainer.style.display = 'none';
    btnRetomar.style.display = 'inline-block';
    
    // Detener stream
    if (streamActivo) {
        streamActivo.getTracks().forEach(track => track.stop());
        streamActivo = null;
    }
});

// Retomar
btnRetomar.addEventListener('click', () => {
    if (inputBase64) {
        inputBase64.value = '';
    }
    fotoPreview.style.display = 'none';
    btnRetomar.style.display = 'none';
    btnIniciar.click(); // Volver a iniciar
});
