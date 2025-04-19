import json
import os
import requests
import boto3
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import timedelta
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.filters import SearchFilter
from rest_framework.exceptions import ValidationError
from student.models import Student
from course.models import Course
from invoice.models import Invoice
from .tasks import process_video
# Create your views here.

#*>>>>>>>>>>>>>>>>>>>>>Convert Video To HLS>>>>>>>>>>>>>>>>>>>>>*#

@csrf_exempt
def convert_video(request):
    """Convert video to HLS, upload to S3, and call API after completion."""
    if request.method == "POST":
        # Get data from the POST request
        body = json.loads(request.body)
        video_url  = body.get("video_url")
        bucket_name = body.get("bucket_name")
        region_name  = body.get("region_name")
        video_id  = body.get("video_id")
        video_s3_path  = body.get("video_s3_path")
        print(body)
        # Call the Celery task
        task = process_video.delay(video_url, video_id,bucket_name, region_name)
            
        # Return the task ID
        return JsonResponse({"message": "Task started", "task_id": task.id})

#*>>>>>>>>>>>>>>>>>>>>>Convert Video To HLS>>>>>>>>>>>>>>>>>>>>>*#



