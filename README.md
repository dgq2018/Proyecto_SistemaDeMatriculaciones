Se recomienda tener instaladas las siguientes herramientas en el ordenador:

                                 Visual Studio Code - PostgreSQL (pgAdmin) - Python 3 

Para instalar los requerimientos del proyecto escribir el siguiente comando en CMD o en la terminal de Visual Studio Code: 
				
					pip install -r requirements.txt


--------------------------------------------------------------------------------------------------------------------------
--------------------------------------------------------------------------------------------------------------------------

El sistema es una página web de gestión académica e inscripciones, pensada para administrar todo el ciclo escolar de una institución educativa.

Funciona en 4 pasos muy simples:

1) Abre el año escolar (Periodos): Primero creas el año lectivo actual (por ejemplo "Ciclo 2026"). Mientras ese año está abierto, puedes inscribir alumnos; cuando termina el año, lo cierras para que los datos no se cambien por error y guardas ese historial.

2) Crea los grados o cursos: Cargas los cursos de la institución (como 1º Grado, etc.) y luego indicas cuál es el siguiente curso, para que al año próximo el sistema detecte el grado al que va a promoverse cada alumno.

3) Registra a los alumnos: Guardas los datos básicos de cada estudiante. Si un alumno deja de asistir, no hace falta borrarlo: pasa a una lista de inactivos y se puede volver a activar si regresa, o lo borras definitivamente: por ejemplo si el alumno solicita la eliminación de sus datos.

4) Inscribe y descarga listas: Eliges al alumno por su documento y lo anotas en su curso dentro del año abierto (el sistema avisa si ya está anotado para no duplicarlo). Además, puedes pasar de grado automáticamente a los alumnos del año anterior y descargar las listas de cada curso en PDF.

Por último tiene una sección de Configuración donde se puede guardar copias de seguridad de los datos y restaurarlas si alguna vez se necesita hacerlo. También tiene una opción de blanqueamiento total de la base de datos, lo elimina todo y no es posible generar copias de seguridad. En esta sección es donde se crean los periodos (años) del sistema.
