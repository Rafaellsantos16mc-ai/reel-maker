import os
import re
import uuid
import random
import shutil
import subprocess

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

# 8 clipes x 7.5 segundos = 60 segundos
CLIP_COUNT = 8
CLIP_DURATION = 7.5

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
        "Brazil ocean cliffs",
    ],

    "Ilhas Faroé": [
        "Faroe Islands mountains ocean",
        "Faroe Islands cliffs",
        "Faroe Islands lake mountains",
        "Faroe Islands green valley",
        "Faroe Islands waterfall mountains",
        "Faroe Islands scenic landscape",
    ],

    "Suíça": [
        "Switzerland mountains lake",
        "Swiss Alps lake",
        "Switzerland mountain cabin",
        "Swiss mountain valley",
        "Swiss Alps chalet",
        "Switzerland green valley",
        "Swiss lake mountains",
    ],

    "Noruega": [
        "Norway fjord mountains",
        "Norway mountain lake",
        "Norway cliffs ocean",
        "Norway green valley",
        "Norway mountain cabin",
        "Norwegian fjord landscape",
    ],

    "Islândia": [
        "Iceland mountains waterfall",
        "Iceland lake mountains",
        "Iceland cliffs ocean",
        "Iceland green valley",
        "Iceland scenic landscape",
        "Iceland waterfall mountains",
    ],

    "Canadá": [
        "Canada Rocky Mountains lake",
        "Canada mountain lake",
        "Canada mountain cabin",
        "Canada green valley",
        "Canadian Rockies landscape",
        "Canada turquoise lake mountains",
    ],

    "Nova Zelândia": [
        "New Zealand mountains lake",
        "New Zealand mountain valley",
        "New Zealand mountain cabin",
        "New Zealand green valley",
        "New Zealand lake mountains",
        "New Zealand scenic landscape",
    ],

    "Áustria": [
        "Austria Alps lake",
        "Austria mountain cabin",
        "Austria mountain valley",
        "Austrian Alps landscape",
        "Austria green valley",
        "Austria lake mountains",
    ],

    "Eslovênia": [
        "Slovenia mountains lake",
        "Slovenia Lake Bled mountains",
        "Slovenia mountain valley",
        "Slovenia green valley",
        "Slovenia mountain waterfall",
    ],

    "França": [
        "French Alps lake",
        "France mountain valley",
        "French Alps cabin",
        "France mountain lake",
        "French Alps landscape",
    ],

    "Itália": [
        "Italian Alps lake",
        "Dolomites lake mountains",
        "Dolomites mountain cabin",
        "Italy green mountain valley",
        "Dolomites landscape",
    ],

    "Estados Unidos": [
        "USA mountain lake",
        "Rocky Mountains lake",
        "USA mountain cabin",
        "USA mountain valley",
        "Yosemite mountains lake",
        "Alaska mountains lake",
    ],

    "Japão": [
        "Japan mountain lake",
        "Japan mountain valley",
        "Japan scenic mountains",
        "Japan lake mountains",
        "Japan green valley",
    ],

    "Peru": [
        "Peru Andes mountains lake",
        "Peru mountain valley",
        "Peru green mountains",
        "Peru scenic mountain lake",
    ],

    "Chile": [
        "Chile Patagonia mountains lake",
        "Chile mountain lake",
        "Patagonia mountains",
        "Chile green valley",
        "Chile scenic landscape",
    ],

    "Argentina": [
        "Argentina Patagonia mountains lake",
        "Argentina mountain lake",
        "Patagonia mountain valley",
        "Argentina green valley",
        "Argentina scenic mountains",
    ],
}


# ============================================================
# TERMOS PARA EVITAR
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
    "trail",
    "trekking",
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

    "airport",
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
    min-height: 100vh;

    background:
        linear-gradient(
            180deg,
            #06151f 0%,
            #0b2633 50%,
            #06151f 100%
        );

    color: white;

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    display: flex;
    align-items: center;
    justify-content: center;

    padding: 20px;
}

.container {
    width: 100%;
    max-width: 500px;

    background: rgba(255,255,255,0.07);

    border: 1px solid rgba(255,255,255,0.12);

    border-radius: 22px;

    padding: 28px;

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

    color: #b9cbd2;

    margin-bottom: 28px;
}

