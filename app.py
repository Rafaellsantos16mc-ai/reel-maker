import os
import random
import uuid
import shutil
import subprocess
import asyncio
import textwrap
import time

import requests
import edge_tts
import imageio_ffmpeg

from PIL import Image, ImageDraw, ImageFont

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

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

VOICE = "pt-BR-AntonioNeural"
VOICE_RATE = "+8%"

TEMP_DIR = "temp"
OUTPUT_DIR = "outputs"

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# FFMPEG
# ============================================================

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

if not FFMPEG:
    FFMPEG = shutil.which("ffmpeg")

if not FFMPEG:
    raise RuntimeError("FFmpeg não encontrado.")


# ============================================================
# FONTES
# ============================================================

FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
]

FONT_PATH = None

for caminho in FONT_PATHS:
    if os.path.exists(caminho):
        FONT_PATH = caminho
        break


def carregar_fonte(tamanho):
    if FONT_PATH:
        try:
            return ImageFont.truetype(
                FONT_PATH,
                tamanho
            )
        except:
            pass

    return ImageFont.load_default()


# ============================================================
# DESTINOS
# ============================================================

PAISES = {

    "Brasil": {
        "titulo": "BRASIL",
        "buscas": [
            "Brazil mountains landscape",
            "Brazil waterfall nature",
            "Brazil lake landscape",
            "Brazil scenic nature"
        ],
        "texto": (
            "O Brasil é conhecido por sua enorme diversidade natural. "
            "Entre montanhas, cachoeiras, rios, florestas e praias, "
            "o país reúne alguns dos cenários mais impressionantes da América do Sul."
        )
    },

    "Ilhas Faroé": {
        "titulo": "ILHAS FAROÉ",
        "buscas": [
            "Faroe Islands mountains",
            "Faroe Islands waterfall",
            "Faroe Islands cliffs",
            "Faroe Islands landscape"
        ],
        "texto": (
            "As Ilhas Faroé ficam no Atlântico Norte e são conhecidas "
            "por suas montanhas verdes, falésias e cachoeiras. "
            "O contraste entre o oceano e as montanhas cria paisagens únicas."
        )
    },

    "Suíça": {
        "titulo": "SUÍÇA",
        "buscas": [
            "Swiss Alps landscape",
            "Switzerland mountains lake",
            "Swiss Alps waterfall",
            "Switzerland scenic landscape"
        ],
        "texto": (
            "Os Alpes suíços formam algumas das paisagens mais conhecidas da Europa. "
            "Montanhas, lagos, vales e pequenas cidades criam cenários "
            "que parecem ter saído de um filme."
        )
    },

    "Noruega": {
        "titulo": "NORUEGA",
        "buscas": [
            "Norway fjords landscape",
            "Norway mountains waterfall",
            "Norway lake mountains",
            "Norway scenic nature"
        ],
        "texto": (
            "A Noruega é famosa pelos seus fiordes, montanhas e cachoeiras. "
            "Em várias regiões, enormes paredes rochosas encontram águas calmas, "
            "formando paisagens impressionantes."
        )
    },

    "Islândia": {
        "titulo": "ISLÂNDIA",
        "buscas": [
            "Iceland waterfall landscape",
            "Iceland mountains",
            "Iceland glacier landscape",
            "Iceland scenic nature"
        ],
        "texto": (
            "A Islândia reúne vulcões, geleiras, cachoeiras e paisagens praticamente intocadas. "
            "É um dos lugares onde a natureza mostra mudanças impressionantes "
            "em pequenas distâncias."
        )
    },

    "Canadá": {
        "titulo": "CANADÁ",
        "buscas": [
            "Canada Rocky Mountains",
            "Canada lake mountains",
            "Canada waterfall landscape",
            "Canada scenic nature"
        ],
        "texto": (
            "O Canadá possui algumas das maiores áreas naturais do planeta. "
            "Montanhas, lagos de águas cristalinas e enormes florestas "
            "formam paisagens impressionantes."
        )
    },

    "Nova Zelândia": {
        "titulo": "NOVA ZELÂNDIA",
        "buscas": [
            "New Zealand mountains",
            "New Zealand waterfall",
            "New Zealand lake landscape",
            "New Zealand scenic nature"
        ],
        "texto": (
            "A Nova Zelândia combina montanhas, lagos, florestas e cachoeiras "
            "em uma paisagem extremamente diversificada. "
            "Muitas dessas regiões parecem cenários de filmes."
        )
    },

    "Áustria": {
        "titulo": "ÁUSTRIA",
        "buscas": [
            "Austria Alps landscape",
            "Austria mountain lake",
            "Austria waterfall",
            "Austria scenic landscape"
        ],
        "texto": (
            "A Áustria é conhecida pelos Alpes, pelos lagos e pelas pequenas cidades cercadas "
            "por montanhas. Durante o inverno, muitas regiões ficam cobertas de neve."
        )
    },

    "Eslovênia": {
        "titulo": "ESLOVÊNIA",
        "buscas": [
            "Slovenia mountains lake",
            "Slovenia waterfall",
            "Slovenia nature landscape",
            "Slovenia Alps"
        ],
        "texto": (
            "A Eslovênia é um pequeno país europeu com uma grande variedade de paisagens. "
            "Montanhas, lagos, rios e florestas formam alguns dos cenários mais tranquilos da Europa."
        )
    },

    "França": {
        "titulo": "FRANÇA",
        "buscas": [
            "France Alps mountains",
            "France mountain lake",
            "France waterfall nature",
            "France scenic landscape"
        ],
        "texto": (
            "Além das cidades históricas, a França possui regiões montanhosas impressionantes. "
            "Os Alpes franceses apresentam lagos, vales e montanhas que mudam completamente "
            "de aparência durante o ano."
        )
    },

    "Itália": {
        "titulo": "ITÁLIA",
        "buscas": [
            "Italy Dolomites mountains",
            "Italy mountain lake",
            "Italy Alps landscape",
            "Italy scenic nature"
        ],
        "texto": (
            "As Dolomitas, no norte da Itália, são famosas por suas formações rochosas. "
            "A região combina montanhas, vales e lagos em uma paisagem bastante característica."
        )
    },

    "Estados Unidos": {
        "titulo": "ESTADOS UNIDOS",
        "buscas": [
            "USA Rocky Mountains",
            "USA mountain lake",
            "USA waterfall landscape",
            "USA scenic nature"
        ],
        "texto": (
            "Os Estados Unidos possuem uma enorme diversidade de paisagens naturais. "
            "Montanhas, cânions, lagos e florestas podem ser encontrados em diferentes regiões."
        )
    },

    "Japão": {
        "titulo": "JAPÃO",
        "buscas": [
            "Japan mountains nature",
            "Japan waterfall",
            "Japan lake mountains",
            "Japan scenic landscape"
        ],
        "texto": (
            "O Japão possui uma paisagem natural muito diversa. "
            "Montanhas, florestas, lagos e cachoeiras aparecem em diferentes regiões, "
            "criando cenários completamente diferentes entre as estações."
        )
    },

    "Peru": {
        "titulo": "PERU",
        "buscas": [
            "Peru Andes mountains",
            "Peru mountain landscape",
            "Peru lake mountains",
            "Peru scenic nature"
        ],
        "texto": (
            "O Peru abriga uma parte importante da Cordilheira dos Andes. "
            "Montanhas enormes, vales e lagos em grandes altitudes "
            "formam algumas das paisagens mais marcantes da América do Sul."
        )
    },

    "Chile": {
        "titulo": "CHILE",
        "buscas": [
            "Chile Patagonia mountains",
            "Chile mountains lake",
            "Chile waterfall nature",
            "Chile Patagonia landscape"
        ],
        "texto": (
            "O Chile possui uma das geografias mais variadas do mundo. "
            "Na Patagônia, montanhas, lagos, geleiras e vales criam paisagens impressionantes."
        )
    },

    "Argentina": {
        "titulo": "ARGENTINA",
        "buscas": [
            "Argentina Patagonia mountains",
            "Argentina lake mountains",
            "Argentina waterfall landscape",
            "Argentina scenic nature"
        ],
        "texto": (
            "A Argentina possui grandes áreas naturais na região da Patagônia. "
            "Montanhas, lagos, geleiras e florestas criam cenários muito diferentes "
            "de outras partes do país."
        )
    }
}


