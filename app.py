import os
import random
import uuid
import shutil
import subprocess
import requests

from flask import Flask, request, render_template_string, send_file
import imageio_ffmpeg


# ============================================================
# APP
# ============================================================

app = Flask(__name__)

PORT = int(os.getenv("PORT", "8080"))

# ============================================================
# CONFIGURAÇÕES
# ============================================================

WIDTH = 1080
HEIGHT = 1920

PROCESS_WIDTH = 540
PROCESS_HEIGHT = 960

FPS = 24

CLIP_DURATION = 15
CLIP_COUNT = 4
FINAL_DURATION = 60

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

VIDEO_DIR = "videos"
TEMP_DIR = "temp"
OUTPUT_DIR = "outputs"

os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# FFmpeg
# ============================================================

try:
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG = shutil.which("ffmpeg")

if not FFMPEG:
    raise RuntimeError("FFmpeg não encontrado.")


print("=" * 60)
print("FFMPEG:", FFMPEG)
print("=" * 60)


# ============================================================
# PAÍSES / LOCAIS
# ============================================================

LOCAIS = {
    "Brasil": [
        "Brazil beautiful landscape nature",
        "Brazil waterfall landscape",
        "Brazil mountains lake nature",
        "Brazil scenic nature"
    ],

    "Ilhas Faroé": [
        "Faroe Islands landscape",
        "Faroe Islands waterfalls",
        "Faroe Islands mountains ocean",
        "Faroe Islands scenic nature"
    ],

    "Suíça": [
        "Switzerland Alps landscape",
        "Swiss mountains lake",
        "Switzerland mountain waterfall",
        "Swiss Alps scenic landscape"
    ],

    "Noruega": [
        "Norway fjord landscape",
        "Norway mountains lake",
        "Norway waterfall nature",
        "Norway scenic landscape"
    ],

    "Islândia": [
        "Iceland waterfall landscape",
        "Iceland mountains nature",
        "Iceland glacier lake",
        "Iceland scenic landscape"
    ],

    "Canadá": [
        "Canada mountain lake landscape",
        "Canada waterfall nature",
        "Canadian Rockies landscape",
        "Canada scenic nature"
    ],

    "Nova Zelândia": [
        "New Zealand mountains lake",
        "New Zealand waterfall landscape",
        "New Zealand nature scenery",
        "New Zealand scenic mountains"
    ],

    "Áustria": [
        "Austria Alps landscape",
        "Austria mountain lake",
        "Austria waterfall nature",
        "Austrian Alps scenic"
    ],

    "Eslovênia": [
        "Slovenia Lake Bled landscape",
        "Slovenia mountains lake",
        "Slovenia waterfall nature",
        "Slovenia scenic landscape"
    ],

    "França": [
        "France mountain landscape",
        "French Alps lake",
        "France waterfall nature",
        "France scenic landscape"
    ],

    "Itália": [
        "Italy Dolomites landscape",
        "Italian Alps lake",
        "Italy mountain waterfall",
        "Italy scenic nature"
    ],

    "Estados Unidos": [
        "USA mountain lake landscape",
        "Yosemite landscape",
        "USA waterfall nature",
        "Rocky Mountains USA"
    ],

    "Japão": [
        "Japan mountain lake nature",
        "Japan waterfall landscape",
        "Japan scenic mountains",
        "Japan forest waterfall"
    ],

    "Peru": [
        "Peru mountains landscape",
        "Peru lake mountains",
        "Peru waterfall nature",
        "Peru scenic landscape"
    ],

    "Chile": [
        "Chile Patagonia landscape",
        "Chile mountains lake",
        "Chile waterfall nature",
        "Torres del Paine landscape"
    ],

    "Argentina": [
        "Argentina Patagonia landscape",
        "Argentina mountains lake",
        "Argentina waterfall nature",
        "Argentina scenic landscape"
    ]
}


# ============================================================
# HTML
# ============================================================

