from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
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
from django.core.cache import cache
import logging
from rest_framework.exceptions import ValidationError

logger = logging.getLogger(__name__)

class ApplicationStatsView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsModerator | IsAdminOrg]

    @extend_schema(
        summary="Статистика заявок по дням недели",
        description="Возвращает количество заявок, поданных в организацию пользователя за текущую неделю, сгруппированное по дням недели (Пн-Вс). Данные кэшируются на 24 часа. Доступно для модераторов и администраторов организации.",
        responses={
            200: OpenApiResponse(
                description="Статистика успешно получена",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value=[
                            {"name": "Пн", "Заявки": 10},
                            {"name": "Вт", "Заявки": 8},
                            {"name": "Ср", "Заявки": 5},
                            {"name": "Чт", "Заявки": 12},
                            {"name": "Пт", "Заявки": 9},
                            {"name": "Сб", "Заявки": 3},
                            {"name": "Вс", "Заявки": 2}
                        ]
                    )
                ]
            ),
            401: OpenApiResponse(
                description="Неавторизованный доступ",
                examples=[
                    OpenApiExample(
                        name="Ошибка 401",
                        value={"detail": "Authentication credentials were not provided."}
                    )
                ]
            ),
            403: OpenApiResponse(
                description="Email не подтверждён или недостаточно прав",
                examples=[
                    OpenApiExample(
                        name="Ошибка 403",
                        value={"message": "У вас недостаточно прав или email не подтверждён"}
                    )
                ]
            )
        }
    )
    def get(self, request):
        if not request.user.organization:
            logger.warning(f"User {request.user.email} has no organization assigned, returning empty data")
            return Response([], status=status.HTTP_200_OK)

        cache_key = f"application_stats_{request.user.organization.id}_{timezone.now().date()}"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.info(f"Cache hit for {cache_key}")
            return Response(cached_data, status=status.HTTP_200_OK)

        today = timezone.now().date()
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)

        applications = Application.objects.filter(
            building_specialty__building__organization=request.user.organization,
            created_at__date__range=[start_date, end_date]
        ).annotate(
            day=ExtractWeekDay('created_at')
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')

        days = {
            2: 'Пн', 3: 'Вт', 4: 'Ср', 5: 'Чт',
            6: 'Пт', 7: 'Сб', 1: 'Вс'
        }

        data = []
        for day in range(2, 8):
            count = next(
                (item['count'] for item in applications if item['day'] == day),
                0
            )
            data.append({'name': days[day], 'Заявки': count})
        count = next(
            (item['count'] for item in applications if item['day'] == 1),
                0
        )
        data.append({'name': 'Вс', 'Заявки': count})

        cache.set(cache_key, data, timeout=86400)
        logger.info(f"Retrieved application stats for {request.user.email}")
        return Response(data, status=status.HTTP_200_OK)

class SpecialtyStatsView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsModerator | IsAdminOrg]

    @extend_schema(
        summary="Статистика специальностей по дням недели",
        description="Возвращает количество заявок на специальности в организации пользователя за текущую неделю, сгруппированное по дням недели (Пн-Вс). Данные кэшируются на 24 часа. Доступно для модераторов и администраторов организации.",
        responses={
            200: OpenApiResponse(
                description="Статистика успешно получена",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value=[
                            {"name": "Пн", "value": 15},
                            {"name": "Вт", "value": 10},
                            {"name": "Ср", "value": 7},
                            {"name": "Чт", "value": 13},
                            {"name": "Пт", "value": 8},
                            {"name": "Сб", "value": 4},
                            {"name": "Вс", "value": 1}
                        ]
                    )
                ]
            ),
            401: OpenApiResponse(
                description="Неавторизованный доступ",
                examples=[
                    OpenApiExample(
                        name="Ошибка 401",
                        value={"detail": "Authentication credentials were not provided."}
                    )
                ]
            ),
            403: OpenApiResponse(
                description="Email не подтверждён или недостаточно прав",
                examples=[
                    OpenApiExample(
                        name="Ошибка 403",
                        value={"message": "У вас недостаточно прав или email не подтверждён"}
                    )
                ]
            )
        }
    )
    def get(self, request):
        if not request.user.organization:
            logger.warning(f"User {request.user.email} has no organization assigned, returning empty data")
            return Response([], status=status.HTTP_200_OK)

        cache_key = f"specialty_stats_{request.user.organization.id}_{timezone.now().date()}"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.info(f"Cache hit for {cache_key}")
            return Response(cached_data, status=status.HTTP_200_OK)

        today = timezone.now().date()
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)

        applications = Application.objects.filter(
            building_specialty__building__organization=request.user.organization,
            created_at__date__range=[start_date, end_date]
        ).annotate(
            day=ExtractWeekDay('created_at')
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')

        days = {
            2: 'Пн', 3: 'Вт', 4: 'Ср', 5: 'Чт',
            6: 'Пт', 7: 'Сб', 1: 'Вс'
        }

        data = []
        for day in range(2, 8):
            count = next(
                (item['count'] for item in applications if item['day'] == day),
                0
            )
            data.append({'name': days[day], 'value': count})
        count = next(
            (item['count'] for item in applications if item['day'] == 1),
            0
        )
        data.append({'name': 'Вс', 'value': count})

        cache.set(cache_key, data, timeout=86400)
        logger.info(f"Retrieved specialty stats for {request.user.email}")
        return Response(data, status=status.HTTP_200_OK)

class ActivityStatsView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsModerator | IsAdminOrg]

    @extend_schema(
        summary="Статистика активности по дням недели",
        description="Возвращает количество заявок в организации пользователя за текущую неделю, сгруппированное по дням недели (Пн-Вс). Данные кэшируются на 24 часа. Доступно для модераторов и администраторов организации.",
        responses={
            200: OpenApiResponse(
                description="Статистика успешно получена",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value=[
                            {"name": "Пн", "Активность": 12},
                            {"name": "Вт", "Активность": 9},
                            {"name": "Ср", "Активность": 6},
                            {"name": "Чт", "Активность": 11},
                            {"name": "Пт", "Активность": 7},
                            {"name": "Сб", "Активность": 2},
                            {"name": "Вс", "Активность": 3}
                        ]
                    )
                ]
            ),
            401: OpenApiResponse(
                description="Неавторизованный доступ",
                examples=[
                    OpenApiExample(
                        name="Ошибка 401",
                        value={"detail": "Authentication credentials were not provided."}
                    )
                ]
            ),
            403: OpenApiResponse(
                description="Email не подтверждён или недостаточно прав",
                examples=[
                    OpenApiExample(
                        name="Ошибка 403",
                        value={"message": "У вас недостаточно прав или email не подтверждён"}
                    )
                ]
            )
        }
    )
    def get(self, request):
        if not request.user.organization:
            logger.warning(f"User {request.user.email} has no organization assigned, returning empty data")
            return Response([], status=status.HTTP_200_OK)

        cache_key = f"activity_stats_{request.user.organization.id}_{timezone.now().date()}"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.info(f"Cache hit for {cache_key}")
            return Response(cached_data, status=status.HTTP_200_OK)

        today = timezone.now().date()
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)

        applications = Application.objects.filter(
            building_specialty__building__organization=request.user.organization,
            created_at__date__range=[start_date, end_date]
        ).annotate(
            day=ExtractWeekDay('created_at')
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')

        days = {
            2: 'Пн', 3: 'Вт', 4: 'Ср', 5: 'Чт',
            6: 'Пт', 7: 'Сб', 1: 'Вс'
        }

        data = []
        for day in range(2, 8):
            count = next(
                (item['count'] for item in applications if item['day'] == day),
                0
            )
            data.append({'name': days[day], 'Активность': count})
        count = next(
            (item['count'] for item in applications if item['day'] == 1),
            0
        )
        data.append({'name': 'Вс', 'Активность': count})

        cache.set(cache_key, data, timeout=86400)
        logger.info(f"Retrieved activity stats for {request.user.email}")
        return Response(data, status=status.HTTP_200_OK)

class ModeratorActivityStatsView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsAdminOrg]

    @extend_schema(
        summary="Статистика активности модераторов по дням недели",
        description="Возвращает количество обновлённых заявок в организации пользователя за текущую неделю, сгруппированное по дням недели (Пн-Вс). Данные кэшируются на 24 часа. Доступно только для администраторов организации.",
        responses={
            200: OpenApiResponse(
                description="Статистика успешно получена",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value=[
                            {"name": "Пн", "Активность": 5},
                            {"name": "Вт", "Активность": 4},
                            {"name": "Ср", "Активность": 3},
                            {"name": "Чт", "Активность": 6},
                            {"name": "Пт", "Активность": 2},
                            {"name": "Сб", "Активность": 1},
                            {"name": "Вс", "Активность": 0}
                        ]
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Нет привязанной организации",
                examples=[
                    OpenApiExample(
                        name="Ошибка 400",
                        value={"detail": "User has no organization assigned"}
                    )
                ]
            ),
            401: OpenApiResponse(
                description="Неавторизованный доступ",
                examples=[
                    OpenApiExample(
                        name="Ошибка 401",
                        value={"detail": "Authentication credentials were not provided."}
                    )
                ]
            ),
            403: OpenApiResponse(
                description="Email не подтверждён или недостаточно прав",
                examples=[
                    OpenApiExample(
                        name="Ошибка 403",
                        value={"message": "У вас недостаточно прав или email не подтверждён"}
                    )
                ]
            )
        }
    )
    def get(self, request):
        if not request.user.organization:
            raise ValidationError("User has no organization assigned")

        cache_key = f"moderator_activity_stats_{request.user.organization.id}_{timezone.now().date()}"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.info(f"Cache hit for {cache_key}")
            return Response(cached_data, status=status.HTTP_200_OK)

        today = timezone.now().date()
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)

        applications = Application.objects.filter(
            building_specialty__building__organization=request.user.organization,
            updated_at__date__range=[start_date, end_date]
        ).annotate(
            day=ExtractWeekDay('updated_at')
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')

        days = {
            2: 'Пн', 3: 'Вт', 4: 'Ср', 5: 'Чт',
            6: 'Пт', 7: 'Сб', 1: 'Вс'
        }

        data = []
        for day in range(2, 8):
            count = next(
                (item['count'] for item in applications if item['day'] == day),
                0
            )
            data.append({'name': days[day], 'Активность': count})
        count = next(
            (item['count'] for item in applications if item['day'] == 1),
            0
        )
        data.append({'name': 'Вс', 'Активность': count})

        cache.set(cache_key, data, timeout=86400)
        logger.info(f"Retrieved moderator activity stats for {request.user.email}")
        return Response(data, status=status.HTTP_200_OK)

class SystemStatsView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsAdminApp]

    @extend_schema(
        summary="Системная статистика по месяцам",
        description="Возвращает количество заявок во всей системе за последние 30 недель, сгруппированное по месяцам (Янв-Дек). Данные кэшируются на 24 часа. Доступно только для администраторов системы.",
        responses={
            200: OpenApiResponse(
                description="Статистика успешно получена",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value=[
                            {"name": "Янв", "Заявки": 100},
                            {"name": "Фев", "Заявки": 120},
                            {"name": "Мар", "Заявки": 90},
                            {"name": "Апр", "Заявки": 110},
                            {"name": "Май", "Заявки": 130},
                            {"name": "Июн", "Заявки": 80},
                            {"name": "Июл", "Заявки": 70},
                            {"name": "Авг", "Заявки": 60},
                            {"name": "Сен", "Заявки": 140},
                            {"name": "Окт", "Заявки": 150},
                            {"name": "Ноя", "Заявки": 160},
                            {"name": "Дек", "Заявки": 170}
                        ]
                    )
                ]
            ),
            401: OpenApiResponse(
                description="Неавторизованный доступ",
                examples=[
                    OpenApiExample(
                        name="Ошибка 401",
                        value={"detail": "Authentication credentials were not provided."}
                    )
                ]
            ),
            403: OpenApiResponse(
                description="Email не подтверждён или недостаточно прав",
                examples=[
                    OpenApiExample(
                        name="Ошибка 403",
                        value={"message": "У вас недостаточно прав или email не подтверждён"}
                    )
                ]
            )
        }
    )
    def get(self, request):
        cache_key = f"system_stats_{timezone.now().date()}"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.info(f"Cache hit for {cache_key}")
            return Response(cached_data, status=status.HTTP_200_OK)

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

        cache.set(cache_key, data, timeout=86400)
        logger.info(f"Retrieved system stats for {request.user.email}")
        return Response(data, status=status.HTTP_200_OK)

