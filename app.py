import os
import uuid
import requests
import subprocess

from flask import Flask, request, render_template_string, send_file
from PIL import Image
from imageio_ffmpeg import get_ffmpeg_exe

app = Flask(__name__)

# ============================================================
# CONFIGURAÇÕES
# ============================================================

WIDTH = 1080
HEIGHT = 1920
FPS = 24
DURACAO = 60

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

VIDEOS_DIR = "videos"
IMAGES_DIR = "imagens"

os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)


# ============================================================
# PAÍSES
# ============================================================

PAISES = [
    "Brasil",
    "Suíça",
    "Noruega",
    "Islândia",
    "Itália",
    "França",
    "Portugal",
    "Espanha",
    "Grécia",
    "Alemanha",
    "Áustria",
    "Holanda",
    "Inglaterra",
    "Escócia",
    "Irlanda",
    "Dinamarca",
    "Suécia",
    "Finlândia",
    "Croácia",
    "Eslovênia",
    "Turquia",
    "Japão",
    "Coreia do Sul",
    "China",
    "Tailândia",
    "Indonésia",
    "Maldivas",
    "Filipinas",
    "Vietnã",
    "Austrália",
    "Nova Zelândia",
    "Canadá",
    "Estados Unidos",
    "México",
    "Argentina",
    "Chile",
    "Peru",
    "Colômbia",
    "África do Sul",
    "Marrocos",
    "Egito",
    "Emirados Árabes Unidos",
    "Jordânia"
]

PAISES_INGLES = {
    "Brasil": "Brazil",
    "Suíça": "Switzerland",
    "Noruega": "Norway",
    "Islândia": "Iceland",
    "Itália": "Italy",
    "França": "France",
    "Portugal": "Portugal",
    "Espanha": "Spain",
    "Grécia": "Greece",
    "Alemanha": "Germany",
    "Áustria": "Austria",
    "Holanda": "Netherlands",
    "Inglaterra": "England",
    "Escócia": "Scotland",
    "Irlanda": "Ireland",
    "Dinamarca": "Denmark",
    "Suécia": "Sweden",
    "Finlândia": "Finland",
    "Croácia": "Croatia",
    "Eslovênia": "Slovenia",
    "Turquia": "Turkey",
    "Japão": "Japan",
    "Coreia do Sul": "South Korea",
    "China": "China",
    "Tailândia": "Thailand",
    "Indonésia": "Indonesia",
    "Maldivas": "Maldives",
    "Filipinas": "Philippines",
    "Vietnã": "Vietnam",
    "Austrália": "Australia",
    "Nova Zelândia": "New Zealand",
    "Canadá": "Canada",
    "Estados Unidos": "United States",
    "México": "Mexico",
    "Argentina": "Argentina",
    "Chile": "Chile",
    "Peru": "Peru",
    "Colômbia": "Colombia",
    "África do Sul": "South Africa",
    "Marrocos": "Morocco",
    "Egito": "Egypt",
    "Emirados Árabes Unidos": "United Arab Emirates",
    "Jordânia": "Jordan"
}


# ============================================================
# BUSCAR FOTO
# ============================================================

def buscar_imagem_pexels(pais):

    if not PEXELS_API_KEY:
        raise Exception(
            "PEXELS_API_KEY não está configurada no Railway."
        )

    pais_ingles = PAISES_INGLES.get(
        pais,
        pais
    )

    url = "https://api.pexels.com/v1/search"

    headers = {
        "Authorization": PEXELS_API_KEY
    }

    buscas = [
        f"{pais_ingles} scenic landscape",
        f"{pais_ingles} beautiful nature",
        f"{pais_ingles} breathtaking landscape",
        f"{pais_ingles} scenic view",
        f"{pais_ingles} travel photography",
        f"{pais_ingles} mountains lake landscape",
        f"{pais_ingles} beautiful places"
    ]

    for busca in buscas:

        try:

            params = {
                "query": busca,
                "orientation": "portrait",
                "size": "large",
                "per_page": 20
            }

            resposta = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=30
            )

            if resposta.status_code != 200:
                continue

            dados = resposta.json()

            fotos = dados.get(
                "photos",
                []
            )

            if not fotos:
                continue

            foto = fotos[
                uuid.uuid4().int % len(fotos)
            ]

            src = foto.get(
                "src",
                {}
            )

            imagem_url = (
                src.get("large2x")
                or src.get("large")
                or src.get("original")
            )

            if imagem_url:
                return imagem_url

        except Exception as erro:

            print(
                f"Erro na busca: {erro}"
            )

    raise Exception(
        f"Não encontrei uma imagem para {pais}."
    )


