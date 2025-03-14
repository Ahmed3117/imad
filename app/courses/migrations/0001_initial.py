# Generated by Django 5.0.4 on 2025-02-19 19:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Level',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Track',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('level', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tracks', to='courses.level')),
            ],
        ),
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('image', models.ImageField(default='defaults/default.jpg', upload_to='courses/')),
                ('preview_video', models.CharField(blank=True, max_length=50, null=True)),
                ('level', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='courses', to='courses.level')),
                ('track', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='courses', to='courses.track')),
            ],
        ),
        migrations.CreateModel(
            name='CourseTranslation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('language', models.CharField(max_length=10)),
                ('translated_name', models.CharField(max_length=200)),
                ('translated_description', models.TextField()),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='translations', to='courses.course')),
            ],
            options={
                'unique_together': {('course', 'language')},
            },
        ),
        migrations.CreateModel(
            name='LevelTranslation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('language', models.CharField(max_length=10)),
                ('translated_name', models.CharField(max_length=200)),
                ('level', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='translations', to='courses.level')),
            ],
            options={
                'unique_together': {('level', 'language')},
            },
        ),
        migrations.CreateModel(
            name='TrackTranslation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('language', models.CharField(max_length=10)),
                ('translated_name', models.CharField(max_length=200)),
                ('track', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='translations', to='courses.track')),
            ],
            options={
                'unique_together': {('track', 'language')},
            },
        ),
    ]