HTML = """
<!DOCTYPE html>
<html lang="pt-BR">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>Mundo Afora</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    padding: 20px;
    background: #111;
    color: white;
    font-family: Arial, sans-serif;
}

.container {
    max-width: 600px;
    margin: auto;
}

h1 {
    text-align: center;
    margin-bottom: 10px;
}

.subtitle {
    text-align: center;
    color: #aaa;
    margin-bottom: 30px;
}

label {
    display: block;
    margin-bottom: 8px;
    font-weight: bold;
}

select,
button {
    width: 100%;
    padding: 15px;
    margin-bottom: 20px;
    border-radius: 10px;
    border: none;
    font-size: 16px;
}

select {
    background: #222;
    color: white;
}

button {
    background: #fff;
    color: #111;
    font-weight: bold;
    cursor: pointer;
}

button:hover {
    opacity: 0.9;
}

.info {
    background: #1d1d1d;
    padding: 15px;
    border-radius: 10px;
    margin-bottom: 20px;
    color: #bbb;
    line-height: 1.5;
}

</style>

</head>

<body>

<div class="container">

<h1>🌎 Mundo Afora</h1>

<div class="subtitle">
Vídeos de paisagens incríveis pelo mundo
</div>

<div class="info">
🎥 Vídeo vertical<br>
⏱️ 60 segundos<br>
📱 1080 × 1920<br>
🔇 Sem áudio<br>
👤 Sem pessoas
</div>

<form method="POST" action="/gerar">

<label>Escolha o país</label>

<select name="local" required>

{% for local in locais %}

<option value="{{ local }}">
{{ local }}
</option>

{% endfor %}

</select>

<button type="submit">
🌎 GERAR VÍDEO
</button>

</form>

</div>

</body>

</html>
"""


# ============================================================
# LIMPAR ARQUIVO
# ============================================================

def remover_arquivo(path):

    try:

        if os.path.exists(path):
            os.remove(path)

    except Exception as e:

        print("[ERRO REMOVENDO]", e)


# ============================================================
# DOWNLOAD PEXELS
# ============================================================

def buscar_video(query):

    if not PEXELS_API_KEY:
        raise RuntimeError("PEXELS_API_KEY não configurada.")

    url = "https://api.pexels.com/videos/search"

    headers = {
        "Authorization": PEXELS_API_KEY
    }

    params = {
        "query": query,
        "per_page": 20,
        "orientation": "portrait"
    }

    print("[PEXELS]", query)

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    videos = data.get("videos", [])

    if not videos:

        # Segunda tentativa sem portrait
        params["orientation"] = "landscape"

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        videos = data.get("videos", [])

    if not videos:
        return None

    random.shuffle(videos)

    for video in videos:

        files = video.get("video_files", [])

        candidatos = []

        for f in files:

            link = f.get("link")

            if not link:
                continue

            width = f.get("width") or 0
            height = f.get("height") or 0

            candidatos.append(
                (
                    width * height,
                    width,
                    height,
                    link
                )
            )

        if not candidatos:
            continue

        # Pega arquivo com melhor resolução disponível
        candidatos.sort(reverse=True)

        _, width, height, link = candidatos[0]

        print(
            "[VIDEO ENCONTRADO]",
            width,
            "x",
            height
        )

        return link

    return None


# ============================================================
# BAIXAR
# ============================================================

def baixar_video(url, destino):

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    print("[DOWNLOAD]", url)

    with requests.get(
        url,
        headers=headers,
        stream=True,
        timeout=60
    ) as response:

        response.raise_for_status()

        with open(destino, "wb") as f:

            for chunk in response.iter_content(
                chunk_size=1024 * 1024
            ):

                if chunk:
                    f.write(chunk)

    tamanho = os.path.getsize(destino)

    print(
        "[DOWNLOAD OK]",
        round(tamanho / 1024 / 1024, 2),
        "MB"
    )

    return destino


# ============================================================
# PROCESSAR CLIPE
# ============================================================

