import os
import re
import uuid
import random
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import imageio_ffmpeg

from flask import Flask, request, render_template_string, send_file
from PIL import Image, ImageDraw, ImageFont


# ============================================================
# CONFIGURAÇÕES
# ============================================================

app = Flask(__name__)

PORT = int(os.getenv("PORT", "8080"))

WIDTH = 1080
HEIGHT = 1920
FPS = 24

DURATION = 60

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

VIDEO_DIR = "videos"
TEMP_DIR = "temp"
OUTPUT_DIR = "outputs"

os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# PAÍSES
# ============================================================

PAISES = {
    "Brasil": [
        "Brazil mountains lake",
        "Brazil sea cliffs",
        "Brazil mountain cabin",
        "Brazil mountain valley",
        "Brazil scenic mountains",
        "Brazil mountain lake",
        "Brazil lake mountains",
        "Brazil ocean cliffs"
    ],

    "Ilhas Faroé": [
        "Faroe Islands mountains ocean",
        "Faroe Islands cliffs",
        "Faroe Islands lake mountains",
        "Faroe Islands green valley",
        "Faroe Islands waterfall mountains",
        "Faroe Islands scenic landscape"
    ],

    "Suíça": [
        "Switzerland mountains lake",
        "Swiss Alps lake",
        "Switzerland mountain cabin",
        "Swiss mountain valley",
        "Swiss Alps chalet",
        "Switzerland green valley",
        "Swiss lake mountains"
    ],

    "Noruega": [
        "Norway fjord mountains",
        "Norway mountain lake",
        "Norway cliffs ocean",
        "Norway green valley",
        "Norway mountain cabin",
        "Norwegian fjord landscape"
    ],

    "Islândia": [
        "Iceland mountains waterfall",
        "Iceland lake mountains",
        "Iceland cliffs ocean",
        "Iceland green valley",
        "Iceland scenic landscape",
        "Iceland waterfall mountains"
    ],

    "Canadá": [
        "Canada Rocky Mountains lake",
        "Canada mountain lake",
        "Canada mountain cabin",
        "Canada green valley",
        "Canadian Rockies landscape",
        "Canada turquoise lake mountains"
    ],

    "Nova Zelândia": [
        "New Zealand mountains lake",
        "New Zealand mountain valley",
        "New Zealand mountain cabin",
        "New Zealand green valley",
        "New Zealand lake mountains",
        "New Zealand scenic landscape"
    ],

    "Áustria": [
        "Austria Alps lake",
        "Austria mountain cabin",
        "Austria mountain valley",
        "Austrian Alps landscape",
        "Austria green valley",
        "Austria lake mountains"
    ],

    "Eslovênia": [
        "Slovenia mountains lake",
        "Slovenia Lake Bled mountains",
        "Slovenia mountain valley",
        "Slovenia green valley",
        "Slovenia mountain waterfall"
    ],

    "França": [
        "French Alps lake",
        "France mountain valley",
        "French Alps cabin",
        "France mountain lake",
        "French Alps landscape"
    ],

    "Itália": [
        "Italian Alps lake",
        "Dolomites lake mountains",
        "Dolomites mountain cabin",
        "Italy green mountain valley",
        "Dolomites landscape"
    ],

    "Estados Unidos": [
        "USA mountain lake",
        "Rocky Mountains lake",
        "USA mountain cabin",
        "USA mountain valley",
        "Yosemite mountains lake",
        "Alaska mountains lake"
    ],

    "Japão": [
        "Japan mountain lake",
        "Japan mountain valley",
        "Japan scenic mountains",
        "Japan lake mountains",
        "Japan green valley"
    ],

    "Peru": [
        "Peru Andes mountains lake",
        "Peru mountain valley",
        "Peru green mountains",
        "Peru scenic mountain lake"
    ],

    "Chile": [
        "Chile Patagonia mountains lake",
        "Chile mountain lake",
        "Patagonia mountains",
        "Chile green valley",
        "Chile scenic landscape"
    ],

    "Argentina": [
        "Argentina Patagonia mountains lake",
        "Argentina mountain lake",
        "Patagonia mountain valley",
        "Argentina green valley",
        "Argentina scenic mountains"
    ]
}


