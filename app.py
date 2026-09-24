import os
import random
import requests

from flask import Flask, request, render_template_string, send_file
from gtts import gTTS

from moviepy import (
    ImageClip,
    concatenate_videoclips,
    AudioFileClip
)

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
PASTA_AUDIO = "audios"

os.makedirs(PASTA_VIDEOS, exist_ok=True)
os.makedirs(PASTA_IMAGENS, exist_ok=True)
os.makedirs(PASTA_AUDIO, exist_ok=True)


# =========================
# CRIAR ROTEIRO
# =========================

def criar_roteiro(tema, estilo):

    roteiros = {

        "Motivacional": [
            f"Você está buscando melhorar em {tema}.",
            f"Muitas pessoas desistem de {tema} antes de conseguir resultados.",
            "Mas a diferença está em continuar mesmo quando fica difícil.",
            "Dê um passo de cada vez e não pare."
        ],

        "Dinheiro": [
            f"Você quer entender melhor {tema}?",
            "Antes de buscar resultados, é importante aprender e entender como as coisas funcionam.",
            "Pequenas decisões podem fazer diferença ao longo do tempo.",
            "Busque conhecimento e tome decisões com responsabilidade."
        ],

        "Curiosidades": [
            f"Você sabia que existem curiosidades incríveis sobre {tema}?",
            "Algumas informações são tão interessantes que poucas pessoas conhecem.",
            f"Quando você pesquisa mais sobre {tema}, descobre detalhes surpreendentes.",
            "Agora você já conhece mais uma curiosidade."
        ],

        "Futebol": [
            f"Hoje vamos falar sobre {tema}.",
            "O futebol é cheio de histórias, números e momentos que marcaram gerações.",
            f"E quando pesquisamos a história de {tema}, encontramos fatos muito interessantes.",
            "Você já conhecia essa história?"
        ],

        "História": [
            f"Hoje vamos conhecer um pouco da história de {tema}.",
            "Ao longo dos anos, muitos acontecimentos ajudaram a construir essa história.",
            f"Conhecer o passado de {tema} ajuda a entender melhor o presente.",
            "Essa é mais uma história que merece ser lembrada."
        ]
    }

    return roteiros.get(
        estilo,
        roteiros["Motivacional"]
    )


# =========================
# BUSCAR IMAGENS
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
        "per_page": 4,
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

    return imagens[:4]


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

    # Corta as laterais
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

    # Corta em cima/baixo
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
# GERAR NARRAÇÃO
# =========================

def criar_narracao(roteiro):

    texto = " ".join(roteiro)

    caminho_audio = os.path.join(
        PASTA_AUDIO,
        "narracao.mp3"
    )

    print("Gerando narração...")

    voz = gTTS(
        text=texto,
        lang="pt",
        slow=False
    )

    voz.save(
        caminho_audio
    )

    if not os.path.exists(
        caminho_audio
    ):
        raise Exception(
            "Falha ao gerar narração."
        )

    return caminho_audio


# =========================
# CRIAR VÍDEO
# =========================

def criar_video(
    tema,
    estilo,
    duracao
):

    # Cria roteiro
    roteiro = criar_roteiro(
        tema,
        estilo
    )

    # Busca imagens
    imagens_urls = buscar_imagens(
        tema
    )

    # Gera voz
    caminho_audio = criar_narracao(
        roteiro
    )

    audio = AudioFileClip(
        caminho_audio
    )

    # A duração real da voz
    # determina a duração final.
    duracao_audio = float(
        audio.duration
    )

    duracao_final = max(
        float(duracao),
        duracao_audio
    )

    # Evita vídeos muito maiores
    # que o escolhido pelo usuário.
    if duracao_final > duracao + 5:
        duracao_final = float(
            duracao + 5
        )

    quantidade = len(
        imagens_urls
    )

    duracao_cena = (
        duracao_final /
        quantidade
    )

    cenas = []

    # =========================
    # CRIAR CENAS
    # =========================

    for i, url in enumerate(
        imagens_urls
    ):

        caminho = preparar_imagem(
            url,
            i
        )

        imagem = ImageClip(
            caminho
        ).with_duration(
            duracao_cena
        )

        # Zoom suave
        imagem = imagem.resized(
            lambda t:
            1 + (0.03 * t)
        )

        cenas.append(
            imagem
        )

    # Junta as imagens
    video = concatenate_videoclips(
        cenas,
        method="compose"
    )

    # =========================
    # ADICIONAR NARRAÇÃO
    # =========================

    if audio.duration > video.duration:

        audio = audio.subclipped(
            0,
            video.duration
        )

    video = video.with_audio(
        audio
    )

    # =========================
    # SALVAR
    # =========================

    nome = (
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
        nome
    )

    print(
        "Renderizando vídeo..."
    )

    video.write_videofile(
        caminho_video,
        fps=FPS,
        codec="libx264",
        audio=True,
        preset="ultrafast",
        threads=1,
        logger=None
    )

    try:
        video.close()
    except:
        pass

    try:
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
Vídeos com imagens e narração automática.
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
🎙️ Criar Reel
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
                    "🎙️ Criando roteiro, "
                    "narração e vídeo..."
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
                    "✅ Reel criado "
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