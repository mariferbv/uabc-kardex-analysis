from datetime import datetime
from .base_parser import IKardexParser
import re

class PdfParser(IKardexParser):
    def __init__(self):
        self.re_identity = re.compile(r'Matrícula:\s+(\d{3}/?\d{5})\s+(.*?)(?=\s+(?:Plan|PAG|Programa|Unidad|$))')
        self.re_stage = re.compile(r'ETAPA\s+([A-ZÁÉÍÓÚÑ\s]+)')
        self.re_plan = re.compile(r'Plan de Estudios:\s+(\d{4}-\d)')
        
        self.re_course_flexible = re.compile(
            r'(\d{3,6})\s+'              # 1. Id
            r'(.*?)\s+'                  # 2. Name
            r'(\d{1,2})\s+'              # 3. Credits
            r'([A-Za-z]{2,5})\s+'        # 4. Exam type (Acr, Ord)
            r'([A-Z\d\.]{1,3})'          # 5. Grade
            r'(?:\s+(\d{1,2}/\d{1,2}/\d{2,4}))?'  # 6. Exam date
            r'(?:\s+([\d-]+))?'          # 7. Extended unit
            r'(?:\s+([\d/-]+))?'         # 8. Reference number
            r'\s+(\d{4}-\d)'             # 9. Period
        )
        # This regex captures the three credit values in the "Créditos Requeridos" line
        self.re_required_table = re.compile(r'Créditos\s+Requeridos:\s+(\d+)\s+(\d+)\s+(\d+)')
        self.re_summary_credits = re.compile(r'Créditos Cursados:\s+(\d+)')

        self.reset()

    def reset(self):
        self.current_student = None
        self.current_stage = "START"
        self.current_plan = "N/A"
        self.results = []

    def parse_line(self, line: str):
        # 1. Study plan
        plan_match = self.re_plan.search(line)
        if plan_match:
            self.current_plan = plan_match.group(1)
            if self.current_student:
                self.current_student['plan_set'].add(self.current_plan)

        # 2. Id
        id_match = self.re_identity.search(line)
        if id_match:
            id_num, full_name = id_match.groups()
            if not self.current_student or self.current_student['id'] != id_num:
                if self.current_student:
                    self.results.append(self.finalize())
                self.current_student = {
                    "id": id_num,
                    "name": full_name.strip(),
                    "processed_at": datetime.now().strftime("%Y-%m-%d"),
                    "courses": [],
                    "pdf_summary_obligatory": 0,
                    "pdf_summary_elective": 0,
                    "pdf_summary_internship": 0,
                    "plan_set": {self.current_plan} if self.current_plan != "N/A" else set()
                }
                return
            
        # 3. Stages
        stage_match = self.re_stage.search(line)
        if stage_match:
            self.current_stage = stage_match.group(1).strip()

        # 4. Courses
        for match in self.re_course_flexible.finditer(line):
            grade = match.group(5)
            exam_type = match.group(4)
            
            passed = self.is_passed(grade, exam_type)
            obligatory = any(s in self.current_stage for s in ["BASICA", "DISCIPLINARIA", "TERMINAL"])

            course_obj = {
                "course_id": match.group(1),
                "course_name": match.group(2).strip(),
                "credits": int(match.group(3)),
                "exam_type": exam_type,
                "grade": grade,
                "exam_date": match.group(6) if match.group(6) else None,
                "extended_unit": match.group(7) if match.group(7) else None,
                "reference_number": match.group(8) if match.group(8) else None,
                "period": match.group(9),
                "stage": self.current_stage,
                "study_plan": self.current_plan,
                "is_passed": passed,
                "is_obligatory": obligatory
            }
            self.current_student['courses'].append(course_obj)

        m_required = self.re_required_table.search(line)
        if m_required:
            # Group 1: Obligatory credits, Group 2: Elective credits, Group 3: Internship credits
            self.current_student['pdf_summary_obligatory'] = int(m_required.group(1))
            self.current_student['pdf_summary_elective'] = int(m_required.group(2))
            self.current_student['pdf_summary_internship'] = int(m_required.group(3))

    def get_results(self):
        if self.current_student:
            self.results.append(self.finalize_student())
        return self.results
    
    def is_passed(self, grade_str: str, exam_type: str) -> bool:
        grade = str(grade_str).upper()
        is_numeric_pass = grade.replace('.', '').isdigit() and float(grade) >= 60
        is_accredited = grade in ['AC', 'A'] or str(exam_type).lower() in ['acr', 'a', 'equiv', 'reval']
        return is_numeric_pass or is_accredited
    
    def finalize_student(self):
        if not self.current_student:
            return {}

        unique_passed_obligatory = {}
        for c in self.current_student['courses']:
            if c['is_passed'] and c['is_obligatory']:
                # Avoids duplicate in case the student took the same course multiple times
                unique_passed_obligatory[c['course_id']] = c['credits']

        calculated_credits = sum(unique_passed_obligatory.values())
        pdf_credits = self.current_student.get('pdf_summary_obligatory', 0)
        
        self.current_student['calculated_obligatory'] = calculated_credits
        self.current_student['is_validated'] = (calculated_credits == pdf_credits)
        self.current_student['plans'] = sorted(list(self.current_student['plan_set']))
        
        return self.current_student
        return

    