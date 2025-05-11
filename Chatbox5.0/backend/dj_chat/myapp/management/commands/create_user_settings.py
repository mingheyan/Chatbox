from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from myapp.models import UserSettings

class Command(BaseCommand):
    help = '为所有现有用户创建默认设置'

    def handle(self, *args, **options):
        users_without_settings = User.objects.filter(settings=None)
        created_count = 0
        
        for user in users_without_settings:
            UserSettings.objects.create(
                user=user,
                dark_mode=False,
                sound_enabled=True,
                show_timestamps=True,
                auto_scroll=True
            )
            created_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'成功为 {created_count} 个用户创建了默认设置'
            )
        ) 