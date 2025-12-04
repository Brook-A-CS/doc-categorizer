import json
import requests
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional
import argparse
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

class PDFLayoutAnalyzer:
    def __init__(self, api_url: str, output_dir: Path, max_workers: int = 4):
        self.api_url = api_url.rstrip('/')
        self.output_dir = output_dir
        self.max_workers = max_workers
        
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.type_mapping = {
            'Text': 'Text',
            'Title': 'Text',
            'Section-header': 'Text', 
            'Page-header': 'Text',
            'Page-footer': 'Text',
            'List': 'Text',
            'Caption': 'Text',
            'Footnote': 'Text',
            
            'Table': 'Table',
            
            'Picture': 'Image',
            'Figure': 'Image',
            'Formula': 'Image'
        }

    def _simplify_category(self, raw_type: str) -> str:
        return self.type_mapping.get(raw_type, 'Text') # Default to Text if unknown

    def process_single_pdf(self, pdf_path: Path) -> Optional[Dict[str, Any]]:
        """
        Worker function to process a single PDF.
        Returns a dictionary with filename and extracted boundaries.
        """
        start_time = time.time()
        try:
            with open(pdf_path, "rb") as f:
                # The 'fast' param usually skips complex OCR, relying on PDF internals
                # 'types' param filters what the model looks for, but we'll fetch all and filter locally
                files = {"file": f}
                data = {"fast": "true"} 
                
                resp = requests.post(self.api_url, files=files, data=data, timeout=60)
            
            resp.raise_for_status()
            raw_data = resp.json()


            processed_elements = []

            elements_list = raw_data if isinstance(raw_data, list) else raw_data.get('elements', [])

            for element in elements_list:

                raw_type = element.get('type', element.get('label', 'Text'))                
                simplified_type = self._simplify_category(raw_type)

                boundary = element.get('box', element.get('bounds', []))

                processed_elements.append({
                    "category": simplified_type,
                    "original_type": raw_type,
                    "boundary": boundary,
                    "page": element.get('page', 1)
                })

            duration = time.time() - start_time
            logging.info(f"Analyzed {pdf_path.name} in {duration:.2f}s - Found {len(processed_elements)} elements")

            return {
                "file_name": pdf_path.name,
                "status": "success",
                "elements": processed_elements
            }

        except Exception as e:
            logging.error(f"Failed to process {pdf_path.name}: {str(e)}")
            return {
                "file_name": pdf_path.name,
                "status": "error",
                "error": str(e)
            }

    def save_result(self, result: Dict[str, Any]):
        if not result:
            return

        file_stem = Path(result['file_name']).stem
        output_path = self.output_dir / f"{file_stem}_layout.json"
        
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=4)

    def run_batch(self, input_dir: Path):
        """Main multithreaded loop """
        pdf_files = list(input_dir.glob("*.pdf"))
        
        if not pdf_files:
            logging.warning(f"No PDF files found in {input_dir}")
            return

        logging.info(f"Starting analysis on {len(pdf_files)} files with {self.max_workers} threads...")

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_pdf = {executor.submit(self.process_single_pdf, pdf): pdf for pdf in pdf_files}

            for future in as_completed(future_to_pdf):
                pdf_path = future_to_pdf[future]
                try:
                    data = future.result()
                    if data != None:
                        self.save_result(data)
                except Exception as exc:
                    logging.error(f"{pdf_path.name} generated an exception: {exc}")

def main():
    parser = argparse.ArgumentParser(description="Multithreaded PDF Layout Analysis Client")
    parser.add_argument("--input", "-i", type=str, default="test_PDFs", help="Input folder containing PDFs")
    parser.add_argument("--output", "-o", type=str, default="layout_results", help="Output folder for JSON results")
    parser.add_argument("--url", "-u", type=str, default="http://localhost:5060", help="API URL")
    parser.add_argument("--threads", "-t", type=int, default=4, help="Number of concurrent threads")
    
    args = parser.parse_args()

    analyzer = PDFLayoutAnalyzer(
        api_url=args.api_url if hasattr(args, 'api_url') else args.url,
        output_dir=Path(args.output),
        max_workers=args.threads
    )

    analyzer.run_batch(Path(args.input))

if __name__ == '__main__':
    main()