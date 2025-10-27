import json
import requests
from pathlib import Path

def visualize_pdf(pdf_path: Path, URL: str = "http://localhost:5060"):
    with open(pdf_path, "rb") as f:
        resp = requests.post(f'{URL}/visualize', files={"file": f}, data={"fast": "true"})
    resp.raise_for_status()

    save_folder = Path('visualize')
    save_folder.mkdir(parents=True, exist_ok=True)

    save_path = save_folder / pdf_path.name

    with open(save_path, "wb") as sf:
        sf.write(resp.content)


def process_pdf(pdf_path: Path, URL: str = "http://localhost:5060"):
    with open(pdf_path, "rb") as f:
        resp = requests.post(URL, files={"file": f}, data={"fast": "true"})
    resp.raise_for_status()

    # file_name = pdf_path.name
    # with open(f"{file_name}.json", 'w') as wf2:
    #     json.dump(resp.json(), wf2, indent=4)
    
    return resp.json()

def process_ocr_pdf(pdf_path: Path, URL: str = "http://localhost:5060"):
    with open(pdf_path, "rb") as f:
        resp = requests.post(f'{URL}/ocr', files={"file": f}, data={"fast": "true"})
    resp.raise_for_status()

    file_name = pdf_path.name
    with open(f"{file_name}.json", 'w') as wf2:
        json.dump(resp.json(), wf2, indent=4)


def main():
    # pdf_paths = [p.resolve() for p in Path("./test_PDFs").iterdir() if p.is_file()]

    # # process_pdf(pdf_paths[0])
    # for p in pdf_paths:
    #     visualize_pdf(p)

    text_img = Path('visualize/full_img_5.pdf')
    process_ocr_pdf(text_img)


if __name__ == '__main__':
    main()