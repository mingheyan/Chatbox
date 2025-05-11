from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from myapp.models import UserProfile

class Command(BaseCommand):
    help = '为所有现有用户创建用户资料'

    def handle(self, *args, **options):
        users_without_profile = User.objects.filter(profile=None)
        created_count = 0
        
        for user in users_without_profile:
            UserProfile.objects.create(user=user)
            created_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'成功创建了 {created_count} 个用户资料'
            )
        ) 