class InstitutionStatsView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsAdminApp]

    @extend_schema(
        summary="Статистика по организациям",
        description="Возвращает статистику по количеству заявок для каждой организации. Если организаций с малым количеством заявок (<5) много, они объединяются в категорию 'Другие'. Данные кэшируются на 1 час. Доступно только для администраторов системы.",
        responses={
            200: OpenApiResponse(
                description="Статистика успешно получена",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value=[
                            {"name": "Университет А", "value": 50},
                            {"name": "Университет Б", "value": 30},
                            {"name": "Другие", "value": 10}
                        ]
                    )
                ]
            ),
            401: OpenApiResponse(
                description="Неавторизованный доступ",
                examples=[
                    OpenApiExample(
                        name="Ошибка 401",
                        value={"detail": "Authentication credentials were not provided."}
                    )
                ]
            ),
            403: OpenApiResponse(
                description="Email не подтверждён или недостаточно прав",
                examples=[
                    OpenApiExample(
                        name="Ошибка 403",
                        value={"message": "У вас недостаточно прав или email не подтверждён"}
                    )
                ]
            )
        }
    )
    def get(self, request):
        cache_key = "institution_stats"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.info(f"Cache hit for {cache_key}")
            return Response(cached_data, status=status.HTTP_200_OK)

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

        cache.set(cache_key, data, timeout=3600)
        logger.info(f"Retrieved institution stats for {request.user.email}")
        return Response(data, status=status.HTTP_200_OK)

