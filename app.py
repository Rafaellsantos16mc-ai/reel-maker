import os
import random
import uuid
import requests
import subprocess
import html

from concurrent.futures import ThreadPoolExecutor, as_completed

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

# Marca d'água
WATERMARK = "mundo.afora0"

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

VIDEO_DIR = "videos"
TEMP_DIR = "temp"
OUTPUT_DIR = "outputs"

os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


# ============================================================
# PAÍSES / DESTINOS
# ============================================================

PAISES = {

    "🇧🇷 Brasil": [
        "Brazil ocean cliffs",
        "Brazil dramatic sea cliffs",
        "Brazil beautiful lake mountains",
        "Brazil green valley cabin",
        "Brazil mountain lake",
        "Brazil green valley chalet",
        "Brazil rocky coastline",
        "Brazil mountain valley landscape"
    ],

    "🇺🇸 Estados Unidos": [
        "USA ocean cliffs",
        "USA dramatic cliffs",
        "USA mountain lake",
        "USA green valley cabin",
        "USA alpine lake",
        "USA mountain cabin",
        "USA rocky coastline",
        "USA green valley"
    ],

    "🇨🇦 Canadá": [
        "Canada mountain lake",
        "Canada turquoise lake mountains",
        "Canada green valley cabin",
        "Canada mountain cabin lake",
        "Canada rocky mountains lake",
        "Canada ocean cliffs",
        "Canada dramatic cliffs",
        "Canada green valley"
    ],

    "🇲🇽 México": [
        "Mexico ocean cliffs",
        "Mexico dramatic sea cliffs",
        "Mexico mountain lake",
        "Mexico green valley",
        "Mexico rocky coastline",
        "Mexico beautiful valley"
    ],

    "🇦🇷 Argentina": [
        "Argentina Patagonia lake mountains",
        "Argentina green valley cabin",
        "Argentina mountain lake",
        "Argentina dramatic cliffs",
        "Patagonia lake valley",
        "Patagonia mountain cabin",
        "Argentina rocky landscape"
    ],

    "🇨🇱 Chile": [
        "Chile Patagonia lake mountains",
        "Chile mountain lake",
        "Chile green valley cabin",
        "Chile dramatic cliffs",
        "Chile fjord cliffs",
        "Chile mountain valley",
        "Chile turquoise lake mountains"
    ],

    "🇵🇪 Peru": [
        "Peru mountain lake",
        "Peru green valley mountains",
        "Peru dramatic cliffs",
        "Peru mountain valley",
        "Peru beautiful lake mountains",
        "Peru green valley landscape"
    ],

    "🇨🇴 Colômbia": [
        "Colombia mountain lake",
        "Colombia green valley",
        "Colombia mountain cabin",
        "Colombia dramatic cliffs",
        "Colombia beautiful valley",
        "Colombia lake mountains"
    ],

    "🇨🇷 Costa Rica": [
        "Costa Rica ocean cliffs",
        "Costa Rica green valley",
        "Costa Rica mountain lake",
        "Costa Rica dramatic coastline",
        "Costa Rica green mountains",
        "Costa Rica valley landscape"
    ],

    "🇮🇸 Islândia": [
        "Iceland ocean cliffs",
        "Iceland dramatic sea cliffs",
        "Iceland mountain lake",
        "Iceland green valley",
        "Iceland waterfall mountains",
        "Iceland fjord mountains",
        "Iceland dramatic coastline",
        "Iceland green valley cabin"
    ],

    "🇳🇴 Noruega": [
        "Norway fjord cliffs",
        "Norway dramatic sea cliffs",
        "Norway mountain lake",
        "Norway green valley cabin",
        "Norway fjord cabin",
        "Norway mountain valley",
        "Norway turquoise lake",
        "Norway dramatic mountains"
    ],

    "🇨🇭 Suíça": [
        "Swiss Alps lake cabin",
        "Switzerland mountain lake",
        "Swiss green valley chalet",
        "Switzerland valley cabin",
        "Swiss Alps dramatic cliffs",
        "Swiss mountain lake chalet",
        "Switzerland green valley",
        "Swiss Alps lake mountains"
    ],

    "🇫🇷 França": [
        "French Alps lake cabin",
        "France mountain lake",
        "French Alps green valley",
        "France mountain chalet",
        "French Alps dramatic cliffs",
        "France green valley cabin"
    ],

    "🇮🇹 Itália": [
        "Italian Alps lake cabin",
        "Italy mountain lake",
        "Dolomites lake cabin",
        "Dolomites green valley",
        "Italian mountain chalet",
        "Dolomites dramatic cliffs",
        "Italy green mountain valley"
    ],

    "🇵🇹 Portugal": [
        "Portugal ocean cliffs",
        "Portugal dramatic coastline",
        "Portugal mountain lake",
        "Portugal green valley",
        "Portugal rocky cliffs",
        "Portugal beautiful valley"
    ],

    "🇪🇸 Espanha": [
        "Spain ocean cliffs",
        "Spain dramatic sea cliffs",
        "Spain mountain lake",
        "Spain green valley",
        "Spain rocky coastline",
        "Spain mountain cabin"
    ],

    "🏴 Escócia": [
        "Scotland dramatic sea cliffs",
        "Scottish Highlands green valley",
        "Scotland mountain lake",
        "Scotland valley cabin",
        "Scotland rocky coastline",
        "Scottish Highlands lake",
        "Scotland dramatic mountains"
    ],

    "🇮🇪 Irlanda": [
        "Ireland dramatic sea cliffs",
        "Ireland green valley",
        "Ireland mountain lake",
        "Ireland rocky coastline",
        "Ireland green mountains",
        "Ireland valley cabin"
    ],

    "🇬🇧 Inglaterra": [
        "England dramatic cliffs",
        "England green valley",
        "England mountain lake",
        "England rocky coastline",
        "England green mountains"
    ],

    "🇩🇪 Alemanha": [
        "Germany mountain lake",
        "Germany green valley cabin",
        "German Alps lake",
        "Germany mountain chalet",
        "Germany dramatic cliffs",
        "Germany green valley"
    ],

    "🇦🇹 Áustria": [
        "Austria Alps lake cabin",
        "Austrian Alps mountain lake",
        "Austria green valley chalet",
        "Austria mountain cabin",
        "Austria dramatic cliffs",
        "Austria turquoise lake",
        "Austria green valley"
    ],

    "🇳🇿 Nova Zelândia": [
        "New Zealand fjord cliffs",
        "New Zealand mountain lake",
        "New Zealand green valley",
        "New Zealand mountain cabin",
        "New Zealand dramatic coastline",
        "New Zealand turquoise lake",
        "New Zealand green mountains"
    ],

    "🇦🇺 Austrália": [
        "Australia ocean cliffs",
        "Australia dramatic coastline",
        "Australia mountain lake",
        "Australia green valley",
        "Australia rocky cliffs",
        "Australia beautiful valley"
    ],

    "🇯🇵 Japão": [
        "Japan mountain lake cabin",
        "Japan green valley",
        "Japan mountain chalet",
        "Japan dramatic cliffs",
        "Japan lake mountains",
        "Japan green mountain valley"
    ],

    "🇨🇳 China": [
        "China dramatic cliffs",
        "China mountain lake",
        "China green valley",
        "China mountain cabin",
        "China rocky mountains",
        "China beautiful valley"
    ],

    "🇰🇷 Coreia do Sul": [
        "South Korea mountain lake",
        "South Korea green valley",
        "South Korea dramatic cliffs",
        "South Korea mountain cabin",
        "South Korea lake mountains"
    ],

    "🇮🇩 Indonésia": [
        "Indonesia ocean cliffs",
        "Indonesia dramatic coastline",
        "Indonesia mountain lake",
        "Indonesia green valley",
        "Indonesia volcanic lake",
        "Indonesia rocky cliffs"
    ],

    "🇹🇭 Tailândia": [
        "Thailand dramatic sea cliffs",
        "Thailand ocean cliffs",
        "Thailand mountain lake",
        "Thailand green valley",
        "Thailand limestone cliffs"
    ],

    "🇵🇭 Filipinas": [
        "Philippines dramatic sea cliffs",
        "Philippines turquoise lake",
        "Philippines ocean cliffs",
        "Philippines green valley",
        "Philippines limestone cliffs"
    ],

    "🇮🇳 Índia": [
        "India mountain lake",
        "India green valley",
        "India dramatic cliffs",
        "India mountain cabin",
        "India beautiful valley"
    ],

    "🇳🇵 Nepal": [
        "Nepal mountain lake",
        "Nepal green valley mountains",
        "Himalayas mountain lake",
        "Nepal mountain cabin",
        "Nepal dramatic cliffs",
        "Nepal green valley"
    ],

    "🇿🇦 África do Sul": [
        "South Africa ocean cliffs",
        "South Africa dramatic coastline",
        "South Africa mountain lake",
        "South Africa green valley",
        "South Africa rocky cliffs"
    ],

    "🇰🇪 Quênia": [
        "Kenya mountain lake",
        "Kenya green valley",
        "Kenya dramatic cliffs",
        "Kenya mountain landscape",
        "Kenya beautiful valley"
    ],

    "🇲🇦 Marrocos": [
        "Morocco dramatic cliffs",
        "Morocco mountain valley",
        "Morocco green valley",
        "Morocco mountain lake",
        "Morocco rocky mountains"
    ],

    "🇹🇿 Tanzânia": [
        "Tanzania mountain lake",
        "Tanzania green valley",
        "Tanzania dramatic cliffs",
        "Tanzania mountain landscape"
    ],

    "🇹🇷 Turquia": [
        "Turkey ocean cliffs",
        "Turkey dramatic coastline",
        "Turkey mountain lake",
        "Turkey green valley",
        "Turkey rocky cliffs"
    ],

    "🇬🇷 Grécia": [
        "Greece dramatic sea cliffs",
        "Greece ocean cliffs",
        "Greece mountain lake",
        "Greece green valley",
        "Greece rocky coastline"
    ],

    "🇭🇷 Croácia": [
        "Croatia dramatic sea cliffs",
        "Croatia turquoise lake",
        "Croatia mountain valley",
        "Croatia rocky coastline",
        "Croatia green valley"
    ],

    "🇸🇮 Eslovênia": [
        "Slovenia lake mountains",
        "Slovenia green valley cabin",
        "Slovenia mountain lake",
        "Slovenia alpine chalet",
        "Slovenia dramatic cliffs",
        "Slovenia green valley"
    ],

    "🇫🇮 Finlândia": [
        "Finland beautiful lake",
        "Finland lake cabin",
        "Finland green valley",
        "Finland forest lake",
        "Finland mountain lake"
    ],

    "🇸🇪 Suécia": [
        "Sweden mountain lake",
        "Sweden lake cabin",
        "Sweden green valley",
        "Sweden dramatic cliffs",
        "Sweden beautiful lake"
    ],

    "🇵🇱 Polônia": [
        "Poland mountain lake",
        "Poland green valley",
        "Poland mountain cabin",
        "Poland dramatic cliffs",
        "Poland lake mountains"
    ],

    "🇫🇴 Ilhas Faroé": [
        "Faroe Islands dramatic sea cliffs",
        "Faroe Islands ocean cliffs",
        "Faroe Islands green valley",
        "Faroe Islands waterfall cliffs",
        "Faroe Islands fjord mountains",
        "Faroe Islands green mountains",
        "Faroe Islands beautiful lake",
        "Faroe Islands valley cabin",
        "Faroe Islands dramatic coastline",
        "Faroe Islands rocky cliffs",
        "Faroe Islands ocean landscape",
        "Faroe Islands mountain valley"
    ]
}


