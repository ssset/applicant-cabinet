import logging
import re
import os
import base64
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError, NotFound
from .serializers import ApplicantProfileSerializer, CustomUserSerializer, AdminOrgListSerializer
from auth_app.serializers import RegisterSerializer
from .models import CustomUser, ApplicantProfile
from auth_app.permissions import IsApplicant, IsEmailVerified, IsAdminApp, IsAdminOrg
from rest_framework.permissions import IsAuthenticated
import cv2
import numpy as np
from org.models import Organization
import pytesseract
from PIL import Image
from dotenv import load_dotenv

# Устанавливаем переменную окружения в самом начале
os.environ['TESSDATA_PREFIX'] = r'C:\Program Files\Tesseract-OCR\tessdata'

logger = logging.getLogger(__name__)
logger.info(f"TESSDATA_PREFIX set to: {os.environ.get('TESSDATA_PREFIX')}")

# Указываем путь к Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Загружаем переменные из .env
load_dotenv()

# Проверяем доступность языков Tesseract
try:
    available_langs = pytesseract.get_languages()
    logger.info(f"Available Tesseract languages: {available_langs}")
except Exception as e:
    logger.error(f"Failed to get Tesseract languages: {str(e)}")

def preprocess_image(image_path):
    """
    Предварительная обработка изображения для улучшения OCR.
    """
    print("TESSDATA_PREFIX:", os.environ.get('TESSDATA_PREFIX'))
    # Читаем изображение
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise Exception("Failed to load image for preprocessing")

    # Увеличиваем контраст
    img = cv2.equalizeHist(img)

    # Исправляем наклон текста
    coords = cv2.findNonZero((img > 200).astype(np.uint8))  # Находим текст
    if coords is not None:
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        (h, w) = img.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        img = cv2.warpAffine(img, M, (w, h))

    # Адаптивная бинаризация
    img = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                cv2.THRESH_BINARY, 11, 2)

    # Удаляем линии таблицы
    kernel = np.ones((3, 3), np.uint8)
    img = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel, iterations=2)

    # Убираем шум
    img = cv2.medianBlur(img, 3)

    # Сохраняем обработанное изображение
    temp_path = "temp_processed_image.png"
    cv2.imwrite(temp_path, img)
    return temp_path

def calculate_average_grade_from_image(image_path, user_id, profile_id):
    """
    Извлекает оценки (цифры) из изображения аттестата с помощью Tesseract OCR и вычисляет средний балл.
    """
    logger.info(
        f"Starting OCR processing for user {user_id} (profile {profile_id}), "
        f"image path: {image_path}"
    )
    try:
        # Нормализуем путь
        image_path = os.path.normpath(image_path)
        logger.debug(f"Normalized image path: {image_path}")

        # Проверяем существование файла
        if not os.path.exists(image_path):
            raise Exception(f"Image file not found: {image_path}")

        # Предобработка изображения
        logger.info("Preprocessing image")
        processed_image_path = preprocess_image(image_path)

        # Выполняем OCR
        logger.info("Running Tesseract OCR")
        custom_config = r'--oem 3 --psm 6 -l rus --tessdata-dir "C:\Program Files\Tesseract-OCR\tessdata" -c tessedit_char_whitelist=0123456789АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'
        text = pytesseract.image_to_string(Image.open(processed_image_path), lang='rus')
        logger.debug(f"Extracted raw text: {text}")

        # Удаляем временный файл
        os.remove(processed_image_path)

        if not text:
            logger.warning(f"No text extracted for user {user_id} (profile {profile_id})")
            return None

        logger.info(f"Extracted raw text for user {user_id} (profile {profile_id}): {text}")

        # Извлекаем числа
        numbers = re.findall(r'\b[2-5]\b', text)  # Ищем только числа от 2 до 5
        grades = []

        for num in numbers:
            try:
                grade = int(num)
                grades.append(grade)
                logger.info(f"Found grade for user {user_id} (profile {profile_id}): {grade}")
            except ValueError:
                logger.debug(f"Skipping non-integer value: {num}")
                continue

        if not grades:
            logger.warning(f"No valid grades found for user {user_id} (profile {profile_id})")
            return None

        # Вычисляем средний балл
        average_grade = round(sum(grades) / len(grades), 1)
        logger.info(f"Calculated average grade for user {user_id} (profile {profile_id}): {average_grade}, based on grades: {grades}")
        return average_grade

    except Exception as e:
        logger.error(f"Error in OCR processing for user {user_id} (profile {profile_id}): {str(e)}", exc_info=True)
        return None

