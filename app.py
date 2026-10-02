import os
import re
import uuid
import random
import shutil
import subprocess

import requests

from flask import Flask, request, render_template_string, send_file


# ============================================================
# CONFIGURAÇÕES
# ============================================================

app = Flask(__name__)

PORT = int(os.getenv("PORT", "8080"))

# Resolução usada durante o processamento
PROCESS_WIDTH = 540
PROCESS_HEIGHT = 960

# Resolução final
FINAL_WIDTH = 1080
FINAL_HEIGHT = 1920

FPS = 24

DURATION = 60

CLIP_COUNT = 8
CLIP_DURATION = 7.5

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

FFMPEG = shutil.which("ffmpeg")

if not FFMPEG:
    FFMPEG = "/usr/bin/ffmpeg"


# ============================================================
# PAÍSES / BUSCAS
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
        "Faroe Islands scenic landscape",
        "Faroe Islands waterfall mountains",
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
# PALAVRAS QUE QUEREMOS EVITAR
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

<html lang="pt-br">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>Mundo Afora</title>

<style>

body {
    font-family: Arial, sans-serif;
    background: #111;
    color: white;
    margin: 0;
    padding: 20px;
}

.container {
    max-width: 600px;
    margin: auto;
}

h1 {
    text-align: center;
    margin-bottom: 30px;
}

.card {
    background: #1c1c1c;
    padding: 20px;
    border-radius: 15px;
}

label {
    display: block;
    margin-top: 15px;
    margin-bottom: 7px;
}

select,
button {
    width: 100%;
    padding: 14px;
    border-radius: 10px;
    border: none;
    font-size: 16px;
}

select {
    background: #292929;
    color: white;
}

button {
    margin-top: 25px;
    background: #fff;
    color: #111;
    font-weight: bold;
    cursor: pointer;
}

.info {
    margin-top: 20px;
    padding: 15px;
    background: #222;
    border-radius: 10px;
    font-size: 14px;
    line-height: 1.5;
}

</style>

</head>

<body>

<div class="container">

<h1>🌎 Mundo Afora</h1>

<div class="card">

<form method="POST">

<label>País</label>

<select name="pais">

{% for pais in paises %}

<option value="{{ pais }}">
{{ pais }}
</option>

{% endfor %}

</select>

<button type="submit">
GERAR VÍDEO
</button>

</form>

<div class="info">

Vídeo vertical 1080×1920<br>
60 segundos<br>
24 FPS<br>
Paisagens reais<br>
Sem música<br>
Sem narração<br>
Sem pessoas<br>
Sem marca d'água

</div>

</div>

</div>

</body>

