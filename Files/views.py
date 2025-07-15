import os
import json
from django.http import FileResponse
from rest_framework.decorators import api_view, permission_classes,authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework import status
from .serializers import FileSerializer
from rest_framework.pagination import PageNumberPagination
from django.conf import settings
from celery import current_app
from .models import File
from django.shortcuts import get_object_or_404
from django.http import FileResponse, Http404
from django.utils.encoding import smart_str

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def upload_file(request):
    uploaded_files = request.FILES.getlist("file_path")

    if not uploaded_files:
        return Response({"error": "Hech qanday fayl yuborilmadi"}, status=400)

    ALLOWED_EXTENSIONS = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt']
    saved_files = []

    for uploaded_file in uploaded_files:
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            return Response({'error': f"{uploaded_file.name} - Yaroqsiz fayl formati."}, status=400)

        if int(uploaded_file.size) > 25 * 1024 * 1024:
            return Response({'error': f"{uploaded_file.name} - Fayl hajmi 25MB dan katta."}, status=400)

        file_obj = File.objects.create(
            avtor=request.user,
            file_path=uploaded_file,
        )

        # Celery taskni ishga tushiramiz
        from .tasks import convert_file_task
        convert_file_task.delay(str(file_obj.uuid))

        saved_files.append({
            "file_id": str(file_obj.uuid),
            "title": file_obj.title,
            "status_check_url": f"/api/files/status/{file_obj.uuid}/",
            "download_url": f"/api/files/download/{file_obj.uuid}/"  # Ishlab bo‘lgach ishlaydi
        })

    return Response({
        "message": f"{len(saved_files)} ta fayl yuklandi. Convertatsiya boshlanmoqda...",
        "files": saved_files
    }, status=201)



@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def my_files(request):
    try:
        user = request.user
        user_files = File.objects.filter(avtor=user).order_by('-created_at')

        paginator = PageNumberPagination()
        paginated_files = paginator.paginate_queryset(user_files, request)

        serializer = FileSerializer(paginated_files, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
    except:
        return Response({'error':'Server error'},status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def check_file_status(request, file_id):
    try:
        file = File.objects.get(uuid=file_id, avtor=request.user)
        data = {
            "file_id": str(file.uuid),
            "title": file.title,
            "status": file.status,
            "created_at": file.created_at,
        }

        # Agar tayyor bo‘lsa — yuklab olish linkini qo‘shamiz
        if file.status == "done" and file.txt_file:
            data["download_url"] = f"/api/files/download/{file.uuid}/"

        return Response(data, status=200)

    except File.DoesNotExist:
        return Response({"error": "Fayl topilmadi"}, status=404)
    


from django.http import FileResponse
from django.utils.encoding import smart_str
    
@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def search_files(request):
    user = request.user
    search_query = request.GET.get('file_name', '').strip()

    files = File.objects.filter(avtor=user)
    if search_query:
        files = files.filter(title__icontains=search_query)

    files = files.order_by('-created_at')

    paginator = PageNumberPagination()
    paginated_files = paginator.paginate_queryset(files, request)

    serializer = FileSerializer(paginated_files, many=True, context={'request': request})
    return paginator.get_paginated_response(serializer.data)


@api_view(['DELETE'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def delete_file(request, uuid):
    user = request.user
    file_obj = get_object_or_404(File, uuid=uuid, avtor=user)

    # Serverdagi fayllarni o‘chirish (agar mavjud bo‘lsa)
    if file_obj.file_path and os.path.isfile(file_obj.file_path.path):
        os.remove(file_obj.file_path.path)

    if file_obj.txt_file and os.path.isfile(file_obj.txt_file.path):
        os.remove(file_obj.txt_file.path)

    # Database'dan o‘chirish
    file_obj.delete()

    return Response({"detail": "Fayl muvaffaqiyatli o‘chirildi."}, status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def download_base_file(request, uuid):
    file_obj = get_object_or_404(File, uuid=uuid, avtor=request.user)

    if not file_obj.file_path or not os.path.isfile(file_obj.file_path.path):
        raise Http404("Asl fayl topilmadi.")

    return FileResponse(open(file_obj.file_path.path, 'rb'),
                        as_attachment=True,
                        filename=smart_str(os.path.basename(file_obj.file_path.name)))


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def download_txt_file(request, uuid):
    file_obj = get_object_or_404(File, uuid=uuid, avtor=request.user)

    if not file_obj.txt_file or not os.path.isfile(file_obj.txt_file.path):
        raise Http404("Tozalangan matn fayli topilmadi.")

    return FileResponse(open(file_obj.txt_file.path, 'rb'),
                        as_attachment=True,
                        filename=smart_str(os.path.basename(file_obj.txt_file.name)))


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def verify_file(request, uuid, value):
    try:
        file = File.objects.get(uuid=uuid, avtor=request.user)
    except File.DoesNotExist:
        return Response({"detail": "Fayl topilmadi."}, status=status.HTTP_404_NOT_FOUND)

    # value string bo‘lganligi sababli, uni boolga aylantiramiz
    if value.lower() == 'true':
        file.is_verified = True
    elif value.lower() == 'false':
        file.is_verified = False
    else:
        return Response({"detail": "Qiymat faqat 'true' yoki 'false' bo‘lishi kerak."},
                        status=status.HTTP_400_BAD_REQUEST)

    file.save()

    # === Qo‘shimcha: for_mixed.json ni yangilash ===
    mixed_dir = os.path.join(settings.MEDIA_ROOT, 'mixed')
    os.makedirs(mixed_dir, exist_ok=True)
    json_path = os.path.join(mixed_dir, 'for_mixed.json')

    # Yoki mavjud jsonni o‘qiymiz
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {}

    uuid_str = str(file.uuid)

    # txt_file mavjud bo‘lsa va fayli bor bo‘lsa
    if file.txt_file and os.path.exists(file.txt_file.path):
        if file.is_verified:
            # txt fayldan matnni o‘qib olish
            with open(file.txt_file.path, 'r', encoding='utf-8') as f:
                text = f.read().strip()

            # JSONga yozish
            data[uuid_str] = {
                "file": os.path.basename(file.title),
                "text": text
            }
        else:
            # Agar verified false bo‘lsa - jsondan olib tashlaymiz
            data.pop(uuid_str, None)

        # for_mixed.json ni qayta saqlaymiz
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    return Response({
        "detail": f"Fayl {'tasdiqlandi' if file.is_verified else 'tasdiqlanmagan'}.",
        "is_verified": file.is_verified
    })