# ============================================================
# PALAVRAS BOAS
# ============================================================

PALAVRAS_BOAS = [

    # MAR
    "ocean",
    "sea",
    "coast",
    "coastline",
    "coastal",
    "shore",
    "seaside",
    "sea cliffs",
    "ocean cliffs",
    "coastal cliffs",

    # PAREDÕES / ROCHAS
    "cliff",
    "cliffs",
    "cliffside",
    "rock",
    "rocks",
    "rocky",
    "rock formation",
    "dramatic cliffs",
    "dramatic rocks",

    # MONTANHAS
    "mountain",
    "mountains",
    "mountain range",
    "alps",
    "peak",
    "peaks",
    "summit",

    # LAGOS
    "lake",
    "lakes",
    "mountain lake",
    "alpine lake",
    "turquoise lake",
    "blue lake",
    "lake mountains",

    # VALES
    "valley",
    "green valley",
    "mountain valley",
    "alpine valley",
    "green mountains",
    "green landscape",

    # CHALÉS
    "cabin",
    "cabins",
    "mountain cabin",
    "lake cabin",
    "chalet",
    "chalet mountain",
    "mountain house",

    # NATUREZA / CENÁRIO
    "landscape",
    "nature",
    "scenic",
    "scenic view",
    "viewpoint",
    "panorama",
    "panoramic",
    "dramatic landscape",
    "wilderness",

    # FAROÉ / FJORDS
    "faroe",
    "faroe islands",
    "fjord",
    "fjords",
    "green mountains",
    "sea cliffs"
]