# ============================================================
# BAIXAR FOTO
# ============================================================

def baixar_imagem(url, caminho):

    resposta = requests.get(
        url,
        timeout=45
    )

    resposta.raise_for_status()

    with open(caminho, "wb") as arquivo:
        arquivo.write(
            resposta.content
        )


# ============================================================
# PREPARAR FOTO 9:16
# ============================================================

def preparar_imagem(caminho):

    imagem = Image.open(
        caminho
    ).convert("RGB")

    largura, altura = imagem.size

    proporcao_destino = WIDTH / HEIGHT
    proporcao_atual = largura / altura

    if proporcao_atual > proporcao_destino:

        nova_largura = int(
            altura * proporcao_destino
        )

        esquerda = (
            largura - nova_largura
        ) // 2

        imagem = imagem.crop(
            (
                esquerda,
                0,
                esquerda + nova_largura,
                altura
            )
        )

    else:

        nova_altura = int(
            largura / proporcao_destino
        )

        topo = (
            altura - nova_altura
        ) // 2

        imagem = imagem.crop(
            (
                0,
                topo,
                largura,
                topo + nova_altura
            )
        )

    imagem = imagem.resize(
        (WIDTH, HEIGHT),
        Image.Resampling.LANCZOS
    )

    imagem.save(
        caminho,
        "JPEG",
        quality=92
    )

    imagem.close()


# ============================================================
# CRIAR VÍDEO
# ============================================================