# ============================================================
# HTML
# ============================================================

HTML = """
<!DOCTYPE html>
<html lang="pt-br">

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>Mundo Afora</title>

<style>

body {
    margin: 0;
    padding: 30px 15px;
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
}

.subtitulo {
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
    border-radius: 10px;
    border: none;
    font-size: 16px;
    margin-bottom: 20px;
}

select {
    background: #222;
    color: white;
}

button {
    background: white;
    color: #111;
    font-weight: bold;
}

.info {
    background: #1d1d1d;
    padding: 15px;
    border-radius: 10px;
    color: #bbb;
    line-height: 1.5;
}

</style>

</head>

<body>

<div class="container">

<h1>🌎 Mundo Afora</h1>

<div class="subtitulo">
Vídeos de lugares incríveis pelo mundo
</div>

<form action="/gerar" method="POST">

<label>Escolha o destino</label>

<select name="pais">

{% for pais in paises %}

<option value="{{ pais }}">
{{ pais }}
</option>

{% endfor %}

</select>

<button type="submit">
🎬 GERAR VÍDEO
</button>

</form>

<div class="info">

Vídeo vertical 1080×1920 com:
<br><br>

• paisagens reais
<br>
• narração em português
<br>
• legendas
<br>
• 60 segundos
<br>
• sem música
<br>
• sem marca d'água

</div>

</div>

</body>

</html>
"""


