from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from myapp.models import UserProfile
import os
from django.conf import settings
import mimetypes

class Command(BaseCommand):
    help = '将现有的头像文件迁移到数据库中'

    def handle(self, *args, **options):
        # 获取所有用户资料
        profiles = UserProfile.objects.all()
        migrated_count = 0
        error_count = 0

        for profile in profiles:
            try:
                # 检查是否有旧的头像文件
                if hasattr(profile, 'avatar') and profile.avatar:
                    avatar_path = os.path.join(settings.MEDIA_ROOT, str(profile.avatar))
                    
                    # 检查文件是否存在
                    if os.path.exists(avatar_path):
                        # 读取文件数据
                        with open(avatar_path, 'rb') as f:
                            avatar_data = f.read()
                        
                        # 获取文件类型
                        content_type, _ = mimetypes.guess_type(avatar_path)
                        if not content_type:
                            content_type = 'image/jpeg'  # 默认类型
                        
                        # 保存到数据库
                        profile.avatar_data = avatar_data
                        profile.avatar_type = content_type
                        profile.save()
                        
                        # 删除旧文件
                        os.remove(avatar_path)
                        migrated_count += 1
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'成功迁移用户 {profile.user.username} 的头像'
                            )
                        )
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'迁移用户 {profile.user.username} 的头像时出错: {str(e)}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'迁移完成。成功: {migrated_count}, 失败: {error_count}'
            )
        ) 