class AdminActivityStatsView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified, IsAdminApp]

    @extend_schema(
        summary="Статистика активности администраторов по дням недели",
        description="Возвращает количество обновлённых заявок во всей системе за последнюю неделю, сгруппированное по дням недели (Вс-Сб). Данные кэшируются на 24 часа. Доступно только для администраторов системы.",
        responses={
            200: OpenApiResponse(
                description="Статистика успешно получена",
                examples=[
                    OpenApiExample(
                        name="Пример ответа",
                        value=[
                            {"name": "Вс", "Активность": 5},
                            {"name": "Пн", "Активность": 20},
                            {"name": "Вт", "Активность": 15},
                            {"name": "Ср", "Активность": 10},
                            {"name": "Чт", "Активность": 12},
                            {"name": "Пт", "Активность": 8},
                            {"name": "Сб", "Активность": 3}
                        ]
                    )
                ]
            ),
            401: OpenApiResponse(
                description="Неавторизованный доступ",
                examples=[
                    OpenApiExample(
                        name="Ошибка 401",
                        value={"detail": "Authentication credentials were not provided."}
                    )
                ]
            ),
            403: OpenApiResponse(
                description="Email не подтверждён или недостаточно прав",
                examples=[
                    OpenApiExample(
                        name="Ошибка 403",
                        value={"message": "У вас недостаточно прав или email не подтверждён"}
                    )
                ]
            )
        }
    )
    def get(self, request):
        cache_key = f"admin_activity_stats_{timezone.now().date()}"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.info(f"Cache hit for {cache_key}")
            return Response(cached_data, status=status.HTTP_200_OK)

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

        cache.set(cache_key, data, timeout=86400)
        logger.info(f"Retrieved admin activity stats for {request.user.email}")
        return Response(data, status=status.HTTP_200_OK)