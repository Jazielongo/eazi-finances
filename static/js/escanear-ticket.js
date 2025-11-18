document.addEventListener('DOMContentLoaded', function() {
    const uploadBox = document.querySelector('.upload-box');
    const uploadArea = document.querySelector('.upload-area');
    const processingArea = document.querySelector('.processing-area');
    const resultsArea = document.querySelector('.results-area');
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = 'image/*';
    fileInput.style.display = 'none';

    // Prevenir comportamiento por defecto del drag and drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadBox.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    // Resaltar zona de drop
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadBox.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadBox.addEventListener(eventName, unhighlight, false);
    });

    // Manejar el drop
    uploadBox.addEventListener('drop', handleDrop, false);

    // Manejar clic en el botón de subida
    uploadBox.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', function() {
        handleFiles(this.files);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function highlight(e) {
        uploadBox.classList.add('dragover');
    }

    function unhighlight(e) {
        uploadBox.classList.remove('dragover');
    }

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    }

    function handleFiles(files) {
        if (files.length === 0) return;
        
        const file = files[0];
        if (!file.type.startsWith('image/')) {
            alert('Por favor, sube solo imágenes.');
            return;
        }

        // Mostrar área de procesamiento
        uploadArea.style.display = 'none';
        processingArea.style.display = 'flex';

        // Crear FormData y enviar
        const formData = new FormData();
        formData.append('ticket', file);

        fetch('/procesar-ticket', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            processingArea.style.display = 'none';
            
            if (data.success) {
                // Mostrar resultados
                document.querySelector('[data-field="fecha"]').textContent = data.fecha || 'No detectada';
                document.querySelector('[data-field="total"]').textContent = data.total ? `$${data.total.toFixed(2)}` : 'No detectado';
                document.querySelector('[data-field="proveedor"]').textContent = data.proveedor || 'No detectado';
                
                resultsArea.style.display = 'flex';
            } else {
                alert('Error al procesar el ticket: ' + data.error);
                resetUpload();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al procesar el ticket');
            resetUpload();
        });
    }

    // Botones de acción en los resultados
    document.getElementById('guardarMovimiento').addEventListener('click', function() {
        const fecha = document.querySelector('[data-field="fecha"]').textContent;
        const total = document.querySelector('[data-field="total"]').textContent.replace('$', '');
        const proveedor = document.querySelector('[data-field="proveedor"]').textContent;

        const formData = new FormData();
        formData.append('tipo_movimiento', 'egreso');
        formData.append('monto_total', total);
        formData.append('fecha_registro', fecha);
        formData.append('descripcion', `Compra en ${proveedor}`);

        fetch('/guardar_movimiento', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.mensaje) {
                alert('Movimiento guardado exitosamente');
                window.location.href = '/dashboard';
            } else {
                alert('Error al guardar el movimiento: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al guardar el movimiento');
        });
    });

    document.getElementById('escanearOtro').addEventListener('click', resetUpload);

    function resetUpload() {
        uploadArea.style.display = 'flex';
        processingArea.style.display = 'none';
        resultsArea.style.display = 'none';
        fileInput.value = '';
    }
});