def processar_clipe(entrada, saida):

    print("=" * 60)
    print("[PROCESSANDO CLIPE]")
    print(entrada)
    print("=" * 60)

    comando = [
        FFMPEG,

        "-hide_banner",
        "-loglevel", "error",

        "-y",

        "-i", entrada,

        "-t", str(CLIP_DURATION),

        "-vf",
        (
            f"scale={PROCESS_WIDTH}:{PROCESS_HEIGHT}:"
            "force_original_aspect_ratio=increase,"
            f"crop={PROCESS_WIDTH}:{PROCESS_HEIGHT},"
            f"fps={FPS},"
            "format=yuv420p"
        ),

        "-an",

        "-c:v", "libx264",

        "-preset", "ultrafast",

        "-crf", "30",

        "-pix_fmt", "yuv420p",

        "-r", str(FPS),

        "-movflags", "+faststart",

        saida
    ]

    result = subprocess.run(
        comando,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:

        print("[ERRO CLIPE]")
        print(result.stderr)

        raise RuntimeError(
            "Falha ao processar clipe."
        )

    if not os.path.exists(saida):

        raise RuntimeError(
            "Clipe processado não foi criado."
        )

    tamanho = os.path.getsize(saida)

    if tamanho < 10000:

        raise RuntimeError(
            "Clipe processado ficou inválido."
        )

    print(
        "[CLIPE OK]",
        round(tamanho / 1024 / 1024, 2),
        "MB"
    )

    return saida


# ============================================================
# CONCATENAR SEM REENCODAR
# ============================================================

def concatenar_clipes(clipes, saida):

    lista = os.path.join(
        TEMP_DIR,
        f"concat_{uuid.uuid4().hex}.txt"
    )

    try:

        with open(lista, "w", encoding="utf-8") as f:

            for clipe in clipes:

                caminho = os.path.abspath(clipe)

                caminho = caminho.replace(
                    "\\",
                    "/"
                )

                caminho = caminho.replace(
                    "'",
                    "'\\''"
                )

                f.write(
                    "file '"
                    + caminho
                    + "'\n"
                )

        print("=" * 60)
        print("[CONCAT]")
        print(lista)
        print("=" * 60)

        comando = [
            FFMPEG,

            "-hide_banner",
            "-loglevel", "error",

            "-y",

            "-f", "concat",

            "-safe", "0",

            "-i", lista,

            "-an",

            "-c", "copy",

            saida
        ]

        result = subprocess.run(
            comando,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:

            print("[ERRO CONCAT]")
            print(result.stderr)

            raise RuntimeError(
                "Falha ao juntar os clipes."
            )

        if not os.path.exists(saida):

            raise RuntimeError(
                "Arquivo concatenado não foi criado."
            )

        tamanho = os.path.getsize(saida)

        print(
            "[CONCAT OK]",
            round(tamanho / 1024 / 1024, 2),
            "MB"
        )

        return saida

    finally:

        remover_arquivo(lista)


# ============================================================
# CONVERTER PARA 1080x1920
# ============================================================

def finalizar_video(entrada, saida):

    print("=" * 60)
    print("[FINALIZANDO]")
    print(entrada)
    print("=" * 60)

    comando = [
        FFMPEG,

        "-hide_banner",
        "-loglevel", "error",

        "-y",

        "-i", entrada,

        "-vf",
        (
            f"scale={WIDTH}:{HEIGHT}:"
            "force_original_aspect_ratio=increase,"
            f"crop={WIDTH}:{HEIGHT},"
            f"fps={FPS},"
            "format=yuv420p"
        ),

        "-an",

        "-c:v", "libx264",

        "-preset", "ultrafast",

        "-crf", "31",

        "-pix_fmt", "yuv420p",

        "-r", str(FPS),

        "-t", str(FINAL_DURATION),

        "-movflags", "+faststart",

        saida
    ]

    result = subprocess.run(
        comando,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    print(
        "[FFMPEG RETURN CODE]",
        result.returncode
    )

    if result.returncode != 0:

        print("[FFMPEG ERRO]")
        print(result.stderr)

        raise RuntimeError(
            "FFmpeg falhou na finalização."
        )

    if not os.path.exists(saida):

        raise RuntimeError(
            "Vídeo final não foi criado."
        )

    tamanho = os.path.getsize(saida)

    if tamanho < 100000:

        raise RuntimeError(
            "Vídeo final ficou inválido."
        )

    print(
        "[VIDEO FINAL OK]",
        round(tamanho / 1024 / 1024, 2),
        "MB"
    )

    return saida


# ============================================================
# GERAR VÍDEO
# ============================================================

def gerar_video(local):

    if local not in LOCAIS:

        raise ValueError(
            "Local inválido."
        )

    trabalho = os.path.join(
        TEMP_DIR,
        uuid.uuid4().hex
    )

    os.makedirs(
        trabalho,
        exist_ok=True
    )

    arquivos_originais = []
    clipes_processados = []

    try:

        queries = LOCAIS[local]

        # ----------------------------------------------------
        # 1. BAIXAR 4 VÍDEOS
        # ----------------------------------------------------

        for i in range(CLIP_COUNT):

            query = queries[
                i % len(queries)
            ]

            url = buscar_video(query)

            if not url:

                print(
                    "[PULAR]",
                    "Nenhum vídeo encontrado:",
                    query
                )

                continue

            original = os.path.join(
                trabalho,
                f"original_{i}.mp4"
            )

            baixar_video(
                url,
                original
            )

            arquivos_originais.append(
                original
            )

            # ------------------------------------------------
            # PROCESSAR
            # ------------------------------------------------

            processado = os.path.join(
                trabalho,
                f"clip_{i}.mp4"
            )

            processar_clipe(
                original,
                processado
            )

            clipes_processados.append(
                processado
            )

            # Remove original imediatamente
            remover_arquivo(original)

        # ----------------------------------------------------
        # VERIFICAR QUANTIDADE
        # ----------------------------------------------------

        print(
            "[CLIPES PROCESSADOS]",
            len(clipes_processados)
        )

        if len(clipes_processados) < 4:

            raise RuntimeError(
                f"Foram encontrados apenas "
                f"{len(clipes_processados)} clipes válidos."
            )

        # ----------------------------------------------------
        # CONCAT
        # ----------------------------------------------------

        concatenado = os.path.join(
            trabalho,
            "concatenado.mp4"
        )

        concatenar_clipes(
            clipes_processados,
            concatenado
        )

        # ----------------------------------------------------
        # FINAL
        # ----------------------------------------------------

        nome_final = (
            "mundo_afora_"
            + uuid.uuid4().hex[:10]
            + ".mp4"
        )

        saida_final = os.path.join(
            OUTPUT_DIR,
            nome_final
        )

        finalizar_video(
            concatenado,
            saida_final
        )

        print("=" * 60)
        print("[GERAÇÃO CONCLUÍDA]")
        print(saida_final)
        print("=" * 60)

        return saida_final

    finally:

        # Limpeza
        try:

            shutil.rmtree(
                trabalho,
                ignore_errors=True
            )

        except Exception:
            pass


# ============================================================
# HOME
# ============================================================

@app.route("/", methods=["GET"])
def index():

    return render_template_string(
        HTML,
        locais=LOCAIS.keys()
    )


# ============================================================
# GERAR
# ============================================================

@app.route("/gerar", methods=["POST"])
def gerar():

    local = request.form.get(
        "local",
        ""
    ).strip()

    try:

        arquivo = gerar_video(local)

        return send_file(
            arquivo,
            as_attachment=True,
            download_name=os.path.basename(
                arquivo
            ),
            mimetype="video/mp4"
        )

    except Exception as e:

        print(
            "[ERRO GERAL]",
            repr(e)
        )

        return f"""
        <!DOCTYPE html>
        <html lang="pt-BR">

        <head>

        <meta charset="UTF-8">

        <meta name="viewport"
              content="width=device-width,initial-scale=1">

        <style>

        body {{
            background:#111;
            color:white;
            font-family:Arial;
            padding:30px;
            text-align:center;
        }}

        .erro {{
            background:#222;
            padding:20px;
            border-radius:12px;
            max-width:600px;
            margin:auto;
        }}

        a {{
            display:block;
            margin-top:20px;
            color:white;
        }}

        </style>

        </head>

        <body>

        <div class="erro">

        <h2>❌ Erro ao gerar vídeo</h2>

        <p>
        Não foi possível gerar o vídeo final.
        </p>

        <p>
        Tente novamente.
        </p>

        <a href="/">
        ← Voltar
        </a>

        </div>

        </body>

        </html>
        """, 500


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health")
def health():

    return {
        "status": "ok",
        "ffmpeg": FFMPEG,
        "clips": CLIP_COUNT,
        "duration": FINAL_DURATION,
        "resolution": f"{WIDTH}x{HEIGHT}"
    }


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=PORT
    )