import os
import random
import uuid
import shutil
import subprocess
import asyncio
import re

import requests
import edge_tts
import imageio_ffmpeg

from flask import Flask, request, render_template_string, send_file


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

VOICE = "pt-BR-AntonioNeural"

# Um pouco mais rápida, mas ainda natural
VOICE_RATE = "+8%"

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

VIDEO_DIR = "videos"
TEMP_DIR = "temp"
OUTPUT_DIR = "outputs"

os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# FFMPEG
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
# LOCAIS
# ============================================================

LOCAIS = {

    "Ilhas Faroé": {
        "buscas": [
            "Faroe Islands landscape",
            "Faroe Islands waterfall",
            "Faroe Islands mountains ocean",
            "Faroe Islands nature"
        ],
        "titulo": "ILHAS FAROÉ",
        "texto": (
            "As Ilhas Faroé são um arquipélago do Atlântico Norte "
            "conhecido por suas montanhas verdes, falésias, cachoeiras "
            "e pequenas vilas cercadas pelo oceano."
        )
    },

    "Suíça": {
        "buscas": [
            "Switzerland Alps landscape",
            "Swiss mountain lake",
            "Swiss Alps waterfall",
            "Switzerland scenic mountains"
        ],
        "titulo": "SUÍÇA",
        "texto": (
            "Os Alpes suíços formam algumas das paisagens mais conhecidas "
            "da Europa. Montanhas, lagos, vales e pequenas cidades criam "
            "cenários que parecem ter saído de um filme."
        )
    },

    "Noruega": {
        "buscas": [
            "Norway fjord landscape",
            "Norway mountains lake",
            "Norway waterfall",
            "Norway scenic nature"
        ],
        "titulo": "NORUEGA",
        "texto": (
            "A Noruega é famosa pelos seus fiordes, enormes montanhas e "
            "cachoeiras. Em algumas regiões, o oceano se mistura diretamente "
            "com vales cercados por montanhas."
        )
    },

    "Islândia": {
        "buscas": [
            "Iceland waterfall",
            "Iceland mountains landscape",
            "Iceland glacier lake",
            "Iceland scenic nature"
        ],
        "titulo": "ISLÂNDIA",
        "texto": (
            "A Islândia reúne vulcões, geleiras, cachoeiras e paisagens "
            "dramáticas. É um dos lugares onde a força da natureza pode "
            "ser percebida praticamente em todos os cantos."
        )
    },

    "Canadá": {
        "buscas": [
            "Canada Rocky Mountains lake",
            "Canada mountain landscape",
            "Canada waterfall",
            "Canadian Rockies nature"
        ],
        "titulo": "CANADÁ",
        "texto": (
            "As Montanhas Rochosas canadenses são conhecidas pelos picos "
            "nevados, lagos de águas cristalinas e grandes áreas naturais. "
            "É uma paisagem que muda completamente conforme a estação."
        )
    },

    "Nova Zelândia": {
        "buscas": [
            "New Zealand mountains lake",
            "New Zealand waterfall",
            "New Zealand scenic landscape",
            "New Zealand nature"
        ],
        "titulo": "NOVA ZELÂNDIA",
        "texto": (
            "A Nova Zelândia combina montanhas, lagos, florestas e "
            "cachoeiras em uma área relativamente pequena. Por isso, "
            "uma viagem pelo país pode revelar paisagens completamente diferentes."
        )
    },

    "Áustria": {
        "buscas": [
            "Austria Alps landscape",
            "Austria mountain lake",
            "Austria waterfall",
            "Austrian Alps nature"
        ],
        "titulo": "ÁUSTRIA",
        "texto": (
            "Grande parte da Áustria é marcada pelos Alpes. A região reúne "
            "vilarejos, lagos, florestas e montanhas que formam algumas das "
            "paisagens mais características da Europa Central."
        )
    },

    "Eslovênia": {
        "buscas": [
            "Slovenia mountains lake",
            "Slovenia waterfall",
            "Slovenia nature landscape",
            "Slovenia Alps"
        ],
        "titulo": "ESLOVÊNIA",
        "texto": (
            "A Eslovênia é um pequeno país europeu com uma grande variedade "
            "de paisagens. Alpes, lagos, rios e florestas aparecem muito "
            "próximos uns dos outros."
        )
    },

    "França": {
        "buscas": [
            "French Alps landscape",
            "France mountain lake",
            "France waterfall nature",
            "French mountains"
        ],
        "titulo": "FRANÇA",
        "texto": (
            "Além das grandes cidades e monumentos, a França também possui "
            "vastas regiões montanhosas. Nos Alpes franceses, lagos e picos "
            "formam paisagens impressionantes."
        )
    },

    "Itália": {
        "buscas": [
            "Dolomites Italy landscape",
            "Italian Alps lake",
            "Italy mountain nature",
            "Dolomites mountains"
        ],
        "titulo": "ITÁLIA",
        "texto": (
            "As Dolomitas, no norte da Itália, são conhecidas pelas suas "
            "formações rochosas marcantes. A combinação entre montanhas, "
            "vales e lagos cria uma paisagem única."
        )
    },

    "Estados Unidos": {
        "buscas": [
            "USA Rocky Mountains",
            "Yosemite landscape",
            "USA mountain lake",
            "USA waterfall nature"
        ],
        "titulo": "ESTADOS UNIDOS",
        "texto": (
            "Os Estados Unidos possuem algumas das maiores áreas naturais "
            "protegidas do mundo. Montanhas, cânions, florestas e cachoeiras "
            "fazem parte de uma enorme diversidade de paisagens."
        )
    },

    "Japão": {
        "buscas": [
            "Japan mountain lake",
            "Japan waterfall nature",
            "Japan scenic mountains",
            "Japan forest landscape"
        ],
        "titulo": "JAPÃO",
        "texto": (
            "O Japão vai muito além das grandes cidades. O país possui "
            "montanhas, florestas, lagos e cachoeiras, com paisagens que "
            "mudam bastante entre as diferentes estações do ano."
        )
    },

    "Peru": {
        "buscas": [
            "Peru Andes mountains",
            "Peru mountain lake",
            "Peru waterfall",
            "Peru scenic landscape"
        ],
        "titulo": "PERU",
        "texto": (
            "A Cordilheira dos Andes atravessa o Peru e cria paisagens "
            "de grande altitude. Montanhas, vales e lagos aparecem em "
            "cenários que mudam rapidamente conforme a região."
        )
    },

    "Chile": {
        "buscas": [
            "Chile Patagonia landscape",
            "Torres del Paine",
            "Chile mountain lake",
            "Chile Patagonia waterfall"
        ],
        "titulo": "CHILE",
        "texto": (
            "A Patagônia chilena é conhecida por suas montanhas, lagos, "
            "geleiras e grandes áreas selvagens. Torres del Paine é um dos "
            "cenários mais conhecidos dessa região."
        )
    },

    "Argentina": {
        "buscas": [
            "Argentina Patagonia landscape",
            "Argentina mountain lake",
            "Argentina waterfall",
            "Argentina scenic nature"
        ],
        "titulo": "ARGENTINA",
        "texto": (
            "A Argentina possui paisagens muito diferentes entre si. "
            "Na Patagônia, montanhas, lagos e geleiras formam alguns dos "
            "cenários naturais mais impressionantes do sul do continente."
        )
    },

    "Brasil": {
        "buscas": [
            "Brazil waterfall landscape",
            "Brazil mountains nature",
            "Brazil lake landscape",
            "Brazil scenic nature"
        ],
        "titulo": "BRASIL",
        "texto": (
            "O Brasil possui uma das maiores diversidades naturais do planeta. "
            "Florestas, rios, cachoeiras, montanhas e praias aparecem em "
            "diferentes regiões do país."
        )
    }
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
    margin-bottom: 5px;
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
    background: white;
    color: #111;
    font-weight: bold;
    cursor: pointer;
}