# ============================================================
# PALAVRAS RUINS
# ============================================================

PALAVRAS_RUINS = [

    "hiking",
    "hike",
    "trail",
    "trails",
    "trekking",
    "trek",
    "walking trail",
    "walking",
    "path",
    "footpath",

    "city",
    "street",
    "road",
    "highway",
    "car",
    "cars",
    "vehicle",
    "building",
    "hotel",
    "restaurant",
    "house interior",
    "home interior",
    "indoor",
    "room",
    "office",

    "pool",
    "swimming pool",

    "boat",
    "boats",
    "ship",
    "cruise",

    "people",
    "person",
    "man",
    "woman",
    "face",
    "selfie",

    "concert",
    "party",
    "wedding",
    "airport",
    "train",
    "bus",
    "traffic",
    "skyscraper"
]


# ============================================================
# INTERFACE
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

body {
    margin: 0;
    padding: 0;
    background: #101010;
    color: white;
    font-family: Arial, sans-serif;
}

.container {
    max-width: 600px;
    margin: auto;
    padding: 25px;
}

h1 {
    text-align: center;
    margin-bottom: 8px;
}

.subtitle {
    text-align: center;
    color: #aaa;
    margin-bottom: 30px;
}

label {
    display: block;
    margin-top: 18px;
    margin-bottom: 8px;
}

