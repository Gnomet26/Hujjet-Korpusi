from django.http import FileResponse, Http404
from rest_framework.decorators import api_view,permission_classes,authentication_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from Users.serializers import RegisterSerializer, LoginSerializer
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterAdminSerializer, UserAdminSerializer, ChangeAnyUserSerializer
from Users.models import CustomUser
from rest_framework.pagination import PageNumberPagination
from Files.serializers import FileSerializer
from Files.models import File
from django.db.models import Sum
from Base.celery import app
from django.db.models import Q
from celery.result import AsyncResult
import os
from django.conf import settings
from django.utils.encoding import smart_str
from django.shortcuts import get_object_or_404
import json
from .tasks import generate_merged_txt_zip

@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([])
def register_admin(request):

    data = request.data

    serializer = RegisterAdminSerializer(data = data)
    if serializer.is_valid():
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        user = CustomUser.objects.filter(username = user.username).first()
        user.is_admin = True
        user.save()
        return Response({'token':token.key},status=status.HTTP_201_CREATED)
    return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([])
def login_admin(request):
    data = request.data
    serializer = LoginSerializer(data = data)
    if serializer.is_valid():
        user = serializer.validated_data
        if user.is_admin:
            token, created = Token.objects.get_or_create(user = user)
            return Response({'token':token.key},status=status.HTTP_200_OK)
        return Response({'detail':'faqat admin kira oladi'}, status=status.HTTP_400_BAD_REQUEST)
    return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def logout_admin(request):
    user = request.user

    if user.is_admin:
        # Tokenni o‘chiramiz
        user.auth_token.delete()
        return Response({'detail': 'Admin muvaffaqiyatli logout qilindi'}, status=status.HTTP_200_OK)

    return Response({'detail': 'Faqat admin logout qilishi mumkin'}, status=status.HTTP_403_FORBIDDEN)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def user_list(request):
    user = request.user

    if user.is_admin:
        users = CustomUser.objects.all().order_by('id')
        paginator = PageNumberPagination()
        paginator.page_size = 10  # yoki settings.py da belgilang

        result_page = paginator.paginate_queryset(users, request)
        serializer = UserAdminSerializer(result_page, many=True)

        return paginator.get_paginated_response(serializer.data)
    return Response({'detail':'Faqat admin ko`ra oladi'},status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def search_user(request):
    user = request.user

    if user.is_admin:
        query = request.GET.get('args', '').strip()

        users = CustomUser.objects.all().order_by('id')

        if query:
            users = users.filter(
                Q(username__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query)
            )

        paginator = PageNumberPagination()
        paginator.page_size = 10  # Yoki settings dan oling

        result_page = paginator.paginate_queryset(users, request)
        serializer = UserAdminSerializer(result_page, many=True)

        return paginator.get_paginated_response(serializer.data)

    return Response({'detail':'Faqat admin ko`ra oladi'},status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def search_files(request):
    user = request.user
    if user.is_admin:
        search_query = request.GET.get('args', '').strip().lower()

        files = File.objects.all()
        if search_query:
            results = []

            for f in files:
                title_text = f.title.lower()
                description_text = f.description.lower()

                # Shart: qisman mos kelsa ham bo‘ladi (masalan: 'hell' => 'hello', '21' => '21-leksiya')
                if search_query in title_text or search_query in description_text:
                    results.append(f.id)

            files = files.filter(id__in=results)

        files = files.order_by('-created_at')

        paginator = PageNumberPagination()
        paginated_files = paginator.paginate_queryset(files, request)

        serializer = FileSerializer(paginated_files, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
    return Response({'detail':'Faqat admin ko`ra oladi'},status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def file_list(request):
    user = request.user
    if user.is_admin:
        try:
            user_files = File.objects.all().order_by('id')

            paginator = PageNumberPagination()
            paginated_files = paginator.paginate_queryset(user_files, request)

            serializer = FileSerializer(paginated_files, many=True, context={'request': request})
            return paginator.get_paginated_response(serializer.data)
        except:
            return Response({'error':'Server error'},status=status.HTTP_400_BAD_REQUEST)
    return Response({'detail':'Faqat admin ko`ra oladi'},status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def check_file(request, uuid,value):

    user = request.user
    if user.is_admin:
        try:
            file = get_object_or_404(File,uuid=uuid)
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

        
    return Response({'detail':'Faqat admin qila oladi'},status=status.HTTP_400_BAD_REQUEST)


def kb_to_bytes(kb):
    return int(kb * 1024)

def bytes_to_human(size_bytes):
    size = float(size_bytes)
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def statistika(request):
    user = request.user
    if not user.is_admin:
        return Response({'detail': 'Faqat adminlar uchun'}, status=status.HTTP_403_FORBIDDEN)

    users_count = CustomUser.objects.count()
    files = File.objects.all()
    files_count = files.count()

    # Original fayllar hajmi
    total_file_size_kb = files.aggregate(total=Sum('file_size'))['total'] or 0
    total_file_size_bytes = kb_to_bytes(total_file_size_kb)
    total_file_size_human = bytes_to_human(total_file_size_bytes)

    # txt fayllar hajmi
    total_txt_file_size_bytes = 0
    for f in files:
        if f.txt_file and os.path.isfile(f.txt_file.path):
            total_txt_file_size_bytes += os.path.getsize(f.txt_file.path)

    total_txt_file_size_human = bytes_to_human(total_txt_file_size_bytes)

    # Fayl statuslari bo‘yicha
    status_counts = {
        'pending': files.filter(status='pending').count(),
        'processing': files.filter(status='processing').count(),
        'done': files.filter(status='done').count(),
        'failed': files.filter(status='failed').count(),
    }

    verified_files = files.filter(is_verified=True).count()
    unverified_files = files.filter(is_verified=False).count()

    # ✅ Token statistikasi
    total_token_count = files.aggregate(total=Sum('token_count'))['total'] or 0
    total_vocab_count = files.aggregate(total=Sum('vocab_count'))['total'] or 0
    total_sentence_count = files.aggregate(total=Sum('sentence_count'))['total'] or 0

    # Celery holati
    try:
        i = app.control.inspect()
        active = i.active() or {}
        reserved = i.reserved() or {}
        scheduled = i.scheduled() or {}

        celery_tasks = {
            "active_tasks": sum(len(v) for v in active.values()),
            "reserved_tasks": sum(len(v) for v in reserved.values()),
            "scheduled_tasks": sum(len(v) for v in scheduled.values()),
        }
        celery_tasks["total_celery_tasks"] = sum(celery_tasks.values())
    except Exception:
        celery_tasks = {
            "active_tasks": 0,
            "reserved_tasks": 0,
            "scheduled_tasks": 0,
            "total_celery_tasks": 0
        }

    message = {
        "users_count": users_count,
        "files_count": files_count,
        "file_sizes": {
            "original_files_bytes": total_file_size_bytes,
            "original_files_human": total_file_size_human,
            "txt_files_bytes": total_txt_file_size_bytes,
            "txt_files_human": total_txt_file_size_human,
        },
        "status_counts": status_counts,
        "verified_files": verified_files,
        "unverified_files": unverified_files,
        "token_stats": {
            "total_token_count": total_token_count,
            "total_vocab_count": total_vocab_count,
            "total_sentence_count": total_sentence_count
        },
        "celery": celery_tasks
    }

    return Response(message, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def delete_user(request, username):
    user = request.user

    if not user.is_admin:
        return Response({'detail': 'Faqat admin foydalanuvchini o‘chira oladi'}, status=403)

    try:
        target_user = CustomUser.objects.get(username=username)

        # AuthToken ni o'chiramiz
        Token.objects.filter(user=target_user).delete()

        # O'zini o'chiramiz
        target_user.delete()

        return Response({'detail': f'{username} foydalanuvchi o‘chirildi'}, status=200)

    except CustomUser.DoesNotExist:
        return Response({'detail': f'{username} degan foydalanuvchi topilmadi'}, status=404)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def create_user(request):
    admin_user = request.user

    if not admin_user.is_admin:
        return Response({'detail': 'Faqat admin foydalanuvchi yaratishi mumkin'}, status=403)

    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'detail': 'Foydalanuvchi muvaffaqiyatli yaratildi',
            'username': user.username,
            'token': token.key
        }, status=201)

    return Response(serializer.errors, status=400)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def delete_file(request, uuid):
    user = request.user

    if not user.is_admin:
        return Response({'detail': 'Faqat admin faylni o‘chira oladi'}, status=403)

    try:
        file = File.objects.get(uuid=uuid)

        # Original faylni o‘chirish
        if file.file_path and os.path.isfile(file.file_path.path):
            os.remove(file.file_path.path)

        # Txt faylni o‘chirish (agar mavjud bo‘lsa)
        if file.txt_file and os.path.isfile(file.txt_file.path):
            os.remove(file.txt_file.path)

        file.delete()

        return Response({'detail': 'Fayl to‘liq o‘chirildi'}, status=200)

    except File.DoesNotExist:
        return Response({'detail': 'Bunday uuid bilan fayl topilmadi'}, status=404)

    except Exception as e:
        return Response({'detail': f'Xatolik: {str(e)}'}, status=500)


@api_view(['PUT', 'PATCH'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def change_user(request, user_id):
    admin = request.user
    if not admin.is_admin:
        return Response({'detail': 'Faqat admin foydalanuvchini tahrirlashi mumkin'}, status=status.HTTP_403_FORBIDDEN)

    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        return Response({'detail': 'Bunday foydalanuvchi topilmadi'}, status=status.HTTP_404_NOT_FOUND)

    serializer = ChangeAnyUserSerializer(user, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'Foydalanuvchi maʼlumotlari yangilandi'}, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def download_any_base_file(request, uuid):
    user = request.user
    if user.is_admin:

        try:
            file_obj = File.objects.get(uuid=uuid)
           #file_obj = File.objects.get(uuid=uuid)
        except File.DoesNotExist:
            raise Http404("Fayl topilmadi.")
           #raise Http404("Fayl topilmadi.")

        if not user.is_admin and file_obj.avtor != user:
            return Response({'detail': 'Ruxsat yo‘q'}, status=status.HTTP_403_FORBIDDEN)
           #return Response({'detail': 'Ruxsat to`q'}, status=status.HTTP_403_FORBIDDEN)

        if not file_obj.file_path or not os.path.isfile(file_obj.file_path.path):
            raise Http404("Asl fayl mavjud emas.")
           #raise Http404("Asl fayl mavjud emas")

        return FileResponse(open(file_obj.file_path.path, 'rb'),
                            as_attachment=True,
                            filename=smart_str(os.path.basename(file_obj.file_path.name)))
    return Response({'detail': 'Faqat adminlar uchun'}, status=status.HTTP_403_FORBIDDEN)
   #return Response({'detail': 'Faqat adminlar uchun'}, status=status.HTTP_403_FORBIDDEN)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def download_any_txt_file(request, uuid):
    user = request.user
    if user.is_admin:
        try:
            file_obj = File.objects.get(uuid=uuid)
        except File.DoesNotExist:
            raise Http404("Fayl topilmadi.")

        if not user.is_admin and file_obj.avtor != user:
            return Response({'detail': 'Ruxsat yo‘q'}, status=status.HTTP_403_FORBIDDEN)

        if not file_obj.txt_file or not os.path.isfile(file_obj.txt_file.path):
            raise Http404("Tozalangan matn fayli mavjud emas.")

        return FileResponse(open(file_obj.txt_file.path, 'rb'),
                            as_attachment=True,
                            filename=smart_str(os.path.basename(file_obj.txt_file.name)))
    
    return Response({'detail': 'Faqat adminlar uchun'}, status=status.HTTP_403_FORBIDDEN)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def start_merge_task(request):
    user = request.user
    if not user.is_admin:
        return Response({'detail': 'Faqat admin qila oladi'}, status=status.HTTP_403_FORBIDDEN)

    task = generate_merged_txt_zip.delay()
    return Response({'task_id': task.id}, status=status.HTTP_202_ACCEPTED)


from celery.result import AsyncResult

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def check_merge_task_status(request, task_id):
    user = request.user
    if not user.is_admin:
        return Response({'detail': 'Faqat admin qila oladi'}, status=status.HTTP_403_FORBIDDEN)
    result = AsyncResult(task_id)

    response_data = {
        'task_id': task_id,
        'state': result.state,
    }
    return Response(response_data)



@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def download_merged_zip(request):
    user = request.user
    if not user.is_admin:
        return Response({'detail': 'Faqat admin qila oladi'}, status=status.HTTP_403_FORBIDDEN)

    task_id = request.query_params.get('task_id')
    if not task_id:
        return Response({'detail': 'task_id query param kerak.'}, status=status.HTTP_400_BAD_REQUEST)

    # Task holatini tekshirish
    result = AsyncResult(task_id)
    if result.state != 'SUCCESS':
        return Response({'detail': f'Task hali tugamagan. Holati: {result.state}'}, status=status.HTTP_202_ACCEPTED)

    zip_path = os.path.join(settings.MEDIA_ROOT, 'merged_files.zip')
    if not os.path.exists(zip_path):
        return Response({'detail': 'Fayl topilmadi.'}, status=status.HTTP_404_NOT_FOUND)

    return FileResponse(open(zip_path, 'rb'), as_attachment=True, filename='merged_files.zip')



@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_text(request, uuid):
    user = request.user
    if not user.is_admin:
        return Response({'detail': 'Faqat admin qila oladi'}, status=status.HTTP_403_FORBIDDEN)

    try:
        file_obj = File.objects.get(uuid=uuid)

        if not file_obj.txt_file:
            return Response({'error': 'txt_file hali mavjud emas'}, status=404)

        file_path = file_obj.txt_file.path

        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()

        return Response({
            'uuid': str(file_obj.uuid),
            'text': text
        })

    except File.DoesNotExist:
        return Response({'error': 'Fayl topilmadi yoki sizga tegishli emas'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)
