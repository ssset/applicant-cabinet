from rest_framework.views import exception_handler
from rest_framework.response import Response

print("Loading error_config.py")

def custom_exception_handler(exc, context):
    print("Custom exception handler called!")
    print(f"Exception: {exc}")
    print(f"Context: {context}")
    response = exception_handler(exc, context)

    if response is not None:
        print(f"Original response.data: {response.data}")
        error_message = None

        # Проверяем, что response.data — это словарь
        if isinstance(response.data, dict):
            # Обрабатываем non_field_errors
            if 'non_field_errors' in response.data:
                error = response.data['non_field_errors']
                if isinstance(error, list) and error:
                    error = error[0]
                if hasattr(error, 'string'):
                    error_message = str(error.string)
                else:
                    error_message = str(error)
            # Обрабатываем detail
            elif 'detail' in response.data:
                error = response.data['detail']
                if hasattr(error, 'string'):
                    error_message = str(error.string)
                else:
                    error_message = str(error)
            # Обрабатываем ошибки полей
            else:
                first_key = next(iter(response.data), None)
                if first_key:
                    error = response.data[first_key]
                    if isinstance(error, list) and error:
                        error = error[0]
                    if hasattr(error, 'string'):
                        error_message = str(error.string)
                    else:
                        error_message = str(error)

        # Если не удалось извлечь сообщение, берём текст исключения
        if not error_message:
            error_message = str(exc)

        # Перезаписываем response.data в нужный формат
        response.data = {'message': error_message}
        print(f"Modified response.data: {response.data}")

    return response