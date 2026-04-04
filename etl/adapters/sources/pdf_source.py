import os
import pdfplumber
from concurrent.futures import ProcessPoolExecutor
from base_source import IKardexSource

class PdfSource(IKardexSource):
    def __init__(self, workers = 3):
        self.workers = workers

        def fetch_data(self, path: str) -> list[str]:

            initials = os.path.splitext(path)[0].upper()
            print(f"Processing {initials}...")

            all_pages = []
            with pdfplumber.open(path) as pdf:
                total_pages = len(pdf.pages)
                ranges = [(i, min(i + 40, total_pages)) for i in range(0, total_pages, 40)]

                with ProcessPoolExecutor(max_workers=self.workers) as executor:
                    futures = [executor.submit(self.extract_text_worker, path, r[0], r[1]) for r in ranges]

                    for future in futures:
                        batch_text = future.result()
                        for page_text in batch_text:
                            if page_text:
                                all_pages.append(page_text)
            return all_pages

        @staticmethod
        def extract_text_worker(path, start, end):
            pages_content = []
            with pdfplumber.open(path) as pdf:
                for i in range(start, end):
                    pages_content.append(pdf.pages[i].extract_text())
            return pages_content