.info {
    background: #1d1d1d;
    padding: 15px;
    border-radius: 10px;
    margin-bottom: 20px;
    color: #bbb;
    line-height: 1.6;
}

</style>

</head>

<body>

<div class="container">

<h1>🌎 Mundo Afora</h1>

<div class="subtitle">
Paisagens incríveis, histórias e curiosidades
</div>

<div class="info">
🎥 Vídeo vertical<br>
⏱️ Aproximadamente 60 segundos<br>
🎙️ Narração masculina em português<br>
📝 Legendas automáticas<br>
📱 1080 × 1920<br>
🚫 Sem música
</div>

<form method="POST" action="/gerar">

<label>Escolha o destino</label>

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
# UTILIDADES
# ============================================================

def remover_arquivo(path):

    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception as e:
        print("[ERRO REMOVENDO]", e)


def rodar_ffmpeg(comando):

    print("=" * 60)
    print("[FFMPEG]")
    print(" ".join(comando))
    print("=" * 60)

    result = subprocess.run(
        comando,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:

        print("[FFMPEG RETURN CODE]", result.returncode)
        print("[FFMPEG ERRO]")
        print(result.stderr)

        raise RuntimeError(
            "FFmpeg falhou."
        )

    return result


# ============================================================
# PEXELS
# ============================================================

def buscar_video(query):

    if not PEXELS_API_KEY:
        raise RuntimeError(
            "PEXELS_API_KEY não configurada."
        )

    url = "https://api.pexels.com/videos/search"

    headers = {
        "Authorization": PEXELS_API_KEY
    }

    params = {
        "query": query,
        "per_page": 20
    }

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

        arquivos = video.get(
            "video_files",
            []
        )

        candidatos = []

        for arquivo in arquivos:

            link = arquivo.get("link")

            if not link:
                continue

            largura = arquivo.get(
                "width"
            ) or 0

            altura = arquivo.get(
                "height"
            ) or 0

            candidatos.append(
                (
                    largura * altura,
                    largura,
                    altura,
                    link
                )
            )

        if candidatos:

            candidatos.sort(
                reverse=True
            )

            _, largura, altura, link = candidatos[0]

            print(
                "[PEXELS OK]",
                query,
                largura,
                "x",
                altura
            )

            return link

    return None


# ============================================================
# DOWNLOAD
# ============================================================

def baixar_video(url, destino):

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    with requests.get(
        url,
        headers=headers,
        stream=True,
        timeout=90
    ) as response:

        response.raise_for_status()

        with open(
            destino,
            "wb"
        ) as arquivo:

            for bloco in response.iter_content(
                chunk_size=1024 * 1024
            ):

                if bloco:
                    arquivo.write(bloco)

    tamanho = os.path.getsize(
        destino
    )

    print(
        "[DOWNLOAD OK]",
        round(
            tamanho / 1024 / 1024,
            2
        ),
        "MB"
    )


# ============================================================
# PROCESSAR CLIPE
# ============================================================

def processar_clipe(
    entrada,
    saida
):

    filtro = (
        f"scale={PROCESS_WIDTH}:"
        f"{PROCESS_HEIGHT}:"
        "force_original_aspect_ratio=increase,"
        f"crop={PROCESS_WIDTH}:"
        f"{PROCESS_HEIGHT},"
        f"fps={FPS},"
        "format=yuv420p"
    )

    comando = [
        FFMPEG,

        "-hide_banner",
        "-loglevel", "error",
        "-y",

        "-i", entrada,

        "-t",
        str(CLIP_DURATION),

        "-vf",
        filtro,

        "-an",

        "-c:v",
        "libx264",

        "-preset",
        "ultrafast",

        "-crf",
        "30",

        "-pix_fmt",
        "yuv420p",

        "-r",
        str(FPS),

        saida
    ]

    rodar_ffmpeg(
        comando
    )

    if not os.path.exists(
        saida
    ):
        raise RuntimeError(
            "Clipe não foi criado."
        )


# ============================================================
# CONCATENAR
# ============================================================

def concatenar_clipes(
    clipes,
    saida
):

    lista = os.path.join(
        TEMP_DIR,
        "lista_" +
        uuid.uuid4().hex +
        ".txt"
    )

    try:

        with open(
            lista,
            "w",
            encoding="utf-8"
        ) as arquivo:

            for clipe in clipes:

                caminho = os.path.abspath(
                    clipe
                )

                caminho = caminho.replace(
                    "\\",
                    "/"
                )

                arquivo.write(
                    "file '" +
                    caminho +
                    "'\n"
                )

        comando = [
            FFMPEG,

            "-hide_banner",
            "-loglevel", "error",
            "-y",

            "-f",
            "concat",

            "-safe",
            "0",

            "-i",
            lista,

            "-an",

            "-c",
            "copy",

            saida
        ]

        rodar_ffmpeg(
            comando
        )

    finally:

        remover_arquivo(
            lista
        )


# ============================================================
# ROTEIRO
# ============================================================

def criar_roteiro(local):

    dados = LOCAIS[local]

    titulo = dados["titulo"]
    texto = dados["texto"]

    roteiro = (
        f"Você já imaginou conhecer este lugar? "
        f"Hoje o Mundo Afora te leva para {titulo}. "
        f"{texto} "
        f"E o mais impressionante é que cada paisagem "
        f"parece revelar um cenário diferente. "
        f"Se você pudesse viajar para qualquer lugar do mundo, "
        f"qual destino escolheria?"
    )

    return roteiro


# ============================================================
# QUEBRAR TEXTO EM LEGENDAS
# ============================================================

def quebrar_legendas(texto):

    palavras = texto.split()

    grupos = []

    atual = []

    for palavra in palavras:

        atual.append(palavra)

        if (
            len(atual) >= 7
            or palavra.endswith(".")
            or palavra.endswith("?")
        ):

            grupos.append(
                " ".join(atual)
            )

            atual = []

    if atual:

        grupos.append(
            " ".join(atual)
        )

    return grupos


# ============================================================
# CRIAR SRT
# ============================================================

def tempo_srt(segundos):

    horas = int(
        segundos // 3600
    )

    minutos = int(
        (segundos % 3600) // 60
    )

    seg = int(
        segundos % 60
    )

    milissegundos = int(
        (segundos -
         int(segundos)) * 1000
    )

    return (
        f"{horas:02d}:"
        f"{minutos:02d}:"
        f"{seg:02d},"
        f"{milissegundos:03d}"
    )


def criar_srt(
    roteiro,
    caminho
):

    partes = quebrar_legendas(
        roteiro
    )

    total_palavras = sum(
        len(x.split())
        for x in partes
    )

    # Aproximação de duração
    # baseada na quantidade de palavras.
    tempo_total = 55.0

    atual = 0.0

    with open(
        caminho,
        "w",
        encoding="utf-8"
    ) as arquivo:

        for numero, parte in enumerate(
            partes,
            start=1
        ):

            qtd = len(
                parte.split()
            )

            duracao = (
                qtd /
                total_palavras
            ) * tempo_total

            inicio = atual

            fim = atual + duracao

            arquivo.write(
                f"{numero}\n"
            )

            arquivo.write(
                f"{tempo_srt(inicio)} --> "
                f"{tempo_srt(fim)}\n"
            )

            arquivo.write(
                parte +
                "\n\n"
            )

            atual = fim


# ============================================================
# NARRAÇÃO EDGE TTS
# ============================================================

async def gerar_audio_async(
    texto,
    saida
):

    comunicacao = edge_tts.Communicate(
        texto,
        VOICE,
        rate=VOICE_RATE,
        volume="+0%",
        pitch="+0Hz"
    )

    await comunicacao.save(
        saida
    )


def gerar_audio(
    texto,
    saida
):

    asyncio.run(
        gerar_audio_async(
            texto,
            saida
        )
    )

    if not os.path.exists(
        saida
    ):
        raise RuntimeError(
            "Narração não foi criada."
        )


# ============================================================
# FINALIZAR VÍDEO
# ============================================================

def finalizar_video(
    video,
    audio,
    srt,
    saida
):

    # Converte caminho para formato
    # aceito pelo filtro subtitles.
    srt_abs = os.path.abspath(
        srt
    )

    srt_abs = srt_abs.replace(
        "\\",
        "/"
    )

    # Escapa caracteres especiais
    srt_filter = (
        srt_abs
        .replace(":", "\\:")
        .replace("'", "\\'")
        .replace("[", "\\[")
        .replace("]", "\\]")
    )

    filtro = (
        f"scale={WIDTH}:{HEIGHT}:"
        "force_original_aspect_ratio=increase,"
        f"crop={WIDTH}:{HEIGHT},"
        "format=yuv420p,"
        f"subtitles='{srt_filter}':"
        "force_style='"
        "FontName=Arial,"
        "FontSize=22,"
        "Bold=1,"
        "Alignment=2,"
        "MarginV=110,"
        "Outline=2,"
        "Shadow=1"
        "'"
    )

    comando = [
        FFMPEG,

        "-hide_banner",
        "-loglevel", "error",
        "-y",

        "-i",
        video,

        "-i",
        audio,

        "-vf",
        filtro,

        "-map",
        "0:v:0",

        "-map",
        "1:a:0",

        "-c:v",
        "libx264",

        "-preset",
        "ultrafast",

        "-crf",
        "31",

        "-pix_fmt",
        "yuv420p",

        "-r",
        str(FPS),

        "-c:a",
        "aac",

        "-b:a",
        "128k",

        "-t",
        str(FINAL_DURATION),

        "-movflags",
        "+faststart",

        saida
    ]

    rodar_ffmpeg(
        comando
    )

    if not os.path.exists(
        saida
    ):
        raise RuntimeError(
            "Vídeo final não foi criado."
        )


# ============================================================
# GERAR
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

    clipes = []

    try:

        dados = LOCAIS[local]

        buscas = dados["buscas"]

        # ====================================================
        # 1. BAIXAR E PROCESSAR 4 CENAS
        # ====================================================

        for i in range(
            CLIP_COUNT
        ):

            query = buscas[
                i % len(buscas)
            ]

            print(
                "[BUSCANDO]",
                query
            )

            url = buscar_video(
                query
            )

            if not url:

                continue

            original = os.path.join(
                trabalho,
                f"original_{i}.mp4"
            )

            processado = os.path.join(
                trabalho,
                f"clip_{i}.mp4"
            )

            baixar_video(
                url,
                original
            )

            processar_clipe(
                original,
                processado
            )

            clipes.append(
                processado
            )

            remover_arquivo(
                original
            )

        if len(clipes) < CLIP_COUNT:

            raise RuntimeError(
                "Não foi possível encontrar "
                "4 vídeos válidos."
            )

        # ====================================================
        # 2. JUNTAR CENAS
        # ====================================================

        video_junto = os.path.join(
            trabalho,
            "video_junto.mp4"
        )

        concatenar_clipes(
            clipes,
            video_junto
        )

        # ====================================================
        # 3. ROTEIRO
        # ====================================================

        roteiro = criar_roteiro(
            local
        )

        print("=" * 60)
        print("[ROTEIRO]")
        print(roteiro)
        print("=" * 60)

        # ====================================================
        # 4. ÁUDIO
        # ====================================================

        audio = os.path.join(
            trabalho,
            "narracao.mp3"
        )

        gerar_audio(
            roteiro,
            audio
        )

        # ====================================================
        # 5. LEGENDAS
        # ====================================================

        srt = os.path.join(
            trabalho,
            "legendas.srt"
        )

        criar_srt(
            roteiro,
            srt
        )

        # ====================================================
        # 6. VÍDEO FINAL
        # ====================================================

        nome = (
            "mundo_afora_" +
            uuid.uuid4().hex[:10] +
            ".mp4"
        )

        saida = os.path.join(
            OUTPUT_DIR,
            nome
        )

        finalizar_video(
            video_junto,
            audio,
            srt,
            saida
        )

        print("=" * 60)
        print("[VIDEO PRONTO]")
        print(saida)
        print("=" * 60)

        return saida

    finally:

        shutil.rmtree(
            trabalho,
            ignore_errors=True
        )


# ============================================================
# HOME
# ============================================================

@app.route("/")
def index():

    return render_template_string(
        HTML,
        locais=LOCAIS.keys()
    )


# ============================================================
# GERAR
# ============================================================

@app.route(
    "/gerar",
    methods=["POST"]
)
def gerar():

    local = request.form.get(
        "local",
        ""
    ).strip()

    try:

        arquivo = gerar_video(
            local
        )

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

        .box {{
            max-width:600px;
            margin:auto;
            background:#222;
            padding:25px;
            border-radius:15px;
        }}

        a {{
            color:white;
            display:block;
            margin-top:20px;
        }}

        </style>

        </head>

        <body>

        <div class="box">

        <h2>❌ Erro ao gerar vídeo</h2>

        <p>
        O processamento encontrou um problema.
        </p>

        <p>
        Confira os logs do Railway.
        </p>

        <a href="/">
        ← Voltar
        </a>

        </div>

        </body>

        </html>
        """, 500


# ============================================================
# HEALTH
# ============================================================

@app.route("/health")
def health():

    return {
        "status": "ok",
        "ffmpeg": FFMPEG,
        "voice": VOICE,
        "rate": VOICE_RATE,
        "resolution": "1080x1920",
        "duration": 60
    }


# ============================================================
# START LOCAL
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=PORT
    )