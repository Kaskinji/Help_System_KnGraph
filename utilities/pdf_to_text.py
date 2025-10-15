from PyPDF2 import PdfReader
import re
def extract_text_with_structure(pdf_path, output_txt_path):
    reader = PdfReader(pdf_path)
    text = ""

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            # Сохраняем разделители (например, заголовки)
            text += page_text + "\n\n"  # Двойной перенос между страницами

    # Сохраняем в файл
    with open(output_txt_path, 'w', encoding='utf-8') as f:
        f.write(text)
    return text

# Извлекаем текст
pdf_text = extract_text_with_structure("../Source_texts/b2boffer.pdf", "b2boffer.txt")
pdf_text2 = extract_text_with_structure("../Source_texts/connecting_client.pdf", "connecting_client.txt")