def criar_video(caminho_imagem):

    nome_video = (
        f"paisagem_{uuid.uuid4().hex}.mp4"
    )

    caminho_video = os.path.join(
        VIDEOS_DIR,
        nome_video
    )

    ffmpeg = get_ffmpeg_exe()

    total_frames = DURACAO * FPS

    filtro = (
        "zoompan="
        "z='min(zoom+0.00008,1.12)':"
        "x='iw/2-(iw/zoom/2)':"
        "y='ih/2-(ih/zoom/2)':"
        f"d={total_frames}:"
        f"s={WIDTH}x{HEIGHT}:"
        f"fps={FPS}"
    )

    comando = [
        ffmpeg,
        "-y",

        "-loop",
        "1",

        "-i",
        caminho_imagem,

        "-vf",
        filtro,

        "-t",
        str(DURACAO),

        "-an",

        "-c:v",
        "libx264",

        "-preset",
        "veryfast",

        "-crf",
        "20",

        "-pix_fmt",
        "yuv420p",

        "-movflags",
        "+faststart",

        "-threads",
        "1",

        caminho_video
    ]

    resultado = subprocess.run(
        comando,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if resultado.returncode != 0:

        print(
            resultado.stderr[-5000:]
        )

        raise Exception(
            "O FFmpeg não conseguiu criar o vídeo."
        )

    return caminho_video


# ============================================================
# INTERFACE
# ============================================================

HTML = """
<!DOCTYPE html>

<html lang="pt-BR">

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>Paisagens do Mundo</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    padding: 20px;
    background: #111;
    color: white;
    font-family: Arial, sans-serif;
    min-height: 100vh;
}

.container {
    max-width: 500px;
    margin: auto;
}

h1 {
    text-align: center;
    margin-top: 30px;
}

.subtitulo {
    text-align: center;
    color: #aaa;
    line-height: 1.5;
    margin-bottom: 30px;
}

label {
    display: block;
    margin-bottom: 10px;
    font-weight: bold;
}

select {
    width: 100%;
    padding: 16px;
    border: none;
    border-radius: 12px;
    font-size: 17px;
    margin-bottom: 20px;
}

button {
    width: 100%;
    padding: 17px;
    border: none;
    border-radius: 12px;
    background: white;
    color: #111;
    font-size: 18px;
    font-weight: bold;
}

.info {
    margin-top: 25px;
    padding: 18px;
    background: #1d1d1d;
    border-radius: 12px;
    color: #ccc;
    line-height: 1.7;
}

</style>

</head>

<body>

<div class="container">

<h1>🌎 Paisagens do Mundo</h1>

<div class="subtitulo">
Uma paisagem realista em vídeo,
com zoom cinematográfico de 60 segundos.
</div>

<form method="POST" action="/criar">

<label>Escolha o país:</label>

<select name="pais" required>

{% for pais in paises %}

<option value="{{ pais }}">
{{ pais }}
</option>

{% endfor %}

</select>

<button type="submit">
🎬 Criar vídeo
</button>

</form>

<div class="info">

📸 1 única imagem<br>
🎥 Zoom lento e suave<br>
⏱️ 60 segundos<br>
📱 1080 × 1920<br>
🔇 Sem música<br>
🔇 Sem narração

</div>

</div>

</body>

</html>
"""


# ============================================================
# HOME
# ============================================================

@app.route("/", methods=["GET"])
def inicio():

    return render_template_string(
        HTML,
        paises=PAISES
    )


# ============================================================
# CRIAR VÍDEO
# ============================================================

@app.route("/criar", methods=["POST"])
def criar():

    pais = request.form.get(
        "pais"
    )

    if not pais:
        return "Escolha um país."

    caminho_imagem = None

    try:

        print(
            f"🌎 País escolhido: {pais}"
        )

        print(
            "🔎 Procurando paisagem..."
        )

        imagem_url = buscar_imagem_pexels(
            pais
        )

        nome_imagem = (
            f"{uuid.uuid4().hex}.jpg"
        )

        caminho_imagem = os.path.join(
            IMAGES_DIR,
            nome_imagem
        )

        print(
            "📥 Baixando imagem..."
        )

        baixar_imagem(
            imagem_url,
            caminho_imagem
        )

        print(
            "🖼️ Preparando imagem..."
        )

        preparar_imagem(
            caminho_imagem
        )

        print(
            "🎥 Criando vídeo de 60 segundos..."
        )

        caminho_video = criar_video(
            caminho_imagem
        )

        print(
            "✅ Vídeo pronto!"
        )

        # Apaga a imagem temporária
        try:

            if os.path.exists(
                caminho_imagem
            ):
                os.remove(
                    caminho_imagem
                )

        except Exception:
            pass

        return send_file(
            caminho_video,
            as_attachment=True,
            download_name=os.path.basename(
                caminho_video
            ),
            mimetype="video/mp4"
        )

    except Exception as erro:

        print(
            f"❌ ERRO: {erro}"
        )

        try:

            if (
                caminho_imagem
                and os.path.exists(
                    caminho_imagem
                )
            ):
                os.remove(
                    caminho_imagem
                )

        except Exception:
            pass

        return f"""
        <html>
        <body style="
            background:#111;
            color:white;
            font-family:Arial;
            padding:30px;
        ">

        <h2>❌ Erro ao criar vídeo</h2>

        <p>{erro}</p>

        <br>

        <a href="/"
        style="color:white;">
        ← Voltar
        </a>

        </body>
        </html>
        """, 500


# ============================================================
# RODAR
# ============================================================

if __name__ == "__main__":

    porta = int(
        os.environ.get(
            "PORT",
            "8080"
        )
    )

    app.run(
        host="0.0.0.0",
        port=porta
    )