document.addEventListener("DOMContentLoaded", function() {
    const sidebar = document.querySelector('.sidebar');
    const toggleBtn = document.getElementById('sidebarToggle');
    const closeBtn = document.getElementById('sidebarClose');
    const overlay = document.getElementById('sidebarOverlay');

    function toggleSidebar() {
        if (window.innerWidth < 768) {
            // Toggle mobile view classes
            sidebar.classList.toggle('-translate-x-full');
            overlay.classList.toggle('hidden');
        } else {
            // Collapse sidebar with negative margin for smooth content expansion
            if (sidebar.style.marginLeft === '-250px') {
                sidebar.style.marginLeft = '0px';
            } else {
                sidebar.style.marginLeft = '-250px';
            }
        }
    }

    if(toggleBtn) {
        toggleBtn.addEventListener('click', toggleSidebar);
    }
    
    if(closeBtn) {
        closeBtn.addEventListener('click', toggleSidebar);
    }
    
    if(overlay) {
        overlay.addEventListener('click', toggleSidebar);
    }

    // Reloj Global
    const dateEl = document.getElementById('live_date');
    const timeEl = document.getElementById('live_time');

    function actualizarReloj() {
        if (!dateEl || !timeEl) return;
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
        
        dateEl.textContent = fechaTexto;
        timeEl.textContent = horas + ':' + minutos + ':' + segundos + ' ' + ampm;
    }

    if (dateEl && timeEl) {
        setInterval(actualizarReloj, 1000);
        actualizarReloj();
    }
});
