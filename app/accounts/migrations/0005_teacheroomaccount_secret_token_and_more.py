# Generated by Django 5.1.7 on 2025-04-13 11:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_teacheroomaccount_is_paid'),
    ]

    operations = [
        migrations.AddField(
            model_name='teacheroomaccount',
            name='secret_token',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='teacheroomaccount',
            name='verification_token',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
