import json
import random
from faker import Faker
from datetime import datetime, timedelta
import uuid
import hashlib

fake = Faker('ru_RU')

# Генерация тестовых данных
def generate_test_data():
    data = {
        'users': [],
        'applicant_profiles': [],
        'organizations': [],
        'buildings': [],
        'specialties': [],
        'building_specialties': [],
        'applications': [],
        'chats': [],
        'messages': []
    }

    # Генерация организаций
    for i in range(5):
        data['organizations'].append({
            'id': i + 1,
            'name': fake.company(),
            'email': f'org{i}@example.com',
            'phone': fake.phone_number(),
            'website': fake.url(),
            'description': fake.text(max_nb_chars=500),
            'address': fake.address(),
            'city': fake.city(),
            'created_at': fake.date_this_year().isoformat(),
            'updated_at': fake.date_this_year().isoformat()
        })

    # Генерация пользователей
    user_id = 1
    # Админы приложения
    for i in range(2):
        data['users'].append({
            'id': user_id,
            'email': f'admin_app{i}@example.com',
            'username': f'admin_app{i}@example.com',
            'password': hashlib.sha256('testpassword123'.encode()).hexdigest(),
            'is_verified': True,
            'role': 'admin_app',
            'consent_to_data_processing': True,
            'verification_token': str(uuid.uuid4()),
            'organization_id': None
        })
        user_id += 1

    # Админы организаций
    for org in data['organizations']:
        for i in range(2):
            data['users'].append({
                'id': user_id,
                'email': f'admin_org{org["id"]}_{i}@example.com',
                'username': f'admin_org{org["id"]}_{i}@example.com',
                'password': hashlib.sha256('testpassword123'.encode()).hexdigest(),
                'is_verified': True,
                'role': 'admin_org',
                'consent_to_data_processing': True,
                'verification_token': str(uuid.uuid4()),
                'organization_id': org['id']
            })
            user_id += 1

    # Модераторы
    for i in range(5):
        data['users'].append({
            'id': user_id,
            'email': f'moderator{i}@example.com',
            'username': f'moderator{i}@example.com',
            'password': hashlib.sha256('testpassword123'.encode()).hexdigest(),
            'is_verified': True,
            'role': 'moderator',
            'consent_to_data_processing': True,
            'verification_token': str(uuid.uuid4()),
            'organization_id': None
        })
        user_id += 1

    # Абитуриенты
    for i in range(50):
        data['users'].append({
            'id': user_id,
            'email': f'applicant{i}@example.com',
            'username': f'applicant{i}@example.com',
            'password': hashlib.sha256('testpassword123'.encode()).hexdigest(),
            'is_verified': True,
            'role': 'applicant',
            'consent_to_data_processing': True,
            'verification_token': str(uuid.uuid4()),
            'organization_id': None
        })
        # Профиль абитуриента
        data['applicant_profiles'].append({
            'id': user_id,
            'user_id': user_id,
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
            'middle_name': fake.first_name(),
            'date_of_birth': fake.date_of_birth(minimum_age=16, maximum_age=25).isoformat(),
            'citizenship': 'Россия',
            'birth_place': fake.city(),
            'passport_series': str(random.randint(1000, 9999)),
            'passport_number': str(random.randint(100000, 999999)),
            'passport_issued_date': fake.date_between(start_date='-10y', end_date='today').isoformat(),
            'passport_issued_by': fake.company(),
            'snils': f'{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(100, 999)} {random.randint(10, 99)}',
            'registration_address': fake.address(),
            'actual_address': fake.address(),
            'phone': fake.phone_number(),
            'education_type': random.choice(['school', 'npo', 'other']),
            'education_institution': fake.company(),
            'graduation_year': random.randint(2018, 2025),
            'document_type': random.choice(['certificate', 'diploma']),
            'document_series': f'MS{user_id:04d}',
            'document_number': str(random.randint(1000000, 9999999)),
            'average_grade': round(random.uniform(3.0, 5.0), 1),
            'calculated_average_grade': round(random.uniform(3.0, 5.0), 1),
            'foreign_languages': [fake.language_name() for _ in range(random.randint(0, 2))],
            'additional_info': fake.text(max_nb_chars=200),
            'mother_full_name': fake.name_female(),
            'mother_workplace': fake.company(),
            'mother_phone': fake.phone_number(),
            'father_full_name': fake.name_male(),
            'father_workplace': fake.company(),
            'father_phone': fake.phone_number()
        })
        user_id += 1

    # Генерация корпусов
    building_id = 1
    for org in data['organizations']:
        for i in range(2):
            data['buildings'].append({
                'id': building_id,
                'organization_id': org['id'],
                'name': f'Корпус {i+1}',
                'address': fake.address(),
                'phone': fake.phone_number(),
                'email': f'building{building_id}@example.com',
                'created_at': fake.date_time_this_year().isoformat(),
                'updated_at': fake.date_time_this_year().isoformat()
            })
            building_id += 1

    # Генерация специальностей
    specialty_id = 1
    for org in data['organizations']:
        for i in range(4):
            data['specialties'].append({
                'id': specialty_id,
                'organization_id': org['id'],
                'code': f'09.02.{i+1:02d}',
                'name': fake.job(),
                'duration': random.choice(['3 года 10 месяцев', '4 года', '2 года 10 месяцев']),
                'requirements': fake.text(max_nb_chars=200),
                'created_at': fake.date_time_this_year().isoformat(),
                'updated_at': fake.date_time_this_year().isoformat()
            })
            specialty_id += 1

    # Генерация BuildingSpecialty
    building_specialty_id = 1
    for building in data['buildings']:
        org_specialties = [s for s in data['specialties'] if s['organization_id'] == building['organization_id']]
        for specialty in random.sample(org_specialties, min(5, len(org_specialties))):
            data['building_specialties'].append({
                'id': building_specialty_id,
                'building_id': building['id'],
                'specialty_id': specialty['id'],
                'budget_places': random.randint(0, 50),
                'commercial_places': random.randint(0, 50),
                'commercial_price': round(random.uniform(50000, 200000), 2)
            })
            building_specialty_id += 1

    # Генерация заявок
    application_id = 1
    applicants = [u for u in data['users'] if u['role'] == 'applicant']
    for applicant in applicants:
        for _ in range(random.randint(2, 3)):
            data['applications'].append({
                'id': application_id,
                'applicant_id': applicant['id'],
                'building_specialty_id': random.choice(data['building_specialties'])['id'],
                'priority': random.randint(1, 5),
                'course': random.randint(1, 4),
                'study_form': random.choice(['full_time', 'part_time']),
                'funding_basis': random.choice(['budget', 'commercial']),
                'dormitory_needed': random.choice([True, False]),
                'first_time_education': random.choice([True, False]),
                'info_source': fake.text(max_nb_chars=100),
                'status': random.choice(['pending', 'accepted', 'rejected']),
                'reject_reason': fake.text(max_nb_chars=200) if random.choice(['rejected', '']) == 'rejected' else None,
                'created_at': fake.date_time_this_year().isoformat(),
                'updated_at': fake.date_time_this_year().isoformat()
            })
            application_id += 1

    # Генерация чатов и сообщений
    chat_id = 1
    for applicant in random.sample(applicants, 10):
        for org in random.sample(data['organizations'], 2):
            data['chats'].append({
                'id': chat_id,
                'organization_id': org['id'],
                'applicant_id': applicant['id'],
                'created_at': fake.date_time_this_year().isoformat(),
                'updated_at': fake.date_time_this_year().isoformat()
            })
            # Генерация сообщений
            senders = [applicant, random.choice([u for u in data['users'] if u['role'] in ['admin_org', 'moderator']])]
            for i in range(random.randint(5, 10)):
                data['messages'].append({
                    'id': chat_id * 10 + i + 1,
                    'chat_id': chat_id,
                    'sender_id': random.choice(senders)['id'],
                    'content': fake.text(max_nb_chars=500),
                    'created_at': fake.date_time_between(start_date='-30d', end_date='now').isoformat()
                })
            chat_id += 1

    return data

# Сохранение в JSON
def save_to_json(data, filename='test_data.json'):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    test_data = generate_test_data()
    save_to_json(test_data)
    print(f"JSON-файл с тестовыми данными создан: test_data.json")