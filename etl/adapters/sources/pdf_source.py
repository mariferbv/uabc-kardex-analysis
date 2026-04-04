import os
import pdfplumber
from concurrent.futures import ProcessPoolExecutor
from .base_source import IKardexSource

class PdfSource(IKardexSource):
    def __init__(self, workers = 3):
        self.workers = workers

    def fetch_data(self, path: str) -> list[str]:
        if not os.path.exists(path):
            print(f"Error: file not found on {path}")
            return []
        
        with pdfplumber.open(path) as pdf:
            total_pages = len(pdf.pages)
        
        chunk_size = 100
        ranges = [(i, i + chunk_size) for i in range(0, total_pages, chunk_size)]
        
        all_pages = []
        with ProcessPoolExecutor(max_workers=self.workers) as executor:
            futures = [executor.submit(self.extract_text_worker, path, r[0], r[1]) for r in ranges]
            
            for i, future in enumerate(futures):
                batch = future.result()
                all_pages.extend(batch)
                print(f"✅ Chunk {i+1}/{len(ranges)} completado. Acumulado: {len(all_pages)} páginas.")

        return all_pages

    @staticmethod
    def extract_text_worker(path, start, end):
        """Worker independiente: abre el PDF, extrae rango y cierra."""
        pages_content = []
        try:
            with pdfplumber.open(path) as pdf:
                for i in range(start, min(end, len(pdf.pages))):
                    text = pdf.pages[i].extract_text()
                    if text:
                        pages_content.append(text)
                    else:
                        print(f"  [Worker] Page {i} is EMPTY (Length 0)")
            return pages_content
        except Exception as e:
            print(f"  [Worker Error] Range {start}-{end}: {e}")
            return []