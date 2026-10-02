import os
import random
import uuid
import shutil
import subprocess
import asyncio
import textwrap

import requests
import edge_tts
import imageio_ffmpeg

from PIL import Image, ImageDraw, ImageFont

from flask import Flask, request, render_template_string, send_file


# ============================================================
# APP
# ============================================================

app = Flask(__name__)


# ============================================================
# CONFIGURAÇÕES
# ============================================================

PORT = int(os.getenv("PORT", "8080"))

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

VIDEO_DIR = "videos"
TEMP_DIR = "temp"
OUTPUT_DIR = "outputs"

os.makedirs(VIDEO_DIR, exist_ok=True)
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
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]


def encontrar_fonte():
    for caminho in FONT_PATHS:
        if os.path.exists(caminho):
            return caminho

    return None


FONT_PATH = encontrar_fonte()


def carregar_fonte(tamanho):
    try:
        if FONT_PATH:
            return ImageFont.truetype(FONT_PATH, tamanho)
    except Exception:
        pass

    return ImageFont.load_default()


# ============================================================
# PAÍSES / DESTINOS
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
            "O contraste entre o oceano e as montanhas cria paisagens impressionantes."
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
            "Em várias regiões, enormes paredes rochosas encontram águas extremamente calmas, "
            "formando paisagens únicas."
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
            "Montanhas, cânions, lagos e florestas podem ser encontrados em diferentes regiões do país."
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
    margin-bottom: 8px;
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
    color: #bbb;
    font-size: 14px;
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

• imagens reais de paisagens
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
# FUNÇÃO PARA EXECUTAR FFMPEG
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

        print("[ERRO FFMPEG]")
        print("RETURN CODE:", resultado.returncode)
        print(resultado.stderr)

        raise RuntimeError("FFmpeg falhou.")

    return resultado


# ============================================================
# BUSCAR VÍDEO NO PEXELS
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

    if response.status_code != 200:
        raise RuntimeError(
            f"Pexels retornou {response.status_code}"
        )

    dados = response.json()

    videos = dados.get("videos", [])

    if not videos:
        raise RuntimeError(
            f"Nenhum vídeo encontrado para: {query}"
        )

    random.shuffle(videos)

    for video in videos:

        arquivos = video.get("video_files", [])

        candidatos = []

        for arquivo in arquivos:

            link = arquivo.get("link")

            if not link:
                continue

            largura = arquivo.get("width") or 0
            altura = arquivo.get("height") or 0

            candidatos.append(
                (
                    largura * altura,
                    link,
                    largura,
                    altura
                )
            )

        if not candidatos:
            continue

        candidatos.sort(
            key=lambda x: x[0],
            reverse=True
        )

        _, link, largura, altura = candidatos[0]

        return link

    raise RuntimeError(
        "Não foi possível encontrar um arquivo de vídeo."
    )


# ============================================================
# BAIXAR VÍDEO
# ============================================================

def baixar_video(url, destino):

    print("[DOWNLOAD]")
    print(url)

    with requests.get(
        url,
        stream=True,
        timeout=120
    ) as response:

        response.raise_for_status()

        with open(destino, "wb") as arquivo:

            for bloco in response.iter_content(
                chunk_size=1024 * 1024
            ):

                if bloco:
                    arquivo.write(bloco)

    tamanho = os.path.getsize(destino)

    print(
        f"[OK DOWNLOAD] "
        f"{tamanho / 1024 / 1024:.1f} MB"
    )


# ============================================================
# PROCESSAR CLIPE
# ============================================================

def processar_clipe(original, saida):

    comando = [

        FFMPEG,

        "-hide_banner",
        "-loglevel", "error",
        "-y",

        "-i", original,

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

        saida
    ]

    executar_ffmpeg(comando)


# ============================================================
# CONCATENAR
# ============================================================

def concatenar_clipes(clipes, saida, pasta):

    lista = os.path.join(
        pasta,
        f"lista_{uuid.uuid4().hex}.txt"
    )

    with open(lista, "w", encoding="utf-8") as arquivo:

        for clipe in clipes:

            caminho = os.path.abspath(clipe)

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
        "-loglevel", "error",
        "-y",

        "-f", "concat",

        "-safe", "0",

        "-i", lista,

        "-an",

        "-c", "copy",

        saida
    ]

    executar_ffmpeg(comando)

    try:
        os.remove(lista)
    except:
        pass


