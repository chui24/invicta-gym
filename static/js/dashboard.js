document.getElementById('form_busqueda').addEventListener('submit', function(e) {
    e.preventDefault();
    const cedula = document.getElementById('cedula_input').value.trim();
    if(!cedula) return;

    fetch(`/api/validar_semaforo/?cedula=${cedula}`)
        .then(response => response.json())
        .then(data => {
            mostrarPerfil(data);
            document.getElementById('cedula_input').value = ''; // limpiar
            document.getElementById('cedula_input').focus();
        })
        .catch(error => {
            console.error('Error:', error);
            alert("Ocurrió un error al validar.");
        });
});

function mostrarPerfil(data) {
    const card = document.getElementById('perfil_validacion');
    const msgContainer = document.getElementById('val_mensaje_container');
    const statusIcon = document.getElementById('val_status_icon');
    
    // Mostrar elemento
    card.style.display = 'block';
    
    // Trigger reflow to restart animation
    card.classList.remove('show-profile');
    void card.offsetWidth;
    card.classList.add('show-profile');
    
    card.className = 'bg-white/5 backdrop-blur-2xl rounded-[2rem] p-8 md:p-12 border-t-2 shadow-[0_20px_50px_rgba(0,0,0,0.5)] relative overflow-hidden transition-all duration-500 show-profile';
    statusIcon.className = 'w-12 h-12 rounded-full flex items-center justify-center border shrink-0 ml-4 shadow-[0_0_15px_rgba(0,0,0,0.5)]';
    
    const foto = document.getElementById('val_foto');
    const nofoto = document.getElementById('val_nofoto');
    
    if (data.cliente) {
        document.getElementById('val_nombre').textContent = data.cliente.nombre;
        document.getElementById('val_cedula').textContent = data.cliente.cedula;
        
        if (data.cliente.foto) {
            foto.src = data.cliente.foto;
            foto.style.display = 'block';
            nofoto.style.display = 'none';
        } else {
            foto.style.display = 'none';
            nofoto.style.display = 'block';
        }
        
        if (data.cliente.id && data.tipo !== 'staff') {
            document.getElementById('btn_renovar').href = `/cliente/renovar/${data.cliente.id}/`;
            document.getElementById('renovar_container').style.display = 'block';
            document.getElementById('renovar_container').classList.remove('hidden');
        } else {
            document.getElementById('renovar_container').style.display = 'none';
            document.getElementById('renovar_container').classList.add('hidden');
        }
    } else {
        document.getElementById('val_nombre').textContent = 'Desconocido';
        document.getElementById('val_cedula').textContent = '-';
        foto.style.display = 'none';
        nofoto.style.display = 'block';
        document.getElementById('renovar_container').style.display = 'none';
        document.getElementById('renovar_container').classList.add('hidden');
    }

    const btnRoutine = document.getElementById('btn_routine');
    const btnDiet = document.getElementById('btn_diet');
    const venceContainer = document.getElementById('val_vence_container');
    const planLabel = document.getElementById('val_plan_label');

    if (data.tipo === 'staff') {
        if (planLabel) planLabel.textContent = 'Rol:';
        if (venceContainer) venceContainer.style.display = 'none';
        if (btnRoutine) btnRoutine.style.display = 'none';
        if (btnDiet) btnDiet.style.display = 'none';
    } else {
        if (planLabel) planLabel.textContent = 'Plan:';
        if (venceContainer) venceContainer.style.display = 'flex';
        if (btnRoutine) btnRoutine.style.display = 'block';
        if (btnDiet) btnDiet.style.display = 'block';
    }

    
    if (data.suscripcion) {
        document.getElementById('val_plan').textContent = data.suscripcion.plan;
        document.getElementById('val_vencimiento').textContent = data.suscripcion.fecha_vencimiento;
    } else {
        document.getElementById('val_plan').textContent = '-';
        document.getElementById('val_vencimiento').textContent = '-';
    }

    const msgEl = document.getElementById('val_mensaje');
    
    if (data.mensaje || data.error) {
        msgEl.textContent = data.mensaje || data.error;
        msgContainer.style.display = 'block';
    } else {
        msgContainer.style.display = 'none';
    }

    // Evaluar color del semáforo
    document.getElementById('val_estado').textContent = data.estado || 'Inactivo';
    statusIcon.classList.remove('hidden');
    
    if (data.estado_color === 'Verde') {
        card.classList.add('border-green-500');
        statusIcon.classList.add('bg-green-500/20', 'text-green-500', 'border-green-500');
        statusIcon.innerHTML = '<i class="bi bi-check-lg text-2xl"></i>';
        msgEl.className = 'font-bold text-lg m-0 drop-shadow-md text-green-400';
    } else if (data.estado_color === 'Amarillo') {
        card.classList.add('border-yellow-500');
        statusIcon.classList.add('bg-yellow-500/20', 'text-yellow-500', 'border-yellow-500');
        statusIcon.innerHTML = '<i class="bi bi-exclamation-triangle-fill text-xl"></i>';
        msgEl.className = 'font-bold text-lg m-0 drop-shadow-md text-yellow-400';
    } else {
        card.classList.add('border-red-500');
        statusIcon.classList.add('bg-red-500/20', 'text-red-500', 'border-red-500');
        statusIcon.innerHTML = '<i class="bi bi-x-lg text-xl"></i>';
        msgEl.className = 'font-bold text-lg m-0 drop-shadow-md text-red-400';
    }
}

