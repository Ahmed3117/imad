# Generated by Django 5.2 on 2025-05-18 16:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_teacheroomaccount_secret_token_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ZoomAccount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('account_id', models.CharField(max_length=100)),
                ('client_id', models.CharField(max_length=100)),
                ('client_secret', models.CharField(max_length=100)),
                ('secret_token', models.CharField(blank=True, max_length=100, null=True)),
                ('verification_token', models.CharField(blank=True, max_length=100, null=True)),
            ],
        ),
    ]
