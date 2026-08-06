const video = document.getElementById('videoElement');
const canvas = document.getElementById('canvasElement');
const fotoActual = document.getElementById('fotoActual');

const btnIniciar = document.getElementById('btnIniciarCamara');
const btnCapturar = document.getElementById('btnCapturar');
const btnRepetir = document.getElementById('btnRepetir');

const fotoInput = document.querySelector('input[name="foto_base64"]');
let stream = null;

async function iniciarCamara() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = stream;
        
        if(fotoActual) fotoActual.style.display = 'none';
        video.style.display = 'block';
        canvas.style.display = 'none';
        
        btnIniciar.style.display = 'none';
        btnCapturar.style.display = 'inline-block';
        btnRepetir.style.display = 'none';
    } catch (err) {
        console.error("Error accediendo a la cámara:", err);
        alert("No se pudo acceder a la cámara.");
    }
}

if(btnIniciar) {
    btnIniciar.addEventListener('click', iniciarCamara);
}

// Si no hay foto actual, intentamos abrir la cámara de inmediato
if(!fotoActual) {
    iniciarCamara();
}

btnCapturar.addEventListener('click', () => {
    const context = canvas.getContext('2d');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    const dataURL = canvas.toDataURL('image/jpeg', 0.8);
    fotoInput.value = dataURL;
    
    video.style.display = 'none';
    canvas.style.display = 'block';
    
    btnCapturar.style.display = 'none';
    btnRepetir.style.display = 'inline-block';
});

btnRepetir.addEventListener('click', () => {
    fotoInput.value = '';
    canvas.style.display = 'none';
    video.style.display = 'block';
    
    btnCapturar.style.display = 'inline-block';
    btnRepetir.style.display = 'none';
});

// Apagar cámara al salir de la página
window.addEventListener('beforeunload', () => {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
    }
});
