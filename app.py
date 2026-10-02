import os
import random
import uuid
import asyncio
import shutil
import subprocess
import html
import textwrap

import requests
from flask import Flask, request, render_template_string, send_file
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
import edge_tts


app = Flask(__name__)


# ============================================================
# CONFIGURAÇÕES
# ============================================================

WIDTH = 1080
HEIGHT = 1920

# Processamento interno mais leve
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
OUTPUT_DIR = "outputs"
TEMP_DIR = "temp"

os.makedirs(VIDEO_DIR, exist_ok=True)
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
    margin-bottom: 10px;
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
    background: #fff;
    color: #111;
    font-weight: bold;
    cursor: pointer;
}

button:hover {
    opacity: .9;
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

    print(" ".join(str(x) for x in comando))

    resultado = subprocess.run(
        comando,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if resultado.returncode != 0:

        print("\n[ERRO FFMPEG]")

        print("RETURN CODE:", resultado.returncode)

        print(resultado.stderr)

        raise RuntimeError(
            "FFmpeg falhou:\n\n" +
            resultado.stderr[-5000:]
        )

    return resultado


# ============================================================
# BUSCAR VÍDEO NO PEXELS
# ============================================================

def buscar_video(termo):

    if not PEXELS_API_KEY:
        raise RuntimeError(
            "PEXELS_API_KEY não configurada."
        )

    url = "https://api.pexels.com/videos/search"

    headers = {
        "Authorization": PEXELS_API_KEY
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

    if resposta.status_code != 200:

        raise RuntimeError(
            f"Pexels retornou HTTP {resposta.status_code}"
        )

    dados = resposta.json()

    videos = dados.get("videos", [])

    if not videos:
        return None

    # Embaralha para evitar sempre os mesmos vídeos
    random.shuffle(videos)

    for video in videos:

        arquivos = video.get("video_files", [])

        candidatos = []

        for arquivo in arquivos:

            largura = arquivo.get("width") or 0
            altura = arquivo.get("height") or 0
            link = arquivo.get("link")

            if not link:
                continue

            # Preferência por vertical
            if altura >= largura:
                candidatos.append(
                    (
                        abs(
                            (altura / max(largura, 1))
                            - (16 / 9)
                        ),
                        link,
                        largura,
                        altura
                    )
                )

        if candidatos:

            candidatos.sort(
                key=lambda x: x[0]
            )

            return candidatos[0][1]

    # Fallback para qualquer vídeo
    for video in videos:

        arquivos = video.get("video_files", [])

        if arquivos:

            arquivos.sort(
                key=lambda x:
                (x.get("width") or 0) *
                (x.get("height") or 0),
                reverse=True
            )

            link = arquivos[0].get("link")

            if link:
                return link

    return None


# ============================================================
# BAIXAR VÍDEO
# ============================================================

def baixar_video(url, caminho):

    print("[DOWNLOAD]", url)

    resposta = requests.get(
        url,
        stream=True,
        timeout=120
    )

    resposta.raise_for_status()

    with open(caminho, "wb") as arquivo:

        for bloco in resposta.iter_content(
            chunk_size=1024 * 1024
        ):

            if bloco:
                arquivo.write(bloco)

    tamanho = os.path.getsize(caminho)

    print(
        "[OK DOWNLOAD]",
        round(tamanho / 1024 / 1024, 2),
        "MB"
    )


# ============================================================
# PROCESSAR CLIPE
# ============================================================

def processar_clipe(entrada, saida):

    comando = [
        FFMPEG,

        "-hide_banner",
        "-loglevel", "error",
        "-y",

        "-i", entrada,

        "-vf",
        (
            f"scale={PROCESS_WIDTH}:{PROCESS_HEIGHT}:"
            "force_original_aspect_ratio=increase,"
            f"crop={PROCESS_WIDTH}:{PROCESS_HEIGHT}"
        ),

        "-an",

        "-t", str(CLIP_DURATION),

        "-r", str(FPS),

        "-c:v", "libx264",

        "-preset", "ultrafast",

        "-crf", "30",

        "-pix_fmt", "yuv420p",

        saida
    ]

    executar_ffmpeg(comando)


# ============================================================
# CONVERTER CLIPES PARA 1080x1920
# ============================================================

def preparar_clipe_final(entrada, saida):

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
            f"crop={WIDTH}:{HEIGHT}"
        ),

        "-an",

        "-r", str(FPS),

        "-c:v", "libx264",

        "-preset", "ultrafast",

        "-crf", "31",

        "-pix_fmt", "yuv420p",

        saida
    ]

    executar_ffmpeg(comando)


# ============================================================
# CONCATENAR CLIPES
# ============================================================

def concatenar_clipes(clipes, saida):

    lista = os.path.join(
        TEMP_DIR,
        f"lista_{uuid.uuid4().hex}.txt"
    )

    with open(
        lista,
        "w",
        encoding="utf-8"
    ) as arquivo:

        for clipe in clipes:

            caminho = os.path.abspath(
                clipe
            ).replace("\\", "/")

            arquivo.write(
                "file '" +
                caminho.replace("'", "'\\''") +
                "'\n"
            )

    comando = [

        FFMPEG,

        "-hide_banner",
        "-loglevel", "error",
        "-y",

        "-f", "concat",

        "-safe", "0",

        "-i", lista,

        "-c", "copy",

        "-t", str(FINAL_DURATION),

        saida
    ]

    try:

        executar_ffmpeg(comando)

    finally:

        try:
            os.remove(lista)
        except:
            pass


# ============================================================
# ROTEIRO
# ============================================================

def criar_roteiro(destino):

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

async def gerar_audio_async(texto, arquivo):

    comunicador = edge_tts.Communicate(
        texto,
        VOICE,
        rate=VOICE_RATE
    )

    await comunicador.save(arquivo)


def gerar_audio(texto, arquivo):

    asyncio.run(
        gerar_audio_async(
            texto,
            arquivo
        )
    )


# ============================================================
# FONTE
# ============================================================

def encontrar_fonte():

    fontes = [

        "/usr/share/fonts/truetype/dejavu/"
        "DejaVuSans-Bold.ttf",

        "/usr/share/fonts/truetype/liberation2/"
        "LiberationSans-Bold.ttf",

        "/usr/share/fonts/truetype/dejavu/"
        "DejaVuSans.ttf"
    ]

    for fonte in fontes:

        if os.path.exists(fonte):
            return fonte

    return None


# ============================================================
# CRIAR IMAGEM DE LEGENDA
# ============================================================

def criar_imagem_legenda(texto, arquivo):

    imagem = Image.new(
        "RGBA",
        (WIDTH, HEIGHT),
        (0, 0, 0, 0)
    )

    desenho = ImageDraw.Draw(imagem)

    fonte_path = encontrar_fonte()

    if fonte_path:

        fonte = ImageFont.truetype(
            fonte_path,
            54
        )

    else:

        fonte = ImageFont.load_default()

    # Quebra automática
    linhas = textwrap.wrap(
        texto,
        width=30
    )

    textos = []

    for linha in linhas:

        caixa = desenho.textbbox(
            (0, 0),
            linha,
            font=fonte
        )

        largura = caixa[2] - caixa[0]
        altura = caixa[3] - caixa[1]

        textos.append(
            (
                linha,
                largura,
                altura
            )
        )

    espacamento = 12

    altura_total = sum(
        item[2]
        for item in textos
    ) + (
        max(len(textos) - 1, 0)
        * espacamento
    )

    # Posição aproximada no centro inferior
    y = int(
        HEIGHT * 0.70
        - altura_total / 2
    )

    padding_x = 45
    padding_y = 30

    largura_max = max(
        item[1]
        for item in textos
    )

    caixa_esquerda = (
        WIDTH // 2
        - largura_max // 2
        - padding_x
    )

    caixa_direita = (
        WIDTH // 2
        + largura_max // 2
        + padding_x
    )

    caixa_cima = y - padding_y

    caixa_baixo = (
        y
        + altura_total
        + padding_y
    )

    # Fundo preto transparente
    desenho.rounded_rectangle(
        (
            caixa_esquerda,
            caixa_cima,
            caixa_direita,
            caixa_baixo
        ),
        radius=25,
        fill=(0, 0, 0, 175)
    )

    for linha, largura, altura in textos:

        x = (
            WIDTH // 2
            - largura // 2
        )

        # Sombra
        desenho.text(
            (x + 3, y + 3),
            linha,
            font=fonte,
            fill=(0, 0, 0, 255)
        )

        # Texto
        desenho.text(
            (x, y),
            linha,
            font=fonte,
            fill=(255, 255, 255, 255)
        )

        y += altura + espacamento

    imagem.save(
        arquivo,
        "PNG"
    )


# ============================================================
# DIVIDIR TEXTO
# ============================================================

def dividir_texto(texto, quantidade=8):

    palavras = texto.split()

    if not palavras:
        return []

    total_caracteres = len(texto)

    alvo = max(
        1,
        total_caracteres / quantidade
    )

    partes = []

    atual = []
    tamanho_atual = 0

    for palavra in palavras:

        atual.append(palavra)

        tamanho_atual += (
            len(palavra) + 1
        )

        if (
            tamanho_atual >= alvo
            and len(partes) < quantidade - 1
        ):

            partes.append(
                " ".join(atual)
            )

            atual = []
            tamanho_atual = 0

    if atual:
        partes.append(
            " ".join(atual)
        )

    while len(partes) < quantidade:

        partes.append(
            partes[-1]
        )

    return partes[:quantidade]


# ============================================================
# CRIAR LEGENDAS
# ============================================================

def criar_legenda_pngs(
    texto,
    pasta
):

    os.makedirs(
        pasta,
        exist_ok=True
    )

    partes = dividir_texto(
        texto,
        8
    )

    # Distribuição baseada no número de caracteres
    tamanhos = [
        max(len(x), 1)
        for x in partes
    ]

    total = sum(tamanhos)

    legendas = []

    tempo_atual = 0

    for i, parte in enumerate(partes):

        duracao = (
            FINAL_DURATION
            * tamanhos[i]
            / total
        )

        inicio = tempo_atual

        fim = (
            tempo_atual
            + duracao
        )

        arquivo = os.path.join(
            pasta,
            f"legenda_{i}.png"
        )

        criar_imagem_legenda(
            parte,
            arquivo
        )

        legendas.append(
            {
                "arquivo": arquivo,
                "inicio": inicio,
                "fim": fim
            }
        )

        print(
            f"[LEGENDA {i + 1}/8]"
        )

        print(
            inicio,
            "->",
            fim
        )

        tempo_atual = fim

    return legendas


# ============================================================
# APLICAR TODAS AS LEGENDAS
# UMA ÚNICA VEZ
# ============================================================

def aplicar_todas_legendas(
    video_entrada,
    legendas,
    saida
):

    print("\n[APLICANDO TODAS AS LEGENDAS DE UMA VEZ]")

    filtros = []

    # Vídeo principal
    filtros.append(
        "[0:v]setpts=PTS-STARTPTS[base0]"
    )

    entrada_atual = "base0"

    # Cada PNG vira uma entrada
    for i, legenda in enumerate(legendas):

        indice_video = i + 1

        nome_legenda = f"leg{i}"

        nome_saida = f"base{i + 1}"

        filtros.append(
            f"[{indice_video}:v]"
            "format=rgba,"
            "setpts=PTS-STARTPTS,"
            f"trim=duration={FINAL_DURATION},"
            "setpts=PTS-STARTPTS"
            f"[{nome_legenda}]"
        )

        filtros.append(
            f"[{entrada_atual}]"
            f"[{nome_legenda}]"
            "overlay="
            "0:0:"
            "eof_action=repeat:"
            "shortest=0:"
            f"enable='between(t,{legenda['inicio']:.3f},{legenda['fim']:.3f})'"
            f"[{nome_saida}]"
        )

        entrada_atual = nome_saida

    filtro_final = ";".join(
        filtros
    )

    comando = [

        FFMPEG,

        "-hide_banner",
        "-loglevel", "error",
        "-y",

        "-i",
        video_entrada
    ]

    # Adiciona todos os PNGs
    for legenda in legendas:

        comando.extend(
            [
                "-loop",
                "1",

                "-framerate",
                str(FPS),

                "-i",
                legenda["arquivo"]
            ]
        )

    comando.extend(
        [

            "-filter_complex",
            filtro_final,

            "-map",
            f"[{entrada_atual}]",

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
# FINALIZAR VÍDEO
# ============================================================

def finalizar_video(
    video,
    audio,
    legendas,
    saida
):

    print("\n[ADICIONANDO NARRAÇÃO]")

    video_audio = os.path.join(
        OUTPUT_DIR,
        f"video_audio_{uuid.uuid4().hex}.mp4"
    )

    comando_audio = [

        FFMPEG,

        "-hide_banner",
        "-loglevel", "error",
        "-y",

        "-i",
        video,

        "-i",
        audio,

        "-map",
        "0:v:0",

        "-map",
        "1:a:0",

        # Não reencoda o vídeo aqui
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

    try:

        print(
            "\n[APLICANDO LEGENDAS]"
        )

        aplicar_todas_legendas(
            video_audio,
            legendas,
            saida
        )

    finally:

        try:
            os.remove(
                video_audio
            )
        except:
            pass


# ============================================================
# LIMPAR ARQUIVO
# ============================================================

def apagar_arquivo(caminho):

    try:

        if caminho and os.path.exists(caminho):

            os.remove(caminho)

    except Exception as erro:

        print(
            "[AVISO] Não foi possível remover:",
            caminho,
            erro
        )


# ============================================================
# CRIAR VÍDEO
# ============================================================

def criar_video(destino):

    if not PEXELS_API_KEY:

        raise RuntimeError(
            "Configure a variável PEXELS_API_KEY no Railway."
        )

    trabalho = os.path.join(
        TEMP_DIR,
        uuid.uuid4().hex
    )

    os.makedirs(
        trabalho,
        exist_ok=True
    )

    downloads = []
    clipes_processados = []
    clipes_finais = []

    try:

        termo = DESTINOS.get(
            destino,
            destino
        )

        # ====================================================
        # 1. DOWNLOAD DOS 4 VÍDEOS
        # ====================================================

        for i in range(CLIP_COUNT):

            print(
                f"\n[BUSCANDO VÍDEO {i + 1}/{CLIP_COUNT}]"
            )

            url = buscar_video(
                termo
            )

            if not url:

                raise RuntimeError(
                    f"Não foi encontrado vídeo para {destino}."
                )

            original = os.path.join(
                trabalho,
                f"original_{i}.mp4"
            )

            processado = os.path.join(
                trabalho,
                f"processado_{i}.mp4"
            )

            final = os.path.join(
                trabalho,
                f"final_{i}.mp4"
            )

            baixar_video(
                url,
                original
            )

            downloads.append(
                original
            )

            # =================================================
            # 2. PROCESSAMENTO LEVE
            # =================================================

            print(
                f"[PROCESSANDO CLIPE {i + 1}/{CLIP_COUNT}]"
            )

            processar_clipe(
                original,
                processado
            )

            clipes_processados.append(
                processado
            )

            apagar_arquivo(
                original
            )

            # =================================================
            # 3. CONVERSÃO FINAL PARA 1080x1920
            # =================================================

            print(
                f"[PREPARANDO CLIPE FINAL {i + 1}/{CLIP_COUNT}]"
            )

            preparar_clipe_final(
                processado,
                final
            )

            clipes_finais.append(
                final
            )

            apagar_arquivo(
                processado
            )

        # ====================================================
        # 4. CONCATENAR
        # ====================================================

        video_concat = os.path.join(
            trabalho,
            "video_concat.mp4"
        )

        print(
            "\n[CONCATENANDO CLIPES]"
        )

        concatenar_clipes(
            clipes_finais,
            video_concat
        )

        # Liberar os clipes individuais
        for clipe in clipes_finais:

            apagar_arquivo(
                clipe
            )

        # ====================================================
        # 5. ROTEIRO
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
        # 6. ÁUDIO
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
        # 7. LEGENDAS
        # ====================================================

        pasta_legendas = os.path.join(
            trabalho,
            "legendas"
        )

        legendas = criar_legenda_pngs(
            roteiro,
            pasta_legendas
        )

        # ====================================================
        # 8. SAÍDA
        # ====================================================

        nome_saida = (
            "mundo_afora_"
            + uuid.uuid4().hex
            + ".mp4"
        )

        saida = os.path.join(
            OUTPUT_DIR,
            nome_saida
        )

        # ====================================================
        # 9. FINALIZAR
        # ====================================================

        finalizar_video(
            video_concat,
            audio,
            legendas,
            saida
        )

        # ====================================================
        # VERIFICAR
        # ====================================================

        if not os.path.exists(saida):

            raise RuntimeError(
                "O vídeo final não foi criado."
            )

        tamanho = os.path.getsize(
            saida
        )

        if tamanho < 100000:

            raise RuntimeError(
                "O vídeo final ficou inválido ou muito pequeno."
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

        # ====================================================
        # LIMPEZA
        # ====================================================

        try:

            if os.path.exists(trabalho):

                shutil.rmtree(
                    trabalho,
                    ignore_errors=True
                )

        except Exception as erro:

            print(
                "[AVISO LIMPEZA]",
                erro
            )


# ============================================================
# ROTA PRINCIPAL
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
                "Vídeo criado com sucesso! "
                "Clique abaixo para baixar."
            )

            arquivo = (
                "/download/"
                + nome
            )

        except Exception as e:

            print(
                "\n[ERRO GERAL]"
            )

            print(
                repr(e)
            )

            erro = str(e)

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

    if not os.path.exists(caminho):

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
# HEALTH CHECK
# ============================================================

@app.route(
    "/health"
)
def health():

    return "OK"


# ============================================================
# RAILWAY
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