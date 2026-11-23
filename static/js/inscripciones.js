    document.addEventListener('DOMContentLoaded', function() {
    // 1. Inicializar búsqueda de estudiantes
    const btnBuscar = document.getElementById('btn_buscar_est');
    if (btnBuscar) {
        initBusquedaEstudiante();
    }

    // 2. Resetear el modal al cerrarlo
    const modalElement = document.getElementById('modalInscripcion');
    if (modalElement) {
        modalElement.addEventListener('hidden.bs.modal', function () {
            const form = modalElement.querySelector('form');
            if (form) form.reset();
            const resDiv = document.getElementById('resultado_busqueda');
            if (resDiv) resDiv.style.display = 'none';
        });
    }

    // ==========================================
    //         LÓGICA DE ELIMINACIÓN
    // ==========================================
    const botonesEliminarInsc = document.querySelectorAll('.btn-eliminar-inscripcion');
    
    botonesEliminarInsc.forEach(boton => {
        boton.addEventListener('click', function(e) {
            e.preventDefault();
            
            const urlEliminar = this.getAttribute('data-url');
            const nombreEstudiante = this.getAttribute('data-nombre');

            Swal.fire({
                title: '<span style="color: #1e293b">Anular Inscripción</span>',
                html: `¿Estás seguro de que deseas anular la inscripción de:<br><br><strong style="font-size: 1.2rem; color: #1e293b;">${nombreEstudiante}</strong>?<br><br>El alumno ya no aparecerá en la nómina de este grado.`,
                icon: 'warning',
                iconColor: '#FFD000', 
                showCancelButton: true,
                confirmButtonColor: '#1e293b', 
                cancelButtonColor: '#6c757d',
                confirmButtonText: '<i class="bi bi-check-circle-fill me-2"></i>Sí, anular inscripción',
                cancelButtonText: 'Cancelar',
                borderRadius: '20px',
                background: '#ffffff',
                customClass: {
                    popup: 'shadow-lg rounded-4 border-0',
                    title: 'fw-bold',
                    confirmButton: 'rounded-pill px-4 fw-bold',
                    cancelButton: 'rounded-pill px-4'
                }
            }).then((result) => {
                if (result.isConfirmed) {
                    window.location.href = urlEliminar;
                }
            });
        });
    });
    // ==========================================
});

/**
* 1. MÓDULO: BÚSQUEDA DE ESTUDIANTES (MODAL)
*/
async function initBusquedaEstudiante() {
    const btnBuscar = document.getElementById('btn_buscar_est');
    const inputDoc = document.getElementById('doc_busqueda');
    const resDiv = document.getElementById('resultado_busqueda');

    btnBuscar.addEventListener('click', async function() {
        const ci = inputDoc.value.trim();
        if (!ci) { 
            alert("Por favor, ingrese un número de documento."); 
            return; 
        }

        const originalHTML = btnBuscar.innerHTML;
        btnBuscar.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';
        btnBuscar.disabled = true;

        try {
            const params = new URLSearchParams();
            params.append('documento', ci);

            const response = await fetch('/buscar_estudiante', { 
                method: 'POST', 
                body: params 
            });
            
            const data = await response.json();

            if (data.error) {
                alert("Estudiante no encontrado o se encuentra inactivo.");
                resetCamposEstudiante();
            } else {
                document.getElementById("nombre_est_confirmado").innerText = `Seleccionado: ${data.nombre} ${data.apellido}`;
                document.getElementById("estudiante_id_hidden").value = data.id;

                resDiv.style.opacity = '0';
                resDiv.style.display = 'block';
                resDiv.offsetHeight; 
                resDiv.style.transition = 'opacity 0.4s ease-in-out';
                resDiv.style.opacity = '1';
            }

        } catch (error) {
            console.error('Error:', error);
            alert("Hubo un problema al conectar con el servidor.");
        } finally {
            btnBuscar.innerHTML = originalHTML;
            btnBuscar.disabled = false;
        }
    });
}

function resetCamposEstudiante() {
    const resDiv = document.getElementById('resultado_busqueda');
    const inputId = document.getElementById('estudiante_id_hidden');
    if(resDiv) resDiv.style.display = 'none';
    if(inputId) inputId.value = "";
}

/**
 * 2. MÓDULO: EXPORTACIÓN PDF (jsPDF)
 */
function generarDescargaDirecta(idTablaOriginal, nombreArchivo, nombreGrado, periodoLectivo) {
    const tablaOriginal = document.getElementById(idTablaOriginal);
    if (!tablaOriginal) return;

    const { jsPDF } = window.jspdf;
    const doc = new jsPDF('p', 'mm', 'a4');
    
    const infoCiclo = periodoLectivo || new Date().getFullYear();
    const pageWidth = doc.internal.pageSize.getWidth();
    const marginLeft = 15;
    const center = pageWidth / 2;

    doc.setFont("helvetica", "bold").setFontSize(10); 
    doc.setFillColor(52, 58, 64);
    doc.roundedRect(marginLeft, 10, 40, 8, 1, 1, 'F'); 
    doc.setTextColor(255, 255, 255);
    doc.text(`${infoCiclo}`, marginLeft + 5, 15.5);

    doc.setFontSize(20).setTextColor(0, 0, 0);
    doc.text("NÓMINA DE ESTUDIANTES", center, 30, { align: "center" });
    
    doc.setFontSize(14).setTextColor(13, 110, 253);
    doc.text(nombreGrado.toUpperCase(), center, 38, { align: "center" });
    
    doc.setDrawColor(200, 200, 200).setLineWidth(0.5).line(marginLeft, 42, pageWidth - marginLeft, 42);
        
    const filas = Array.from(tablaOriginal.querySelectorAll('tbody tr')).map((tr, i) => [
        i + 1, 
        tr.cells[1].innerText.trim(), 
        tr.cells[2].innerText.trim(), 
        tr.cells[3].innerText.trim()
    ]);

    doc.autoTable({
        head: [['#', 'Apellido', 'Nombre', 'Documento']],
        body: filas,
        startY: 48,
        margin: { left: marginLeft, right: marginLeft },
        theme: 'grid',
        headStyles: { fillColor: [52, 58, 64], halign: 'center' },
        columnStyles: { 0: { halign: 'center', cellWidth: 12 }, 3: { halign: 'center' } }
    });

    doc.save(`${nombreArchivo}_${infoCiclo}.pdf`);
}