select,
button {
    width: 100%;
    padding: 15px;
    border-radius: 10px;
    border: none;
    font-size: 16px;
    box-sizing: border-box;
}

select {
    background: #222;
    color: white;
}

button {
    margin-top: 25px;
    background: #ffffff;
    color: #000;
    font-weight: bold;
    cursor: pointer;
}

button:hover {
    opacity: 0.85;
}

.info {
    margin-top: 25px;
    padding: 15px;
    background: #1c1c1c;
    border-radius: 10px;
    line-height: 1.6;
}

</style>

</head>

<body>

<div class="container">

<h1>🌎 Mundo Afora</h1>

<div class="subtitle">
Paisagens incríveis pelo mundo
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
🎬 Criar vídeo
</button>

</form>

<div class="info">

<b>Configurações:</b><br><br>

📱 1080 × 1920<br>
🎞️ 24 FPS<br>
⏱️ Aproximadamente 60 segundos<br>
🔇 Sem áudio<br>
📝 Sem texto<br>
🌊 Mar e oceanos<br>
🪨 Grandes paredões e falésias<br>
🏞️ Lagos e vales verdes<br>
🏡 Chalés e cabanas<br>
🔍 Zoom suave<br>
©️ mundo.afora0

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

        raise RuntimeError(
            "PEXELS_API_KEY não configurada."
        )

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

    resposta = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=30
    )

    resposta.raise_for_status()

    dados = resposta.json()

    return dados.get("videos", [])


# ============================================================
# ESCOLHER ARQUIVO DO VÍDEO
# ============================================================

def escolher_arquivo(video):

    arquivos = video.get(
        "video_files",
        []
    )

    candidatos = []

    for arquivo in arquivos:

        link = arquivo.get("link")

        largura = arquivo.get(
            "width"
        ) or 0

        altura = arquivo.get(
            "height"
        ) or 0

        if not link:
            continue

        if largura <= 0 or altura <= 0:
            continue

        if not link.lower().endswith(".mp4"):
            continue

        proporcao = altura / largura

        if proporcao < 1.35:
            continue

        area = largura * altura

        candidatos.append({

            "link": link,
            "width": largura,
            "height": altura,
            "area": area

        })

    if not candidatos:
        return None

    candidatos.sort(
        key=lambda x: x["area"],
        reverse=True
    )

    adequados = [

        x for x in candidatos

        if x["width"] <= 2160
        and x["height"] <= 3840

    ]

    if adequados:

        return adequados[0]

    return candidatos[0]