# ============================================================
# TERMOS QUE NÃO QUEREMOS
# ============================================================

PALAVRAS_RUINS = [
    "person",
    "people",
    "man",
    "woman",
    "men",
    "women",
    "hiker",
    "hiking",
    "trekking",
    "trail",
    "trek",
    "walking",
    "walk",
    "runner",
    "running",
    "road",
    "street",
    "highway",
    "car",
    "vehicle",
    "city",
    "urban",
    "building",
    "house",
    "hotel",
    "boat",
    "ship",
    "yacht",
    "pool",
    "swimming",
    "event",
    "festival",
    "concert",
    "party",
    "crowd",
    "airport"
]


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
    padding: 0;

    min-height: 100vh;

    background:
        linear-gradient(
            135deg,
            #071b16,
            #102d25,
            #06110e
        );

    color: white;

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    display: flex;
    justify-content: center;
    align-items: center;
}

.container {

    width: 92%;
    max-width: 500px;

    background: rgba(255,255,255,0.07);

    border: 1px solid rgba(255,255,255,0.12);

    border-radius: 22px;

    padding: 30px;

    backdrop-filter: blur(12px);

    box-shadow:
        0 20px 60px rgba(0,0,0,0.35);
}

h1 {

    text-align: center;

    margin-top: 0;
    margin-bottom: 8px;

    font-size: 30px;
}

.subtitle {

    text-align: center;

    color: #b9c8c2;

    margin-bottom: 30px;

    font-size: 15px;
}

label {

    display: block;

    margin-bottom: 8px;

    color: #dce8e3;

    font-weight: bold;
}

select {

    width: 100%;

    padding: 14px;

    border-radius: 12px;

    border: 1px solid rgba(255,255,255,0.15);

    background: #142c25;

    color: white;

    font-size: 16px;

    margin-bottom: 20px;

    outline: none;
}

button {

    width: 100%;

    padding: 15px;

    border: none;

    border-radius: 13px;

    background: #ffffff;

    color: #10231d;

    font-size: 17px;

    font-weight: bold;

    cursor: pointer;

    transition: 0.2s;
}

button:hover {

    transform: translateY(-1px);

    opacity: 0.92;
}

.info {

    margin-top: 22px;

    text-align: center;

    color: #9eb3aa;

    font-size: 13px;

    line-height: 1.5;
}

</style>

</head>

<body>

<div class="container">

<h1>🌎 Mundo Afora</h1>

<div class="subtitle">
Paisagens bonitas para vídeos verticais
</div>

<form method="POST">

<label>Escolha o destino</label>

<select name="pais" required>

{% for pais in paises %}

<option value="{{ pais }}">
{{ pais }}
</option>

{% endfor %}

</select>

<button type="submit">
🎬 Gerar vídeo
</button>

</form>

<div class="info">

Vídeo vertical 1080×1920<br>
60 segundos • 24 FPS<br>
Sem música • Sem narração

</div>

</div>

</body>

