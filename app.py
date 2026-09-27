import os
import uuid
import random
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
    "Áustria",
    "Escócia",
    "Irlanda",
    "Suécia",
    "Finlândia",
    "Croácia",
    "Eslovênia",
    "Turquia",
    "Japão",
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
    "Áustria": "Austria",
    "Escócia": "Scotland",
    "Irlanda": "Ireland",
    "Suécia": "Sweden",
    "Finlândia": "Finland",
    "Croácia": "Croatia",
    "Eslovênia": "Slovenia",
    "Turquia": "Turkey",
    "Japão": "Japan",
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
    "Jordânia": "Jordan"
}


# ============================================================
# TIPOS DE PAISAGEM
# ============================================================

TIPOS_NATUREZA = [
    "epic mountains",
    "beautiful mountains",
    "dramatic mountain landscape",
    "waterfall",
    "giant waterfall",
    "beautiful waterfall",
    "crystal clear lake",
    "turquoise lake",
    "mountain lake",
    "alpine lake",
    "glacier lake",
    "fjord",
    "dramatic valley",
    "green valley",
    "snow mountains",
    "glacier mountains",
    "pristine nature",
    "wild nature",
    "remote landscape",
    "breathtaking nature",
    "cinematic landscape"
]


# ============================================================
# BUSCAR PAISAGEM EXÓTICA
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

    # Escolhe aleatoriamente um tipo de natureza
    tipo1 = random.choice(TIPOS_NATUREZA)
    tipo2 = random.choice(TIPOS_NATUREZA)

    buscas = [
        f"{pais_ingles} {tipo1}",
        f"{pais_ingles} {tipo2}",
        f"{pais_ingles} breathtaking nature",
        f"{pais_ingles} spectacular landscape",
        f"{pais_ingles} wild mountains",
        f"{pais_ingles} pristine nature",
        f"{pais_ingles} exotic landscape"
    ]

    # Palavras que queremos evitar
    palavras_evitar = [
        "car",
        "cars",
        "people",
        "person",
        "man",
        "woman",
        "city",
        "street",
        "building",
        "hotel",
        "restaurant",
        "house",
        "road",
        "traffic",
        "airport",
        "shopping",
        "fashion"
    ]

    candidatos = []

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

            for foto in fotos:

                alt = (
                    foto.get("alt")
                    or ""
                ).lower()

                # Ignora fotos com conteúdo urbano/pessoas
                if any(
                    palavra in alt
                    for palavra in palavras_evitar
                ):
                    continue

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
                    candidatos.append(
                        imagem_url
                    )

        except Exception as erro:

            print(
                f"Erro na busca: {erro}"
            )

    if not candidatos:
        raise Exception(
            f"Não encontrei uma paisagem natural para {pais}."
        )

    # Remove duplicadas
    candidatos = list(
        dict.fromkeys(candidatos)
    )

    # Escolhe uma imagem
    return random.choice(candidatos)


# ============================================================
# BAIXAR IMAGEM
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
# PREPARAR IMAGEM
# ============================================================

def preparar_imagem(caminho):

    imagem = Image.open(
        caminho
    ).convert("RGB")

    largura, altura = imagem.size

    proporcao_destino = WIDTH / HEIGHT
    proporcao_atual = largura / altura

    # Corte para 9:16
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

    # Redimensiona para o vídeo
    imagem = imagem.resize(
        (WIDTH, HEIGHT),
        Image.Resampling.LANCZOS
    )

    imagem.save(
        caminho,
        "JPEG",
        quality=92,
        optimize=True
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

    # Zoom MUITO lento.
    # Começa normal e termina com aproximadamente 12% de zoom.

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
            "Erro ao criar o vídeo com FFmpeg."
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

<title>Natureza Exótica</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    padding: 20px;
    background: #101010;
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
    font-size: 30px;
}

.subtitulo {
    text-align: center;
    color: #aaa;
    line-height: 1.6;
    margin-bottom: 35px;
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
    cursor: pointer;
}

.info {
    margin-top: 25px;
    padding: 18px;
    background: #1d1d1d;
    border-radius: 12px;
    color: #ccc;
    line-height: 1.8;
}

.destaque {
    text-align: center;
    margin-top: 25px;
    color: #ddd;
}

</style>

</head>

<body>

<div class="container">

<h1>🏔️ Natureza Exótica</h1>

<div class="subtitulo">

Montanhas gigantes, cachoeiras,
lagos cristalinos, geleiras,
fiordes e paisagens naturais incríveis.

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
🌎 Criar vídeo
</button>

</form>

<div class="info">

🏔️ Montanhas<br>
💧 Cachoeiras<br>
🏞️ Lagos cristalinos<br>
🧊 Geleiras<br>
🌊 Fiordes<br>
🌿 Vales naturais<br>
📸 1 imagem real<br>
🎥 Zoom cinematográfico<br>
⏱️ 60 segundos<br>
📱 1080 × 1920<br>
🔇 Sem música e sem narração

</div>

<div class="destaque">

✨ Apenas natureza e paisagens

</div>

</div>

</body>

</html>
"""


# ============================================================
# PÁGINA PRINCIPAL
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
            f"🌎 País: {pais}"
        )

        print(
            "🏔️ Procurando paisagem exótica..."
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
            "✅ VÍDEO PRONTO!"
        )

        # Remove imagem temporária
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
# EXECUÇÃO
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