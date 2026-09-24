from flask import Flask, request, send_file, render_template_string
from moviepy import ImageClip, ColorClip, TextClip, CompositeVideoClip, concatenate_videoclips
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


HTML = """
<!DOCTYPE html>
<html lang="pt-BR">

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>Reel Maker</title>

<style>

body {
    margin: 0;
    padding: 20px;
    background: #111;
    color: white;
    font-family: Arial;
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
            "PEXELS_API_KEY não configurada no Railway."
        )

    url = "https://api.pexels.com/v1/search"

    headers = {

        "Authorization":
        PEXELS_API_KEY

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

            f"Erro Pexels: "
            f"{resposta.status_code}"

        )

    dados = resposta.json()

    fotos = dados.get("photos", [])

    if not fotos:

        raise Exception(
            "Nenhuma imagem encontrada para esse tema."
        )

    arquivos = []

    for foto in fotos:

        imagem_url = foto["src"]["portrait"]

        nome = (
            f"{uuid.uuid4().hex}.jpg"
        )

        caminho = os.path.join(

            IMAGE_DIR,

            nome

        )

        imagem = requests.get(

            imagem_url,

            timeout=20

        )

        if imagem.status_code != 200:

            continue

        with open(caminho, "wb") as arquivo:

            arquivo.write(imagem.content)

        arquivos.append(caminho)

    if not arquivos:

        raise Exception(
            "Não foi possível baixar as imagens."
        )

    return arquivos


def preparar_imagem(caminho):

    imagem = Image.open(caminho)

    imagem = imagem.convert("RGB")

    largura = 540

    altura = 960

    proporcao_original = (
        imagem.width / imagem.height
    )

    proporcao_video = (
        largura / altura
    )

    if proporcao_original > proporcao_video:

        nova_altura = altura

        nova_largura = int(
            nova_altura *
            proporcao_original
        )

    else:

        nova_largura = largura

        nova_altura = int(
            nova_largura /
            proporcao_original
        )

    imagem = imagem.resize(
        (nova_largura, nova_altura)
    )

    esquerda = (
        nova_largura - largura
    ) // 2

    cima = (
        nova_altura - altura
    ) // 2

    imagem = imagem.crop(

        (
            esquerda,
            cima,
            esquerda + largura,
            cima + altura
        )

    )

    imagem.save(
        caminho,
        quality=85,
        optimize=True
    )


@app.route("/gerar", methods=["POST"])
def gerar():

    tema = request.form.get(
        "tema",
        "Meu vídeo"
    )

    duracao = int(
        request.form.get(
            "duracao",
            10
        )
    )

    nome = (
        f"{uuid.uuid4().hex}.mp4"
    )

    caminho_video = os.path.join(

        VIDEO_DIR,

        nome

    )

    clips = []

    try:

        imagens = buscar_imagens(
            tema
        )

        tempo_por_imagem = (
            duracao / len(imagens)
        )

        for caminho_imagem in imagens:

            preparar_imagem(
                caminho_imagem
            )

            clip = ImageClip(
                caminho_imagem
            )

            clip = clip.with_duration(
                tempo_por_imagem
            )

            clips.append(clip)

        video_base = concatenate_videoclips(
            clips,
            method="compose"
        )

        titulo = TextClip(

            text=tema,

            font_size=45,

            color="white",

            size=(460, 220),

            method="caption"

        )

        titulo = titulo.with_duration(
            duracao
        )

        titulo = titulo.with_position(
            ("center", 650)
        )

        video = CompositeVideoClip(

            [
                video_base,
                titulo
            ],

            size=(540, 960)

        )

        video.write_videofile(

            caminho_video,

            fps=15,

            codec="libx264",

            audio=False,

            preset="ultrafast",

            threads=1,

            logger=None

        )

        video.close()

        video_base.close()

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