label {
    display: block;

    margin-top: 18px;
    margin-bottom: 8px;

    font-weight: bold;
}

select,
button {

    width: 100%;

    border-radius: 12px;

    padding: 15px;

    font-size: 16px;
}

select {

    background: #102f3d;

    color: white;

    border: 1px solid rgba(255,255,255,0.15);
}

button {

    margin-top: 24px;

    border: 0;

    background: #ffffff;

    color: #09202b;

    font-weight: bold;

    cursor: pointer;
}

button:hover {
    opacity: 0.9;
}

.info {

    margin-top: 20px;

    padding: 15px;

    border-radius: 12px;

    background: rgba(255,255,255,0.05);

    color: #b9cbd2;

    font-size: 14px;

    line-height: 1.6;
}

</style>

</head>

<body>

<div class="container">

    <h1>🌎 MUNDO AFORA</h1>

    <div class="subtitle">
        Paisagens incríveis pelo mundo
    </div>

    <form method="POST">

        <label>Destino</label>

        <select name="pais" required>

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

        📱 Formato: 1080 × 1920<br>
        ⏱️ Duração: aproximadamente 60 segundos<br>
        🎞️ FPS: 24<br>
        🔇 Sem música e sem narração<br>
        🌎 Apenas paisagens<br>
        ✨ Marca: mundo.afora0

    </div>

</div>

</body>

