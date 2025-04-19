import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from auth_app.permissions import IsEmailVerified, IsModerator, IsAdminOrg, IsAdminApp
from applications.models import Application
from org.models import Specialty, BuildingSpecialty, Organization
from django.db.models import Count
from django.db.models.functions import ExtractWeekDay
from datetime import timedelta, datetime
from django.utils import timezone

logger = logging.getLogger(__name__)

class ApplicationStatsView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsModerator | IsAdminOrg]

    def get(self, request):
        try:
            if not request.user.organization:
                logger.warning(f"User {request.user.email} has no organization assigned, returning empty data")
                return Response([], status=status.HTTP_200_OK)

            # Определяем начало и конец текущей недели (понедельник–воскресенье)
            today = timezone.now().date()
            # Находим понедельник текущей недели
            start_date = today - timedelta(days=today.weekday())  # weekday(): 0=Пн, 6=Вс
            end_date = start_date + timedelta(days=6)  # Воскресенье

            applications = Application.objects.filter(
                building_specialty__building__organization=request.user.organization,
                created_at__date__range=[start_date, end_date]
            ).annotate(
                day=ExtractWeekDay('created_at')  # 1=Вс, 2=Пн, ..., 7=Сб
            ).values('day').annotate(
                count=Count('id')
            ).order_by('day')

            days = {
                2: 'Пн', 3: 'Вт', 4: 'Ср', 5: 'Чт',
                6: 'Пт', 7: 'Сб', 1: 'Вс'
            }

            # Формируем данные для всех дней недели
            data = []
            for day in range(2, 8):  # Пн–Сб
                count = next(
                    (item['count'] for item in applications if item['day'] == day),
                    0
                )
                data.append({'name': days[day], 'Заявки': count})
            # Добавляем воскресенье (day=1)
            count = next(
                (item['count'] for item in applications if item['day'] == 1),
                0
            )
            data.append({'name': 'Вс', 'Заявки': count})

            logger.info(f"Retrieved application stats for {request.user.email}")
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error retrieving application stats: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SpecialtyStatsView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsModerator | IsAdminOrg]

    def get(self, request):
        try:
            if not request.user.organization:
                logger.warning(f"User {request.user.email} has no organization assigned, returning empty data")
                return Response([], status=status.HTTP_200_OK)

            # Определяем начало и конец текущей недели
            today = timezone.now().date()
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)

            applications = Application.objects.filter(
                building_specialty__building__organization=request.user.organization,
                created_at__date__range=[start_date, end_date]
            ).annotate(
                day=ExtractWeekDay('created_at')  # 1=Вс, 2=Пн, ..., 7=Сб
            ).values('day').annotate(
                count=Count('id')
            ).order_by('day')

            days = {
                2: 'Пн', 3: 'Вт', 4: 'Ср', 5: 'Чт',
                6: 'Пт', 7: 'Сб', 1: 'Вс'
            }

            # Формируем данные для всех дней недели
            data = []
            for day in range(2, 8):  # Пн–Сб
                count = next(
                    (item['count'] for item in applications if item['day'] == day),
                    0
                )
                data.append({'name': days[day], 'value': count})
            # Воскресенье
            count = next(
                (item['count'] for item in applications if item['day'] == 1),
                0
            )
            data.append({'name': 'Вс', 'value': count})

            logger.info(f"Retrieved specialty stats for {request.user.email}")
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error retrieving specialty stats: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ActivityStatsView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsModerator | IsAdminOrg]

    def get(self, request):
        try:
            if not request.user.organization:
                logger.warning(f"User {request.user.email} has no organization assigned, returning empty data")
                return Response([], status=status.HTTP_200_OK)

            # Определяем начало и конец текущей недели
            today = timezone.now().date()
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)

            applications = Application.objects.filter(
                building_specialty__building__organization=request.user.organization,
                created_at__date__range=[start_date, end_date]
            ).annotate(
                day=ExtractWeekDay('created_at')  # 1=Вс, 2=Пн, ..., 7=Сб
            ).values('day').annotate(
                count=Count('id')
            ).order_by('day')

            days = {
                2: 'Пн', 3: 'Вт', 4: 'Ср', 5: 'Чт',
                6: 'Пт', 7: 'Сб', 1: 'Вс'
            }

            # Формируем данные для всех дней недели
            data = []
            for day in range(2, 8):  # Пн–Сб
                count = next(
                    (item['count'] for item in applications if item['day'] == day),
                    0
                )
                data.append({'name': days[day], 'Активность': count})
            # Воскресенье
            count = next(
                (item['count'] for item in applications if item['day'] == 1),
                0
            )
            data.append({'name': 'Вс', 'Активность': count})

            logger.info(f"Retrieved activity stats for {request.user.email}")
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error retrieving activity stats: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ModeratorActivityStatsView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsAdminOrg]

    def get(self, request):
        try:
            if not request.user.organization:
                logger.error(f"User {request.user.email} has no organization assigned")
                return Response({'error': 'User has no organization assigned'}, status=status.HTTP_400_BAD_REQUEST)

            # Определяем начало и конец текущей недели
            today = timezone.now().date()
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)

            applications = Application.objects.filter(
                building_specialty__building__organization=request.user.organization,
                updated_at__date__range=[start_date, end_date]
            ).annotate(
                day=ExtractWeekDay('updated_at')  # 1=Вс, 2=Пн, ..., 7=Сб
            ).values('day').annotate(
                count=Count('id')
            ).order_by('day')

            days = {
                2: 'Пн', 3: 'Вт', 4: 'Ср', 5: 'Чт',
                6: 'Пт', 7: 'Сб', 1: 'Вс'
            }

            # Формируем данные для всех дней недели
            data = []
            for day in range(2, 8):  # Пн–Сб
                count = next(
                    (item['count'] for item in applications if item['day'] == day),
                    0
                )
                data.append({'name': days[day], 'Активность': count})
            # Воскресенье
            count = next(
                (item['count'] for item in applications if item['day'] == 1),
                0
            )
            data.append({'name': 'Вс', 'Активность': count})

            logger.info(f"Retrieved moderator activity stats for {request.user.email}")
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error retrieving moderator activity stats: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SystemStatsView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsAdminApp]

    def get(self, request):
        try:
            end_date = timezone.now()
            start_date = end_date - timedelta(days=7 * 30)
            applications = Application.objects.filter(
                created_at__range=[start_date, end_date]
            ).extra(
                select={'month': "strftime('%%m', created_at)"}
            ).values('month').annotate(count=Count('id')).order_by('month')

            months = {
                '01': 'Янв', '02': 'Фев', '03': 'Мар', '04': 'Апр',
                '05': 'Май', '06': 'Июн', '07': 'Июл', '08': 'Авг',
                '09': 'Сен', '10': 'Окт', '11': 'Ноя', '12': 'Дек'
            }

            data = []
            for month in range(1, 13):
                month_str = f"{month:02d}"
                count = next((item['count'] for item in applications if item['month'] == month_str), 0)
                data.append({'name': months[month_str], 'Заявки': count})

            logger.info(f"Retrieved system stats for {request.user.email}")
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error retrieving system stats: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class InstitutionStatsView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsAdminApp]

    def get(self, request):
        try:
            organizations = Organization.objects.annotate(
                application_count=Count('building__building_specialties__applications')
            ).values('name', 'application_count')

            data = [
                {'name': org['name'], 'value': org['application_count']}
                for org in organizations
            ]

            if len(data) < 5:
                other_count = sum(item['value'] for item in data if item['value'] < 5)
                data = [item for item in data if item['value'] >= 5]
                if other_count > 0:
                    data.append({'name': 'Другие', 'value': other_count})

            logger.info(f"Retrieved institution stats for {request.user.email}")
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error retrieving institution stats: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AdminActivityStatsView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsAdminApp]

    def get(self, request):
        try:
            end_date = timezone.now()
            start_date = end_date - timedelta(days=7)
            applications = Application.objects.filter(
                updated_at__range=[start_date, end_date]
            ).extra(
                select={'day': "strftime('%%w', updated_at)"}
            ).values('day').annotate(count=Count('id')).order_by('day')

            days = {
                '0': 'Вс', '1': 'Пн', '2': 'Вт', '3': 'Ср',
                '4': 'Чт', '5': 'Пт', '6': 'Сб'
            }

            data = []
            for day in range(7):
                day_str = str(day)
                count = next((item['count'] for item in applications if item['day'] == day_str), 0)
                data.append({'name': days[day_str], 'Активность': count})

            logger.info(f"Retrieved admin activity stats for {request.user.email}")
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error retrieving admin activity stats: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)