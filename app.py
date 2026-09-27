import os
import random
import uuid
import requests
import subprocess
import re

from flask import Flask, request, render_template_string, send_file
import imageio_ffmpeg


app = Flask(__name__)

# ============================================================
# CONFIGURAÇÕES
# ============================================================

WIDTH = 1080
HEIGHT = 1920
FPS = 24
DURATION = 60

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

VIDEO_DIR = "videos"
TEMP_DIR = "temp"

os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


# ============================================================
# PAÍSES
# ============================================================

PAISES = {
    "Brasil": "Brazil",
    "Estados Unidos": "United States",
    "Canadá": "Canada",
    "México": "Mexico",
    "Argentina": "Argentina",
    "Chile": "Chile",
    "Peru": "Peru",
    "Colômbia": "Colombia",
    "Costa Rica": "Costa Rica",
    "Islândia": "Iceland",
    "Noruega": "Norway",
    "Suíça": "Switzerland",
    "França": "France",
    "Itália": "Italy",
    "Portugal": "Portugal",
    "Espanha": "Spain",
    "Escócia": "Scotland",
    "Irlanda": "Ireland",
    "Inglaterra": "England",
    "Alemanha": "Germany",
    "Áustria": "Austria",
    "Nova Zelândia": "New Zealand",
    "Austrália": "Australia",
    "Japão": "Japan",
    "China": "China",
    "Coreia do Sul": "South Korea",
    "Indonésia": "Indonesia",
    "Tailândia": "Thailand",
    "Filipinas": "Philippines",
    "Índia": "India",
    "Nepal": "Nepal",
    "África do Sul": "South Africa",
    "Quênia": "Kenya",
    "Marrocos": "Morocco",
    "Tanzânia": "Tanzania",
    "Turquia": "Turkey",
    "Grécia": "Greece",
    "Croácia": "Croatia",
    "Eslovênia": "Slovenia",
    "Finlândia": "Finland",
    "Suécia": "Sweden",
    "Polônia": "Poland"
}


# ============================================================
# PÁGINA
# ============================================================

HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>Nature Reel Maker</title>

<style>

body {
    margin: 0;
    padding: 20px;
    background: #111;
    color: white;
    font-family: Arial, sans-serif;
}

.container {
    max-width: 500px;
    margin: auto;
}

h1 {
    text-align: center;
    margin-bottom: 8px;
}

.subtitle {
    text-align: center;
    color: #aaa;
    margin-bottom: 25px;
}

.card {
    background: #1c1c1c;
    padding: 20px;
    border-radius: 18px;
}

label {
    display: block;
    margin-bottom: 8px;
    font-weight: bold;
}

select {
    width: 100%;
    padding: 15px;
    border-radius: 10px;
    border: none;
    font-size: 16px;
    margin-bottom: 20px;
}

button {
    width: 100%;
    padding: 16px;
    border: none;
    border-radius: 12px;
    background: #ffffff;
    color: #111;
    font-size: 17px;
    font-weight: bold;
    cursor: pointer;
}

button:hover {
    opacity: 0.9;
}

.info {
    margin-top: 20px;
    padding: 15px;
    background: #252525;
    border-radius: 12px;
    color: #bbb;
    font-size: 14px;
    line-height: 1.6;
}

</style>
</head>

<body>

<div class="container">

<h1>🌎 Nature Reel Maker</h1>

<div class="subtitle">
Vídeos reais de lagos e cachoeiras
</div>

<div class="card">

<form method="POST">

<label>Escolha o país</label>

<select name="pais" required>

{% for nome in paises %}
<option value="{{ nome }}">{{ nome }}</option>
{% endfor %}

</select>

<button type="submit">
🎬 Criar Reel
</button>

</form>

<div class="info">

🌊 Apenas lagos e cachoeiras<br>
🎥 Vídeo real<br>
🌎 Paisagens naturais<br>
📱 Formato vertical 1080x1920<br>
⏱️ Até 60 segundos<br>
🔇 Sem música<br>
🔇 Sem narração<br>
🚫 Sem texto<br>
🚫 Sem zoom artificial

