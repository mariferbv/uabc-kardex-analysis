import psycopg2
from .base_repository import IKardexRepository

class SqlRepository(IKardexRepository):
    def __init__(self, db_config: dict):
        self.config = db_config

    def save(self, student: dict) -> bool:
        conn = None
        try:
            conn = psycopg2.connect(**self.config)
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO unidad_academica (nombre_unidad) 
                VALUES (%s) ON CONFLICT (nombre_unidad) DO NOTHING;
            """, ("Facultad de Ciencias Químicas e Ingeniería",))

            cur.execute("""
                INSERT INTO programa_educativo (id_unidad, nombre_programa)
                VALUES ((SELECT id_unidad FROM unidad_academica LIMIT 1), %s)
                ON CONFLICT (nombre_programa) DO NOTHING;
            """, (student['career'],))

            plan_clave = student['plans'][0] if student['plans'] else "N/A"
            cur.execute("""
                INSERT INTO plan_estudio (id_programa_educativo, clave_plan)
                VALUES ((SELECT id_programa_educativo FROM programa_educativo WHERE nombre_programa=%s), %s)
                ON CONFLICT (clave_plan) DO NOTHING;
            """, (student['career'], plan_clave))

            cur.execute("""
                INSERT INTO alumno (matricula, id_plan_estudio, nombre_completo)
                VALUES (%s, (SELECT id_plan_estudio FROM plan_estudio WHERE clave_plan=%s), %s)
                ON CONFLICT (matricula) DO UPDATE SET nombre_completo = EXCLUDED.nombre_completo;
            """, (student['id'], plan_clave, student['name']))

            cur.execute("""
                INSERT INTO kardex (matricula, fecha_emision, archivo_origen)
                VALUES (%s, %s, %s) RETURNING id_kardex;
            """, (student['id'], student['processed_at'], student['career']))
            id_kardex = cur.fetchone()[0]

            cur.execute("""
                INSERT INTO kardex_resumen (id_kardex, req_opt_pdf, req_prac_pdf, cur_oblig_pdf, cur_oblig_calc, is_validated)
                VALUES (%s, %s, %s, %s, %s, %s);
            """, (id_kardex, student.get('pdf_summary_elective', 0), student.get('pdf_summary_internship', 0), 
                  student.get('pdf_summary_obligatory', 0), student['calculated_obligatory'], student['is_validated']))

            for course in student['courses']:
                cur.execute("INSERT INTO etapa (nombre) VALUES (%s) ON CONFLICT (nombre) DO NOTHING;", (course['stage'],))
                cur.execute("""
                    INSERT INTO asignatura (clave_asignatura, nombre_asignatura, creditos) 
                    VALUES (%s, %s, %s) ON CONFLICT (clave_asignatura) DO NOTHING;
                """, (course['course_id'], course['course_name'], course['credits']))

                cur.execute("""
                    INSERT INTO kardex_asignatura (
                        id_kardex, id_asignatura, id_etapa, tipo_examen,
                        calificacion, fecha_examen, unidad_ext ,no_oficio, periodo, plan_estudio_materia
                    ) VALUES (%s, 
                        (SELECT id_asignatura FROM asignatura WHERE clave_asignatura=%s),
                        (SELECT id_etapa FROM etapa WHERE nombre=%s),
                        %s, %s, %s, %s, %s, %s, %s);
                """, (id_kardex, course['course_id'], course['stage'], course['exam_type'], course['grade'],
                      course['exam_date'], course['extended_unit'], course['reference_number'], course['period'], course['study_plan']))

            conn.commit()
            print(f"Success: Student {student['id']} persisted to Supabase")
            return True

        except Exception as e:
            if conn: conn.rollback()
            print(f"Database Error: {e}")
            return False
        finally:
            if conn: conn.close()