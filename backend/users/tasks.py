from celery import shared_task

@shared_task
def test_task():
    print("Test task is running!")
    return "Task completed"