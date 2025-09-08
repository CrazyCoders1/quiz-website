import os
from pdf2image import convert_from_path
import mysql.connector
# MySQL Connection
db = mysql.connector.connect(
    host="sql303.infinityfree.com",
    user="if0_39895407",
    password="XV2TDjmrp1GJl3l",
    database="if0_39895407_quiz_db"
)

cursor = db.cursor(dictionary=True)

pdf_paths = {
    'Easy':'data/PDFs/Easy/',
    'Tough':'data/PDFs/Tough/'
}

for difficulty, folder in pdf_paths.items():
    for file in os.listdir(folder):
        if file.endswith('.pdf'):
            pdf_file = os.path.join(folder,file)
            pages = convert_from_path(pdf_file)
            for i,page in enumerate(pages[:-1]):  # last page assumed answers
                image_name = f"{difficulty}_{file.replace('.pdf','')}_page{i+1}.png"
                save_path = f"static/images/{difficulty}/{image_name}"
                page.save(save_path,'PNG')
                cursor.execute("""
                    INSERT INTO questions (image_url,pdf_url,pdf_page,exam_type,answer)
                    VALUES (%s,%s,%s,%s,%s)
                """,(save_path,pdf_file,i+1,difficulty,'A'))
            db.commit()
print("OCR extraction and DB population done!")
