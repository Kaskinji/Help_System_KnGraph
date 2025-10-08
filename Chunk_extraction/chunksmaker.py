import random
import time
import requests
import PyPDF2
import os
import json
from openai import OpenAI


def start():
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key="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",
    )
    return client


def function_snans(chunk, prompt, client):
    time.sleep(random.randrange(1, 3))
    completion = client.chat.completions.create(
        model="deepseek/deepseek-chat-v3-0324:free",
        messages=[
            {
                "role": "user",
                "temperature": 0,
                "content": f"""{prompt}\nТЕКСТ: {chunk}"""
            }
        ]
    )
    return completion.choices[0].message.content


def json_creator(chunk, json_id, source):
    data = {
        "id": json_id,
        "source": source,
        "content": chunk,
        "size": len(chunk),
    }
    folder_path = "chunks_sex"

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    file_path = os.path.join(folder_path, f"chunk{json_id:02d}.json")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def chunk_creator(massage, json_id, last=False):
    prechunk = ''
    chunk = list(filter(lambda x: len(x) > 0, massage.split(SEPERATOR)))
    for i in chunk:
        for j in i.split(InSEPERATOR):
            if len(prechunk) + len(j) > 750 and len(prechunk) > 0:
                json_creator(prechunk, json_id, name)
                json_id += 1
                prechunk = ''
            prechunk += j
        if i != chunk[-1] or last:
            json_creator(prechunk, json_id, name)
            json_id += 1
            prechunk = ''
    return prechunk, json_id if not last else None


def text_to_chunks(text):
    client = start()
    chunk = ''
    json_id = 0
    save = False
    for i in map(lambda x: x.rstrip(), text.split("\n")):
        save = True
        chunk += f" {i}"
        if (len(chunk) > 8000) and (chunk[-1] == '.'):
            save = False
            print(chunk)
            chunk, json_id = chunk_creator(function_snans(chunk, PROMPT, client), json_id)
            print(json_id)
    if save:
        chunk_creator(function_snans(chunk, PROMPT, client), json_id, True)


def download_file(url):
    try:
        # Send a request to the URL
        response = requests.get(url)
        local_filename = url.split('/')[-1]
        # Check if the request was successful
        if response.status_code == 200:
            # Open a local file in binary write mode
            with open(local_filename, 'wb') as f:
                f.write(response.content)  # Write the content of the response
            print(f'Document downloaded successfully and saved as {local_filename}')
        else:
            print(f'Failed to retrieve document. Status code: {response.status_code}')
        return local_filename
    except Exception as e:
        print(f'An error occurred: {e}')
        return None


def read_text_from_pdf(pdf_file_path: str):
    if not os.path.exists(pdf_file_path) or not pdf_file_path.lower().endswith(".pdf"):
        return ""
    with open(pdf_file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ''.join(page.extract_text() for page in reader.pages)
    return text


def read_text_from_txt(txt_file_path: str):
    if not os.path.exists(txt_file_path):
        return "", 0
    if ".txt" not in txt_file_path:
        return "", 0
    with open(txt_file_path, 'r') as file:
        text = file.read()
    return text


site_url1 = 'https://www.moneta.ru/info/d/ru/public/users/nko/monetaoffer.pdf'
site_url2 = 'https://moneta.ru/info/d/ru/public/merchants/b2boffer.pdf'

SEPERATOR = '<NO>'
InSEPERATOR = '<YES>'

PROMPT = f"""
Разбить текстовый документ на маленькие чанки с учетом следующих требований:
1) Чанк должен включать в себя полностью целые смысловые абзацы, недопустимо, чтобы абзац или подпункт начинался в одном чанке, а заканчивался в другом.
2) Если текст содержит разделы/параграфы, то начало раздела/параграфа, включающий заголовок должно быть началом очередного чанка, нумерацию страниц не включаем.
3) Если начинаеться новый раздела/параграф, включающий заголовок, должен использовать разделитель "{SEPERATOR}", иначе - "{InSEPERATOR}".

В ответ строго ПИШИ ТОЛЬКО ЧАНКИ, разделенные разделителями.

ПРИМЕР ОТВЕТА:
{SEPERATOR}Утверждено Решением Правления НКО «МОНЕТА» (ООО) Протокол № 26-24 от 24.07.2024 года Вступает в силу 25.07.2024 года...
"""

name = download_file(site_url2)
# name = "secondone.pdf"
work = read_text_from_pdf(name)
text_to_chunks(work)