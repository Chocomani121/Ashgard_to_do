from celery import shared_task


@shared_task
def db_backup_task():
    print("\n\n\nHello World!\n\n\n")
    # return 
    pass



