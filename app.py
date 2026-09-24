import os
import random
import requests

from flask import Flask, request, render_template_string, send_file
from moviepy import ImageClip, TextClip, CompositeVideoClip, concatenate_videoclips
from moviepy import AudioFileClip

app = Flask(__name__)

# =========================
# CONFIGURAÇÕES
# =========================

LARGURA = 540
ALTURA = 960
FPS = 15

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

PASTA_VIDEOS = "videos"
PASTA_IMAGENS = "imagens"
PASTA_MUSICAS = "music"

# Criar somente as pastas geradas pelo programa.
# A pasta "music" deve existir no projeto.
os.makedirs(PASTA_VIDEOS, exist_ok=True)
os.makedirs(PASTA_IMAGENS, exist_ok=True)


# =========================
# FRASES
# =========================

def criar_frases(tema, estilo):

    frases = {
        "Motivacional": [
            f"Não desista de {tema}.",
            "Continue mesmo quando estiver difícil.",
            "O resultado vem para quem continua."
        ],

        "Dinheiro": [
            f"Quer aprender mais sobre {tema}?",
            "Conhecimento pode abrir novas oportunidades.",
            "Comece pequeno e evolua todos os dias."
        ],

        "Curiosidades": [
            f"Você sabia disso sobre {tema}?",
            "Essa informação pode surpreender você.",
            "Compartilhe com alguém que precisa saber."
        ],

        "Futebol": [
            f"Você sabia disso sobre {tema}?",
            "O futebol sempre tem uma história interessante.",
            "Você conhecia essa curiosidade?"
        ],

        "História": [
            f"Você conhece a história de {tema}?",
            "O passado guarda histórias incríveis.",
            "Essa história merece ser conhecida."
        ]
    }

    return frases.get(
        estilo,
        frases["Motivacional"]
    )


# =========================
# BUSCAR IMAGENS PEXELS
# =========================

def buscar_imagens(tema):

    if not PEXELS_API_KEY:
        raise Exception(
            "PEXELS_API_KEY não configurada."
        )

    url = "https://api.pexels.com/v1/search"

    headers = {
        "Authorization": PEXELS_API_KEY
    }

    params = {
        "query": tema,
        "per_page": 3,
        "orientation": "portrait"
    }

    resposta = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=20
    )

    if resposta.status_code != 200:
        raise Exception(
            f"Erro Pexels: {resposta.status_code}"
        )

    dados = resposta.json()

    fotos = dados.get("photos", [])

    if not fotos:
        raise Exception(
            "Nenhuma imagem encontrada."
        )

    imagens = []

    for foto in fotos:

        src = foto.get("src", {})

        link = (
            src.get("large2x")
            or src.get("large")
            or src.get("original")
        )

        if link:
            imagens.append(link)

    if not imagens:
        raise Exception(
            "Não foi possível encontrar imagens."
        )

    return imagens[:3]


# =========================
# PREPARAR IMAGEM
# =========================

def preparar_imagem(url, numero):

    caminho = os.path.join(
        PASTA_IMAGENS,
        f"imagem_{numero}.jpg"
    )

    resposta = requests.get(
        url,
        timeout=30
    )

    if resposta.status_code != 200:
        raise Exception(
            "Erro ao baixar imagem."
        )

    with open(caminho, "wb") as arquivo:
        arquivo.write(resposta.content)

    from PIL import Image

    imagem = Image.open(
        caminho
    ).convert("RGB")

    proporcao_desejada = (
        LARGURA / ALTURA
    )

    largura_original, altura_original = (
        imagem.size
    )

    proporcao_original = (
        largura_original / altura_original
    )

    # Cortar largura
    if proporcao_original > proporcao_desejada:

        nova_largura = int(
            altura_original *
            proporcao_desejada
        )

        esquerda = (
            largura_original -
            nova_largura
        ) // 2

        imagem = imagem.crop(
            (
                esquerda,
                0,
                esquerda + nova_largura,
                altura_original
            )
        )

    # Cortar altura
    else:

        nova_altura = int(
            largura_original /
            proporcao_desejada
        )

        topo = (
            altura_original -
            nova_altura
        ) // 2

        imagem = imagem.crop(
            (
                0,
                topo,
                largura_original,
                topo + nova_altura
            )
        )

    imagem = imagem.resize(
        (LARGURA, ALTURA)
    )

    imagem.save(
        caminho,
        "JPEG",
        quality=85,
        optimize=True
    )

    return caminho


# =========================
# ENCONTRAR MÚSICA
# =========================

def encontrar_musica():

    # Se a pasta não existir,
    # simplesmente cria o vídeo sem música.
    if not os.path.isdir(PASTA_MUSICAS):
        return None

    extensoes = [
        ".mp3",
        ".wav",
        ".m4a",
        ".aac"
    ]

    arquivos = []

    for nome in os.listdir(
        PASTA_MUSICAS
    ):

        caminho = os.path.join(
            PASTA_MUSICAS,
            nome
        )

        if not os.path.isfile(caminho):
            continue

        extensao = os.path.splitext(
            nome
        )[1].lower()

        if extensao in extensoes:
            arquivos.append(caminho)

    if not arquivos:
        return None

    return random.choice(arquivos)


# =========================
# CRIAR VÍDEO
# =========================

