import os
from dotenv import load_dotenv
from adapters.parsers.pdf_parser import PdfParser
from adapters.respositories.sql_repository import SqlRepository
from adapters.sources.pdf_source import PdfSource
from use_cases.process_kardex import ProcessKardexUseCase

load_dotenv()


def main():
    file_path = os.getenv(r'FILE_PATH')
    career_code = os.getenv("CAREER_CODE")
    

    db_config={
        "host": os.getenv("DB_HOST"),
        "dbname": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASS"),
        "port": os.getenv("DB_PORT")
    }

    print(db_config)

    source = PdfSource(workers=3)
    parser = PdfParser()
    repository = SqlRepository(db_config)

    use_case = ProcessKardexUseCase(source, parser, repository)    

    use_case.execute(file_path, career_code)

if __name__ == "__main__":
    main()