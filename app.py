from flask import Flask, request, send_file, render_template_string
from moviepy import ColorClip, TextClip, CompositeVideoClip
import os
import uuid

app = Flask(__name__)

VIDEO_DIR = "videos"
os.makedirs(VIDEO_DIR, exist_ok=True)

HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reel Maker</title>

    <style>
        body {
            font-family: Arial, sans-serif;
            background: #111;
            color: white;
            margin: 0;
            padding: 20px;
        }

        .container {
            max-width: 500px;
            margin: auto;
        }

        h1 {
            text-align: center;
        }

        input, select, button {
            width: 100%;
            padding: 14px;
            margin-top: 10px;
            margin-bottom: 15px;
            border-radius: 8px;
            border: none;
            box-sizing: border-box;
            font-size: 16px;
        }

        button {
            background: #ff0050;
            color: white;
            font-weight: bold;
            cursor: pointer;
        }

        button:hover {
            opacity: 0.9;
        }

        .resultado {
            margin-top: 20px;
            text-align: center;
        }

        a {
            color: white;
            text-decoration: none;
        }
    </style>
</head>

<body>

<div class="container">

    <h1>🎬 REEL MAKER</h1>

    <form action="/gerar" method="POST">

        <label>Digite o tema do vídeo:</label>

        <input
            type="text"
            name="tema"
            placeholder="Ex: Como ficar rico"
            required
        >

        <label>Duração:</label>

        <select name="duracao">
            <option value="30">30 segundos</option>
            <option value="45">45 segundos</option>
            <option value="60">60 segundos</option>
        </select>

        <button type="submit">
            🚀 GERAR VÍDEO
        </button>

    </form>

    {% if video %}
        <div class="resultado">
            <h2>✅ Vídeo criado!</h2>

            <a href="/baixar/{{ video }}">
                <button>⬇️ BAIXAR VÍDEO</button>
            </a>
        </div>
    {% endif %}

</div>

</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/gerar", methods=["POST"])
def gerar():

    tema = request.form.get("tema", "Meu vídeo")
    duracao = int(request.form.get("duracao", 30))

    nome = f"{uuid.uuid4().hex}.mp4"
    caminho = os.path.join(VIDEO_DIR, nome)

    largura = 1080
    altura = 1920

    fundo = ColorClip(
        size=(largura, altura),
        color=(15, 15, 15),
        duration=duracao
    )

    texto = TextClip(
        text=tema,
        font_size=80,
        color="white",
        size=(900, None),
        method="caption"
    )

    texto = texto.with_position("center").with_duration(duracao)

    video = CompositeVideoClip(
        [fundo, texto],
        size=(largura, altura)
    )

    video.write_videofile(
        caminho,
        fps=30,
        codec="libx264",
        audio=False,
        logger=None
    )

    video.close()
    fundo.close()
    texto.close()

    return render_template_string(
        HTML,
        video=nome
    )


@app.route("/baixar/<nome>")
def baixar(nome):

    caminho = os.path.join(VIDEO_DIR, nome)

    if not os.path.exists(caminho):
        return "Vídeo não encontrado.", 404

    return send_file(
        caminho,
        as_attachment=True,
        download_name="reel.mp4"
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080))
    )