# ============================================================
# ROTEIRO
# ============================================================

def criar_roteiro(pais):

    dados = PAISES[pais]

    introducao = (
        f"Você já imaginou conhecer este lugar? "
        f"Hoje o Mundo Afora te leva para {dados['titulo']}. "
    )

    fechamento = (
        "E o mais impressionante é que cada paisagem parece "
        "revelar um cenário diferente. "
        "Se você pudesse viajar para qualquer lugar do mundo, "
        "qual destino escolheria?"
    )

    texto = (
        introducao
        + dados["texto"]
        + " "
        + fechamento
    )

    return texto


# ============================================================
# QUEBRAR TEXTO
# ============================================================

def quebrar_legendas(texto, max_chars=55):

    palavras = texto.split()

    linhas = []

    atual = ""

    for palavra in palavras:

        tentativa = (
            atual + " " + palavra
        ).strip()

        if len(tentativa) <= max_chars:

            atual = tentativa

        else:

            if atual:
                linhas.append(atual)

            atual = palavra

    if atual:
        linhas.append(atual)

    return linhas


# ============================================================
# CRIAR IMAGEM DE LEGENDA
# ============================================================

def criar_imagem_legenda(
    texto,
    caminho
):

    imagem = Image.new(
        "RGBA",
        (WIDTH, HEIGHT),
        (0, 0, 0, 0)
    )

    desenho = ImageDraw.Draw(imagem)

    fonte = carregar_fonte(48)

    # Quebra automática
    linhas = textwrap.wrap(
        texto,
        width=34
    )

    if not linhas:
        linhas = [texto]

    # Limita quantidade
    linhas = linhas[:3]

    # Medidas
    caixas = []

    espacamento = 12

    altura_total = 0

    for linha in linhas:

        bbox = desenho.textbbox(
            (0, 0),
            linha,
            font=fonte
        )

        largura = bbox[2] - bbox[0]
        altura = bbox[3] - bbox[1]

        caixas.append(
            (linha, largura, altura)
        )

        altura_total += altura

    altura_total += (
        espacamento * (len(caixas) - 1)
    )

    # Posição inferior
    y = HEIGHT - 300 - altura_total

    # Fundo preto transparente
    padding_x = 35
    padding_y = 25

    largura_max = 0

    for _, largura, _ in caixas:
        largura_max = max(
            largura_max,
            largura
        )

    fundo_largura = (
        largura_max + padding_x * 2
    )

    fundo_altura = (
        altura_total + padding_y * 2
    )

    fundo_x = (
        WIDTH - fundo_largura
    ) // 2

    fundo_y = y - padding_y

    desenho.rounded_rectangle(
        [
            fundo_x,
            fundo_y,
            fundo_x + fundo_largura,
            fundo_y + fundo_altura
        ],
        radius=22,
        fill=(0, 0, 0, 175)
    )

    # Texto
    for linha, largura, altura in caixas:

        x = (
            WIDTH - largura
        ) // 2

        desenho.text(
            (x, y),
            linha,
            font=fonte,
            fill=(255, 255, 255, 255),
            stroke_width=3,
            stroke_fill=(0, 0, 0, 255)
        )

        y += altura + espacamento

    imagem.save(
        caminho,
        "PNG"
    )


# ============================================================
# CRIAR LEGENDAS COMO PNG
# ============================================================

def criar_legendas_png(
    texto,
    pasta
):

    frases = quebrar_legendas(
        texto,
        max_chars=55
    )

    if not frases:
        return []

    # Aproximação de duração.
    # A narração é distribuída pelos caracteres.
    pesos = [
        max(len(frase), 1)
        for frase in frases
    ]

    total_peso = sum(pesos)

    duracao_total = 60.0

    tempo_atual = 0.0

    legendas = []

    for indice, frase in enumerate(frases):

        duracao = (
            duracao_total
            * pesos[indice]
            / total_peso
        )

        inicio = tempo_atual

        fim = (
            tempo_atual
            + duracao
        )

        # Evita terminar exatamente em 60
        if indice == len(frases) - 1:
            fim = 60.0

        caminho = os.path.join(
            pasta,
            f"legenda_{indice}.png"
        )

        criar_imagem_legenda(
            frase,
            caminho
        )

        legendas.append(
            {
                "arquivo": caminho,
                "inicio": inicio,
                "fim": fim
            }
        )

        tempo_atual = fim

    return legendas