</html>
"""


# ============================================================
# EXECUTAR COMANDO
# ============================================================

def executar(comando):

    try:

        print("")
        print("[COMANDO]")
        print(" ".join(str(x) for x in comando))
        print("")

        resultado = subprocess.run(
            comando,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        print(
            f"[FFMPEG RETURN CODE] "
            f"{resultado.returncode}"
        )

        if resultado.stdout:

            print("[FFMPEG STDOUT]")
            print(resultado.stdout[-3000:])

        if resultado.stderr:

            print("[FFMPEG STDERR]")
            print(resultado.stderr[-5000:])

        return resultado

    except Exception as e:

        print("[ERRO SUBPROCESS]")
        print(repr(e))

        return None


# ============================================================
# LIMPAR DIRETÓRIOS
# ============================================================

def limpar_diretorio(diretorio):

    if not os.path.exists(diretorio):
        os.makedirs(diretorio, exist_ok=True)
        return

    for nome in os.listdir(diretorio):

        caminho = os.path.join(
            diretorio,
            nome
        )

        try:

            if os.path.isdir(caminho):

                shutil.rmtree(caminho)

            else:

                os.remove(caminho)

        except Exception as e:

            print(
                f"[ERRO LIMPEZA] "
                f"{caminho}: {e}"
            )


# ============================================================
# BUSCAR VÍDEOS NO PEXELS
# ============================================================

def buscar_videos(query):

    if not PEXELS_API_KEY:

        print(
            "[ERRO] PEXELS_API_KEY "
            "não configurada."
        )

        return []

    url = "https://api.pexels.com/videos/search"

    headers = {
        "Authorization": PEXELS_API_KEY
    }

    params = {
        "query": query,
        "orientation": "portrait",
        "size": "large",
        "per_page": 80,
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
            f"[PEXELS] "
            f"{len(videos)} resultados"
        )

        return videos

    except Exception as e:

        print(
            f"[ERRO PEXELS] {e}"
        )

        return []


# ============================================================
# ESCOLHER ARQUIVO DO VÍDEO
# ============================================================

def escolher_arquivo_video(video):

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

        if largura <= 0 or altura <= 0:
            continue

        proporcao = altura / largura

        if proporcao < 1.35:
            continue

        tipo = (
            arquivo.get("file_type")
            or ""
        ).lower()

        if "mp4" not in tipo:
            continue

        candidatos.append(
            (
                largura,
                altura,
                link
            )
        )

    if not candidatos:

        return None

    # Preferência por 1080x1920
    preferencias = [
        (1080, 1920),
        (1440, 2560),
        (720, 1280),
        (2160, 3840),
    ]

    for largura_pref, altura_pref in preferencias:

        for largura, altura, link in candidatos:

            if (
                largura == largura_pref
                and
                altura == altura_pref
            ):

                return {
                    "link": link,
                    "width": largura,
                    "height": altura
                }

    # Se não encontrou exatamente,
    # pega o mais próximo de 1080x1920

    candidatos.sort(
        key=lambda x:
            abs(x[0] - 1080)
            +
            abs(x[1] - 1920)
    )

    largura, altura, link = candidatos[0]

    return {
        "link": link,
        "width": largura,
        "height": altura
    }


# ============================================================
# PONTUAR VÍDEO
# ============================================================

def pontuar_video(video):

    score = 0

    texto = ""

    texto += str(
        video.get("url", "")
    ).lower()

    texto += " "

    texto += str(
        video.get("image", "")
    ).lower()

    for palavra in PALAVRAS_RUINS:

        if palavra in texto:

            score -= 20

    largura = video.get(
        "width"
    ) or 0

    altura = video.get(
        "height"
    ) or 0

    if largura and altura:

        proporcao = altura / largura

        if proporcao >= 1.7:

            score += 10

        elif proporcao >= 1.45:

            score += 5

    return score


# ============================================================
# SELECIONAR VÍDEOS
# ============================================================

def selecionar_videos(pais):

    consultas = PAISES.get(
        pais,
        []
    )

    encontrados = {}

    for consulta in consultas:

        resultados = buscar_videos(
            consulta
        )

        for video in resultados:

            video_id = video.get("id")

            if not video_id:
                continue

            if video_id in encontrados:
                continue

            arquivo = escolher_arquivo_video(
                video
            )

            if not arquivo:
                continue

            video["_arquivo_escolhido"] = arquivo

            encontrados[video_id] = video

    print("")
    print(
        f"[TOTAL] "
        f"{len(encontrados)} vídeos únicos"
    )

    videos = list(
        encontrados.values()
    )

    videos.sort(
        key=pontuar_video,
        reverse=True
    )

    # Pegamos alguns a mais porque
    # alguns podem falhar no download/processamento

    selecionados = videos[:20]

    random.shuffle(
        selecionados
    )

    print(
        f"[SELECIONADOS] "
        f"{len(selecionados)}"
    )

    return selecionados


# ============================================================
# DOWNLOAD DE UM VÍDEO
# ============================================================

def baixar_video(video, indice):

    arquivo = video.get(
        "_arquivo_escolhido"
    )

    if not arquivo:

        print(
            "[ERRO] Arquivo de vídeo "
            "não encontrado."
        )

        return None

    url = arquivo["link"]

    nome = (
        f"{uuid.uuid4().hex}.mp4"
    )

    caminho = os.path.join(
        VIDEO_DIR,
        nome
    )

    print("")
    print(
        f"[DOWNLOAD] {indice} "
        f"{arquivo['width']}x"
        f"{arquivo['height']}"
    )

    try:

        with requests.get(
            url,
            stream=True,
            timeout=(20, 120)
        ) as resposta:

            resposta.raise_for_status()

            with open(
                caminho,
                "wb"
            ) as arquivo_saida:

                for bloco in resposta.iter_content(
                    chunk_size=1024 * 1024
                ):

                    if bloco:

                        arquivo_saida.write(
                            bloco
                        )

        tamanho = (
            os.path.getsize(caminho)
            / 1024
            / 1024
        )

        print(
            f"[OK DOWNLOAD] "
            f"{tamanho:.1f} MB"
        )

        return caminho

    except Exception as e:

        print(
            f"[ERRO DOWNLOAD] {e}"
        )

        try:

            if os.path.exists(caminho):

                os.remove(caminho)

        except Exception:
            pass

        return None


# ============================================================
# VERIFICAR VÍDEO
# ============================================================

def verificar_video(caminho):

    if not caminho:
        return False

    if not os.path.exists(caminho):
        return False

    tamanho = os.path.getsize(
        caminho
    )

    if tamanho < 10000:

        print(
            "[ERRO] Arquivo muito pequeno."
        )

        return False

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

    if resultado is None:

        return False

    if resultado.returncode != 0:

        print(
            "[ERRO] Vídeo inválido."
        )

        return False

    return True


# ============================================================
# PROCESSAR CLIPE
# ============================================================

def processar_clipe(
    input_path,
    output_path,
    duracao=CLIP_DURATION
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
        "warning",

        "-threads",
        "1",

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
        "30",

        "-pix_fmt",
        "yuv420p",

        "-r",
        "24",

        "-movflags",
        "+faststart",

        output_path
    ]

    print("")
    print(
        "===================================="
    )

    print(
        "[FFMPEG] Iniciando processamento"
    )

    print(
        f"Entrada: {input_path}"
    )

    print(
        f"Saída: {output_path}"
    )

    print(
        "===================================="
    )

    resultado = executar(
        comando
    )

    if resultado is None:

        print(
            "[ERRO] FFmpeg não conseguiu executar."
        )

        return False

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
            "===================================="
        )

        return False

    if not os.path.exists(
        output_path
    ):

        print(
            "[ERRO] FFmpeg terminou, "
            "mas o arquivo não existe."
        )

        return False

    tamanho = (
        os.path.getsize(output_path)
        / 1024
        / 1024
    )

    print(
        f"[OK PROCESSAMENTO] "
        f"{tamanho:.1f} MB"
    )

    return True


# ============================================================
# CRIAR MARCA D'ÁGUA
# ============================================================

def criar_marca_dagua():

    caminho = os.path.join(
        TEMP_DIR,
        "watermark.png"
    )

    texto = "mundo.afora0"

    fontes = [

        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",

        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",

        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",

    ]

    fonte = None

    for caminho_fonte in fontes:

        if os.path.exists(
            caminho_fonte
        ):

            fonte = caminho_fonte
            break

    if fonte:

        try:

            font = ImageFont.truetype(
                fonte,
                38
            )

        except Exception:

            font = ImageFont.load_default()

    else:

        font = ImageFont.load_default()

    dummy = Image.new(
        "RGBA",
        (100, 100),
        (0, 0, 0, 0)
    )

    draw = ImageDraw.Draw(
        dummy
    )

    bbox = draw.textbbox(
        (0, 0),
        texto,
        font=font
    )

    largura = (
        bbox[2] - bbox[0]
    )

    altura = (
        bbox[3] - bbox[1]
    )

    margem = 18

    imagem = Image.new(
        "RGBA",
        (
            largura + margem * 2,
            altura + margem * 2
        ),
        (0, 0, 0, 0)
    )

    draw = ImageDraw.Draw(
        imagem
    )

    # sombra discreta
    draw.text(
        (
            margem + 2,
            margem + 2
        ),
        texto,
        font=font,
        fill=(0, 0, 0, 80)
    )

    # texto branco transparente
    draw.text(
        (
            margem,
            margem
        ),
        texto,
        font=font,
        fill=(255, 255, 255, 185)
    )

    imagem.save(
        caminho,
        "PNG"
    )

    return caminho


# ============================================================
# APLICAR MARCA D'ÁGUA
# ============================================================

def aplicar_marca_dagua(
    input_path,
    output_path
):

    watermark = criar_marca_dagua()

    posicao_x = (
        "(main_w-overlay_w)/2"
    )

    posicao_y = (
        "main_h*0.58"
    )

    filtro = (
        f"overlay="
        f"{posicao_x}:"
        f"{posicao_y}"
    )

    comando = [

        FFMPEG,

        "-y",

        "-hide_banner",

        "-loglevel",
        "warning",

        "-threads",
        "1",

        "-i",
        input_path,

        "-i",
        watermark,

        "-filter_complex",
        filtro,

        "-map",
        "0:v:0",

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
        "24",

        "-movflags",
        "+faststart",

        output_path
    ]

    print("")
    print(
        "[WATERMARK] Aplicando..."
    )

    resultado = executar(
        comando
    )

    if resultado is None:
        return False

    if resultado.returncode != 0:

        print(
            "[ERRO WATERMARK]"
        )

        return False

    if not os.path.exists(
        output_path
    ):

        return False

    return True


# ============================================================
# CRIAR LISTA CONCAT
# ============================================================

def criar_lista_concat(
    clipes,
    lista_path
):

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
                .replace("\\", "/")
            )

            caminho_absoluto = (
                caminho_absoluto
                .replace("'", "'\\''")
            )

            arquivo.write(
                f"file '{caminho_absoluto}'\n"
            )


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

    criar_lista_concat(
        clipes,
        lista_path
    )

    comando = [

        FFMPEG,

        "-y",

        "-hide_banner",

        "-loglevel",
        "warning",

        "-f",
        "concat",

        "-safe",
        "0",

        "-i",
        lista_path,

        "-c",
        "copy",

        output_path
    ]

    print("")
    print(
        "[CONCAT] Juntando clipes..."
    )

    resultado = executar(
        comando
    )

    try:

        if os.path.exists(
            lista_path
        ):

            os.remove(
                lista_path
            )

    except Exception:
        pass

    if resultado is None:
        return False

    if resultado.returncode != 0:

        print(
            "[ERRO CONCAT]"
        )

        return False

    if not os.path.exists(
        output_path
    ):

        return False

    return True


# ============================================================
# LIMITAR VÍDEO A 60 SEGUNDOS
# ============================================================

def limitar_duracao(
    input_path,
    output_path
):

    comando = [

        FFMPEG,

        "-y",

        "-hide_banner",

        "-loglevel",
        "warning",

        "-threads",
        "1",

        "-i",
        input_path,

        "-t",
        str(DURATION),

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
        "24",

        output_path
    ]

    resultado = executar(
        comando
    )

    if resultado is None:
        return False

    if resultado.returncode != 0:
        return False

    return os.path.exists(
        output_path
    )


# ============================================================
# GERAR VÍDEO
# ============================================================

def gerar_video(pais):

    print("")
    print(
        "===================================="
    )
    print(
        "🌎 MUNDO AFORA"
    )
    print(
        "===================================="
    )

    print(
        f"Destino: {pais}"
    )

    if not PEXELS_API_KEY:

        raise Exception(
            "PEXELS_API_KEY não configurada."
        )

    # --------------------------------------------------------
    # LIMPAR ARQUIVOS ANTERIORES
    # --------------------------------------------------------

    limpar_diretorio(
        VIDEO_DIR
    )

    limpar_diretorio(
        TEMP_DIR
    )

    # --------------------------------------------------------
    # BUSCAR VÍDEOS
    # --------------------------------------------------------

    videos = selecionar_videos(
        pais
    )

    if not videos:

        raise Exception(
            "Nenhum vídeo encontrado."
        )

    random.shuffle(
        videos
    )

    clipes_processados = []

    # --------------------------------------------------------
    # PROCESSAMENTO SEQUENCIAL
    # --------------------------------------------------------

    for indice, video in enumerate(
        videos
    ):

        if len(
            clipes_processados
        ) >= CLIP_COUNT:

            break

        caminho_original = None

        caminho_clipe = os.path.join(
            TEMP_DIR,
            f"clip_{len(clipes_processados):02d}.mp4"
        )

        try:

            # ----------------------------------------------
            # DOWNLOAD
            # ----------------------------------------------

            caminho_original = baixar_video(
                video,
                indice
            )

            if not caminho_original:

                print(
                    "[PULAR] Falha no download."
                )

                continue

            # ----------------------------------------------
            # VERIFICAR
            # ----------------------------------------------

            if not verificar_video(
                caminho_original
            ):

                print(
                    "[PULAR] Vídeo inválido."
                )

                continue

            # ----------------------------------------------
            # PROCESSAR
            # ----------------------------------------------

            numero_clipe = (
                len(clipes_processados)
            )

            print("")
            print(
                f"[PROCESSANDO] "
                f"Clipe {numero_clipe}"
            )

            sucesso = processar_clipe(
                caminho_original,
                caminho_clipe,
                CLIP_DURATION
            )

            if not sucesso:

                print(
                    "[PULAR] Falha no processamento."
                )

                continue

            # ----------------------------------------------
            # GUARDAR
            # ----------------------------------------------

            clipes_processados.append(
                caminho_clipe
            )

            print(
                f"[CLIPES OK] "
                f"{len(clipes_processados)}/"
                f"{CLIP_COUNT}"
            )

        except Exception as e:

            print(
                f"[ERRO CLIPE] {repr(e)}"
            )

        finally:

            # ----------------------------------------------
            # APAGAR ORIGINAL IMEDIATAMENTE
            # ----------------------------------------------

            if caminho_original:

                try:

                    if os.path.exists(
                        caminho_original
                    ):

                        os.remove(
                            caminho_original
                        )

                        print(
                            "[LIMPO] "
                            "Vídeo original removido."
                        )

                except Exception as e:

                    print(
                        f"[ERRO AO APAGAR] {e}"
                    )

    # --------------------------------------------------------
    # VERIFICAR QUANTIDADE
    # --------------------------------------------------------

    print("")
    print(
        f"[BAIXADOS/PROCESSADOS] "
        f"{len(clipes_processados)}"
    )

    if len(
        clipes_processados
    ) < 4:

        raise Exception(
            "Não foi possível processar "
            "vídeos suficientes."
        )

    # --------------------------------------------------------
    # JUNTAR
    # --------------------------------------------------------

    video_base = os.path.join(
        TEMP_DIR,
        f"base_{uuid.uuid4().hex}.mp4"
    )

    sucesso = juntar_clipes(
        clipes_processados,
        video_base
    )

    if not sucesso:

        raise Exception(
            "Erro ao juntar os clipes."
        )

    # --------------------------------------------------------
    # APLICAR WATERMARK
    # --------------------------------------------------------

    video_watermark = os.path.join(
        TEMP_DIR,
        f"watermark_{uuid.uuid4().hex}.mp4"
    )

    sucesso = aplicar_marca_dagua(
        video_base,
        video_watermark
    )

    if not sucesso:

        raise Exception(
            "Erro ao aplicar marca d'água."
        )

    # --------------------------------------------------------
    # GARANTIR 60 SEGUNDOS
    # --------------------------------------------------------

    nome_final = (
        f"mundo_afora_"
        f"{re.sub(r'[^a-zA-Z0-9]+', '_', pais)}_"
        f"{uuid.uuid4().hex[:8]}.mp4"
    )

    caminho_final = os.path.join(
        OUTPUT_DIR,
        nome_final
    )

    sucesso = limitar_duracao(
        video_watermark,
        caminho_final
    )

    if not sucesso:

        # Caso o corte final falhe,
        # usa o arquivo com watermark.

        shutil.copy2(
            video_watermark,
            caminho_final
        )

    # --------------------------------------------------------
    # LIMPEZA
    # --------------------------------------------------------

    try:

        limpar_diretorio(
            VIDEO_DIR
        )

        limpar_diretorio(
            TEMP_DIR
        )

    except Exception as e:

        print(
            f"[ERRO LIMPEZA FINAL] {e}"
        )

    if not os.path.exists(
        caminho_final
    ):

        raise Exception(
            "Vídeo final não foi criado."
        )

    tamanho_final = (
        os.path.getsize(
            caminho_final
        )
        / 1024
        / 1024
    )

    print("")
    print(
        "===================================="
    )

    print(
        "🎉 VÍDEO FINALIZADO"
    )

    print(
        f"Arquivo: {caminho_final}"
    )

    print(
        f"Tamanho: "
        f"{tamanho_final:.1f} MB"
    )

    print(
        "===================================="
    )

    return caminho_final


# ============================================================
# ROTA PRINCIPAL
# ============================================================

@app.route(
    "/",
    methods=["GET", "POST"]
)

def index():

    if request.method == "GET":

        return render_template_string(
            HTML,
            paises=list(
                PAISES.keys()
            )
        )

    pais = request.form.get(
        "pais"
    )

    if not pais:

        return (
            "Selecione um destino.",
            400
        )

    try:

        caminho = gerar_video(
            pais
        )

        return send_file(
            caminho,
            as_attachment=True,
            download_name=os.path.basename(
                caminho
            ),
            mimetype="video/mp4"
        )

    except Exception as e:

        print("")
        print(
            "===================================="
        )

        print(
            "[ERRO GERAL]"
        )

        print(
            repr(e)
        )

        print(
            "===================================="
        )

        return f"""
        <!DOCTYPE html>

        <html lang="pt-BR">

        <head>

        <meta charset="UTF-8">

        <meta name="viewport"
              content="width=device-width,
              initial-scale=1.0">

        <style>

        body {{
            background:#081820;
            color:white;
            font-family:Arial;
            padding:30px;
        }}

        .box {{
            max-width:600px;
            margin:auto;
            background:#102b36;
            padding:25px;
            border-radius:18px;
        }}

        </style>

        </head>

        <body>

        <div class="box">

        <h2>❌ Não foi possível gerar o vídeo</h2>

        <p>
        {str(e)}
        </p>

        <p>
        Volte e tente novamente.
        </p>

        </div>

        </body>

        </html>
        """, 500


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route(
    "/health"
)

def health():

    return {
        "status": "ok",
        "app": "Mundo Afora"
    }


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=PORT
    )