// Funcionalidad del Reloj en Vivo
function actualizarReloj() {
    const ahora = new Date();
    const opcionesFecha = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    let fechaTexto = ahora.toLocaleDateString('es-ES', opcionesFecha);
    fechaTexto = fechaTexto.charAt(0).toUpperCase() + fechaTexto.slice(1);
    
    let horas = ahora.getHours();
    let minutos = ahora.getMinutes();
    let segundos = ahora.getSeconds();
    const ampm = horas >= 12 ? 'PM' : 'AM';
    
    horas = horas % 12;
    horas = horas ? horas : 12;
    minutos = minutos < 10 ? '0' + minutos : minutos;
    segundos = segundos < 10 ? '0' + segundos : segundos;
    
    document.getElementById('live_date').textContent = fechaTexto;
    document.getElementById('live_time').textContent = horas + ':' + minutos + ':' + segundos + ' ' + ampm;
}

setInterval(actualizarReloj, 1000);
actualizarReloj();

// --- Lógica del Escáner Facial (Backend) ---
const btnEscaner = document.getElementById('btn_escaner_facial');
const modalEscaner = document.getElementById('modal_escaner');
const btnCerrarEscaner = document.getElementById('btn_cerrar_escaner');
const videoEscaner = document.getElementById('video_escaner');
const canvasEscaner = document.getElementById('canvas_escaner');
const overlayCargando = document.getElementById('overlay_cargando_escaner');
const overlayExito = document.getElementById('overlay_exito_escaner');
const estadoEscaner = document.getElementById('estado_escaner');

let escanerStream = null;
let scanInterval = null;
let isScanning = false;

function cerrarEscaner() {
    modalEscaner.classList.add('hidden');
    isScanning = false;
    if (scanInterval) clearInterval(scanInterval);
    if (escanerStream) {
        escanerStream.getTracks().forEach(t => t.stop());
        escanerStream = null;
    }
}

if (btnCerrarEscaner) {
    btnCerrarEscaner.addEventListener('click', cerrarEscaner);
}

if (btnEscaner) {
    btnEscaner.addEventListener('click', async () => {
        modalEscaner.classList.remove('hidden');
        overlayCargando.classList.remove('hidden');
        overlayExito.classList.add('hidden');
        estadoEscaner.textContent = 'Iniciando cámara...';
        
        try {
            escanerStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' } });
            videoEscaner.srcObject = escanerStream;
            
            videoEscaner.onloadedmetadata = () => {
                overlayCargando.classList.add('hidden');
                estadoEscaner.textContent = "Analizando... por favor mire a la cámara.";
                canvasEscaner.width = videoEscaner.videoWidth;
                canvasEscaner.height = videoEscaner.videoHeight;
                isScanning = true;
                
                // Enviar un frame cada 1.5 segundos
                scanInterval = setInterval(async () => {
                    if (!isScanning) return;
                    
                    const context = canvasEscaner.getContext('2d');
                    context.drawImage(videoEscaner, 0, 0, canvasEscaner.width, canvasEscaner.height);
                    const dataUrl = canvasEscaner.toDataURL('image/jpeg', 0.7);
                    
                    try {
                        const response = await fetch('/api/validar_rostro/', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({ image: dataUrl })
                        });
                        
                        const result = await response.json();
                        if (result.status === 'success') {
                            // Match encontrado!
                            isScanning = false;
                            clearInterval(scanInterval);
                            
                            overlayExito.classList.remove('hidden');
                            estadoEscaner.textContent = `¡Identificado: ${result.cliente.nombre}!`;
                            
                            setTimeout(() => {
                                cerrarEscaner();
                                mostrarPerfil(result);
                            }, 1500);
                        } else if (result.status === 'unknown_face') {
                            estadoEscaner.textContent = "Rostro detectado pero el cliente es desconocido.";
                            estadoEscaner.classList.add('text-red-500');
                            estadoEscaner.classList.remove('text-brand-muted');
                        } else {
                            estadoEscaner.textContent = "Analizando... por favor mire a la cámara.";
                            estadoEscaner.classList.remove('text-red-500');
                            estadoEscaner.classList.add('text-brand-muted');
                        }
                    } catch (err) {
                        console.error('Error enviando frame:', err);
                    }
                }, 1500);
            };
            
        } catch (error) {
            console.error(error);
            estadoEscaner.textContent = "Error al inicializar la cámara.";
            overlayCargando.classList.add('hidden');
        }
    });
}
