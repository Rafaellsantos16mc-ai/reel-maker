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
            <option value="motivacional">🔥 Motivacional</option>
            <option value="dinheiro">💰 Dinheiro</option>
            <option value="curiosidades">🤯 Curiosidades</option>
            <option value="futebol">⚽ Futebol</option>
            <option value="historia">📖 História</option>
        </select>

        <select name="duracao">
            <option value="10">10 segundos - teste</option>
            <option value="15">15 segundos</option>
            <option value="30">30 segundos</option>
        </select>

        <button type="submit">
            🚀 GERAR REEL
        </button>

    </form>

    {% if video %}

    <div class="resultado">

        <h2>✅ Reel criado!</h2>

        <a href="/baixar/{{ video }}">
            <button>⬇️ BAIXAR REEL</button>
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


@app.route("/gerar", methods=["POST"])
def gerar():

    tema = request.form.get("tema", "Meu vídeo")
    estilo = request.form.get("estilo", "motivacional")
    duracao = int(request.form.get("duracao", 10))

    nome = f"{uuid.uuid4().hex}.mp4"
    caminho = os.path.join(VIDEO_DIR, nome)

    try:

        # Resolução otimizada para o Railway
        largura = 540
        altura = 960

        # Fundos diferentes por estilo
        fundos = {
            "motivacional": (20, 20, 20),
            "dinheiro": (15, 40, 20),
            "curiosidades": (30, 20, 50),
            "futebol": (10, 50, 25),
            "historia": (45, 30, 15)
        }

        cor_fundo = fundos.get(
            estilo,
            (20, 20, 20)
        )

        fundo = ColorClip(
            size=(largura, altura),
            color=cor_fundo,
            duration=duracao
        )

        titulo = TextClip(
            text=tema,
            font_size=55,
            color="white",
            size=(460, 350),
            method="caption"
        )

        titulo = titulo.with_duration(duracao)

        # Entrada suave
        titulo = titulo.with_position(
            lambda t: (
                "center",
                int(altura / 2 - 175 + max(0, 80 - t * 80))
            )
        )

        # Texto inferior
        rodape = TextClip(
            text="@ReelMaker",
            font_size=28,
            color="white",
            size=(400, 60),
            method="caption"
        )

        rodape = rodape.with_duration(duracao)
        rodape = rodape.with_position(
            ("center", 850)
        )

        video = CompositeVideoClip(
            [
                fundo,
                titulo,
                rodape
            ],
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
        titulo.close()
        rodape.close()

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

    caminho = os.path.join(
        VIDEO_DIR,
        nome
    )

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
        port=int(
            os.environ.get(
                "PORT",
                8080
            )
        )
    )