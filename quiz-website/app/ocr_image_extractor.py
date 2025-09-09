# ocr_image_extractor.py
import os
from pdf2image import convert_from_path
import psycopg2
import psycopg2.extras
import sys

DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

pdf_paths = {
    'Easy': 'data/PDFs/Easy/',
    'Tough': 'data/PDFs/Tough/'
}

for difficulty, folder in pdf_paths.items():
    if not os.path.isdir(folder):
        continue
    for file in os.listdir(folder):
        if not file.lower().endswith('.pdf'):
            continue
        pdf_file = os.path.join(folder, file)
        pages = convert_from_path(pdf_file)
        for i, page in enumerate(pages[:-1]):  # skip last page as answers page
            image_name = f"{difficulty}_{file.replace('.pdf','')}_page{i+1}.png"
            save_path = os.path.join('static', 'images', difficulty, image_name)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            page.save(save_path, 'PNG')

            # Insert into Postgres
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO questions (image_url, pdf_url, pdf_page, exam_type, answer)
                VALUES (%s, %s, %s, %s, %s)
            """, (save_path, pdf_file, i+1, difficulty, None))
            conn.commit()
            cur.close()
            conn.close()
print("Done")