def criar_video(
    tema,
    estilo,
    duracao
):

    imagens_urls = buscar_imagens(
        tema
    )

    frases = criar_frases(
        tema,
        estilo
    )

    quantidade_cenas = len(
        imagens_urls
    )

    duracao_cena = (
        duracao /
        quantidade_cenas
    )

    cenas = []

    for i, url in enumerate(
        imagens_urls
    ):

        caminho_imagem = preparar_imagem(
            url,
            i
        )

        imagem = ImageClip(
            caminho_imagem
        ).with_duration(
            duracao_cena
        )

        # Zoom suave
        imagem = imagem.resized(
            lambda t:
            1 + (0.03 * t)
        )

        # Texto
        texto = TextClip(
            text=frases[i],
            font_size=42,
            color="white",
            stroke_color="black",
            stroke_width=3,
            method="caption",
            size=(460, 220),
            text_align="center"
        )

        texto = texto.with_duration(
            duracao_cena
        )

        texto = texto.with_position(
            ("center", "center")
        )

        cena = CompositeVideoClip(
            [
                imagem,
                texto
            ],
            size=(
                LARGURA,
                ALTURA
            )
        )

        cenas.append(cena)

    video = concatenate_videoclips(
        cenas,
        method="compose"
    )

    # =========================
    # ADICIONAR MÚSICA
    # =========================

    caminho_musica = encontrar_musica()

    audio = None

    if caminho_musica:

        try:

            audio = AudioFileClip(
                caminho_musica
            )

            # Cortar música se ela for
            # maior que o vídeo.
            if audio.duration > duracao:

                audio = audio.subclipped(
                    0,
                    duracao
                )

            # Volume da música
            audio = audio.with_volume_scaled(
                0.20
            )

            video = video.with_audio(
                audio
            )

            print(
                "Música adicionada:",
                caminho_musica
            )

        except Exception as erro:

            print(
                "Erro ao adicionar música:",
                erro
            )

            audio = None

    else:

        print(
            "Nenhuma música encontrada. "
            "Vídeo será criado sem música."
        )

    # =========================
    # SALVAR VÍDEO
    # =========================

    nome_arquivo = (
        "reel_"
        + str(
            random.randint(
                10000,
                99999
            )
        )
        + ".mp4"
    )

    caminho_video = os.path.join(
        PASTA_VIDEOS,
        nome_arquivo
    )

    video.write_videofile(
        caminho_video,
        fps=FPS,
        codec="libx264",
        audio=audio is not None,
        preset="ultrafast",
        threads=1,
        logger=None
    )

    # Fechar recursos
    try:
        video.close()
    except:
        pass

    try:
        if audio:
            audio.close()
    except:
        pass

    return caminho_video


# =========================
# INTERFACE
# =========================

HTML = """
<!DOCTYPE html>

<html lang="pt-br">

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>Reel Maker</title>

<style>

body {
    background: #111;
    color: white;
    font-family: Arial, sans-serif;
    text-align: center;
    padding: 30px;
}

.container {
    max-width: 500px;
    margin: auto;
}

input,
select,
button {

    width: 100%;
    padding: 15px;
    margin: 10px 0;

    border-radius: 8px;
    border: none;

    font-size: 16px;
}

button {

    background: #00c853;
    color: white;

    font-weight: bold;

    cursor: pointer;
}

button:hover {
    opacity: 0.9;
}

.info {

    margin-top: 20px;
    padding: 15px;

    background: #222;

    border-radius: 10px;
}

</style>

</head>

<body>

<div class="container">

<h1>🎬 Reel Maker</h1>

<p>
Crie vídeos para Reels e TikTok automaticamente.
</p>

<form method="POST">

<input
    type="text"
    name="tema"
    placeholder="Digite o tema do vídeo"
    required
>

<select name="estilo">

<option value="Motivacional">
Motivacional
</option>

<option value="Dinheiro">
Dinheiro
</option>

<option value="Curiosidades">
Curiosidades
</option>

<option value="Futebol">
Futebol
</option>

<option value="História">
História
</option>

</select>

<select name="duracao">

<option value="10">
10 segundos
</option>

<option value="15">
15 segundos
</option>

<option value="30">
30 segundos
</option>

</select>

<button type="submit">
🚀 Criar Reel
</button>

</form>

{% if mensagem %}

<div class="info">

<p>{{ mensagem }}</p>

{% if video %}

<a href="/download/{{ video }}">

<button>
⬇️ Baixar vídeo
</button>

</a>

{% endif %}

</div>

{% endif %}

</div>

</body>

</html>
"""


# =========================
# ROTA PRINCIPAL
# =========================

@app.route(
    "/",
    methods=["GET", "POST"]
)
def index():

    mensagem = ""
    video = None

    if request.method == "POST":

        tema = request.form.get(
            "tema",
            ""
        ).strip()

        estilo = request.form.get(
            "estilo",
            "Motivacional"
        )

        try:

            duracao = int(
                request.form.get(
                    "duracao",
                    10
                )
            )

        except:

            duracao = 10

        if not tema:

            mensagem = (
                "Digite um tema."
            )

        else:

            try:

                mensagem = (
                    "Criando seu vídeo..."
                )

                caminho = criar_video(
                    tema,
                    estilo,
                    duracao
                )

                video = os.path.basename(
                    caminho
                )

                mensagem = (
                    "✅ Vídeo criado "
                    "com sucesso!"
                )

            except Exception as erro:

                mensagem = (
                    "❌ Erro: "
                    + str(erro)
                )

                print(
                    "ERRO:",
                    erro
                )

    return render_template_string(
        HTML,
        mensagem=mensagem,
        video=video
    )


# =========================
# DOWNLOAD
# =========================

@app.route(
    "/download/<nome>"
)
def download(nome):

    caminho = os.path.join(
        PASTA_VIDEOS,
        nome
    )

    if not os.path.exists(caminho):

        return (
            "Vídeo não encontrado.",
            404
        )

    return send_file(
        caminho,
        as_attachment=True
    )


# =========================
# SERVIDOR
# =========================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                8080
            )
        )
    )