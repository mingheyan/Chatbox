# Generated by Django 5.2 on 2025-05-12 15:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("myapp", "0006_userprofile_avatar"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="userprofile",
            name="avatar",
        ),
        migrations.AddField(
            model_name="userprofile",
            name="avatar_data",
            field=models.BinaryField(blank=True, null=True, verbose_name="头像数据"),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="avatar_type",
            field=models.CharField(
                blank=True, max_length=50, null=True, verbose_name="头像类型"
            ),
        ),
    ]
