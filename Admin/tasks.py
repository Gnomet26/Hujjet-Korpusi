# Admin/tasks.py
import os
import json
import io
import zipfile

from celery import shared_task
from django.conf import settings

@shared_task
def generate_merged_txt_zip():
    json_file_path = os.path.join(settings.MEDIA_ROOT, 'mixed', 'for_mixed.json')
    output_filename = 'merged_files.zip'
    output_path = os.path.join(settings.MEDIA_ROOT, output_filename)

    # Eski faylni o‘chirish (agar mavjud bo‘lsa)
    if os.path.exists(output_path):
        os.remove(output_path)

    if not os.path.exists(json_file_path):
        return {'error': 'for_mixed.json fayli topilmadi.'}

    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            texts_to_merge = [entry.get('text', '') for entry in data.values() if isinstance(entry, dict)]
    except json.JSONDecodeError:
        return {'error': 'for_mixed.json faylini o‘qishda xatolik.'}

    merged_text = "\n".join(texts_to_merge)

    # Zip yaratish
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('merged.txt', merged_text)

    zip_buffer.seek(0)

    with open(output_path, 'wb') as f:
        f.write(zip_buffer.read())

    # Foydalanuvchiga beriladigan yo‘l (nisbiy URL)
    download_url = os.path.join(settings.MEDIA_URL, output_filename)

    return {'download_path': download_url}