# ============================================================
# PONTUAÇÃO
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
            "user",
            {}
        ).get(
            "name",
            ""
        )
    )

    texto = texto.lower()

    score = 0

    for palavra in PALAVRAS_BOAS:

        if palavra.lower() in texto:

            score += 5

    for palavra in PALAVRAS_RUINS:

        if palavra.lower() in texto:

            score -= 15

    return score


# ============================================================
# SELECIONAR MELHORES
# ============================================================

def selecionar_melhores_videos(
    videos,
    quantidade=12
):

    unicos = {}

    for video in videos:

        video_id = video.get("id")

        if not video_id:
            continue

        if video_id in unicos:
            continue

        duracao = video.get(
            "duration",
            0
        )

        if duracao < 5:
            continue

        arquivo = escolher_arquivo(
            video
        )

        if not arquivo:
            continue

        video[
            "_arquivo_escolhido"
        ] = arquivo

        video[
            "_score"
        ] = pontuar_video(
            video
        )

        unicos[
            video_id
        ] = video

    lista = list(
        unicos.values()
    )

    lista.sort(
        key=lambda x: x.get(
            "_score",
            0
        ),
        reverse=True
    )

    lista = lista[:30]

    random.shuffle(
        lista
    )

    return lista[:quantidade]


# ============================================================
# BAIXAR UM VÍDEO
# ============================================================

def baixar_video(video):

    arquivo = video[
        "_arquivo_escolhido"
    ]

    url = arquivo[
        "link"
    ]

    nome = (
        f"{uuid.uuid4().hex}.mp4"
    )

    caminho = os.path.join(
        VIDEO_DIR,
        nome
    )

    resposta = requests.get(
        url,
        stream=True,
        timeout=60
    )

    resposta.raise_for_status()

    with open(
        caminho,
        "wb"
    ) as f:

        for bloco in resposta.iter_content(
            chunk_size=1024 * 1024
        ):

            if bloco:

                f.write(
                    bloco
                )

    return caminho


# ============================================================
# DOWNLOAD PARALELO
# ============================================================

def baixar_videos_paralelo(
    videos
):

    resultados = []

    with ThreadPoolExecutor(
        max_workers=3
    ) as executor:

        tarefas = [

            executor.submit(
                baixar_video,
                video
            )

            for video in videos

        ]

        for tarefa in as_completed(
            tarefas
        ):

            try:

                caminho = (
                    tarefa.result()
                )

                resultados.append(
                    caminho
                )

            except Exception as e:

                print(
                    "Erro ao baixar vídeo:",
                    e
                )

    return resultados


# ============================================================
# PROCESSAR CLIPE
# ============================================================

