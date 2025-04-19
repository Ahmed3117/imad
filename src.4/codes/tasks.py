import os
import boto3
import time
import subprocess
import shutil
import concurrent.futures
from celery import shared_task
from django.conf import settings
from urllib.parse import urlparse
from botocore.exceptions import NoCredentialsError
import requests


def upload_to_s3(local_path, bucket_name, s3_path, s3_client):
    """Uploads a file to S3 and deletes it locally after successful upload."""
    try:
        s3_client.upload_file(local_path, bucket_name, s3_path)
        print(f"Uploaded {local_path} to s3://{bucket_name}/{s3_path}")
        os.remove(local_path)  # Delete after upload
    except NoCredentialsError:
        print("S3 credentials not available")
    except Exception as e:
        print(f"Failed to upload {local_path}: {e}")


def convert_to_hls(input_s3_url, output_folder, bucket_name, s3_folder, region_name, video_id):
    """Convert video to HLS by first downloading the file from S3."""
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=region_name,
    )

    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Download the input file from S3 to a local temp file
    parsed_url = urlparse(input_s3_url)
    input_key = parsed_url.path.lstrip('/')
    local_input_path = os.path.join(output_folder, "input_video")
    
    try:
        s3_client.download_file(bucket_name, input_key, local_input_path)
        print(f"Downloaded input file to {local_input_path}")
    except Exception as e:
        print(f"Failed to download input file: {e}")
        raise

    # Define stream profiles
    stream_profiles = [
        {"label": "360p", "resolution": "640x360", "video_bitrate": "400k", "audio_bitrate": "128k", "bandwidth": 528000},
        {"label": "480p", "resolution": "854x480", "video_bitrate": "800k", "audio_bitrate": "128k", "bandwidth": 928000},
        {"label": "720p", "resolution": "1280x720", "video_bitrate": "1500k", "audio_bitrate": "128k", "bandwidth": 1628000},
    ]

    def encode_and_upload(profile):
        label = profile["label"]
        output_file = os.path.join(output_folder, f"{label}.m3u8")
        segment_pattern = os.path.join(output_folder, f"{label}_%03d.ts")

        cmd = [
            "ffmpeg", "-y", "-i", local_input_path,
            "-vf", f"scale={profile['resolution']},format=yuv420p",
            "-c:v", "libx264", "-preset", "fast",
            "-b:v", profile["video_bitrate"],
            "-maxrate", profile["video_bitrate"],
            "-bufsize", f"{2 * int(profile['video_bitrate'].strip('k'))}k",
            "-c:a", "aac", "-b:a", profile["audio_bitrate"],
            "-hls_time", "6", "-hls_playlist_type", "vod",
            "-hls_segment_filename", segment_pattern, output_file
        ]

        process = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"{label} FFmpeg Output: {process.stderr}")

        upload_to_s3(output_file, bucket_name, f"{s3_folder}/{label}.m3u8", s3_client)
        for segment in os.listdir(output_folder):
            if segment.startswith(label) and segment.endswith(".ts"):
                segment_path = os.path.join(output_folder, segment)
                upload_to_s3(segment_path, bucket_name, f"{s3_folder}/{segment}", s3_client)

        return profile

    # Step 1: Process 360p first (sequentially) and notify backend
    successful_streams = []
    for profile in stream_profiles:
        if profile["label"] == "360p":
            try:
                result = encode_and_upload(profile)
                successful_streams.append(result)
                print(f"Completed 360p encoding and upload first.")

                # Notify backend that 360p is ready
                server_call_back = settings.EASY_STREAM_BASE
                data = {
                    "video_ready": True,
                    "video_id": video_id,
                    "streaming_url": f"{s3_folder}/360p.m3u8",
                    "resolution": "360p"
                }
                response = requests.post(server_call_back, data=data)
                print(f"Notified backend of 360p availability: {response}")

            except RuntimeError as e:
                print(e)

    # Step 2: Process 480p and 720p concurrently
    remaining_profiles = [p for p in stream_profiles if p["label"] != "360p"]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(encode_and_upload, p) for p in remaining_profiles]
        successful_streams.extend([future.result() for future in concurrent.futures.as_completed(futures)])

    # Step 3: Create and upload the master playlist
    if successful_streams:
        master_playlist = os.path.join(output_folder, "master.m3u8")
        with open(master_playlist, "w") as f:
            f.write("#EXTM3U\n")
            for profile in successful_streams:
                f.write(f"#EXT-X-STREAM-INF:BANDWIDTH={profile['bandwidth']},RESOLUTION={profile['resolution']}\n{profile['label']}.m3u8\n")
        
        upload_to_s3(master_playlist, bucket_name, f"{s3_folder}/master.m3u8", s3_client)
        print(f"Successfully created and uploaded HLS streams. Master playlist: {master_playlist}")
    else:
        print("No streams were successfully created")

    # Cleanup: Delete the downloaded input file
    if os.path.exists(local_input_path):
        os.remove(local_input_path)
        print(f"Deleted local input file: {local_input_path}")


@shared_task
def process_video(input_s3_url, video_id, bucket_name, region_name):
    """Process video by downloading from S3, converting to HLS, and uploading back to S3."""
    # Record start time
    start_time = time.time()
    
    # Step 1: Create HLS output folder
    hls_folder = f"media/tmp/hls/{video_id}"
    if not os.path.exists(hls_folder):
        os.makedirs(hls_folder)

    # Step 2: Convert and upload
    s3_folder = f"uploads/{video_id}/hls"
    convert_to_hls(input_s3_url, hls_folder, bucket_name, s3_folder, region_name, video_id)

    # Step 3: Cleanup temporary folder after upload
    if os.path.isdir(hls_folder):
        shutil.rmtree(hls_folder)
        print(f"Deleted temp folder: {hls_folder}")

    # Calculate time taken in seconds
    time_taken = time.time() - start_time

    # Step 4: Notify backend that all resolutions are ready (master playlist)
    server_call_back = settings.EASY_STREAM_BASE
    data = {
        "video_ready": True,
        "video_id": video_id,
        "streaming_url": f'{s3_folder}/master.m3u8',
        "resolution": "all",
        "time_taken": time_taken  # Time in seconds
    }
    response = requests.post(server_call_back, data=data)
    print(f"Notified backend of all resolutions: {response}")