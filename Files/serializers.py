from rest_framework import serializers
from .models import File

class FileUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ['uuid', 'file_path']
        read_only_fields = ['uuid']

class FileSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = [
            'uuid',
            'title',
            'file_type',
            'file_size',
            'status',
            'created_at',
            'file_path',
            'content',
            'download_url',
            'is_verified',
            'token_count',       # ✅ Qo‘shildi
            'vocab_count',       # ✅ Qo‘shildi
            'sentence_count',    # ✅ Qo‘shildi
        ]

    def get_download_url(self, obj):
        request = self.context.get('request')
        if obj.txt_file and request:
            return request.build_absolute_uri(obj.txt_file.url)
        return None