def processar_clipe_zoom(
    input_path,
    output_path,
    duracao,
    zoom_final=1.12
):

    duracao = max(
        1.0,
        float(duracao)
    )

    velocidade_zoom = (
        zoom_final - 1.0
    ) / duracao

    largura_crop = (
        f"2160/(1+{velocidade_zoom:.6f}*t)"
    )

    altura_crop = (
        f"3840/(1+{velocidade_zoom:.6f}*t)"
    )

    x_crop = (
        f"(iw-2160/(1+{velocidade_zoom:.6f}*t))/2"
    )

    y_crop = (
        f"(ih-3840/(1+{velocidade_zoom:.6f}*t))/2"
    )

    filtro = (
        "scale=2160:3840:"
        "force_original_aspect_ratio=increase,"
        "crop=2160:3840,"
        f"crop={largura_crop}:"
        f"{altura_crop}:"
        f"{x_crop}:"
        f"{y_crop},"
        "scale=1080:1920,"
        "fps=24,"
        "setsar=1"
    )

    comando = [

        FFMPEG,

        "-y",

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
        "veryfast",

        "-crf",
        "23",

        "-pix_fmt",
        "yuv420p",

        "-movflags",
        "+faststart",

        output_path
    ]

    print(
        "\n=============================="
    )

    print(
        "PROCESSANDO CLIPE"
    )

    print(
        "=============================="
    )

    resultado = subprocess.run(
        comando,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if resultado.returncode != 0:

        print(
            resultado.stderr
        )

        raise RuntimeError(
            "Erro real do FFmpeg:\n\n"
            + resultado.stderr[-6000:]
        )

    return output_path


# ============================================================
# APLICAR MARCA D'ÁGUA
# ============================================================

def aplicar_marca_dagua(
    input_path,
    output_path
):

    """
    Marca d'água:
    mundo.afora0

    Posição:
    canto inferior direito.

    Transparência:
    75%.

    Tamanho:
    aproximadamente 32 px.

    Margem:
    45 px.
    """

    texto = WATERMARK.replace(
        "'",
        "\\'"
    )

    filtro = (
        "drawtext="
        "text='"
        + texto
        + "':"
        "fontcolor=white@0.75:"
        "fontsize=32:"
        "x=w-tw-45:"
        "y=h-th-55:"
        "shadowcolor=black@0.55:"
        "shadowx=2:"
        "shadowy=2"
    )

    comando = [

        FFMPEG,

        "-y",

        "-i",
        input_path,

        "-vf",
        filtro,

        "-an",

        "-c:v",
        "libx264",

        "-preset",
        "veryfast",

        "-crf",
        "23",

        "-pix_fmt",
        "yuv420p",

        "-movflags",
        "+faststart",

        output_path
    ]

    print(
        "\n=============================="
    )

    print(
        "APLICANDO MARCA D'ÁGUA"
    )

    print(
        "=============================="
    )

    print(
        "Marca:",
        WATERMARK
    )

    resultado = subprocess.run(
        comando,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if resultado.returncode != 0:

        print(
            "ERRO NA MARCA D'ÁGUA:"
        )

        print(
            resultado.stderr
        )

        raise RuntimeError(
            "Erro ao aplicar marca d'água:\n\n"
            + resultado.stderr[-6000:]
        )

    return output_path


# ============================================================
# JUNTAR CLIPES
# ============================================================

def juntar_clipes(
    clipes,
    output_path
):

    lista_path = os.path.join(
        TEMP_DIR,
        f"concat_{uuid.uuid4().hex}.txt"
    )

    with open(
        lista_path,
        "w",
        encoding="utf-8"
    ) as f:

        for clipe in clipes:

            caminho = os.path.abspath(
                clipe
            )

            caminho = caminho.replace(
                "\\",
                "/"
            )

            f.write(
                "file '"
                + caminho.replace(
                    "'",
                    "'\\''"
                )
                + "'\n"
            )

    comando = [

        FFMPEG,

        "-y",

        "-f",
        "concat",

        "-safe",
        "0",

        "-i",
        lista_path,

        "-c",
        "copy",

        "-an",

        "-movflags",
        "+faststart",

        output_path
    ]

    print(
        "\n=============================="
    )

    print(
        "JUNTANDO CLIPES"
    )

    print(
        "=============================="
    )

    resultado = subprocess.run(
        comando,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    try:

        os.remove(
            lista_path
        )

    except Exception:

        pass

    if resultado.returncode != 0:

        print(
            resultado.stderr
        )

        raise RuntimeError(
            "Erro ao juntar os clipes:\n\n"
            + resultado.stderr[-6000:]
        )

    return output_path


# ============================================================
# CRIAR REEL
# ============================================================

def criar_reel(
    videos,
    output_path
):

    clipes_processados = []

    tempo_restante = DURATION

    video_base = None

    try:

        for index, video_path in enumerate(
            videos
        ):

            if tempo_restante <= 0:
                break

            duracao_clipe = random.uniform(
                7.0,
                11.0
            )

            duracao_clipe = min(
                duracao_clipe,
                tempo_restante
            )

            nome_clipe = (
                f"{uuid.uuid4().hex}.mp4"
            )

            caminho_clipe = os.path.join(
                TEMP_DIR,
                nome_clipe
            )

            zoom = random.uniform(
                1.08,
                1.14
            )

            processar_clipe_zoom(
                video_path,
                caminho_clipe,
                duracao_clipe,
                zoom_final=zoom
            )

            clipes_processados.append(
                caminho_clipe
            )

            tempo_restante -= (
                duracao_clipe
            )

            print(
                f"Clipe {index + 1} concluído"
            )

        if not clipes_processados:

            raise RuntimeError(
                "Nenhum clipe foi processado."
            )

        # ----------------------------------------------------
        # PRIMEIRO: juntar todos os clipes
        # ----------------------------------------------------

        video_base = os.path.join(
            TEMP_DIR,
            f"base_{uuid.uuid4().hex}.mp4"
        )

        juntar_clipes(
            clipes_processados,
            video_base
        )

        # ----------------------------------------------------
        # DEPOIS: aplicar marca d'água
        # ----------------------------------------------------

        aplicar_marca_dagua(
            video_base,
            output_path
        )

    finally:

        # Remove vídeos originais
        for caminho in videos:

            try:
                os.remove(
                    caminho
                )

            except Exception:
                pass

        # Remove clipes
        for caminho in clipes_processados:

            try:
                os.remove(
                    caminho
                )

            except Exception:
                pass

        # Remove vídeo base
        if video_base:

            try:
                os.remove(
                    video_base
                )

            except Exception:
                pass

    return output_path


# ============================================================
# GERAR VÍDEO
# ============================================================

def gerar_video(pais):

    if pais not in PAISES:

        raise ValueError(
            "Destino inválido."
        )

    consultas = PAISES[pais]

    todos_videos = []

    print(
        "\n=============================="
    )

    print(
        "BUSCANDO PAISAGEM"
    )

    print(
        "=============================="
    )

    for query in consultas[:10]:

        try:

            print(
                "Pesquisa:",
                query
            )

            encontrados = buscar_videos(
                query
            )

            todos_videos.extend(
                encontrados
            )

            print(
                "Encontrados:",
                len(encontrados)
            )

            if len(todos_videos) >= 150:

                break

        except Exception as e:

            print(
                "Erro na pesquisa:",
                query,
                e
            )

    if not todos_videos:

        raise RuntimeError(
            "Nenhum vídeo encontrado no Pexels."
        )

    print(
        "Total encontrado:",
        len(todos_videos)
    )

    videos_selecionados = (
        selecionar_melhores_videos(
            todos_videos,
            quantidade=12
        )
    )

    if not videos_selecionados:

        raise RuntimeError(
            "Nenhum vídeo vertical adequado foi encontrado."
        )

    print(
        "Vídeos selecionados:",
        len(videos_selecionados)
    )

    videos_baixados = (
        baixar_videos_paralelo(
            videos_selecionados
        )
    )

    if not videos_baixados:

        raise RuntimeError(
            "Não foi possível baixar os vídeos."
        )

    print(
        "Downloads concluídos:",
        len(videos_baixados)
    )

    nome_saida = (
        "mundo_afora_"
        + uuid.uuid4().hex
        + ".mp4"
    )

    output_path = os.path.join(
        OUTPUT_DIR,
        nome_saida
    )

    criar_reel(
        videos_baixados,
        output_path
    )

    return output_path


# ============================================================
# HOME
# ============================================================

@app.route(
    "/",
    methods=["GET", "POST"]
)

def index():

    if request.method == "POST":

        pais = request.form.get(
            "pais"
        )

        try:

            arquivo = gerar_video(
                pais
            )

            return send_file(
                arquivo,
                as_attachment=True,
                download_name="mundo_afora.mp4",
                mimetype="video/mp4"
            )

        except Exception as e:

            print(
                "\nERRO FINAL:"
            )

            print(
                str(e)
            )

            return f"""

            <html>

            <body style="
                background:#111;
                color:white;
                font-family:Arial;
                padding:30px;
            ">

            <h2>
                ❌ Erro ao criar vídeo
            </h2>

            <pre style="
                white-space:pre-wrap;
                background:#222;
                padding:20px;
                border-radius:10px;
            ">
{html.escape(str(e))}
            </pre>

            <br>

            <a href="/"
               style="
               color:white;
               background:#333;
               padding:12px 20px;
               border-radius:8px;
               text-decoration:none;
               ">

               ← Voltar

            </a>

            </body>

            </html>

            """

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

        "status": "online",

        "app": "Mundo Afora",

        "type":
        "nature_vertical_video",

        "duration":
        DURATION,

        "resolution":
        f"{WIDTH}x{HEIGHT}",

        "fps":
        FPS,

        "zoom":
        True,

        "watermark":
        WATERMARK,

        "audio":
        False,

        "text":
        False

    }


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    port = int(
        os.getenv(
            "PORT",
            "8080"
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )