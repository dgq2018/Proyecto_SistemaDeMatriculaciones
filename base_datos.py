import psycopg2
import pandas as pd
import datetime
import json
import os

def obtener_conexion():
    return psycopg2.connect(
        host="localhost",
        database="proyecto_matriculaciones",
        user="DB_USUARIO", #colocar el usuario que aparece en el gestor de base de datos de su pc
        password="DB_CONTRASEÑA" #colocar la contraseña del gestor de base de datos de su pc
    )

#------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------- ESTUDIANTES ---------------------------------------------------
#------------------------------------------------------------------------------------------------------------------

def obtener_estudiantes():
    con = obtener_conexion()
    cur = con.cursor()
    cur.execute("""
        SELECT id, nombre, apellido, documento, fecha_nacimiento
        FROM estudiantes
        WHERE activo = TRUE  
        ORDER BY apellido ASC, nombre ASC
    """)
    rows = cur.fetchall()
    con.close()
    return rows

def crear_estudiante(nombre, apellido, documento, fecha_nacimiento):
    con = obtener_conexion()
    cur = con.cursor()
    try:
        # 1. Verificar si ya existe (aunque esté inactivo)
        cur.execute("SELECT id, activo FROM estudiantes WHERE documento = %s", (documento,))
        existente = cur.fetchone()

        if existente:
            id_est, esta_activo = existente
            if not esta_activo:
                # Si existe pero está de baja, lo reactivamos y actualizamos sus datos
                cur.execute("""
                    UPDATE estudiantes 
                    SET nombre=%s, apellido=%s, fecha_nacimiento=%s, activo=TRUE 
                    WHERE id=%s
                """, (nombre, apellido, fecha_nacimiento, id_est))
                con.commit()
                return "reactivado"
            else:
                return "duplicado" 

        # 2. Si no existe en absoluto, lo creamos 
        cur.execute("""
            INSERT INTO estudiantes (nombre, apellido, documento, fecha_nacimiento, activo) 
            VALUES (%s,%s,%s,%s, TRUE)
        """, (nombre, apellido, documento, fecha_nacimiento))
        con.commit()
        return "creado"
    except Exception as e:
        print(f"Error: {e}")
        con.rollback()
        return "error"
    finally:
        con.close()


def eliminar_estudiante_definitivo(id_estudiante):
    con = obtener_conexion()
    cur = con.cursor()
    try:
        # Borramos primero sus inscripciones para evitar errores de clave foránea
        cur.execute("DELETE FROM inscripciones WHERE estudiante_id = %s", (id_estudiante,))
        # Borramos al estudiante
        cur.execute("DELETE FROM estudiantes WHERE id = %s", (id_estudiante,))
        con.commit()
        return True
    except Exception as e:
        print(f"Error al eliminar estudiante: {e}")
        con.rollback()
        return False
    finally:
        con.close()

def obtener_estudiante_por_id(id):
    con = obtener_conexion()
    cur = con.cursor()
    cur.execute("SELECT * FROM estudiantes WHERE id=%s", (id,))
    est = cur.fetchone()
    con.close()
    return est

def actualizar_estudiante(id, nombre, apellido, documento, fecha_nacimiento):
    con = obtener_conexion()
    cur = con.cursor()
    try:
        cur.execute("""
            UPDATE estudiantes
            SET nombre=%s, apellido=%s, documento=%s, fecha_nacimiento=%s
            WHERE id=%s
        """, (nombre, apellido, documento, fecha_nacimiento, id))
        con.commit()
        return True
    except:
        con.rollback()
        return False
    finally:
        con.close()

def obtener_estudiante_por_documento(documento):
    con = obtener_conexion()
    cur = con.cursor()
    cur.execute("SELECT * FROM estudiantes WHERE documento=%s AND activo = TRUE", (documento,))
    est = cur.fetchone()
    con.close()
    return est

