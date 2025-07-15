# Files/models.py
import uuid
import os
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class File(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('processing', 'Jarayonda'),
        ('done', 'Tayyor'),
        ('failed', 'Xatolik'),
    ]

    avtor = models.ForeignKey(User, on_delete=models.CASCADE)
    file_path = models.FileField(upload_to='files/upload/')
    txt_file = models.FileField(upload_to='files/converted/', null=True, blank=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    file_type = models.CharField(max_length=20)
    file_size = models.BigIntegerField(null=True, blank=True)
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_verified = models.BooleanField(default=False)

    token_count = models.IntegerField(null=True, blank=True)
    vocab_count = models.IntegerField(null=True, blank=True)
    sentence_count = models.IntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.title:
            self.title = os.path.basename(self.file_path.name)

        if self.file_path:
            try:
                size_kb = self.file_path.size / 1024
                self.file_size = round(size_kb, 2)
                self.file_type = self.file_path.name.split('.')[-1].lower()
            except Exception:
                self.file_size = 0
                self.file_type = "unknown"

        try:
            if self.file_path and hasattr(self.file_path, 'open'):
                ext = self.file_path.name.lower()
                if ext.endswith((".txt", ".md", ".csv", ".py")):
                    self.file_path.seek(0)
                    self.content = self.file_path.read().decode('utf-8', errors='ignore')[:5000]
                else:
                    self.content = "📁 Fayl ko‘rish qo‘llab-quvvatlanmaydi."
        except Exception:
            self.content = "📁 Faylni o‘qishda xatolik yuz berdi."

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.file_type})"
