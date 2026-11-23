import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from base_datos import *

app = Flask(__name__)
app.secret_key = "12345k00007*"

# ----------------------------------------- PROCESADOR DE CONTEXTO GLOBAL ------------------------------------------
@app.context_processor
def inject_global_vars():
    periodo_actual = obtener_periodo_activo()
    
    # El sistema es "editable" si el periodo actual NO está cerrado
    es_editable = False
    if periodo_actual:
        # Verificamos si existe la columna estado y si es 'abierto'
        es_editable = (periodo_actual[4] == 'abierto') if len(periodo_actual) > 4 else True
    
    return {
        'current_year': datetime.datetime.now().year,
        'periodo_nombre': periodo_actual[1] if periodo_actual else "Sin Periodo",
        'es_periodo_editable': es_editable
    }

#------------------------------------------------------------------------------------------------------------------
# ------------------------------------------- INICIO / RAÍZ -------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------

@app.route('/')
def index():
    return render_template('inicio.html')

#------------------------------------------------------------------------------------------------------------------
# ------------------------------------------- INSCRIPCIONES -------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------

@app.route('/inscripciones')
def inscripciones():
    try:
        # 1. Obtener el periodo activo global (el marcado como 'En Uso')
        p_actual = obtener_periodo_activo()
        id_activo_global = p_actual[0] if p_actual else None
        
        # 2. Obtener el periodo que el usuario quiere VER (por defecto el activo)
        periodo_id_consulta = request.args.get('periodo_id', id_activo_global, type=int)
        
        # 3. Obtener los datos del periodo consultado para verificar su estado real
        info_periodo = obtener_periodo_por_id(periodo_id_consulta)
        
        # LÓGICA DE PERMISOS: Basada en el estado del periodo consultado
        # Si el estado es 'cerrado', es historial y NO es editable
        es_historial = False
        es_periodo_editable = False
        
        if info_periodo:
            es_historial = (info_periodo[4] == 'cerrado')
            es_periodo_editable = (info_periodo[4] == 'abierto')

        grados = obtener_grados()
        inscripciones_por_grado = {}

        for grado in grados:
            # Traemos datos de la tabla de inscripciones (en vivo)
            filas_crudas = obtener_inscripciones_por_grado(grado[0], periodo_id_consulta)
            
            # Si no hay (y es historial), traemos del snapshot JSON
            if not filas_crudas and es_historial:
                filas_crudas = obtener_nomina_historica(periodo_id_consulta, grado[0])

            alumnos_procesados = []
            for f in filas_crudas:
                # Traductor Universal
                if isinstance(f, (tuple, list)):
                    d = {
                        'id': f[0] if len(f) > 0 else None,
                        'apellido': f[1] if len(f) > 1 else '',
                        'nombre': f[2] if len(f) > 2 else '',
                        'documento': f[3] if len(f) > 3 else '',
                        'fecha_nacimiento': f[4] if len(f) > 4 else None,
                        'fecha_inscripcion': f[5] if len(f) > 5 else None
                    }
                elif isinstance(f, dict):
                    d = f
                else: continue

                # Formateo de fechas seguro
                for campo in ['fecha_nacimiento', 'fecha_inscripcion']:
                    valor = d.get(campo)
                    if valor:
                        if hasattr(valor, 'strftime'):
                            d[campo] = valor.strftime('%d/%m/%Y')
                        elif isinstance(valor, str) and '-' in valor:
                            try:
                                p = valor.split(' ')[0].split('-')
                                d[campo] = f"{p[2]}/{p[1]}/{p[0]}"
                            except: d[campo] = valor
                    else:
                        d[campo] = "---"
                
                alumnos_procesados.append(d)
            
            inscripciones_por_grado[grado[0]] = alumnos_procesados

        return render_template(
            "inscripciones.html",
            grados=grados,
            inscripciones_por_grado=inscripciones_por_grado,
            es_historial=es_historial,
            es_periodo_editable=es_periodo_editable, 
            periodo_seleccionado_id=periodo_id_consulta,
            id_periodo_activo=id_activo_global
        )
    except Exception as e:
        import traceback
        print(f"ERROR CRÍTICO: {traceback.format_exc()}")
        return f"Error: {e}", 500

@app.route('/agregar_inscripcion', methods=['POST'])
def agregar_inscripcion_ruta():
    # 1. Obtención de datos
    estudiante_id = request.form.get('estudiante_id')
    grado_id = request.form.get('grado')
    fecha_inscripcion = request.form.get('fecha_inscripcion')
    
    # 2. Obtener el periodo que está marcado como activo en la sesión
    periodo_actual = obtener_periodo_activo()
    
    if not periodo_actual:
        flash("🚫 No hay un periodo activo seleccionado en el sistema.", "danger")
        return redirect(url_for('inscripciones'))

    # 3. BLOQUEO DE SEGURIDAD POR ESTADO
    # Si el estado es 'cerrado', bloqueamos cualquier inserción nueva.
    if len(periodo_actual) > 4 and periodo_actual[4] == 'cerrado':
        flash(f"🚫 El ciclo {periodo_actual[1]} está CERRADO. No se permiten nuevas matrículas en periodos históricos.", "warning")
        return redirect(url_for('inscripciones'))

    # 4. Validación de campos obligatorios
    if not estudiante_id or not grado_id or not fecha_inscripcion:
        flash("⚠️ Por favor, busque un alumno y complete todos los campos obligatorios.", "danger")
        return redirect(url_for('inscripciones'))

    periodo_id = periodo_actual[0]

    # 5. Validación de duplicados (Evitar doble inscripción en el mismo ciclo)
    if tiene_matricula_periodo(estudiante_id, periodo_id):
        flash("ℹ️ El estudiante ya se encuentra matriculado en este ciclo lectivo.", "info")
        return redirect(url_for('inscripciones'))

    # 6. Ejecución del registro
    if agregar_inscripcion(estudiante_id, grado_id, periodo_id, fecha_inscripcion):
        flash(f"✅ ¡Éxito! Estudiante matriculado correctamente en {periodo_actual[1]}.", "success")
    else:
        flash("❌ Error técnico: No se pudo completar el registro en la base de datos.", "danger")

    return redirect(url_for('inscripciones'))


@app.route('/eliminar_inscripcion/<int:id>')
def eliminar_inscripcion_ruta(id):
    # En lugar de mirar el año del reloj, miramos si el registro 
    # pertenece a un periodo que todavía está 'abierto'
    exito, mensaje = eliminar_inscripcion(id)
    
    if exito:
        flash(mensaje, "success")
    else:
        flash(mensaje, "danger")
        
    return redirect(url_for('inscripciones'))


@app.route('/promover_grado/<int:grado_id>')
def promover_grado_ruta(grado_id):
    periodo_actual = obtener_periodo_activo()
    
    if not periodo_actual or periodo_actual[4] == 'cerrado':
        flash("Acción no permitida en este periodo.", "danger")
        return redirect(url_for('inscripciones'))

    exito, mensaje = promover_alumnos_grado(grado_id, periodo_actual[0])
    
    if exito:
        flash(mensaje, "success")
    else:
        flash(mensaje, "warning")
        
    return redirect(url_for('inscripciones'))


#------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------- ESTUDIANTES -----------------------------------------------------
#------------------------------------------------------------------------------------------------------------------


@app.route('/estudiantes')
def estudiantes():
    lista = obtener_estudiantes()
    return render_template('estudiantes.html', estudiantes=lista)

@app.route('/buscar_estudiante', methods=['POST'])
def buscar_estudiante():
    documento = request.form.get('documento', '').strip()
    est = obtener_estudiante_por_documento(documento)
    if est:
        fecha_nac = est[4].strftime('%Y-%m-%d') if isinstance(est[4], datetime.date) else str(est[4])
        return jsonify({
            'id': est[0],
            'nombre': est[1],
            'apellido': est[2],
            'fecha_nacimiento': fecha_nac
        })
    return jsonify({'error': 'Estudiante no encontrado'}), 404

