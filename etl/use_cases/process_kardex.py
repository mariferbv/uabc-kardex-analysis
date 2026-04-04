class ProcessKardexUseCase:
    def __init__(self, source, parser, repository):
        self.source = source
        self.parser = parser
        self.repository = repository

    def execute(self, path: str, career_code: str):
        print(f"🚀 Iniciando UseCase para {career_code}...")
        pages = self.source.fetch_data(path)
        
        self.parser.reset()

        for page_text in pages:
            for line in page_text.split('\n'):
                self.parser.parse_line(line)

        students = self.parser.get_results()

        for student in students:
            student['career'] = career_code
            self.repository.save(student)