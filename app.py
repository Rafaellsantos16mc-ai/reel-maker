import os
import uuid
import requests
import subprocess

from flask import Flask, request, render_template_string, send_file
from PIL import Image
from imageio_ffmpeg import get_ffmpeg_exe

app = Flask(__name__)

# ============================================================
# CONFIGURAÇÕES
# ============================================================

WIDTH = 1080
HEIGHT = 1920
FPS = 24
DURACAO = 60

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

VIDEOS_DIR = "videos"
IMAGES_DIR = "imagens"

os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(IM