from Base.celery import app
from .models import File
from .converter import extract_and_clean_text
from django.core.files.base import ContentFile
import os
from django.conf import settings

@app.task(name='files.convert_file_task')
def convert_file_task(file_id):
    print("📦 CELERY TASK BOSHLANDI")

    try:
        file = File.objects.get(uuid=file_id)
        file.status = 'processing'
        file.save()

        ext = file.file_path.name.split('.')[-1].lower()
        cleaned_data = extract_and_clean_text(file.file_path.path, ext)

        cleaned_text = cleaned_data.get("text", "")
        token_count = cleaned_data.get("token_count")
        vocab_count = cleaned_data.get("vocab_count")
        sentence_count = cleaned_data.get("sentence_count")

        original_name = os.path.splitext(os.path.basename(file.file_path.name))[0]
        new_txt_filename = f"{original_name}.txt"

        # Duplicate prevention
        if file.txt_file and os.path.exists(file.txt_file.path):
            os.remove(file.txt_file.path)

        # Create text file object
        text_file = ContentFile(cleaned_text.encode('utf-8'))

        file.txt_file.save(new_txt_filename, text_file, save=False)

        # YANGI QO‘SHILGAN QISM:
        file.token_count = token_count
        file.vocab_count = vocab_count
        file.sentence_count = sentence_count

        file.status = 'done'
        file.save()

        print("✅ Matn saqlandi va fayl bog‘landi.")
        return "Yakunlandi."

    except Exception as e:
        print("❌ Xatolik:", e)
        try:
            file.status = 'failed'
            file.save()
        except:
            pass
        return str(e)