# ============================================================
# GERAR NARRAÇÃO
# ============================================================

async def gerar_audio_async(
    texto,
    saida
):

    comunicador = edge_tts.Communicate(
        texto,
        VOICE,
        rate=VOICE_RATE,
        volume="+0%",
        pitch="+0Hz"
    )

    await comunicador.save(saida)


def gerar_audio(texto, saida):

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
# FINALIZAR VÍDEO
# ============================================================

def finalizar_video(
    video,
    audio,
    legendas,
    saida
):

    # --------------------------------------------------------
    # Entradas
    # --------------------------------------------------------

    comando = [

        FFMPEG,

        "-hide_banner",
        "-loglevel", "error",
        "-y",

        "-i", video,

        "-i", audio
    ]

    # --------------------------------------------------------
    # Adiciona PNGs das legendas
    # --------------------------------------------------------

    for legenda in legendas:

        comando.extend(
            [
                "-loop",
                "1",

                "-i",
                legenda["arquivo"]
            ]
        )

    # --------------------------------------------------------
    # FILTER COMPLEX
    # --------------------------------------------------------

    filtros = []

    ultimo_video = "[0:v]"

    for indice, legenda in enumerate(legendas):

        entrada = f"[{indice + 2}:v]"

        saida_video = (
            f"[v{indice}]"
        )

        inicio = legenda["inicio"]
        fim = legenda["fim"]

        filtro = (
            f"{ultimo_video}{entrada}"
            f"overlay=0:0:"
            f"enable='between(t,{inicio:.3f},{fim:.3f})'"
            f"{saida_video}"
        )

        filtros.append(filtro)

        ultimo_video = saida_video

    filter_complex = ";".join(
        filtros
    )

    # --------------------------------------------------------
    # Mapeamento
    # --------------------------------------------------------

    comando.extend(
        [
            "-filter_complex",
            filter_complex,

            "-map",
            ultimo_video,

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
    )

    executar_ffmpeg(
        comando
    )


# ============================================================
# GERAR VÍDEO
# ============================================================

def gerar_video(pais):

    if pais not in PAISES:
        raise RuntimeError(
            "País inválido."
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

    clipes_processados = []

    try:

        # ====================================================
        # BAIXAR E PROCESSAR 4 CLIPES
        # ====================================================

        for indice in range(CLIP_COUNT):

            query = random.choice(
                dados["buscas"]
            )

            print("=" * 60)
            print(
                f"[BUSCA {indice + 1}/{CLIP_COUNT}]"
            )
            print(query)
            print("=" * 60)

            url = buscar_video(query)

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

            clipes_processados.append(
                processado
            )

        # ====================================================
        # JUNTAR CLIPES
        # ====================================================

        video_junto = os.path.join(
            pasta,
            "video_junto.mp4"
        )

        concatenar_clipes(
            clipes_processados,
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
        # NARRAÇÃO
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

        legendas = criar_legendas_png(
            roteiro,
            pasta
        )

        print("=" * 60)
        print(
            f"[LEGENDAS] {len(legendas)}"
        )
        print("=" * 60)

        # ====================================================
        # OUTPUT
        # ====================================================

        nome_saida = (
            "mundo_afora_"
            + uuid.uuid4().hex[:10]
            + ".mp4"
        )

        saida = os.path.join(
            OUTPUT_DIR,
            nome_saida
        )

        # ====================================================
        # FINALIZAR
        # ====================================================

        finalizar_video(
            video_junto,
            narracao,
            legendas,
            saida
        )

        if not os.path.exists(saida):

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
            f"Tamanho: "
            f"{tamanho / 1024 / 1024:.2f} MB"
        )
        print("=" * 60)

        return saida

    finally:

        # ====================================================
        # LIMPEZA
        # ====================================================

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
# ROTA PRINCIPAL
# ============================================================

@app.route("/", methods=["GET"])
def index():

    return render_template_string(
        HTML,
        paises=list(PAISES.keys())
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
# HEALTH CHECK
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
# EXECUÇÃO LOCAL
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False
    )