def dar_de_baja_estudiante(id):
    con = obtener_conexion()
    cur = con.cursor()
    try:
        cur.execute("UPDATE estudiantes SET activo = FALSE WHERE id = %s", (id,))
        con.commit()
        return True
    except Exception as e:
        print(f"Error en baja: {e}")
        con.rollback()
        return False
    finally:
        con.close()

def obtener_estudiantes_activos():
    con = obtener_conexion()
    cur = con.cursor()
    cur.execute("SELECT id, nombre, apellido, documento, fecha_nacimiento FROM estudiantes WHERE activo = TRUE ORDER BY apellido ASC")
    res = cur.fetchall()
    con.close()
    return res

def obtener_estudiantes_inactivos():
    con = obtener_conexion()
    cur = con.cursor()
    # Traemos solo a los que no están activos
    cur.execute("""
        SELECT id, apellido, nombre, documento, fecha_nacimiento 
        FROM estudiantes 
        WHERE activo = FALSE 
        ORDER BY apellido ASC
    """)
    rows = cur.fetchall()
    con.close()
    return rows

def tiene_matricula_periodo(estudiante_id, periodo_id): 
    con = obtener_conexion()
    cur = con.cursor()
    try:
        cur.execute("""
            SELECT COUNT(*) FROM inscripciones 
            WHERE estudiante_id = %s AND periodo_id = %s
        """, (estudiante_id, periodo_id))
        
        resultado = cur.fetchone()[0]
        return resultado > 0
    except Exception as e:
        print(f"Error al verificar matrícula: {e}")
        return False
    finally:
        con.close()

#------------------------------------------------------------------------------------------------------------------
# ----------------------------------------------------- GRADOS ----------------------------------------------------
#------------------------------------------------------------------------------------------------------------------

def obtener_grados():
    con = obtener_conexion()
    cur = con.cursor()
    cur.execute("""
        SELECT id, nombre, descripcion, orden, siguiente_grado_id 
        FROM grados 
        ORDER BY orden ASC
    """)
    rows = cur.fetchall()
    con.close()
    return rows

def agregar_grado(nombre, descripcion):
    con = obtener_conexion()
    cur = con.cursor()
    try:
        # Obtener el siguiente orden
        cur.execute("SELECT COALESCE(MAX(orden), 0) + 1 FROM grados")
        orden = cur.fetchone()[0]
        cur.execute("INSERT INTO grados (nombre, descripcion, orden) VALUES (%s,%s,%s)", (nombre, descripcion, orden))
        con.commit()
        return True
    except:
        con.rollback()
        return False
    finally:
        con.close()

def obtener_grado_por_id(id):
    con = obtener_conexion()
    cur = con.cursor()
    cur.execute("SELECT * FROM grados WHERE id=%s", (id,))
    dato = cur.fetchone()
    con.close()
    return dato

def actualizar_grado(id, nombre, descripcion, siguiente_grado_id=None):
    con = obtener_conexion()
    cur = con.cursor()
    try:
        cur.execute("""
            UPDATE grados 
            SET nombre = %s, descripcion = %s, siguiente_grado_id = %s 
            WHERE id = %s
        """, (nombre, descripcion, siguiente_grado_id, id))
        con.commit()
        return True
    except Exception as e:
        con.rollback()
        return False
    finally:
        con.close()

def eliminar_grado(id):
    con = obtener_conexion()
    cur = con.cursor()
    cur.execute("DELETE FROM grados WHERE id=%s", (id,))
    con.commit()
    con.close()

    
#------------------------------------------------------------------------------------------------------------------
# -------------------------------------------------- INSCRIPCIONES ------------------------------------------------
#------------------------------------------------------------------------------------------------------------------

