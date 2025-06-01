import os
from PyPDF2 import PdfReader #
from PyPDF2.errors import PdfReadError, DependencyError
from typing import Tuple, Optional

def validate_pdf_file(file_path: str) -> Tuple[bool, Optional[str]]:
    if not os.path.exists(file_path):
        return False, "File does not exist on disk."

    if not file_path.lower().endswith(".pdf"):
        return False, "File is not a PDF based on its extension."

    try:
        reader = PdfReader(file_path)

        if reader.is_encrypted:
            return False, "PDF is password-protected."

        num_pages = len(reader.pages)
        
        if num_pages == 0:
            return False, "PDF contains no pages."

        return True, None

    except PdfReadError as e:
        return False, f"PDF content is corrupted or malformed: {e}"
    except Exception as e:
        return False, f"An unexpected error occurred during PDF validation: {e}"