# ============================================================
# FFMPEG
# ============================================================

def executar_ffmpeg(comando):

    print("=" * 60)
    print("[FFMPEG]")
    print(" ".join(comando))
    print("=" * 60)

    resultado = subprocess.run(
        comando,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if resultado.returncode != 0:

        print("=" * 60)
        print("[ERRO FFMPEG]")
        print("RETURN CODE:", resultado.returncode)
        print(resultado.stderr)
        print("=" * 60)

        raise RuntimeError(
            "FFmpeg falhou."
        )

    return resultado


# ============================================================
# BUSCAR VÍDEO
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
        "per_page": 20,
        "orientation": "portrait"
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    dados = response.json()

    videos = dados.get(
        "videos",
        []
    )

    if not videos:

        raise RuntimeError(
            f"Nenhum vídeo encontrado: {query}"
        )

    random.shuffle(videos)

    candidatos = []

    for video in videos:

        arquivos = video.get(
            "video_files",
            []
        )

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

            tamanho = (
                largura * altura
            )

            # Queremos algo suficientemente bom
            # sem pegar arquivos gigantes.
            if largura >= 500 and altura >= 800:

                candidatos.append(
                    {
                        "link": link,
                        "width": largura,
                        "height": altura,
                        "pixels": tamanho
                    }
                )

    if not candidatos:

        raise RuntimeError(
            "Nenhum arquivo compatível encontrado."
        )

    # --------------------------------------------------------
    # Prioridade:
    # 1. vertical
    # 2. resolução intermediária
    # 3. evitar arquivos enormes
    # --------------------------------------------------------

    def pontuacao(item):

        largura = item["width"]
        altura = item["height"]

        vertical = altura > largura

        score = 0

        if vertical:
            score += 100000000

        # Preferência por algo próximo de 540x960
        distancia = abs(
            (largura * altura)
            -
            (540 * 960)
        )

        score -= distancia

        # Penaliza resoluções absurdamente grandes
        if largura > 1500 or altura > 2500:
            score -= 5000000

        return score

    candidatos.sort(
        key=pontuacao,
        reverse=True
    )

    escolhido = candidatos[0]

    print("=" * 60)
    print("[PEXELS ESCOLHIDO]")
    print(
        escolhido["width"],
        "x",
        escolhido["height"]
    )
    print(escolhido["link"])
    print("=" * 60)

    return escolhido["link"]


# ============================================================
# DOWNLOAD
# ============================================================

def baixar_video(url, destino):

    print("[DOWNLOAD]")
    print(url)

    with requests.get(
        url,
        stream=True,
        timeout=180
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

                    arquivo.write(
                        bloco
                    )

    tamanho = os.path.getsize(
        destino
    )

    print(
        "[OK DOWNLOAD]",
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
    original,
    saida
):

    comando = [

        FFMPEG,

        "-hide_banner",
        "-loglevel",
        "error",
        "-y",

        "-i",
        original,

        "-t",
        str(CLIP_DURATION),

        "-vf",

        (
            f"scale={PROCESS_WIDTH}:{PROCESS_HEIGHT}:"
            "force_original_aspect_ratio=increase,"
            f"crop={PROCESS_WIDTH}:{PROCESS_HEIGHT},"
            f"fps={FPS},"
            "format=yuv420p"
        ),

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

    executar_ffmpeg(
        comando
    )


# ============================================================
# CONCATENAR
# ============================================================

def concatenar_clipes(
    clipes,
    saida,
    pasta
):

    lista = os.path.join(
        pasta,
        "lista.txt"
    )

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
                "'",
                "'\\''"
            )

            arquivo.write(
                f"file '{caminho}'\n"
            )

    comando = [

        FFMPEG,

        "-hide_banner",
        "-loglevel",
        "error",
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

    executar_ffmpeg(
        comando
    )

    try:
        os.remove(lista)
    except:
        pass


# ============================================================
# ROTEIRO
# ============================================================

def criar_roteiro(
    pais
):

    dados = PAISES[pais]

    texto = (
        f"Você já imaginou conhecer este lugar? "
        f"Hoje o Mundo Afora te leva para {dados['titulo']}. "
        f"{dados['texto']} "
        "E o mais impressionante é que cada paisagem "
        "parece revelar um cenário diferente. "
        "Se você pudesse viajar para qualquer lugar do mundo, "
        "qual destino escolheria?"
    )

    return texto


# ============================================================
# NARRAÇÃO
# ============================================================

async def gerar_audio_async(
    texto,
    saida
):

    comunicador = edge_tts.Communicate(
        text=texto,
        voice=VOICE,
        rate=VOICE_RATE,
        volume="+0%",
        pitch="+0Hz"
    )

    await comunicador.save(
        saida
    )


def gerar_audio(
    texto,
    saida
):

    print("=" * 60)
    print("[NARRAÇÃO]")
    print(texto)
    print("=" * 60)

    asyncio.run(
        gerar_audio_async(
            texto,
            saida
        )
    )


# ============================================================
# CRIAR IMAGEM DE LEGENDA
# ============================================================

def criar_imagem_legenda(
    texto,
    caminho
):

    imagem = Image.new(
        "RGBA",
        (
            WIDTH,
            HEIGHT
        ),
        (
            0,
            0,
            0,
            0
        )
    )

    draw = ImageDraw.Draw(
        imagem
    )

    fonte = carregar_fonte(
        48
    )

    linhas = textwrap.wrap(
        texto,
        width=34
    )

    linhas = linhas[:3]

    espacamento = 10

    medidas = []

    altura_total = 0

    largura_max = 0

    for linha in linhas:

        bbox = draw.textbbox(
            (0, 0),
            linha,
            font=fonte
        )

        largura = (
            bbox[2] -
            bbox[0]
        )

        altura = (
            bbox[3] -
            bbox[1]
        )

        medidas.append(
            (
                linha,
                largura,
                altura
            )
        )

        largura_max = max(
            largura_max,
            largura
        )

        altura_total += altura

    altura_total += (
        espacamento *
        max(
            len(medidas) - 1,
            0
        )
    )

    padding_x = 35
    padding_y = 25

    box_width = (
        largura_max +
        padding_x * 2
    )

    box_height = (
        altura_total +
        padding_y * 2
    )

    box_x = (
        WIDTH -
        box_width
    ) // 2

    box_y = (
        HEIGHT -
        320 -
        altura_total -
        padding_y
    )

    draw.rounded_rectangle(
        (
            box_x,
            box_y,
            box_x + box_width,
            box_y + box_height
        ),
        radius=20,
        fill=(
            0,
            0,
            0,
            165
        )
    )

    y = box_y + padding_y

    for linha, largura, altura in medidas:

        x = (
            WIDTH -
            largura
        ) // 2

        draw.text(
            (
                x,
                y
            ),
            linha,
            font=fonte,
            fill=(
                255,
                255,
                255,
                255
            ),
            stroke_width=3,
            stroke_fill=(
                0,
                0,
                0,
                255
            )
        )

        y += (
            altura +
            espacamento
        )

    imagem.save(
        caminho,
        "PNG"
    )


# ============================================================
# DIVIDIR ROTEIRO
# ============================================================

def dividir_texto(
    texto,
    max_chars=55
):

    palavras = texto.split()

    frases = []

    atual = ""

    for palavra in palavras:

        tentativa = (
            atual +
            " " +
            palavra
        ).strip()

        if len(tentativa) <= max_chars:

            atual = tentativa

        else:

            if atual:
                frases.append(
                    atual
                )

            atual = palavra

    if atual:
        frases.append(
            atual
        )

    return frases


# ============================================================
# CRIAR UMA LEGENDA POR VEZ
# ============================================================

def criar_legenda_pngs(
    texto,
    pasta
):

    frases = dividir_texto(
        texto,
        55
    )

    if not frases:
        return []

    pesos = [
        max(
            len(frase),
            1
        )
        for frase in frases
    ]

    total = sum(
        pesos
    )

    resultado = []

    tempo = 0.0

    for indice, frase in enumerate(frases):

        duracao = (
            FINAL_DURATION *
            pesos[indice] /
            total
        )

        inicio = tempo

        fim = (
            tempo +
            duracao
        )

        if indice == len(frases) - 1:
            fim = FINAL_DURATION

        caminho = os.path.join(
            pasta,
            f"legenda_{indice}.png"
        )

        criar_imagem_legenda(
            frase,
            caminho
        )

        resultado.append(
            {
                "arquivo": caminho,
                "inicio": inicio,
                "fim": fim
            }
        )

        tempo = fim

    return resultado


# ============================================================
# APLICAR UMA LEGENDA
# ============================================================

def aplicar_legenda(
    video_entrada,
    imagem,
    inicio,
    fim,
    saida
):

    duracao = fim - inicio

    comando = [

        FFMPEG,

        "-hide_banner",
        "-loglevel",
        "error",
        "-y",

        "-i",
        video_entrada,

        "-loop",
        "1",

        "-i",
        imagem,

        "-filter_complex",

        (
            f"[0:v][1:v]"
            f"overlay=0:0:"
            f"enable='between(t,{inicio:.3f},{fim:.3f})'"
            f"[v]"
        ),

        "-map",
        "[v]",

        "-map",
        "0:a?",

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
        "copy",

        "-t",
        str(FINAL_DURATION),

        saida
    ]

    executar_ffmpeg(
        comando
    )


# ============================================================
# FINALIZAR COM LEGENDAS SEQUENCIALMENTE
# ============================================================

def finalizar_video(
    video,
    audio,
    legendas,
    saida
):

    # --------------------------------------------------------
    # Primeiro coloca o áudio no vídeo
    # --------------------------------------------------------

    video_audio = os.path.join(
        os.path.dirname(saida),
        f"video_audio_{uuid.uuid4().hex}.mp4"
    )

    comando_audio = [

        FFMPEG,

        "-hide_banner",
        "-loglevel",
        "error",
        "-y",

        "-i",
        video,

        "-i",
        audio,

        "-map",
        "0:v:0",

        "-map",
        "1:a:0",

        "-c:v",
        "copy",

        "-c:a",
        "aac",

        "-b:a",
        "128k",

        "-t",
        str(FINAL_DURATION),

        "-movflags",
        "+faststart",

        video_audio
    ]

    executar_ffmpeg(
        comando_audio
    )

    atual = video_audio

    arquivos_temporarios = []

    # --------------------------------------------------------
    # Aplica UMA legenda por vez
    # --------------------------------------------------------

    for indice, legenda in enumerate(legendas):

        if indice == len(legendas) - 1:

            destino = saida

        else:

            destino = os.path.join(
                os.path.dirname(saida),
                f"legenda_temp_{uuid.uuid4().hex}.mp4"
            )

            arquivos_temporarios.append(
                destino
            )

        print("=" * 60)
        print(
            f"[LEGENDA {indice + 1}/{len(legendas)}]"
        )
        print(
            legenda["inicio"],
            "->",
            legenda["fim"]
        )
        print("=" * 60)

        aplicar_legenda(
            atual,
            legenda["arquivo"],
            legenda["inicio"],
            legenda["fim"],
            destino
        )

        if atual != video_audio:
            try:
                os.remove(atual)
            except:
                pass

        atual = destino

    # --------------------------------------------------------
    # Limpeza
    # --------------------------------------------------------

    try:
        os.remove(video_audio)
    except:
        pass

    for arquivo in arquivos_temporarios:

        if arquivo != saida:

            try:
                os.remove(arquivo)
            except:
                pass


# ============================================================
# GERAR VÍDEO
# ============================================================

def gerar_video(
    pais
):

    if pais not in PAISES:

        raise RuntimeError(
            "Destino inválido."
        )

    dados = PAISES[pais]

    pasta = os.path.join(
        TEMP_DIR,
        uuid.uuid4().hex
    )

    os.makedirs(
        pasta,
        exist_ok=True
    )

    clipes = []

    try:

        # ====================================================
        # 4 CLIPES
        # ====================================================

        for indice in range(
            CLIP_COUNT
        ):

            query = random.choice(
                dados["buscas"]
            )

            print("=" * 60)
            print(
                f"[BUSCA {indice + 1}/{CLIP_COUNT}]"
            )
            print(query)
            print("=" * 60)

            url = buscar_video(
                query
            )

            original = os.path.join(
                pasta,
                f"original_{indice}.mp4"
            )

            processado = os.path.join(
                pasta,
                f"clip_{indice}.mp4"
            )

            baixar_video(
                url,
                original
            )

            processar_clipe(
                original,
                processado
            )

            # ------------------------------------------------
            # Remove o arquivo original imediatamente
            # ------------------------------------------------

            try:
                os.remove(
                    original
                )
            except:
                pass

            clipes.append(
                processado
            )

        # ====================================================
        # JUNTAR
        # ====================================================

        video_junto = os.path.join(
            pasta,
            "video_junto.mp4"
        )

        concatenar_clipes(
            clipes,
            video_junto,
            pasta
        )

        # ====================================================
        # ROTEIRO
        # ====================================================

        roteiro = criar_roteiro(
            pais
        )

        print("=" * 60)
        print("[ROTEIRO]")
        print(roteiro)
        print("=" * 60)

        # ====================================================
        # ÁUDIO
        # ====================================================

        narracao = os.path.join(
            pasta,
            "narracao.mp3"
        )

        gerar_audio(
            roteiro,
            narracao
        )

        # ====================================================
        # LEGENDAS
        # ====================================================

        legendas = criar_legenda_pngs(
            roteiro,
            pasta
        )

        print(
            "[LEGENDAS]",
            len(legendas)
        )

        # ====================================================
        # SAÍDA
        # ====================================================

        nome = (
            "mundo_afora_"
            +
            uuid.uuid4().hex[:10]
            +
            ".mp4"
        )

        saida = os.path.join(
            OUTPUT_DIR,
            nome
        )

        # ====================================================
        # FINAL
        # ====================================================

        finalizar_video(
            video_junto,
            narracao,
            legendas,
            saida
        )

        if not os.path.exists(
            saida
        ):

            raise RuntimeError(
                "Vídeo final não foi criado."
            )

        tamanho = os.path.getsize(
            saida
        )

        print("=" * 60)
        print("[VÍDEO PRONTO]")
        print(saida)
        print(
            "Tamanho:",
            round(
                tamanho / 1024 / 1024,
                2
            ),
            "MB"
        )
        print("=" * 60)

        return saida

    finally:

        try:

            shutil.rmtree(
                pasta,
                ignore_errors=True
            )

        except Exception as erro:

            print(
                "[ERRO LIMPEZA]",
                erro
            )


# ============================================================
# HOME
# ============================================================

@app.route(
    "/",
    methods=["GET"]
)
def index():

    return render_template_string(
        HTML,
        paises=list(
            PAISES.keys()
        )
    )


# ============================================================
# GERAR
# ============================================================

@app.route(
    "/gerar",
    methods=["POST"]
)
def gerar():

    pais = request.form.get(
        "pais"
    )

    if not pais:

        return (
            "Escolha um destino.",
            400
        )

    try:

        arquivo = gerar_video(
            pais
        )

        return send_file(
            arquivo,
            as_attachment=True,
            download_name=os.path.basename(
                arquivo
            ),
            mimetype="video/mp4"
        )

    except Exception as erro:

        print("=" * 60)
        print("[ERRO GERAL]")
        print(repr(erro))
        print("=" * 60)

        return f"""
        <html>

        <body style="
            background:#111;
            color:white;
            font-family:Arial;
            padding:30px;
        ">

        <h2>❌ Erro ao gerar vídeo</h2>

        <pre style="
            white-space:pre-wrap;
            background:#222;
            padding:20px;
            border-radius:10px;
        ">{erro}</pre>

        <br>

        <a href="/"
        style="
        color:white;
        background:#333;
        padding:12px 20px;
        border-radius:8px;
        text-decoration:none;
        ">
        Voltar
        </a>

        </body>

        </html>
        """, 500


# ============================================================
# HEALTH
# ============================================================

@app.route(
    "/health",
    methods=["GET"]
)
def health():

    return {
        "status": "ok",
        "ffmpeg": FFMPEG,
        "voice": VOICE
    }


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False
    )