def obtener_inscripciones_por_grado(grado_id, periodo_id):
    """
    Retorna estudiantes inscritos en un grado Y un periodo específico.
    """
    # Si no hay periodo_id (es None), devolvemos lista vacía de inmediato
    if not periodo_id:
        return []

    con = obtener_conexion()
    cur = con.cursor()
    cur.execute("""
        SELECT i.id, e.id AS estudiante_id, e.nombre, e.apellido, e.documento, e.fecha_nacimiento, i.fecha_inscripcion
        FROM inscripciones i
        JOIN estudiantes e ON i.estudiante_id = e.id
        WHERE i.grado_id = %s AND i.periodo_id = %s
        ORDER BY e.apellido ASC
    """, (grado_id, periodo_id))
    rows = cur.fetchall()
    columnas = [desc[0] for desc in cur.description]
    resultados = [dict(zip(columnas, row)) for row in rows]
    con.close()
    return resultados

def obtener_inscripcion_por_estudiante(estudiante_id):
    """
    Verifica si un estudiante ya tiene una inscripción activa.
    """
    con = obtener_conexion()
    cur = con.cursor()
    cur.execute("""
        SELECT id, grado_id FROM inscripciones
        WHERE estudiante_id = %s
    """, (estudiante_id,))
    dato = cur.fetchone()
    con.close()
    return dato

def agregar_inscripcion(estudiante_id, grado_id, periodo_id, fecha_inscripcion):
    """
    Registra una inscripción vinculándola a un periodo lectivo específico.
    """
    con = obtener_conexion()
    cur = con.cursor()
    try:
        cur.execute("""
            INSERT INTO inscripciones (estudiante_id, grado_id, periodo_id, fecha_inscripcion) 
            VALUES (%s, %s, %s, %s)
        """, (estudiante_id, grado_id, periodo_id, fecha_inscripcion))
        con.commit()
        return True
    except Exception as e:
        print(f"Error al inscribir: {e}")
        con.rollback()
        return False
    finally:
        con.close()


def eliminar_inscripcion(id_inscripcion):
    con = obtener_conexion()
    cur = con.cursor()
    try:
        # 1. Buscamos el estado del periodo al que pertenece ESTA inscripción específica
        cur.execute("""
            SELECT p.estado 
            FROM inscripciones i
            JOIN periodos p ON i.periodo_id = p.id
            WHERE i.id = %s
        """, (id_inscripcion,))
        res = cur.fetchone()
        
        # 2. Si el periodo de ese registro está 'cerrado', se bloquea
        if res and res[0] == 'cerrado':
            return False, "No puedes modificar registros de un ciclo lectivo ya cerrado."

        # 3. Si está abierto, se procede
        cur.execute("DELETE FROM inscripciones WHERE id = %s", (id_inscripcion,))
        con.commit()
        return True, "Registro eliminado correctamente."
    except Exception as e:
        con.rollback()
        return False, str(e)
    finally:
        con.close()