class ApplicantProfileView(APIView):
    """
    API для управления профилем абитуриента.
    """
    permission_classes = [IsAuthenticated, IsEmailVerified, IsApplicant]

    def get(self, request):
        try:
            profile = ApplicantProfile.objects.get(user=request.user)
            serializer = ApplicantProfileSerializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except ApplicantProfile.DoesNotExist:
            return Response({'message': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        try:
            ApplicantProfile.objects.get(user=request.user)
            return Response({'message': 'Profile already exists'}, status=status.HTTP_400_BAD_REQUEST)

        except ApplicantProfile.DoesNotExist:
            serializer = ApplicantProfileSerializer(data=request.data)
            if serializer.is_valid():
                profile = serializer.save(user=request.user)
                # Если загружено изображение аттестата, выполняем OCR
                if 'attestation_photo' in request.FILES:
                    logger.info(
                        f"New attestation photo uploaded for user {request.user.id} "
                        f"(profile {profile.id}), path: {profile.attestation_photo.path}"
                    )
                    average_grade = calculate_average_grade_from_image(
                        profile.attestation_photo.path, request.user.id, profile.id
                    )
                    if average_grade is not None:
                        profile.calculated_average_grade = average_grade
                        profile.save()
                    else:
                        logger.warning(
                            f"Failed to calculate average grade for user {request.user.id} "
                            f"(profile {profile.id})"
                        )
                else:
                    logger.info(f"No attestation photo in request for user {request.user.id}")
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        try:
            profile = ApplicantProfile.objects.get(user=request.user)
            serializer = ApplicantProfileSerializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                # Если обновлено изображение аттестата, пересчитываем средний балл
                if 'attestation_photo' in request.FILES:
                    logger.info(
                        f"Attestation photo updated via PATCH for user {request.user.id} "
                        f"(profile {profile.id})"
                    )
                    average_grade = calculate_average_grade_from_image(
                        profile.attestation_photo.path, request.user.id, profile.id
                    )
                    if average_grade is not None:
                        profile.calculated_average_grade = average_grade
                        profile.save()
                    else:
                        logger.warning(
                            f"Failed to calculate average grade for user {request.user.id} "
                            f"(profile {profile.id})"
                        )
                return Response(ApplicantProfileSerializer(profile).data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except ApplicantProfile.DoesNotExist:
            return Response({'message': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request):
        try:
            profile = ApplicantProfile.objects.get(user=request.user)
            profile.delete()
            return Response({'message': 'Profile deleted'}, status=status.HTTP_204_NO_CONTENT)

        except ApplicantProfile.DoesNotExist:
            return Response({'message': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)

class AdminAppCreationView(APIView):
    """
    API для создания первого admin_app.
    """
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        if CustomUser.objects.filter(role='admin_app').exists():
            return Response({'message': 'Admin app already exists'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.role = 'admin_app'
            user.save()
            return Response({
                'message': 'Admin app registered, check your email for verification code'
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = CustomUserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = CustomUserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminOrgView(APIView):
    """
    API для управления admin_org (доступно только для admin_app).
    - POST: создание admin_org.
    - GET: получение списка admin_org.
    - PATCH: обновление admin_org.
    - DELETE: удаление admin_org.
    """
    permission_classes = [IsAuthenticated, IsEmailVerified, IsAdminApp]

    def post(self, request):
        # Создание admin_org
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.role = 'admin_org'
            organization_id = request.data.get('organization_id')
            try:
                organization = Organization.objects.get(id=organization_id)
                user.organization = organization
                user.save()
                return Response({
                    'message': 'Admin org registered, check your email for verification code'
                }, status=status.HTTP_201_CREATED)

            except Organization.DoesNotExist:
                user.delete()
                return Response({'message': 'Organization not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        # Получение списка admin_org
        logger.info("Fetching admin_org users")
        admin_orgs = CustomUser.objects.filter(role='admin_org')
        serializer = AdminOrgListSerializer(admin_orgs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, id=None):
        logger.info(f"AdminOrgView PATCH: user={request.user}, id={id}, data={request.data}")
        try:
            if id is None:
                logger.error("No user_id provided in URL")
                return Response({'message': 'User ID is required'}, status=status.HTTP_400_BAD_REQUEST)

            admin_org = CustomUser.objects.get(id=id, role='admin_org')
            serializer = RegisterSerializer(admin_org, data=request.data, partial=True)
            if serializer.is_valid():
                organization_id = request.data.get('organization_id')
                if organization_id:
                    try:
                        organization = Organization.objects.get(id=organization_id)
                        admin_org.organization = organization
                        admin_org.save()
                    except Organization.DoesNotExist:
                        logger.error(f"Organization with id {organization_id} not found")
                        return Response({'message': 'Organization not found'}, status=status.HTTP_404_NOT_FOUND)
                serializer.save()
                logger.info(f"Admin org with id {id} updated by {request.user.email}")
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                logger.error(f"Serializer errors: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except CustomUser.DoesNotExist:
            logger.error(f"Admin org with id {id} not found")
            return Response({'message': 'Admin org not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Unexpected error in AdminOrgView.patch: {str(e)}")
            return Response({'message': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, id=None):  # Добавляем параметр id
        try:
            if id is None:
                logger.error("No user_id provided in URL")
                return Response({'message': 'User ID is required'}, status=status.HTTP_400_BAD_REQUEST)

            admin_org = CustomUser.objects.get(id=id, role='admin_org')
            admin_org.delete()
            logger.info(f"Admin org with id {id} deleted by {request.user.email}")
            return Response({'message': 'Admin org deleted'}, status=status.HTTP_204_NO_CONTENT)
        except CustomUser.DoesNotExist:
            logger.error(f"Admin org with id {id} not found")
            return Response({'message': 'Admin org not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Unexpected error in AdminOrgView.delete: {str(e)}")
            return Response({'message': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ModeratorView(APIView):
    """
    API для управления модераторами (доступно только для admin_org)
    """
    permission_classes = [IsAuthenticated, IsEmailVerified, IsAdminOrg]

    def post(self, request):
        logger.info(f'Creating moderator with data: {request.data}')
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.role = 'moderator'
            user.organization = request.user.organization
            user.save()
            return Response({
                'message': 'Moderator registered, check email for verification code'
            }, status=status.HTTP_201_CREATED)

        logger.error(f'Serializer errors: {serializer.errors}')
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        logger.info(f"Fetching moderators for organization: {request.user.organization}")
        moderators = CustomUser.objects.filter(role='moderator', organization=request.user.organization)
        serializer = RegisterSerializer(moderators, many=True)
        logger.info(f"moderators info: {serializer.data}")
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        logger.info(
            f"ModeratorView PATCH: user={request.user}, authenticated={request.user.is_authenticated}, organization={request.user.organization}")
        if not request.user.organization:
            logger.error(f"User {request.user.email} has no organization assigned")
            return Response({'message': 'User has no organization assigned'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_id = request.data.get('id')
            if not user_id:
                logger.error("No user_id provided in request data")
                return Response({'message': 'User ID is required'}, status=status.HTTP_400_BAD_REQUEST)

            moderator = CustomUser.objects.get(id=user_id, role='moderator', organization=request.user.organization)
            serializer = RegisterSerializer(moderator, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                logger.error(f"Serializer errors: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except CustomUser.DoesNotExist:
            logger.error(f"Moderator with id {user_id} not found")
            return Response({'message': 'Moderator not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Unexpected error in ModeratorView.patch: {str(e)}")
            return Response({'message': 'An unexpected error occurred'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request):
        try:
            user_id = request.query_params.get('id')
            moderator = CustomUser.objects.get(id=user_id, role='moderator', organization=request.user.organization)
            moderator.delete()
            return Response({'message': 'Moderator deleted'}, status=status.HTTP_204_NO_CONTENT)

        except CustomUser.DoesNotExist:
            return Response({'message': 'Moderator not found'}, status=status.HTTP_404_NOT_FOUND)