</div>

</div>

</div>

</body>
</html>
"""


# ============================================================
# BUSCAR VÍDEOS NO PEXELS
# ============================================================

def buscar_videos(query):

    if not PEXELS_API_KEY:
        raise Exception(
            "PEXELS_API_KEY não configurada no Railway."
        )

    url = "https://api.pexels.com/v1/videos/search"

    headers = {
        "Authorization": PEXELS_API_KEY
    }

    params = {
        "query": query,
        "orientation": "landscape",
        "size": "large",
        "per_page": 80
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=30
    )

    if response.status_code != 200:
        raise Exception(
            f"Erro Pexels {response.status_code}: {response.text}"
        )

    data = response.json()

    return data.get("videos", [])


# ============================================================
# ESCOLHER VÍDEO
# ============================================================

def escolher_video(videos):

    candidatos = []

    palavras_boas = [
        "landscape",
        "scenic",
        "nature",
        "waterfall",
        "lake",
        "mountain",
        "river",
        "valley",
        "aerial",
        "drone",
        "panoramic",
        "view"
    ]

    palavras_ruins = [
        "person",
        "people",
        "man",
        "woman",
        "city",
        "street",
        "road",
        "car",
        "building",
        "hotel",
        "pool",
        "boat",
        "ship",
        "restaurant",
        "house"
    ]

    for video in videos:

        duracao = int(video.get("duration", 0))

        if duracao < 5:
            continue

        texto = str(video.get("url", "")).lower()

        score = 0

        for palavra in palavras_boas:
            if palavra in texto:
                score += 2

        for palavra in palavras_ruins:
            if palavra in texto:
                score -= 5

        # Dá preferência para vídeos que já tenham 60 segundos
        if duracao >= DURATION:
            score += 20

        # Dá preferência para vídeos longos
        score += min(duracao, 120) / 5

        # Escolhe arquivos disponíveis
        arquivos = video.get("video_files", [])

        if not arquivos:
            continue

        melhores = []

        for arquivo in arquivos:

            link = arquivo.get("link")

            if not link:
                continue

            if arquivo.get("file_type") != "video/mp4":
                continue

            largura = arquivo.get("width", 0)
            altura = arquivo.get("height", 0)

            if largura <= 0 or altura <= 0:
                continue

            melhores.append(arquivo)

        if not melhores:
            continue

        # Preferir maior resolução
        melhores.sort(
            key=lambda x: (
                x.get("width", 0) * x.get("height", 0)
            ),
            reverse=True
        )

        arquivo = melhores[0]

        candidatos.append({
            "video": video,
            "arquivo": arquivo,
            "score": score,
            "duracao": duracao
        })

    if not candidatos:
        return None

    candidatos.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    # Pega entre os melhores para não ficar sempre no mesmo vídeo
    melhores = candidatos[:10]

    return random.choice(melhores)


# ============================================================
# DOWNLOAD DO VÍDEO
# ============================================================

def baixar_video(url, destino):

    response = requests.get(
        url,
        stream=True,
        timeout=120
    )

    if response.status_code != 200:
        raise Exception(
            f"Erro ao baixar vídeo: HTTP {response.status_code}"
        )

    with open(destino, "wb") as arquivo:

        for bloco in response.iter_content(
            chunk_size=1024 * 1024
        ):

            if bloco:
                arquivo.write(bloco)


# ============================================================
# CRIAR REEL
# ============================================================

def criar_reel(video_path, output_path):

    comando = [
        FFMPEG,

        "-y",

        "-i",
        video_path,

        "-vf",

        (
            "scale=1080:1920:"
            "force_original_aspect_ratio=increase,"
            "crop=1080:1920"
        ),

        "-r",
        str(FPS),

        "-t",
        str(DURATION),

        "-an",

        "-c:v",
        "libx264",

        "-preset",
        "veryfast",

        "-crf",
        "20",

        "-pix_fmt",
        "yuv420p",

        "-movflags",
        "+faststart",

        output_path
    ]

    processo = subprocess.run(
        comando,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if processo.returncode != 0:

        raise Exception(
            "Erro FFmpeg:\n"
            + processo.stderr[-5000:]
        )


# ============================================================
# GERAR
# ============================================================

def gerar_video(pais):

    nome_pais = PAISES.get(
        pais,
        pais
    )

    # Várias buscas para aumentar a chance
    # de encontrar uma paisagem realmente bonita.
    consultas = [
        f"{nome_pais} waterfall landscape",
        f"{nome_pais} beautiful waterfall nature",
        f"{nome_pais} lake landscape",
        f"{nome_pais} beautiful lake nature",
        f"{nome_pais} scenic waterfall",
        f"{nome_pais} scenic lake",
        f"{nome_pais} panoramic nature landscape",
        f"{nome_pais} mountain lake"
    ]

    todos = []

    consultas_embaralhadas = consultas[:]
    random.shuffle(consultas_embaralhadas)

    for consulta in consultas_embaralhadas[:4]:

        videos = buscar_videos(consulta)

        todos.extend(videos)

        # Se já encontramos bastante material,
        # não fazemos chamadas desnecessárias.
        if len(todos) >= 80:
            break

    if not todos:
        raise Exception(
            "Nenhum vídeo encontrado para esse país."
        )

    escolhido = escolher_video(todos)

    if not escolhido:
        raise Exception(
            "Não encontrei um vídeo adequado de natureza."
        )

    video = escolhido["video"]
    arquivo = escolhido["arquivo"]

    video_id = video.get("id")

    url_video = arquivo["link"]

    temp_name = (
        f"{uuid.uuid4().hex}_original.mp4"
    )

    output_name = (
        f"nature_{pais.lower().replace(' ', '_')}_"
        f"{uuid.uuid4().hex[:8]}.mp4"
    )

    temp_path = os.path.join(
        TEMP_DIR,
        temp_name
    )

    output_path = os.path.join(
        VIDEO_DIR,
        output_name
    )

    try:

        print("====================================")
        print("🌎 PAÍS:", pais)
        print("🎥 VÍDEO PEXELS:", video_id)
        print("⏱️ DURAÇÃO ORIGINAL:", video.get("duration"))
        print("📐 RESOLUÇÃO:", arquivo.get("width"),
              "x", arquivo.get("height"))
        print("====================================")

        baixar_video(
            url_video,
            temp_path
        )

        criar_reel(
            temp_path,
            output_path
        )

        return output_path

    finally:

        if os.path.exists(temp_path):

            try:
                os.remove(temp_path)
            except:
                pass


# ============================================================
# ROTAS
# ============================================================

@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == "POST":

        pais = request.form.get("pais")

        try:

            caminho = gerar_video(pais)

            return send_file(
                caminho,
                as_attachment=True,
                download_name="nature_reel.mp4",
                mimetype="video/mp4"
            )

        except Exception as e:

            return f"""
            <html>
            <body style="
                background:#111;
                color:white;
                font-family:Arial;
                padding:30px;
            ">

            <h2>❌ Erro ao criar vídeo</h2>

            <pre style="
                white-space:pre-wrap;
                background:#222;
                padding:15px;
                border-radius:10px;
            ">{str(e)}</pre>

            <br>

            <a
            href="/"
            style="color:white;"
            >
            ← Voltar
            </a>

            </body>
            </html>
            """, 500

    return render_template_string(
        HTML,
        paises=PAISES.keys()
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health")
def health():

    return {
        "status": "ok",
        "app": "Nature Reel Maker"
    }


# ============================================================
# RODAR
# ============================================================

if __name__ == "__main__":

    port = int(
        os.getenv("PORT", "8080")
    )

    app.run(
        host="0.0.0.0",
        port=port
    )