</html>
"""


# ============================================================
# UTILIDADES
# ============================================================

def limpar_nome(texto):

    texto = re.sub(
        r"[^a-zA-Z0-9_-]",
        "_",
        texto
    )

    return texto[:80]


def rodar_ffmpeg(comando):

    print("=" * 70)
    print("[FFMPEG]")
    print(" ".join(str(x) for x in comando))
    print("=" * 70)

    resultado = subprocess.run(
        comando,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    print(
        "[RETURN CODE]",
        resultado.returncode
    )

    if resultado.stderr:
        print(
            resultado.stderr[-4000:]
        )

    return resultado


# ============================================================
# PEXELS
# ============================================================

def buscar_videos(query):

    if not PEXELS_API_KEY:

        raise Exception(
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
        "per_page": 80,
    }

    print(
        "[PEXELS BUSCA]",
        query
    )

    resposta = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=30
    )

    resposta.raise_for_status()

    dados = resposta.json()

    return dados.get(
        "videos",
        []
    )


# ============================================================
# ESCOLHER ARQUIVO
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
            "width",
            0
        )

        altura = arquivo.get(
            "height",
            0
        )

        tipo = arquivo.get(
            "file_type",
            ""
        )

        if not link:
            continue

        if (
            tipo
            and tipo.lower()
            != "video/mp4"
        ):
            continue

        if (
            largura <= 0
            or altura <= 0
        ):
            continue

        # Precisamos de vídeo vertical
        if altura <= largura:
            continue

        proporcao = altura / largura

        if proporcao < 1.25:
            continue

        candidatos.append({
            "link": link,
            "width": largura,
            "height": altura,
            "size": arquivo.get(
                "file_size"
            ) or 0
        })

    if not candidatos:

        return None

    candidatos.sort(
        key=lambda x: (
            abs(
                x["width"]
                - FINAL_WIDTH
            ),
            abs(
                x["height"]
                - FINAL_HEIGHT
            ),
            x["size"] or 0
        )
    )

    return candidatos[0]


# ============================================================
# SELECIONAR VÍDEOS
# ============================================================

def selecionar_videos(
    consultas
):

    encontrados = {}

    for consulta in consultas:

        try:

            videos = buscar_videos(
                consulta
            )

        except Exception as erro:

            print(
                "[ERRO PEXELS]",
                erro
            )

            continue

        for video in videos:

            video_id = video.get(
                "id"
            )

            if not video_id:
                continue

            if video_id in encontrados:
                continue

            texto = (
                str(
                    video.get(
                        "url",
                        ""
                    )
                )
                + " "
                + str(
                    video.get(
                        "user",
                        {}
                    ).get(
                        "name",
                        ""
                    )
                )
                + " "
                + str(
                    video.get(
                        "alt",
                        ""
                    )
                )
            ).lower()

            pontos_ruins = 0

            for palavra in PALAVRAS_RUINS:

                if palavra in texto:

                    pontos_ruins += 1

            arquivo = escolher_arquivo_video(
                video
            )

            if not arquivo:

                continue

            encontrados[
                video_id
            ] = {
                "id": video_id,
                "arquivo": arquivo,
                "score": pontos_ruins,
            }

    lista = list(
        encontrados.values()
    )

    lista.sort(
        key=lambda x: x["score"]
    )

    lista = lista[:30]

    random.shuffle(
        lista
    )

    print(
        "[VÍDEOS SELECIONADOS]",
        len(lista)
    )

    return lista


# ============================================================
# DOWNLOAD
# ============================================================

def baixar_video(item):

    nome = (
        str(uuid.uuid4())
        + ".mp4"
    )

    caminho = os.path.join(
        VIDEO_DIR,
        nome
    )

    link = item[
        "arquivo"
    ]["link"]

    print(
        "[DOWNLOAD]",
        item["id"],
        item["arquivo"]["width"],
        "x",
        item["arquivo"]["height"]
    )

    resposta = requests.get(
        link,
        stream=True,
        timeout=60
    )

    resposta.raise_for_status()

    tamanho = 0

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

                tamanho += len(
                    bloco
                )

    print(
        "[OK DOWNLOAD]",
        round(
            tamanho / 1024 / 1024,
            1
        ),
        "MB"
    )

    return caminho


# ============================================================
# VALIDAR VÍDEO
# ============================================================

def verificar_video(
    caminho
):

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

    resultado = rodar_ffmpeg(
        comando
    )

    return (
        resultado.returncode
        == 0
    )


# ============================================================
# PROCESSAR CLIPE EM 540x960
# ============================================================

def processar_clipe(
    entrada,
    saida,
    duracao=CLIP_DURATION
):

    print(
        "[PROCESSANDO CLIPE]"
    )

    comando = [
        FFMPEG,

        "-y",

        "-hide_banner",

        "-loglevel",
        "error",

        "-threads",
        "1",

        "-i",
        entrada,

        "-t",
        str(duracao),

        "-vf",
        (
            "scale=540:960:"
            "force_original_aspect_ratio=increase,"
            "crop=540:960,"
            "fps=24,"
            "setsar=1"
        ),

        "-an",

        "-c:v",
        "libx264",

        "-preset",
        "ultrafast",

        "-crf",
        "32",

        "-pix_fmt",
        "yuv420p",

        "-r",
        "24",

        "-movflags",
        "+faststart",

        saida
    ]

    resultado = rodar_ffmpeg(
        comando
    )

    if resultado.returncode != 0:

        print(
            "[ERRO CLIPE]"
        )

        return False

    if not os.path.exists(
        saida
    ):

        return False

    tamanho = os.path.getsize(
        saida
    )

    if tamanho < 10000:

        return False

    print(
        "[CLIPE OK]",
        round(
            tamanho / 1024 / 1024,
            2
        ),
        "MB"
    )

    return True


# ============================================================
# JUNTAR CLIPES
# ============================================================

def juntar_clipes(
    clipes,
    saida
):

    lista = os.path.join(
        TEMP_DIR,
        "concat.txt"
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
                "file '"
                + caminho
                + "'\n"
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
        lista,

        "-c",
        "copy",

        "-an",

        saida
    ]

    resultado = rodar_ffmpeg(
        comando
    )

    if resultado.returncode != 0:

        return False

    return os.path.exists(
        saida
    )


# ============================================================
# FINAL 1080x1920 SEM MARCA D'ÁGUA
# ============================================================

def finalizar_video(
    entrada,
    saida
):

    print(
        "[FINALIZANDO SEM MARCA D'ÁGUA]"
    )

    comando = [
        FFMPEG,

        "-y",

        "-hide_banner",

        "-loglevel",
        "error",

        "-threads",
        "1",

        "-i",
        entrada,

        "-t",
        str(DURATION),

        "-vf",
        (
            "scale=1080:1920:"
            "force_original_aspect_ratio=increase,"
            "crop=1080:1920,"
            "fps=24,"
            "setsar=1"
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
        "24",

        "-movflags",
        "+faststart",

        saida
    ]

    resultado = rodar_ffmpeg(
        comando
    )

    if resultado.returncode != 0:

        print(
            "[ERRO FINAL]"
        )

        return False

    if not os.path.exists(
        saida
    ):

        return False

    tamanho = os.path.getsize(
        saida
    )

    print(
        "[VÍDEO FINAL SEM MARCA D'ÁGUA]",
        round(
            tamanho / 1024 / 1024,
            2
        ),
        "MB"
    )

    return True


# ============================================================
# LIMPAR ARQUIVOS
# ============================================================

def limpar_temporarios():

    for pasta in [
        VIDEO_DIR,
        TEMP_DIR
    ]:

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

            except Exception as erro:

                print(
                    "[ERRO LIMPEZA]",
                    erro
                )


# ============================================================
# GERAR VÍDEO
# ============================================================

def gerar_video(
    pais
):

    if pais not in PAISES:

        raise Exception(
            "País inválido."
        )

    limpar_temporarios()

    consultas = PAISES[
        pais
    ].copy()

    random.shuffle(
        consultas
    )

    candidatos = selecionar_videos(
        consultas
    )

    if not candidatos:

        raise Exception(
            "Nenhum vídeo encontrado."
        )

    clipes = []

    numero = 0

    for item in candidatos:

        if len(clipes) >= CLIP_COUNT:

            break

        original = None

        try:

            original = baixar_video(
                item
            )

            if not verificar_video(
                original
            ):

                print(
                    "[PULAR] Vídeo inválido."
                )

                os.remove(
                    original
                )

                original = None

                continue

            saida_clipe = os.path.join(
                TEMP_DIR,
                f"clip_{numero:02d}.mp4"
            )

            sucesso = processar_clipe(
                original,
                saida_clipe,
                CLIP_DURATION
            )

            # Remove imediatamente o original
            try:

                if os.path.exists(
                    original
                ):

                    os.remove(
                        original
                    )

                original = None

            except Exception:

                pass

            if not sucesso:

                print(
                    "[PULAR] Falha no processamento."
                )

                continue

            clipes.append(
                saida_clipe
            )

            numero += 1

            print(
                "[CLIPE ADICIONADO]",
                len(clipes),
                "/",
                CLIP_COUNT
            )

        except Exception as erro:

            print(
                "[ERRO PROCESSANDO]",
                erro
            )

            try:

                if original and os.path.exists(
                    original
                ):

                    os.remove(
                        original
                    )

            except Exception:

                pass

            continue

    if len(clipes) < CLIP_COUNT:

        raise Exception(
            "Não foi possível processar "
            "vídeos suficientes. "
            f"Obtidos: {len(clipes)}/{CLIP_COUNT}"
        )

    # ========================================================
    # JUNTAR
    # ========================================================

    video_base = os.path.join(
        TEMP_DIR,
        "video_base.mp4"
    )

    if not juntar_clipes(
        clipes,
        video_base
    ):

        raise Exception(
            "Erro ao juntar os clipes."
        )

    # ========================================================
    # SAÍDA FINAL
    # ========================================================

    nome_final = (
        "mundo_afora_"
        + limpar_nome(pais)
        + "_"
        + uuid.uuid4().hex[:8]
        + ".mp4"
    )

    saida_final = os.path.join(
        OUTPUT_DIR,
        nome_final
    )

    sucesso = finalizar_video(
        video_base,
        saida_final
    )

    if not sucesso:

        raise Exception(
            "Erro ao gerar vídeo final."
        )

    # ========================================================
    # LIMPEZA
    # ========================================================

    try:

        for clipe in clipes:

            if os.path.exists(
                clipe
            ):

                os.remove(
                    clipe
                )

        if os.path.exists(
            video_base
        ):

            os.remove(
                video_base
            )

    except Exception as erro:

        print(
            "[ERRO LIMPEZA FINAL]",
            erro
        )

    print(
        "========================================"
    )

    print(
        "[VÍDEO GERADO COM SUCESSO]"
    )

    print(
        "[SEM MARCA D'ÁGUA]"
    )

    print(
        saida_final
    )

    print(
        "========================================"
    )

    return saida_final


# ============================================================
# ROTA PRINCIPAL
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
                download_name=os.path.basename(
                    arquivo
                ),
                mimetype="video/mp4"
            )

        except Exception as erro:

            print(
                "[ERRO GERAL]",
                repr(erro)
            )

            return f"""
            <html>

            <body style="
                background:#111;
                color:white;
                font-family:Arial;
                padding:30px;
            ">

            <h2>❌ Erro ao gerar vídeo</h2>

            <pre>{erro}</pre>

            <br>

            <a href="/" style="color:white;">
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
# START
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False
    )