</html>
"""


# ============================================================
# UTILIDADES
# ============================================================

def limpar_nome(nome):

    nome = re.sub(
        r"[^a-zA-Z0-9_-]",
        "_",
        nome
    )

    return nome


def executar(comando):

    return subprocess.run(
        comando,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )


# ============================================================
# CRIAR MARCA D'ÁGUA PNG
# ============================================================

def criar_marca_dagua():

    caminho = os.path.join(
        TEMP_DIR,
        "watermark.png"
    )

    # --------------------------------------------------------
    # Tenta encontrar uma fonte disponível
    # --------------------------------------------------------

    fontes = [

        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",

        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",

        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",

        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
    ]

    fonte = None

    for caminho_fonte in fontes:

        if os.path.exists(caminho_fonte):

            fonte = caminho_fonte

            break

    # --------------------------------------------------------
    # Tamanho do texto
    # --------------------------------------------------------

    tamanho = 38

    if fonte:

        font = ImageFont.truetype(
            fonte,
            tamanho
        )

    else:

        font = ImageFont.load_default()

    texto = "mundo.afora0"

    # --------------------------------------------------------
    # Calcula tamanho
    # --------------------------------------------------------

    dummy = Image.new(
        "RGBA",
        (10, 10),
        (0, 0, 0, 0)
    )

    draw = ImageDraw.Draw(dummy)

    bbox = draw.textbbox(
        (0, 0),
        texto,
        font=font
    )

    largura = bbox[2] - bbox[0]
    altura = bbox[3] - bbox[1]

    # Pequena margem
    margem = 12

    img_largura = largura + margem * 2
    img_altura = altura + margem * 2

    # --------------------------------------------------------
    # PNG transparente
    # --------------------------------------------------------

    img = Image.new(
        "RGBA",
        (
            img_largura,
            img_altura
        ),
        (0, 0, 0, 0)
    )

    draw = ImageDraw.Draw(img)

    # Sombra discreta
    draw.text(
        (
            margem + 2,
            margem + 2
        ),
        texto,
        font=font,
        fill=(0, 0, 0, 110)
    )

    # Texto branco
    draw.text(
        (
            margem,
            margem
        ),
        texto,
        font=font,
        fill=(255, 255, 255, 185)
    )

    img.save(
        caminho,
        "PNG"
    )

    return caminho


# ============================================================
# BUSCAR VÍDEOS NO PEXELS
# ============================================================

def buscar_pexels(query):

    if not PEXELS_API_KEY:

        print("❌ PEXELS_API_KEY não configurada")

        return []

    url = "https://api.pexels.com/videos/search"

    headers = {
        "Authorization": PEXELS_API_KEY
    }

    params = {
        "query": query,
        "orientation": "portrait",
        "size": "large",
        "per_page": 80
    }

    try:

        resposta = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=30
        )

        resposta.raise_for_status()

        dados = resposta.json()

        videos = dados.get(
            "videos",
            []
        )

        print(
            f"[PEXELS] {query}"
        )

        print(
            f"[PEXELS] {len(videos)} resultados"
        )

        return videos

    except Exception as e:

        print(
            f"[ERRO PEXELS] {query}: {e}"
        )

        return []


# ============================================================
# ESCOLHER ARQUIVO DO PEXELS
# ============================================================

def escolher_arquivo_video(video):

    arquivos = video.get(
        "video_files",
        []
    )

    candidatos = []

    for arquivo in arquivos:

        link = arquivo.get(
            "link"
        )

        largura = arquivo.get(
            "width"
        ) or 0

        altura = arquivo.get(
            "height"
        ) or 0

        tipo = arquivo.get(
            "file_type",
            ""
        )

        if not link:
            continue

        if tipo and "mp4" not in tipo.lower():
            continue

        if largura <= 0 or altura <= 0:
            continue

        # Vertical
        proporcao = altura / largura

        if proporcao < 1.35:
            continue

        # Prioridade de resolução
        if largura == 1080 and altura == 1920:

            prioridade = 1

        elif largura == 1440 and altura == 2560:

            prioridade = 2

        elif largura == 720 and altura == 1280:

            prioridade = 3

        elif largura == 2160 and altura == 3840:

            prioridade = 4

        else:

            prioridade = 5

        candidatos.append(
            (
                prioridade,
                largura * altura,
                link,
                largura,
                altura
            )
        )

    if not candidatos:

        return None

    candidatos.sort(
        key=lambda x: (
            x[0],
            x[1]
        )
    )

    escolhido = candidatos[0]

    return (
        escolhido[2],
        escolhido[3],
        escolhido[4]
    )


# ============================================================
# PONTUAR VÍDEO
# ============================================================

def pontuar_video(video):

    texto = ""

    texto += str(
        video.get(
            "url",
            ""
        )
    )

    texto += " "

    texto += str(
        video.get(
            "image",
            ""
        )
    )

    texto += " "

    texto += str(
        video.get(
            "user",
            {}
        )
    )

    texto = texto.lower()

    pontos = random.randint(
        0,
        20
    )

    for palavra in PALAVRAS_RUINS:

        if palavra.lower() in texto:

            pontos -= 100

    return pontos


# ============================================================
# SELECIONAR VÍDEOS
# ============================================================

def selecionar_videos(pais):

    consultas = PAISES.get(
        pais,
        []
    )

    todos = {}

    for consulta in consultas:

        resultados = buscar_pexels(
            consulta
        )

        for video in resultados:

            video_id = video.get(
                "id"
            )

            if not video_id:
                continue

            arquivo = escolher_arquivo_video(
                video
            )

            if not arquivo:
                continue

            link, largura, altura = arquivo

            video["_arquivo"] = link
            video["_largura"] = largura
            video["_altura"] = altura

            todos[video_id] = video

    print(
        f"[TOTAL] {len(todos)} vídeos únicos"
    )

    lista = list(
        todos.values()
    )

    lista.sort(
        key=pontuar_video,
        reverse=True
    )

    selecionados = lista[:15]

    print(
        f"[SELECIONADOS] {len(selecionados)}"
    )

    return selecionados


# ============================================================
# DOWNLOAD
# ============================================================

def baixar_video(item):

    indice, video = item

    link = video.get(
        "_arquivo"
    )

    largura = video.get(
        "_largura",
        0
    )

    altura = video.get(
        "_altura",
        0
    )

    caminho = os.path.join(
        VIDEO_DIR,
        f"{uuid.uuid4().hex}.mp4"
    )

    print(
        f"[DOWNLOAD] {indice} "
        f"{largura}x{altura}"
    )

    try:

        resposta = requests.get(
            link,
            stream=True,
            timeout=60
        )

        resposta.raise_for_status()

        with open(
            caminho,
            "wb"
        ) as arquivo:

            for bloco in resposta.iter_content(
                chunk_size=1024 * 1024
            ):

                if bloco:

                    arquivo.write(
                        bloco
                    )

        tamanho_mb = (
            os.path.getsize(caminho)
            / 1024
            / 1024
        )

        print(
            f"[OK DOWNLOAD] {indice} "
            f"{tamanho_mb:.1f} MB"
        )

        return caminho

    except Exception as e:

        print(
            f"[ERRO DOWNLOAD] {indice}: {e}"
        )

        try:

            if os.path.exists(caminho):

                os.remove(caminho)

        except:

            pass

        return None


# ============================================================
# VERIFICAR VÍDEO
# ============================================================

def verificar_video(caminho):

    comando = [

        FFMPEG,

        "-v",
        "error",

        "-i",
        caminho,

        "-f",
        "null",

        "-"
    ]

    resultado = executar(
        comando
    )

    if resultado.returncode != 0:

        print(
            "[VIDEO INVALIDO]"
        )

        print(
            resultado.stderr[-5000:]
        )

        return False

    return True


# ============================================================
# PROCESSAR CLIPE
# ============================================================

def processar_clipe(
    input_path,
    output_path,
    duracao=8
):

    filtro = (
        "scale=1080:1920,"
        "fps=24,"
        "setsar=1"
    )

    comando = [

        FFMPEG,

        "-y",

        "-hide_banner",

        "-loglevel",
        "error",

        "-i",
        input_path,

        "-t",
        str(duracao),

        "-vf",
        filtro,

        "-an",

        "-c:v",
        "libx264",

        "-preset",
        "ultrafast",

        "-crf",
        "28",

        "-pix_fmt",
        "yuv420p",

        "-r",
        "24",

        "-movflags",
        "+faststart",

        output_path
    ]

    resultado = executar(
        comando
    )

    if resultado.returncode != 0:

        print(
            "===================================="
        )

        print(
            "[ERRO PROCESSANDO CLIPE]"
        )

        print(
            f"Return code: "
            f"{resultado.returncode}"
        )

        print(
            resultado.stderr[-10000:]
        )

        print(
            "===================================="
        )

        return False

    return True


# ============================================================
# JUNTAR CLIPES
# ============================================================

def juntar_clipes(
    clipes,
    output_path
):

    lista_path = os.path.join(
        TEMP_DIR,
        f"lista_{uuid.uuid4().hex}.txt"
    )

    try:

        with open(
            lista_path,
            "w",
            encoding="utf-8"
        ) as arquivo:

            for clipe in clipes:

                caminho_absoluto = os.path.abspath(
                    clipe
                )

                caminho_absoluto = (
                    caminho_absoluto
                    .replace(
                        "'",
                        "'\\''"
                    )
                )

                arquivo.write(
                    f"file '{caminho_absoluto}'\n"
                )

        comando = [

            FFMPEG,

            "-y",

            "-hide_banner",

            "-loglevel",
            "error",

            "-f",
            "concat",

            "-safe",
            "0",

            "-i",
            lista_path,

            "-c",
            "copy",

            "-movflags",
            "+faststart",

            output_path
        ]

        resultado = executar(
            comando
        )

        if resultado.returncode != 0:

            print(
                "[ERRO AO JUNTAR]"
            )

            print(
                resultado.stderr[-10000:]
            )

            return False

        return True

    finally:

        if os.path.exists(
            lista_path
        ):

            os.remove(
                lista_path
            )


# ============================================================
# APLICAR MARCA D'ÁGUA
# ============================================================

def aplicar_marca_dagua(
    input_path,
    output_path
):

    print(
        "[MARCA D'ÁGUA] Criando PNG..."
    )

    watermark = criar_marca_dagua()

    # --------------------------------------------------------
    # POSIÇÃO
    #
    # vídeo: 1080 x 1920
    #
    # x = centralizado
    #
    # y = aproximadamente 58%
    # um pouco abaixo do meio
    # --------------------------------------------------------

    x = "(main_w-overlay_w)/2"

    y = "main_h*0.58"

    filtro = (
        f"overlay={x}:{y}"
    )

    comando = [

        FFMPEG,

        "-y",

        "-hide_banner",

        "-loglevel",
        "error",

        "-i",
        input_path,

        "-i",
        watermark,

        "-filter_complex",
        filtro,

        "-map",
        "0:v:0",

        "-map",
        "0:a?",
        
        "-c:v",
        "libx264",

        "-preset",
        "ultrafast",

        "-crf",
        "28",

        "-pix_fmt",
        "yuv420p",

        "-c:a",
        "copy",

        "-movflags",
        "+faststart",

        output_path
    ]

    resultado = executar(
        comando
    )

    if resultado.returncode != 0:

        print(
            "===================================="
        )

        print(
            "[ERRO AO APLICAR MARCA D'ÁGUA]"
        )

        print(
            f"Return code: "
            f"{resultado.returncode}"
        )

        print(
            resultado.stderr[-10000:]
        )

        print(
            "===================================="
        )

        return False

    return True


# ============================================================
# LIMPAR ARQUIVOS
# ============================================================

def limpar_temporarios():

    for pasta in [
        VIDEO_DIR,
        TEMP_DIR
    ]:

        if not os.path.exists(pasta):
            continue

        for nome in os.listdir(
            pasta
        ):

            caminho = os.path.join(
                pasta,
                nome
            )

            try:

                if os.path.isfile(
                    caminho
                ):

                    os.remove(
                        caminho
                    )

            except Exception as e:

                print(
                    f"[LIMPEZA] {e}"
                )


# ============================================================
# GERAR VÍDEO
# ============================================================

def gerar_video(pais):

    limpar_temporarios()

    print("")
    print("====================================")
    print("🌎 MUNDO AFORA")
    print("====================================")

    print(
        f"Destino: {pais}"
    )

    # --------------------------------------------------------
    # Buscar
    # --------------------------------------------------------

    videos = selecionar_videos(
        pais
    )

    if not videos:

        raise Exception(
            "Nenhum vídeo encontrado."
        )

    # --------------------------------------------------------
    # Download
    # --------------------------------------------------------

    baixados = []

    with ThreadPoolExecutor(
        max_workers=2
    ) as executor:

        tarefas = [

            executor.submit(
                baixar_video,
                (indice, video)
            )

            for indice, video
            in enumerate(videos)
        ]

        for tarefa in as_completed(
            tarefas
        ):

            resultado = tarefa.result()

            if resultado:

                baixados.append(
                    resultado
                )

    print(
        f"[BAIXADOS] {len(baixados)}"
    )

    if not baixados:

        raise Exception(
            "Nenhum vídeo pôde ser baixado."
        )

    # --------------------------------------------------------
    # Processar
    # --------------------------------------------------------

    random.shuffle(
        baixados
    )

    clipes_processados = []

    for indice, video in enumerate(
        baixados
    ):

        print(
            f"[PROCESSANDO] Clipe {indice