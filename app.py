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
            padding: 20px;
            text-align: center;
        }

        .box {
            max-width: 500px;
            margin: auto;
        }

        input, select, button {
            width: 100%;
            padding: 14px;
            margin: 10px 0;
            box-sizing: border-box;
            border-radius: 8px;
            border: none;
            font-size: 16px;
        }

        button {
            background: #ff0050;
            color: white;
            font-weight: bold;
        }

        .msg {
            margin-top: 20px;
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
            placeholder="Digite o tema"
            required
        >

        <select name="duracao">
            <option value="10">10 segundos - teste</option>
            <option value="15">15 segundos</option>
            <option value="30">30 segundos</option>
        </select>

        <button type="submit">
            🚀 GERAR VÍDEO
        </button>

    </form>

    {% if video %}
        <div class="msg">
            <h2>✅ Vídeo criado!</h2>

            <a href="/baixar/{{ video }}">
                <button>⬇️ BAIXAR VÍDEO</button>
            </a>
        </div>
    {% endif %}

    {% if erro %}
        <div class="msg">
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


@app.route("/gerar", methods=["POST"])
def gerar():

    tema = request.form.get("tema", "Meu vídeo")
    duracao = int(request.form.get("duracao", 10))

    nome = f"{uuid.uuid4().hex}.mp4"
    caminho = os.path.join(VIDEO_DIR, nome)

    try:

        # Resolução reduzida para evitar falta de memória
        largura = 540
        altura = 960

        fundo = ColorClip(
            size=(largura, altura),
            color=(15, 15, 15),
            duration=duracao
        )

        texto = TextClip(
            text=tema,
            font_size=50,
            color="white",
            size=(460, 300),
            method="caption"
        )

        texto = texto.with_position("center")
        texto = texto.with_duration(duracao)

        video = CompositeVideoClip(
            [fundo, texto],
            size=(largura, altura)
        )

        video.write_videofile(
            caminho,
            fps=15,
            codec="libx264",
            audio=False,
            preset="ultrafast",
            threads=1,
            logger=None
        )

        video.close()
        fundo.close()
        texto.close()

        return render_template_string(
            HTML,
            video=nome
        )

    except Exception as e:

        return render_template_string(
            HTML,
            erro=str(e)
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