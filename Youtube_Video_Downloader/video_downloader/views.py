from datetime import datetime
from django.shortcuts import render
from django.http import HttpResponse
from googleapiclient.discovery import build
import yt_dlp as youtube_dl
import os
from django.conf import settings
from urllib.error import HTTPError
import time
from urllib.parse import urlparse, parse_qs
import re

# YouTube API configuration
API_KEY = 'AIzaSyA71ET0YPk-8BEc75082ypqGkmbzxxswBw'
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

def sanitize_filename(title):
    # Replace invalid characters with underscores
    return re.sub(r'[<>:"/\\|?*]', '_', title)

def get_video_details(video_url):
    try:
        # Extract the video ID from the URL
        parsed_url = urlparse(video_url)
        if parsed_url.netloc == 'youtu.be':
            video_id = parsed_url.path[1:]
        else:
            query_params = parse_qs(parsed_url.query)
            video_id = query_params.get('v', [None])[0]

        if not video_id:
            raise ValueError("Invalid YouTube URL")

        # Build the YouTube API client
        youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)

        # Fetch video details
        response = youtube.videos().list(part='snippet,statistics', id=video_id).execute()
        video = response['items'][0]

        video_details = {
            'title': video['snippet']['title'],
            'channel': video['snippet']['channelTitle'],
            'views': video['statistics']['viewCount'],
            'thumbnail_url': video['snippet']['thumbnails']['default']['url'],
            'video_url': video_url,
        }
        return video_details
    except HTTPError as e:
        print(f"HTTP error occurred: {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def list_formats(video_url):
    ydl_opts = {
        'listformats': True,
        'format': 'best',
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(video_url, download=False)
        formats = result.get('formats', None)

        format_list = []
        for f in formats:
            format_list.append({
                'format_id': f['format_id'],
                'ext': f['ext'],
                'resolution': f['resolution'],
                'note': f.get('format_note', '')
            })

        return format_list

def index(request):
    video_details = None
    formats = None
    if request.method == 'POST':
        video_url = request.POST.get('video_url')
        video_details = get_video_details(video_url)
        formats = list_formats(video_url)

    return render(request, 'video_downloader/index.html', {'video_details': video_details, 'formats': formats})

def download_video(request):
    if request.method == 'POST':
        video_url = request.POST.get('video_url')
        format_id = request.POST.get('format_id')

        try:
            # Use yt-dlp to download the video with cookies
            current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            cookies_file_path = os.path.join(settings.BASE_DIR, 'cookies.txt')  # Update this path to match the location of your cookies.txt file
            output_template = os.path.join(settings.MEDIA_ROOT, '%(title)s.%(ext)s')
            ydl_opts = {
                'format': format_id,
                'outtmpl': output_template,
                'cookiefile': cookies_file_path,
            }
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(video_url)
                title = sanitize_filename(info_dict.get('title', 'video'))
                ext = info_dict.get('ext', 'mp4')
                downloaded_file_path = os.path.join(settings.MEDIA_ROOT, f"{title}_{current_time}.{ext}")

                # Ensure the file exists before setting the modification time
                if os.path.exists(downloaded_file_path):
                    # Set file modification time to current time
                    os.utime(downloaded_file_path, (time.time(), time.time()))
                # else:
                #     # Log an error if the file does not exist
                #     print(f"File not found: {downloaded_file_path}")
                #     return HttpResponse(f"File not found: {downloaded_file_path}", status=500)

            return HttpResponse(f"Video downloaded successfully: {downloaded_file_path}")
        except HTTPError as e:
            print(f"HTTP error occurred: {e}")
            return HttpResponse(f"HTTP error occurred: {e}", status=403)
        except Exception as e:
            print(f"An error occurred: {e}")
            return HttpResponse(f"An error occurred: {e}", status=500)

    return HttpResponse("Invalid request method", status=405)