def tiene_matricula_periodo(estudiante_id, periodo_id):
    """
    Evita que el alumno sea inscrito dos veces en el mismo ciclo.
    """
    con = obtener_conexion()
    cur = con.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM inscripciones 
        WHERE estudiante_id = %s AND periodo_id = %s
    """, (estudiante_id, periodo_id))
    existe = cur.fetchone()[0] > 0
    con.close()
    return existe


def promover_alumnos_grado(grado_destino_id, periodo_destino_id):
    con = obtener_conexion()
    cur = con.cursor()
    try:
        # 1. Identificar grado anterior
        cur.execute("SELECT id FROM grados WHERE siguiente_grado_id = %s", (grado_destino_id,))
        res = cur.fetchone()
        if not res: return False, "No hay grado anterior configurado."
        grado_origen_id = res[0]

        # 2. Obtener el Snapshot
        cur.execute("""
            SELECT nominas_json FROM historial_nominas 
            WHERE grado_id = %s ORDER BY id DESC LIMIT 1
        """, (grado_origen_id,))
        
        resultado = cur.fetchone()
        if not resultado: return False, "No hay historial para promover."

        estudiantes_historial = resultado[0] 
        if isinstance(estudiantes_historial, str): 
            estudiantes_historial = json.loads(estudiantes_historial)
        
        contador = 0
        for est_viejo in estudiantes_historial:
            # EXTRAEMOS EL DOCUMENTO (que es único y no cambia)
            documento = est_viejo.get('documento')
            if not documento: continue

            # BUSCAMOS EL NUEVO ID usando el documento
            cur.execute("SELECT id FROM estudiantes WHERE documento = %s AND activo = TRUE", (documento,))
            res_nuevo = cur.fetchone()
            
            if res_nuevo:
                nuevo_id = res_nuevo[0]
                # Intentamos inscribir con el ID actualizado
                cur.execute("""
                    INSERT INTO inscripciones (estudiante_id, grado_id, periodo_id, fecha_inscripcion)
                    VALUES (%s, %s, %s, CURRENT_DATE)
                    ON CONFLICT (estudiante_id, periodo_id) DO NOTHING
                """, (nuevo_id, grado_destino_id, periodo_destino_id))
                
                if cur.rowcount > 0:
                    contador += 1
            else:
                print(f"Aviso: El alumno con documento {documento} no existe en el nuevo sistema.")

        con.commit()
        return True, f"Se han promovido {contador} alumnos exitosamente con IDs actualizados."
        
    except Exception as e:
        con.rollback()
        return False, f"Error técnico: {str(e)}"
    finally:
        con.close()


#------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------- PERIODOS ------------------------------------------------------
#------------------------------------------------------------------------------------------------------------------

def obtener_periodo_activo():
    """Retorna el periodo marcado como activo (id, nombre, anio, activo, estado)"""
    con = obtener_conexion()
    cur = con.cursor()
    cur.execute("SELECT id, nombre, anio, activo, estado FROM periodos WHERE activo = TRUE LIMIT 1")
    periodo = cur.fetchone()
    con.close()
    return periodo

def obtener_todos_los_periodos():
    """Retorna todos los periodos con su estado (id, nombre, anio, activo, estado)"""
    con = obtener_conexion()
    cur = con.cursor()
    cur.execute("SELECT id, nombre, anio, activo, estado FROM periodos ORDER BY anio DESC")
    rows = cur.fetchall()
    con.close()
    return rows

def crear_periodo(nombre, anio):
    """Crea un nuevo periodo y lo marca como abierto y activo por defecto"""
    con = obtener_conexion()
    cur = con.cursor()
    try:
        # 1. Desactivamos todos los demás periodos
        cur.execute("UPDATE periodos SET activo = FALSE")
        
        # 2. Insertamos el nuevo con estado 'abierto'
        cur.execute("""
            INSERT INTO periodos (nombre, anio, activo, estado) 
            VALUES (%s, %s, TRUE, 'abierto')
        """, (nombre, anio))
        
        con.commit()
        return True
    except Exception as e:
        print(f"Error al crear periodo: {e}")
        con.rollback()
        return False
    finally:
        con.close()

def activar_periodo(periodo_id):
    """Cambia el periodo activo sin alterar el estado (abierto/cerrado)"""
    con = obtener_conexion()
    cur = con.cursor()
    try:
        cur.execute("UPDATE periodos SET activo = FALSE")
        cur.execute("UPDATE periodos SET activo = TRUE WHERE id = %s", (periodo_id,))
        con.commit()
        return True
    except Exception as e:
        con.rollback()
        return False
    finally:
        con.close()


def obtener_periodo_por_id(id_periodo):
    con = obtener_conexion()
    cur = con.cursor()
    try:
        # Traemos los datos básicos para validar el estado
        cur.execute("""
            SELECT id, nombre, anio, activo, estado 
            FROM periodos 
            WHERE id = %s
        """, (id_periodo,))
        return cur.fetchone()
    except Exception as e:
        print(f"Error al obtener periodo por ID: {e}")
        return None
    finally:
        con.close()


#------------------------------------------------------------------------------------------------------------------
#----------------------------------------------------MANTENIMIENTO-------------------------------------------------
#------------------------------------------------------------------------------------------------------------------

def obtener_anio_actual():
    import datetime
    return datetime.datetime.now().year


def restablecer_periodos_maestro():
    con = obtener_conexion()
    cur = con.cursor()
    try:
        # --- 1. CAPTURA DE DATOS TOTAL (BACKUP) ---
        cur.execute("SELECT * FROM estudiantes")
        estudiantes = cur.fetchall()
        
        cur.execute("SELECT * FROM periodos")
        periodos = cur.fetchall()
        
        cur.execute("SELECT * FROM inscripciones")
        inscripciones = cur.fetchall()

        # Captura el historial de nóminas
        cur.execute("SELECT * FROM historial_nominas")
        historial = cur.fetchall()

        paquete_seguridad = {
            "estudiantes": estudiantes,
            "periodos": periodos,
            "inscripciones": inscripciones,
            "historial_nominas": historial, 
            "fecha_reset": datetime.datetime.now().isoformat()
        }

        cur.execute("""
            INSERT INTO backups_sistema (datos_json, descripcion)
            VALUES (%s, %s)
        """, (json.dumps(paquete_seguridad, default=str), "Respaldo TOTAL (incluye Historial)"))

        # --- 2. ELIMINACIÓN ---
        cur.execute("DELETE FROM historial_nominas")
        cur.execute("DELETE FROM inscripciones")
        cur.execute("DELETE FROM periodos")
        
        # Reiniciar con el año actual
        anio_actual = datetime.datetime.now().year
        cur.execute("INSERT INTO periodos (nombre, anio, activo, estado) VALUES (%s, %s, TRUE, 'abierto')", 
                    (f"Ciclo Lectivo {anio_actual}", anio_actual))

        con.commit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        con.rollback()
        return False
    finally:
        con.close()


def generar_snapshot_inscripciones(periodo_id):
    con = obtener_conexion()
    cur = con.cursor()
    try:
        cur.execute("SELECT id FROM grados")
        grados = [r[0] for r in cur.fetchall()]

        for g_id in grados:
            cur.execute("""
                SELECT e.id, e.apellido, e.nombre, e.documento, e.fecha_nacimiento, i.fecha_inscripcion
                FROM inscripciones i
                JOIN estudiantes e ON i.estudiante_id = e.id
                WHERE i.periodo_id = %s AND i.grado_id = %s
            """, (periodo_id, g_id))
            
            rows = cur.fetchall()
            if rows:
                lista_json = []
                for r in rows:
                    lista_json.append({
                        'id': r[0],         
                        'apellido': r[1],
                        'nombre': r[2],
                        'documento': r[3],
                        'fecha_nacimiento': str(r[4]) if r[4] else None,
                        'fecha_inscripcion': str(r[5]) if r[5] else None
                    })
                
                cur.execute("""
                    INSERT INTO historial_nominas (periodo_id, grado_id, nominas_json, fecha_cierre)
                    VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                """, (periodo_id, g_id, json.dumps(lista_json)))

        cur.execute("DELETE FROM inscripciones WHERE periodo_id = %s", (periodo_id,))
        con.commit()
        return True
    except Exception as e:
        print(f"Error en snapshot: {e}")
        con.rollback()
        return False
    finally:
        con.close()


def obtener_nomina_historica(periodo_id, grado_id):
    con = obtener_conexion()
    cur = con.cursor()
    try:
        cur.execute("""
            SELECT nominas_json 
            FROM historial_nominas 
            WHERE periodo_id = %s AND grado_id = %s
        """, (periodo_id, grado_id))
        res = cur.fetchone()
        if res:
            datos = res[0]
            # Si es un string, lo convertimos. Si ya es lista, lo usamos directo.
            if isinstance(datos, str):
                datos = json.loads(datos)
            
            print(f"DEBUG: Encontrados {len(datos)} alumnos en el historial")
            return datos
        return []
    except Exception as e:
        print(f"Error en obtener_nomina_historica: {e}")
        return []
    finally:
        con.close()


def cerrar_y_promover_alumnos(id_viejo, nombre_nuevo, anio_nuevo):
    con = obtener_conexion()
    cur = con.cursor()
    try:
        # 1. Generar el Snapshot JSON del periodo que se cierra
        generar_snapshot_inscripciones(id_viejo)

        # 2. Marcar el periodo viejo como INACTIVO y CERRADO
        cur.execute("UPDATE periodos SET activo = FALSE, estado = 'cerrado' WHERE id = %s", (id_viejo,))

        # 3. Crear el nuevo periodo (activo y abierto)
        cur.execute("""
            INSERT INTO periodos (nombre, anio, activo, estado) 
            VALUES (%s, %s, TRUE, 'abierto')
        """, (nombre_nuevo, anio_nuevo))

        con.commit()
        return True
    except Exception as e:
        print(f"Error en promoción: {e}")
        con.rollback()
        return False
    finally:
        con.close()
    

def obtener_backups():
    con = obtener_conexion()
    cur = con.cursor()
    cur.execute("SELECT id, fecha_generacion, descripcion FROM backups_sistema ORDER BY fecha_generacion DESC")
    rows = cur.fetchall()
    con.close()
    return rows

def restaurar_backup_por_id(backup_id):
    con = obtener_conexion()
    cur = con.cursor()
    try:
        cur.execute("SELECT datos_json FROM backups_sistema WHERE id = %s", (backup_id,))
        res = cur.fetchone()
        if not res: return False
        
        datos = res[0]
        if isinstance(datos, str):
            datos = json.loads(datos)

        # 1. Limpieza total (Orden para evitar errores de llaves foráneas)
        cur.execute("DELETE FROM historial_nominas")
        cur.execute("DELETE FROM inscripciones")
        cur.execute("DELETE FROM periodos")

        # 2. Restaurar Periodos
        for p in datos.get('periodos', []):
            cur.execute("INSERT INTO periodos (id, nombre, anio, activo, estado) VALUES (%s, %s, %s, %s, %s)", p)

        # 3. Restaurar Estudiantes
        for e in datos.get('estudiantes', []):
            cur.execute("""
                INSERT INTO estudiantes (id, nombre, apellido, documento, fecha_nacimiento, activo)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET activo = EXCLUDED.activo
            """, e)

        # 4. Restaurar Historial de Nóminas
        historial = datos.get('historial_nominas', [])
        for h in historial:
            nominas_data = h[3]
            if isinstance(nominas_data, (dict, list)):
                nominas_data = json.dumps(nominas_data)
            
            cur.execute("""
                INSERT INTO historial_nominas (id, periodo_id, grado_id, nominas_json, fecha_cierre) 
                VALUES (%s, %s, %s, %s, %s)
            """, (h[0], h[1], h[2], nominas_data, h[4]))

        # 5. Restaurar Inscripciones
        inscripciones = datos.get('inscripciones', [])
        for i in inscripciones:
            cur.execute("INSERT INTO inscripciones (id, estudiante_id, grado_id, periodo_id, fecha_inscripcion) VALUES (%s, %s, %s, %s, %s)", i)

        con.commit()
        return True
    except Exception as e:
        print(f"Error crítico: {e}") 
        con.rollback()
        return False
    finally:
        con.close()


def limpiar_toda_la_base_datos():
    con = obtener_conexion()
    cur = con.cursor()
    try:
        # TRUNCATE borra el contenido de las tablas y RESTART IDENTITY vuelve los IDs a 1
        # El CASCADE se encarga de que se borren en el orden correcto
        cur.execute("""
            TRUNCATE TABLE 
                backups_sistema, 
                historial_nominas, 
                inscripciones, 
                estudiantes, 
                grados, 
                periodos 
            RESTART IDENTITY CASCADE
        """)
        
        anio_actual = datetime.datetime.now().year
        cur.execute("""
            INSERT INTO periodos (nombre, anio, activo, estado) 
            VALUES (%s, %s, TRUE, 'abierto')
        """, (f"Ciclo Lectivo {anio_actual}", anio_actual))
        
        con.commit()
        return True
    except Exception as e:
        print(f"Error al limpiar el sistema: {e}")
        con.rollback()
        return False
    finally:
        con.close()