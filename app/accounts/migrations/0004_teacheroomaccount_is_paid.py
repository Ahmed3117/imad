# Generated by Django 5.1.7 on 2025-04-13 11:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_teacheroomaccount'),
    ]

    operations = [
        migrations.AddField(
            model_name='teacheroomaccount',
            name='is_paid',
            field=models.BooleanField(default=False),
        ),
    ]
