from flask import Flask, request, send_file, render_template_string
from moviepy import ImageClip, TextClip, CompositeVideoClip, concatenate_videoclips
import requests
import os
import uuid
from PIL import Image

app = Flask(__name__)

VIDEO_DIR = "videos"
IMAGE_DIR = "images"

os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(IMAGE_DIR, exist_ok=True)

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

WIDTH = 540
HEIGHT = 960
FPS = 15


HTML = """
<!DOCTYPE html>
<html lang="pt-BR">

<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>Reel Maker</title>

<style>

body {
    margin: 0;
    padding: 20px;
    background: #111;
    color: white;
    font-family: Arial, sans-serif;
}

.box {
    max-width: 500px;
    margin: auto;
    text-align: center;
}

h1 {
    margin-bottom: 30px;
}

input,
select,
button {

    width: 100%;
    padding: 15px;
    margin: 8px 0;
    box-sizing: border-box;
    border: none;
    border-radius: 8px;
    font-size: 16px;
}

button {
    background: #ff0050;
    color: white;
    font-weight: bold;
    cursor: pointer;
}

button:hover {
    opacity: 0.85;
}

.resultado {
    margin-top: 25px;
}

</style>

</head>

<body>

<div class="box">

<h1>🎬 REEL MAKER</h1>

<form action="/gerar" method="POST">

<input
    type="text"
    name="tema"
    placeholder="Digite o tema do vídeo"
    required
>

<select name="estilo">

<option value="motivacional">
🔥 Motivacional
</option>

<option value="dinheiro">
💰 Dinheiro
</option>

<option value="curiosidades">
🤯 Curiosidades
</option>

<option value="futebol">
⚽ Futebol
</option>

<option value="historia">
📖 História
</option>

</select>

<select name="duracao">

<option value="10">
10 segundos - teste
</option>

<option value="15">
15 segundos
</option>

<option value="30">
30 segundos
</option>

</select>

<button type="submit">
🚀 GERAR REEL
</button>

</form>

{% if video %}

<div class="resultado">

<h2>✅ Reel criado!</h2>

<a href="/baixar/{{ video }}">

<button>
⬇️ BAIXAR REEL
</button>

</a>

</div>

{% endif %}

{% if erro %}

<div class="resultado">

<h2>❌ Erro</h2>

<p>{{ erro }}</p>

</div>

{% endif %}

</div>

</body>

</html>
"""


@app.route("/")
def home():
    return render_template_string(HTML)


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

    arquivos = []

    for foto in fotos:

        imagem_url = foto["src"]["portrait"]

        nome = f"{uuid.uuid4().hex}.jpg"

        caminho = os.path.join(
            IMAGE_DIR,
            nome
        )

        resposta_imagem = requests.get(
            imagem_url,
            timeout=20
        )

        if resposta_imagem.status_code != 200:
            continue

        with open(caminho, "wb") as arquivo:
            arquivo.write(
                resposta_imagem.content
            )

        arquivos.append(caminho)

    if not arquivos:
        raise Exception(
            "Não foi possível baixar as imagens."
        )

    return arquivos


def preparar_imagem(caminho):

    imagem = Image.open(caminho)

    imagem = imagem.convert("RGB")

    proporcao_original = (
        imagem.width / imagem.height
    )

    proporcao_video = (
        WIDTH / HEIGHT
    )

    if proporcao_original > proporcao_video:

        nova_altura = HEIGHT

        nova_largura = int(
            nova_altura *
            proporcao_original
        )

    else:

        nova_largura = WIDTH

        nova_altura = int(
            nova_largura /
            proporcao_original
        )

    imagem = imagem.resize(
        (nova_largura, nova_altura)
    )

    esquerda = (
        nova_largura - WIDTH
    ) // 2

    cima = (
        nova_altura - HEIGHT
    ) // 2

    imagem = imagem.crop(
        (
            esquerda,
            cima,
            esquerda + WIDTH,
            cima + HEIGHT
        )
    )

    imagem.save(
        caminho,
        quality=80,
        optimize=True
    )


def criar_frases(tema, estilo):

    frases = {

        "motivacional": [
            f"Você pode mudar sua vida com {tema}.",
            "Comece hoje.",
            "Não desista dos seus objetivos."
        ],

        "dinheiro": [
            f"Quer aprender sobre {tema}?",
            "Conhecimento pode abrir novas oportunidades.",
            "Comece estudando e evoluindo."
        ],

        "curiosidades": [
            f"Você sabia disso sobre {tema}?",
            "Essa informação pode surpreender você.",
            "Agora você já sabe!"
        ],

        "futebol": [
            f"Você conhece essa história do {tema}?",
            "O futebol sempre tem grandes histórias.",
            "Compartilhe com quem gosta de futebol."
        ],

        "historia": [
            f"Conheça essa história sobre {tema}.",
            "O passado ajuda a entender o presente.",
            "Você já conhecia essa história?"
        ]

    }

    return frases.get(
        estilo,
        [
            f"Você conhece {tema}?",
            "Continue acompanhando.",
            "Até o próximo vídeo!"
        ]
    )


@app.route("/gerar", methods=["POST"])
def gerar():

    tema = request.form.get(
        "tema",
        "Meu vídeo"
    )

    estilo = request.form.get(
        "estilo",
        "motivacional"
    )

    duracao = int(
        request.form.get(
            "duracao",
            10
        )
    )

    nome = f"{uuid.uuid4().hex}.mp4"

    caminho_video = os.path.join(
        VIDEO_DIR,
        nome
    )

    clips = []

    try:

        imagens = buscar_imagens(tema)

        frases = criar_frases(
            tema,
            estilo
        )

        tempo_por_imagem = (
            duracao / len(imagens)
        )

        for i, caminho_imagem in enumerate(imagens):

            preparar_imagem(
                caminho_imagem
            )

            clip = ImageClip(
                caminho_imagem
            )

            clip = clip.with_duration(
                tempo_por_imagem
            )

            # Zoom suave
            clip = clip.resized(
                lambda t: 1 + (0.03 * t)
            )

            clip = clip.with_position(
                "center"
            )

            texto = TextClip(

                text=frases[
                    i % len(frases)
                ],

                font_size=38,

                color="white",

                size=(460, 180),

                method="caption"

            )

            texto = texto.with_duration(
                tempo_por_imagem
            )

            texto = texto.with_position(
                ("center", 680)
            )

            cena = CompositeVideoClip(
                [
                    clip,
                    texto
                ],
                size=(WIDTH, HEIGHT)
            )

            clips.append(cena)

        video = concatenate_videoclips(
            clips,
            method="compose"
        )

        video.write_videofile(

            caminho_video,

            fps=FPS,

            codec="libx264",

            audio=False,

            preset="ultrafast",

            threads=1,

            logger=None

        )

        video.close()

        for clip in clips:
            clip.close()

        return render_template_string(
            HTML,
            video=nome
        )

    except Exception as e:

        for clip in clips:

            try:
                clip.close()
            except:
                pass

        return render_template_string(
            HTML,
            erro=str(e)
        )


@app.route("/baixar/<nome>")
def baixar(nome):

    caminho = os.path.join(
        VIDEO_DIR,
        nome
    )

    if not os.path.exists(caminho):

        return (
            "Vídeo não encontrado.",
            404
        )

    return send_file(

        caminho,

        as_attachment=True,

        download_name="reel.mp4"

    )


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