@app.route('/crear_estudiante', methods=['POST'])
def crear_estudiante_ruta():
    nombre = request.form["nombre"].strip()
    apellido = request.form["apellido"].strip()
    documento = request.form["documento"].strip()
    fecha_nacimiento = request.form["fecha_nacimiento"].strip()

    if not nombre or not apellido or not documento or not fecha_nacimiento:
        flash("Todos los campos son obligatorios", "danger")
        return redirect(url_for("estudiantes"))

    resultado = crear_estudiante(nombre, apellido, documento, fecha_nacimiento)

    if resultado == "creado":
        flash(f"Estudiante {apellido} registrado con éxito.", "success")
    elif resultado == "reactivado":
        flash(f"¡Bienvenido de nuevo! Se ha reactivado la ficha de {nombre} {apellido}.", "info")
    elif resultado == "duplicado":
        flash("Este documento ya pertenece a un alumno activo en el sistema.", "warning")
    else:
        flash("Hubo un problema técnico al procesar el registro.", "danger")
    
    return redirect(url_for("estudiantes"))


@app.route('/actualizar_estudiante/<int:id>', methods=['POST'])
def actualizar_estudiante_ruta(id):
    # Flask recibe los datos del modal automáticamente por el método POST
    nombre = request.form['nombre']
    apellido = request.form['apellido']
    documento = request.form['documento']
    fecha_nacimiento = request.form['fecha_nacimiento']
    
    if actualizar_estudiante(id, nombre, apellido, documento, fecha_nacimiento):
        flash("Datos actualizados correctamente", "success")
    else:
        flash("Error al actualizar los datos", "danger")
    
    # Al terminar, recargamos la misma página de estudiantes
    return redirect(url_for('estudiantes'))

@app.route('/eliminar_estudiante/<int:id>')
def eliminar_estudiante_ruta(id):
    # Verificamos si tiene historial de inscripciones (en cualquier año)
    if obtener_inscripcion_por_estudiante(id):
        flash("¡Atención! El estudiante posee historial de inscripciones. "
              "Debe eliminar sus registros previos antes de darlo de baja definitiva.", "danger")
        return redirect(url_for('estudiantes'))

    if dar_de_baja_estudiante(id):
        flash("Estudiante enviado al archivo de inactivos correctamente.", "success")
    else:
        flash("Error al procesar la baja del estudiante", "danger")
    
    return redirect(url_for('estudiantes'))

@app.route('/eliminar_definitivo/<int:id>', methods=['POST'])
def eliminar_estudiante_definitivo_ruta(id):
    if eliminar_estudiante_definitivo(id):
        flash("Estudiante eliminado permanentemente de la base de datos.", "success")
    else:
        flash("No se pudo eliminar al estudiante. Verifique si tiene datos asociados.", "danger")
    return redirect(url_for('estudiantes_inactivos_ruta'))

@app.route('/estudiantes/archivo')
def estudiantes_inactivos_ruta():
    inactivos = obtener_estudiantes_inactivos() # <--- Usar la función de base_datos.py
    return render_template("estudiantes_inactivos.html", estudiantes=inactivos)

@app.route('/estudiantes/reactivar/<int:id>', methods=['POST'])
def reactivar_estudiante_ruta(id):
    con = obtener_conexion()
    cur = con.cursor()
    try:
        cur.execute("UPDATE estudiantes SET activo = TRUE WHERE id = %s", (id,))
        con.commit()
        flash("Estudiante reactivado con éxito", "success")
    except Exception as e:
        con.rollback()
        flash("Error al reactivar", "danger")
    finally:
        con.close()
    return redirect(url_for('estudiantes'))


#------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------- GRADOS ----------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------


@app.route('/grados')
def grados():
    lista = obtener_grados()
    return render_template("grados.html", grados=lista)

@app.route('/agregar_grado', methods=['POST'])
def agregar_grado_ruta():
    nombre = request.form['nombre'].strip()
    descripcion = request.form['descripcion'].strip()

    if not nombre:
        flash("El nombre del grado es obligatorio", "danger")
        return redirect(url_for('grados'))

    if agregar_grado(nombre, descripcion):
        flash("Grado agregado", "success")
    else:
        flash("Error al agregar grado", "danger")
    return redirect(url_for('grados'))


