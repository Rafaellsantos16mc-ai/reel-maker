import os
import random
import uuid
import asyncio
import shutil
import subprocess
import textwrap

import requests
from flask import Flask, request, render_template_string, send_file
import imageio_ffmpeg
import edge_tts


app = Flask(__name__)


# ============================================================
# CONFIGURAÇÕES
# ============================================================

WIDTH = 1080
HEIGHT = 1920

PROCESS_WIDTH = 540
PROCESS_HEIGHT = 960

FPS = 20

CLIP_DURATION = 15
CLIP_COUNT = 4
FINAL_DURATION = 60

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

VOICE = "pt-BR-AntonioNeural"
VOICE_RATE = "+8%"

OUTPUT_DIR = "outputs"
TEMP_DIR = "temp"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)


# ============================================================
# FFMPEG
# ============================================================

try:
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG = shutil.which("ffmpeg")

if not FFMPEG:
    raise RuntimeError("FFmpeg não encontrado.")


# ============================================================
# DESTINOS
# ============================================================

DESTINOS = {
    "Brasil": "Brazil",
    "Ilhas Faroé": "Faroe Islands",
    "Suíça": "Switzerland",
    "Noruega": "Norway",
    "Islândia": "Iceland",
    "Canadá": "Canada",
    "Nova Zelândia": "New Zealand",
    "Áustria": "Austria",
    "Eslovênia": "Slovenia",
    "França": "France",
    "Itália": "Italy",
    "Estados Unidos": "United States",
    "Japão": "Japan",
    "Peru": "Peru",
    "Chile": "Chile",
    "Argentina": "Argentina",
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

body {
    margin: 0;
    background: #111;
    color: white;
    font-family: Arial, sans-serif;
}

.container {
    max-width: 600px;
    margin: auto;
    padding: 30px 20px;
}

h1 {
    text-align: center;
}

p {
    text-align: center;
    color: #aaa;
}

label {
    display: block;
    margin-top: 25px;
    margin-bottom: 8px;
}

select,
button {
    width: 100%;
    padding: 15px;
    border-radius: 10px;
    border: none;
    font-size: 16px;
}

select {
    background: #222;
    color: white;
}

button {
    margin-top: 30px;
    background: white;
    color: #111;
    font-weight: bold;
    cursor: pointer;
}

.erro {
    background: #500;
    padding: 15px;
    border-radius: 10px;
    margin-top: 20px;
}

.sucesso {
    background: #153d20;
    padding: 15px;
    border-radius: 10px;
    margin-top: 20px;
}

a {
    display: block;
    text-align: center;
    color: white;
    margin-top: 20px;
}

</style>

</head>

<body>

<div class="container">

<h1>🌎 Mundo Afora</h1>

<p>
Vídeos de destinos incríveis para TikTok, Reels e Shorts
</p>

<form method="POST">

<label>Escolha o destino</label>

<select name="destino" required>

{% for nome in destinos %}

<option value="{{ nome }}">
{{ nome }}
</option>

{% endfor %}

</select>

<button type="submit">
🎬 Criar vídeo
</button>

</form>

{% if erro %}

<div class="erro">
{{ erro }}
</div>

{% endif %}

{% if sucesso %}

<div class="sucesso">
{{ sucesso }}
</div>

<a href="{{ arquivo }}" download>
⬇️ Baixar vídeo
</a>

{% endif %}

</div>

</body>

</html>
"""


# ============================================================
# EXECUTAR FFMPEG
# ============================================================

def executar_ffmpeg(comando):

    print("\n[FFMPEG]")

    print(
        " ".join(
            str(x)
            for x in comando
        )
    )

    resultado = subprocess.run(
        comando,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if resultado.returncode != 0:

        print(
            "\n[ERRO FFMPEG]"
        )

        print(
            "RETURN CODE:",
            resultado.returncode
        )

        print(
            resultado.stderr
        )

        raise RuntimeError(
            "FFmpeg falhou:\n\n"
            +
            resultado.stderr[-5000:]
        )

    return resultado


# ============================================================
# BUSCAR VÍDEO
# ============================================================

def buscar_video(termo):

    if not PEXELS_API_KEY:

        raise RuntimeError(
            "PEXELS_API_KEY não configurada."
        )

    url = (
        "https://api.pexels.com/videos/search"
    )

    headers = {
        "Authorization":
        PEXELS_API_KEY
    }

    params = {
        "query": termo,
        "per_page": 20,
        "orientation": "portrait"
    }

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

    if not videos:
        return None

    random.shuffle(
        videos
    )

    # Preferir vídeos verticais
    for video in videos:

        arquivos = video.get(
            "video_files",
            []
        )

        candidatos = []

        for arquivo in arquivos:

            largura = (
                arquivo.get(
                    "width"
                )
                or 0
            )

            altura = (
                arquivo.get(
                    "height"
                )
                or 0
            )

            link = arquivo.get(
                "link"
            )

            if not link:
                continue

            if altura >= largura:

                diferenca = abs(
                    (
                        altura
                        /
                        max(
                            largura,
                            1
                        )
                    )
                    -
                    (
                        16 / 9
                    )
                )

                candidatos.append(
                    (
                        diferenca,
                        link
                    )
                )

        if candidatos:

            candidatos.sort(
                key=lambda x: x[0]
            )

            return candidatos[0][1]

    # Fallback
    for video in videos:

        arquivos = video.get(
            "video_files",
            []
        )

        if arquivos:

            arquivos.sort(
                key=lambda x:
                (
                    x.get(
                        "width"
                    )
                    or 0
                )
                *
                (
                    x.get(
                        "height"
                    )
                    or 0
                ),
                reverse=True
            )

            link = arquivos[0].get(
                "link"
            )

            if link:
                return link

    return None


# ============================================================
# DOWNLOAD
# ============================================================

def baixar_video(
    url,
    caminho
):

    print(
        "[DOWNLOAD]",
        url
    )

    resposta = requests.get(
        url,
        stream=True,
        timeout=120
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

    tamanho = os.path.getsize(
        caminho
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
    entrada,
    saida
):

    comando = [

        FFMPEG,

        "-hide_banner",
        "-loglevel", "error",
        "-y",

        "-i",
        entrada,

        "-vf",
        (
            f"scale={PROCESS_WIDTH}:"
            f"{PROCESS_HEIGHT}:"
            "force_original_aspect_ratio=increase,"
            f"crop={PROCESS_WIDTH}:"
            f"{PROCESS_HEIGHT}"
        ),

        "-an",

        "-t",
        str(CLIP_DURATION),

        "-r",
        str(FPS),

        "-c:v",
        "libx264",

        "-preset",
        "ultrafast",

        "-crf",
        "32",

        "-pix_fmt",
        "yuv420p",

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
    saida
):

    lista = os.path.join(
        TEMP_DIR,
        "lista_"
        +
        uuid.uuid4().hex
        +
        ".txt"
    )

    with open(
        lista,
        "w",
        encoding="utf-8"
    ) as arquivo:

        for clipe in clipes:

            caminho = os.path.abspath(
                clipe
            ).replace(
                "\\",
                "/"
            )

            arquivo.write(
                "file '"
                +
                caminho
                +
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

        "-c",
        "copy",

        "-t",
        str(FINAL_DURATION),

        saida
    ]

    try:

        executar_ffmpeg(
            comando
        )

    finally:

        apagar_arquivo(
            lista
        )


# ============================================================
# ROTEIRO
# ============================================================

def criar_roteiro(
    destino
):

    textos = {

        "Brasil":
        "O Brasil é um país de paisagens impressionantes. "
        "Da floresta amazônica às praias paradisíacas, "
        "cada região guarda lugares que parecem ter saído de um filme.",

        "Ilhas Faroé":
        "As Ilhas Faroé parecem pertencer a outro planeta. "
        "Montanhas verdes, cachoeiras, falésias e pequenas vilas "
        "formam uma das paisagens mais impressionantes do Atlântico Norte.",

        "Suíça":
        "A Suíça é conhecida por suas montanhas gigantes, "
        "lagos cristalinos e pequenas cidades cercadas pelos Alpes. "
        "É um daqueles lugares que parecem uma pintura.",

        "Noruega":
        "A Noruega reúne fiordes gigantes, montanhas e pequenas vilas "
        "em meio a uma natureza praticamente intocada. "
        "Uma paisagem que impressiona em qualquer época do ano.",

        "Islândia":
        "A Islândia é uma terra de extremos. "
        "Vulcões, geleiras, cachoeiras e praias de areia negra "
        "fazem parte de uma das paisagens mais diferentes do mundo.",

        "Canadá":
        "O Canadá possui algumas das maiores áreas naturais preservadas "
        "do planeta. Lagos azul-turquesa, florestas e enormes montanhas "
        "criam cenários impressionantes.",

        "Nova Zelândia":
        "A Nova Zelândia parece ter sido criada para quem ama natureza. "
        "Montanhas, lagos, florestas e praias aparecem lado a lado "
        "em paisagens incríveis.",

        "Áustria":
        "A Áustria combina cidades históricas com enormes montanhas, "
        "lagos e vilarejos alpinos. "
        "Durante o inverno, o cenário fica ainda mais impressionante.",

        "Eslovênia":
        "A Eslovênia é um pequeno país europeu com paisagens gigantes. "
        "Lagos, montanhas, florestas e cachoeiras fazem parte "
        "de um dos cenários mais bonitos dos Alpes.",

        "França":
        "A França vai muito além de Paris. "
        "O país possui montanhas, vilarejos históricos, praias "
        "e paisagens naturais espalhadas por diferentes regiões.",

        "Itália":
        "A Itália reúne história, montanhas, lagos e pequenas cidades "
        "que parecem ter parado no tempo. "
        "Cada região possui uma paisagem completamente diferente.",

        "Estados Unidos":
        "Os Estados Unidos possuem alguns dos cenários naturais "
        "mais impressionantes do planeta. "
        "De grandes montanhas a desertos e parques nacionais.",

        "Japão":
        "O Japão mistura cidades modernas com montanhas, florestas "
        "e paisagens naturais impressionantes. "
        "Durante o outono e a primavera, o cenário fica ainda mais especial.",

        "Peru":
        "O Peru possui montanhas gigantes, vales profundos "
        "e paisagens que contam milhares de anos de história. "
        "É um dos destinos mais fascinantes da América do Sul.",

        "Chile":
        "O Chile se estende por milhares de quilômetros "
        "e possui desertos, vulcões, lagos e enormes montanhas. "
        "A diversidade de paisagens é impressionante.",

        "Argentina":
        "A Argentina possui algumas das paisagens mais impressionantes "
        "da América do Sul. "
        "Montanhas, geleiras, lagos e grandes áreas naturais "
        "formam cenários inesquecíveis."
    }

    return textos.get(
        destino,
        f"Conheça as paisagens incríveis de {destino}. "
        "Um destino cheio de lugares impressionantes "
        "que merecem ser descobertos."
    )


# ============================================================
# GERAR ÁUDIO
# ============================================================

async def gerar_audio_async(
    texto,
    arquivo
):

    comunicador = edge_tts.Communicate(
        texto,
        VOICE,
        rate=VOICE_RATE
    )

    await comunicador.save(
        arquivo
    )


def gerar_audio(
    texto,
    arquivo
):

    asyncio.run(
        gerar_audio_async(
            texto,
            arquivo
        )
    )


# ============================================================
# DIVIDIR TEXTO
# ============================================================

def dividir_texto(
    texto,
    quantidade=8
):

    palavras = texto.split()

    if not palavras:
        return []

    alvo = max(
        1,
        len(texto)
        /
        quantidade
    )

    partes = []

    atual = []

    tamanho = 0

    for palavra in palavras:

        atual.append(
            palavra
        )

        tamanho += (
            len(palavra)
            +
            1
        )

        if (
            tamanho >= alvo
            and
            len(partes)
            <
            quantidade - 1
        ):

            partes.append(
                " ".join(
                    atual
                )
            )

            atual = []

            tamanho = 0

    if atual:

        partes.append(
            " ".join(
                atual
            )
        )

    while len(partes) < quantidade:

        partes.append(
            partes[-1]
        )

    return partes[:quantidade]


# ============================================================
# CRIAR TEMPOS DAS LEGENDAS
# ============================================================

def criar_tempos_legendas(
    texto
):

    partes = dividir_texto(
        texto,
        8
    )

    tamanhos = [
        max(
            len(parte),
            1
        )
        for parte in partes
    ]

    total = sum(
        tamanhos
    )

    legendas = []

    tempo = 0

    for parte, tamanho in zip(
        partes,
        tamanhos
    ):

        duracao = (
            FINAL_DURATION
            *
            tamanho
            /
            total
        )

        inicio = tempo

        fim = (
            tempo
            +
            duracao
        )

        legendas.append(
            {
                "texto": parte,
                "inicio": inicio,
                "fim": fim
            }
        )

        print(
            f"[LEGENDA "
            f"{len(legendas)}/8]"
        )

        print(
            inicio,
            "->",
            fim
        )

        tempo = fim

    return legendas


# ============================================================
# ESCAPAR TEXTO PARA DRAWTEXT
# ============================================================

def escapar_drawtext(
    texto
):

    texto = texto.replace(
        "\\",
        "\\\\"
    )

    texto = texto.replace(
        "'",
        "\\'"
    )

    texto = texto.replace(
        ":",
        "\\:"
    )

    texto = texto.replace(
        "%",
        "\\%"
    )

    texto = texto.replace(
        "[",
        "\\["
    )

    texto = texto.replace(
        "]",
        "\\]"
    )

    texto = texto.replace(
        "\n",
        "\\n"
    )

    return texto


# ============================================================
# APLICAR TUDO
#
# SEM PNG
# SEM 8 ENTRADAS
# SEM OVERLAY
# ============================================================

def aplicar_video_final(
    video,
    audio,
    legendas,
    saida
):

    print(
        "\n[RENDER FINAL]"
    )

    filtros = []

    # ========================================================
    # VÍDEO BASE
    # ========================================================

    filtros.append(
        "[0:v]"
        "setpts=PTS-STARTPTS"
        "[base]"
    )

    atual = "base"

    # ========================================================
    # LEGENDAS COM DRAWTEXT
    # ========================================================

    for i, legenda in enumerate(
        legendas
    ):

        texto = escapar_drawtext(
            legenda["texto"]
        )

        saida_filtro = (
            f"leg{i}"
        )

        filtro = (
            f"[{atual}]"
            "drawtext="
            f"text='{texto}':"
            "fontcolor=white:"
            "fontsize=30:"
            "fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
            "x=(w-text_w)/2:"
            "y=h*0.70:"
            "line_spacing=8:"
            "box=1:"
            "boxcolor=black@0.68:"
            "boxborderw=18:"
            f"enable='between(t,"
            f"{legenda['inicio']:.3f},"
            f"{legenda['fim']:.3f})'"
            f"[{saida_filtro}]"
        )

        filtros.append(
            filtro
        )

        atual = saida_filtro

    # ========================================================
    # UPSCALE FINAL
    # ========================================================

    filtros.append(
        f"[{atual}]"
        f"scale={WIDTH}:{HEIGHT}:"
        "flags=fast_bilinear,"
        "format=yuv420p"
        "[final]"
    )

    filtro_final = ";".join(
        filtros
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

        "-filter_complex",
        filtro_final,

        "-map",
        "[final]",

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

    executar_ffmpeg(
        comando
    )


# ============================================================
# APAGAR ARQUIVO
# ============================================================

def apagar_arquivo(
    caminho
):

    try:

        if (
            caminho
            and
            os.path.exists(
                caminho
            )
        ):

            os.remove(
                caminho
            )

    except Exception as erro:

        print(
            "[AVISO LIMPEZA]",
            erro
        )


# ============================================================
# CRIAR VÍDEO
# ============================================================

def criar_video(
    destino
):

    if not PEXELS_API_KEY:

        raise RuntimeError(
            "Configure PEXELS_API_KEY no Railway."
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

        termo = DESTINOS.get(
            destino,
            destino
        )

        # ====================================================
        # 4 CLIPES
        # ====================================================

        for i in range(
            CLIP_COUNT
        ):

            print(
                f"\n[BUSCANDO VÍDEO "
                f"{i + 1}/{CLIP_COUNT}]"
            )

            url = buscar_video(
                termo
            )

            if not url:

                raise RuntimeError(
                    "Não foi encontrado vídeo "
                    f"para {destino}."
                )

            original = os.path.join(
                trabalho,
                f"original_{i}.mp4"
            )

            processado = os.path.join(
                trabalho,
                f"processado_{i}.mp4"
            )

            baixar_video(
                url,
                original
            )

            print(
                f"[PROCESSANDO CLIPE "
                f"{i + 1}/{CLIP_COUNT}]"
            )

            processar_clipe(
                original,
                processado
            )

            clipes.append(
                processado
            )

            apagar_arquivo(
                original
            )

        # ====================================================
        # CONCAT
        # ====================================================

        video_concat = os.path.join(
            trabalho,
            "video_concat.mp4"
        )

        print(
            "\n[CONCATENANDO]"
        )

        concatenar_clipes(
            clipes,
            video_concat
        )

        for clipe in clipes:

            apagar_arquivo(
                clipe
            )

        # ====================================================
        # ROTEIRO
        # ====================================================

        roteiro = criar_roteiro(
            destino
        )

        print(
            "\n[ROTEIRO]"
        )

        print(
            roteiro
        )

        # ====================================================
        # ÁUDIO
        # ====================================================

        audio = os.path.join(
            trabalho,
            "narracao.mp3"
        )

        print(
            "\n[GERANDO NARRAÇÃO]"
        )

        gerar_audio(
            roteiro,
            audio
        )

        # ====================================================
        # TEMPOS DAS LEGENDAS
        # ====================================================

        legendas = criar_tempos_legendas(
            roteiro
        )

        # ====================================================
        # SAÍDA
        # ====================================================

        nome_saida = (
            "mundo_afora_"
            +
            uuid.uuid4().hex
            +
            ".mp4"
        )

        saida = os.path.join(
            OUTPUT_DIR,
            nome_saida
        )

        # ====================================================
        # RENDER FINAL
        # ====================================================

        aplicar_video_final(
            video_concat,
            audio,
            legendas,
            saida
        )

        # ====================================================
        # VERIFICAÇÃO
        # ====================================================

        if not os.path.exists(
            saida
        ):

            raise RuntimeError(
                "Vídeo final não foi criado."
            )

        tamanho = os.path.getsize(
            saida
        )

        if tamanho < 100000:

            raise RuntimeError(
                "Vídeo final inválido."
            )

        print(
            "\n===================================="
        )

        print(
            "[VÍDEO CRIADO COM SUCESSO]"
        )

        print(
            saida
        )

        print(
            "Tamanho:",
            round(
                tamanho / 1024 / 1024,
                2
            ),
            "MB"
        )

        print(
            "===================================="
        )

        return saida

    finally:

        try:

            shutil.rmtree(
                trabalho,
                ignore_errors=True
            )

        except:
            pass


# ============================================================
# HOME
# ============================================================

@app.route(
    "/",
    methods=["GET", "POST"]
)
def index():

    erro = None
    sucesso = None
    arquivo = None

    if request.method == "POST":

        destino = request.form.get(
            "destino"
        )

        try:

            if not destino:

                raise RuntimeError(
                    "Selecione um destino."
                )

            caminho = criar_video(
                destino
            )

            nome = os.path.basename(
                caminho
            )

            sucesso = (
                "Vídeo criado com sucesso!"
            )

            arquivo = (
                "/download/"
                +
                nome
            )

        except Exception as erro_real:

            print(
                "\n[ERRO GERAL]"
            )

            print(
                repr(
                    erro_real
                )
            )

            erro = str(
                erro_real
            )

    return render_template_string(
        HTML,
        destinos=DESTINOS.keys(),
        erro=erro,
        sucesso=sucesso,
        arquivo=arquivo
    )


# ============================================================
# DOWNLOAD
# ============================================================

@app.route(
    "/download/<nome>"
)
def download(nome):

    caminho = os.path.join(
        OUTPUT_DIR,
        nome
    )

    if not os.path.exists(
        caminho
    ):

        return (
            "Arquivo não encontrado.",
            404
        )

    return send_file(
        caminho,
        as_attachment=True,
        download_name=nome,
        mimetype="video/mp4"
    )


# ============================================================
# HEALTH
# ============================================================

@app.route(
    "/health"
)
def health():

    return "OK"


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    porta = int(
        os.getenv(
            "PORT",
            "8080"
        )
    )

    app.run(
        host="0.0.0.0",
        port=porta
    )