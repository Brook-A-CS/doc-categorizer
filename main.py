import json
import requests
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional
import argparse
import time
from datetime import datetime

class PDFLayoutAnalyzer:
    def __init__(self, api_url: str, output_dir: Path, max_workers: int = 4, visualize: bool = False):
        self.api_url = api_url.rstrip('/')
        self.output_dir = output_dir
        self.max_workers = max_workers
        self.visualize = visualize
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        if self.visualize:
            (self.output_dir / "visualizations").mkdir(parents=True, exist_ok=True)

        self.type_mapping = {
            'Text': 'Text',
            'Title': 'Text',
            'Section-header': 'Text', 
            'Page-header': 'Text',
            'Page-footer': 'Text',
            'List item': 'Text',
            'Caption': 'Text',
            'Footnote': 'Text',
            
            'Table': 'Table',
            
            'Picture': 'Image',
            'Figure': 'Image',
            'Formula': 'Image'
        }

    def _simplify_category(self, raw_type: str) -> str:
        return self.type_mapping.get(raw_type, 'Text')

    def get_visualization(self, pdf_path: Path, fast_mode: str = "true"):
        """
        Hits the /visualize endpoint to get a PDF with bounding boxes drawn.
        """
        viz_url = f"{self.api_url}/visualize"
        try:
            with open(pdf_path, "rb") as f:
                files = {"file": (pdf_path.name, f, "application/pdf")}
                data = {"fast": fast_mode}
                
                resp = requests.post(viz_url, files=files, data=data, timeout=600)
            
            resp.raise_for_status()
            
            output_filename = f"{pdf_path.stem}_annotated.pdf"
            output_path = self.output_dir / "visualizations" / output_filename
            
            with open(output_path, "wb") as f_out:
                f_out.write(resp.content)
                
            logging.info(f"Saved visualization to {output_filename}")

        except Exception as e:
            logging.error(f"Visualization failed for {pdf_path.name}: {str(e)}")

    def process_single_pdf(self, pdf_path: Path) -> Optional[Dict[str, Any]]:
        start_time = time.time()
        fast_mode = "false" 

        if self.visualize:
            self.get_visualization(pdf_path, fast_mode)

        try:
            with open(pdf_path, "rb") as f:
                files = {"file": (pdf_path.name, f, "application/pdf")}
                data = {"fast": fast_mode, "language": "en"}
                
                resp = requests.post(self.api_url, files=files, data=data, timeout=60)  

            resp.raise_for_status()
            raw_data = resp.json()

            processed_elements = []
            
            elements_list = raw_data

            for element in elements_list:

                raw_type = element.get('type', 'Text')             
                simplified_type = self._simplify_category(raw_type)

                # { "left": 72.0, "top": 84.0, "width": 451.2, "height": 23.04 }
                left = element.get('left', 0)
                top = element.get('top', 0)
                width = element.get('width', 0)
                height = element.get('height', 0)

                # Convert to boundary box [x1, y1, x2, y2]
                if width > 0 and height > 0:
                    boundary = [left, top, left + width, top + height]
                else:
                    boundary = []

                processed_elements.append({
                    "category": simplified_type,
                    "original_type": raw_type,
                    "boundary": boundary,
                    "page": element.get('page_number', 1),
                    "text": element.get('text', '')
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
        pdf_files = list(input_dir.glob("*.pdf"))
        
        if not pdf_files:
            logging.warning(f"No PDF files found in {input_dir}")
            return

        logging.info(f"Starting analysis on {len(pdf_files)} files with {self.max_workers} threads...")

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_pdf = {executor.submit(self.process_single_pdf, pdf): pdf for pdf in pdf_files}

            for future in as_completed(future_to_pdf):
                pdf_path = future_to_pdf[future]
                try:
                    data = future.result()
                    if data is not None:
                        self.save_result(data)
                except Exception as exc:
                    logging.error(f"{pdf_path.name} generated an exception: {exc}")

def main():
    parser = argparse.ArgumentParser(description="Multithreaded PDF Layout Analysis Client")
    parser.add_argument("--input", "-i", type=str, default="test_PDFs", help="Input folder containing PDFs")
    parser.add_argument("--output", "-o", type=str, default="layout_results", help="Output folder for JSON results")
    parser.add_argument("--url", "-u", type=str, default="http://localhost:5060", help="API URL")
    parser.add_argument("--threads", "-t", type=int, default=1, help="Number of concurrent threads")
    parser.add_argument("--viz", action="store_true", help="Enable generation of annotated PDFs")
    
    args = parser.parse_args()

    output_path = Path(args.output) / "logs"
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"process_{timestamp}.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            # logging.StreamHandler(),                        # Print to console
            logging.FileHandler(output_path / log_filename)
        ],
        force=True 
    )

    input_path = Path(args.input)
    if not input_path.exists():
        logging.error(f"Input directory not found: {input_path}")
        return

    analyzer = PDFLayoutAnalyzer(
        api_url=args.api_url if hasattr(args, 'api_url') else args.url,
        output_dir=Path(args.output),
        max_workers=args.threads,
        visualize=args.viz
    )

    analyzer.run_batch(Path(args.input))

if __name__ == '__main__':
    main()