@app.route('/actualizar_grado/<int:id>', methods=['POST'])
def actualizar_grado_ruta(id):
    nombre = request.form.get('nombre')
    descripcion = request.form.get('descripcion')
    # Manejamos el valor vacío del select como None
    sig_id = request.form.get('siguiente_grado_id')
    siguiente_id = int(sig_id) if sig_id else None
    
    if actualizar_grado(id, nombre, descripcion, siguiente_id):
        flash("Grado actualizado y conectado correctamente", "success")
    else:
        flash("Error al actualizar el grado", "danger")
    return redirect(url_for('grados'))

@app.route('/eliminar_grado/<int:id>')
def eliminar_grado_ruta(id):
    eliminar_grado(id)
    flash("Grado eliminado", "success")
    return redirect(url_for('grados'))

@app.route('/actualizar_orden_grados', methods=['POST'])
def actualizar_orden_grados():
    data = request.get_json()
    if not data or 'orden' not in data:
        return "Datos inválidos", 400
    con = None  
    try:
        con = obtener_conexion()
        cur = con.cursor()
    
        for item in data['orden']:
            cur.execute("UPDATE grados SET orden=%s WHERE id=%s", (item['orden'], item['id']))
            
        con.commit()
        return "OK", 200
    except Exception as e:
        if con:
            con.rollback()
        return str(e), 500
    finally:
        if con:
            con.close()



#------------------------------------------------------------------------------------------------------
#------------------------------------------------CONFIGURACIÓN-----------------------------------------
#------------------------------------------------------------------------------------------------------


@app.route('/configuracion')
def configuracion():
    periodos = obtener_todos_los_periodos() 
    
    # Llamamos a la función de backups
    lista_backups = obtener_backups()
    
    # Pasar 'backups=lista_backups' al HTML
    return render_template('configuracion.html', 
                           periodos=periodos, 
                           backups=lista_backups)


@app.route('/nuevo_periodo', methods=['POST'])
def nuevo_periodo_ruta():
    nombre = request.form['nombre']
    anio = int(request.form['anio'])
    anio_hoy = datetime.datetime.now().year
    
    # Validación: No permitir crear años pasados como nuevos
    if anio < anio_hoy:
        flash("No puedes abrir un ciclo con un año pasado.", "warning")
        return redirect(url_for('configuracion'))

    periodo_a_cerrar = obtener_periodo_activo()
    
    if periodo_a_cerrar:
        # Usamos la nueva función que archiva y bloquea
        if cerrar_y_promover_alumnos(periodo_a_cerrar[0], nombre, anio):
            flash(f"Ciclo {nombre} activado y año {periodo_a_cerrar[2]} bloqueado.", "success")
        else:
            flash("Error al procesar el cierre de ciclo.", "danger")
    else:
        # Si no había periodos, creamos el primero normal
        crear_periodo(nombre, anio)
        flash("Primer periodo creado con éxito.", "success")
        
    return redirect(url_for('configuracion'))


@app.route('/cambiar_periodo/<int:id>')
def cambiar_periodo_ruta(id):
    if activar_periodo(id):
        flash("Periodo lectivo actualizado correctamente", "success")
    else:
        flash("No se pudo cambiar el periodo", "danger")
    return redirect(url_for('configuracion'))


@app.route('/restablecer_sistema')
def restablecer_sistema_ruta():
    if restablecer_periodos_maestro():
        # Al no pasarle año, la función toma el del reloj automáticamente
        flash("Sistema restablecido al año actual correctamente.", "success")
    else:
        flash("Error crítico al intentar restablecer el sistema.", "danger")
    return redirect(url_for('configuracion'))


@app.route('/restaurar_backup/<int:id>')
def restaurar_backup_ruta(id):
    if restaurar_backup_por_id(id):
        flash("¡Viaje en el tiempo exitoso! Los datos han sido restaurados.", "success")
    else:
        flash("Error al intentar restaurar los datos.", "danger")
    return redirect(url_for('configuracion'))


@app.route('/limpieza_total')
def limpieza_total_ruta():
    if limpiar_toda_la_base_datos():
        flash("Sistema blanqueado exitosamente. Se ha creado un nuevo periodo inicial.", "success")
    else:
        flash("Error al intentar limpiar la base de datos.", "danger")
    return redirect(url_for('configuracion'))


#------------------------------------------------------------------------------------------------------
# ------------------------------------------- LANZADOR ------------------------------------------------
#------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)






