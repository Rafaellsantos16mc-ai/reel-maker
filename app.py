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

DURACAO_TOTAL = 60

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

VIDEOS_DIR = "videos"
IMAGES_DIR = "imagens"
TEMP_DIR = "temp"

os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)


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
# BUSCAR UMA ÚNICA IMAGEM
# ============================================================

def buscar_imagem(pais):

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

    # ========================================================
    # BUSCAS
    # ========================================================

    buscas = [
        f"{pais_ingles} beautiful natural lake",
        f"{pais_ingles} crystal clear lake nature",
        f"{pais_ingles} waterfall nature landscape",
        f"{pais_ingles} beautiful waterfall landscape",
        f"{pais_ingles} turquoise lake mountains",
        f"{pais_ingles} hidden waterfall nature"
    ]

    # ========================================================
    # PALAVRAS QUE NÃO QUEREMOS
    # ========================================================

    palavras_evitar = [
        "car",
        "cars",
        "vehicle",
        "road",
        "street",
        "traffic",

        "person",
        "people",
        "man",
        "woman",
        "child",
        "children",

        "city",
        "building",
        "buildings",
        "hotel",
        "house",
        "restaurant",
        "airport",
        "shopping",
        "fashion",

        "boat",
        "ship",

        "pool",
        "swimming pool",

        "cityscape",
        "urban",
        "downtown",

        "office",
        "architecture"
    ]

    candidatos = []

    for busca in buscas:

        try:

            params = {
                "query": busca,
                "orientation": "portrait",
                "size": "large",
                "per_page": 40
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

                # Ignora imagens com elementos indesejados
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

                if not imagem_url:
                    continue

                candidatos.append({
                    "id": foto.get("id"),
                    "url": imagem_url,
                    "alt": alt
                })

        except Exception as erro:

            print(
                f"Erro na busca Pexels: {erro}"
            )

    # ========================================================
    # VERIFICAÇÃO
    # ========================================================

    if not candidatos:

        raise Exception(
            f"Não encontrei uma paisagem natural adequada para {pais}."
        )

    # ========================================================
    # REMOVER DUPLICADAS
    # ========================================================

    unicos = {}

    for foto in candidatos:

        foto_id = foto.get("id")

        if foto_id:
            unicos[foto_id] = foto

    candidatos = list(
        unicos.values()
    )

    # ========================================================
    # PRIORIZAR TERMOS RELACIONADOS
    # ========================================================

    palavras_positivas = [
        "lake",
        "waterfall",
        "water",
        "nature",
        "mountain",
        "river",
        "landscape",
        "forest",
        "valley",
        "turquoise",
        "crystal",
        "clear",
        "nature"
    ]

    def pontuacao(foto):

        texto = foto["alt"]

        pontos = 0

        for palavra in palavras_positivas:

            if palavra in texto:
                pontos += 1

        return pontos

    candidatos.sort(
        key=pontuacao,
        reverse=True
    )

    # Pegamos somente os melhores resultados
    melhores = candidatos[:15]

    # Mistura entre os melhores para não ficar
    # sempre escolhendo exatamente a mesma foto
    random.shuffle(melhores)

    escolhida = melhores[0]

    print(
        "🖼️ Imagem escolhida:"
    )

    print(
        escolhida["alt"]
    )

    return escolhida["url"]


# ============================================================
# BAIXAR IMAGEM
# ============================================================

def baixar_imagem(url, caminho):

    resposta = requests.get(
        url,
        timeout=45
    )

    resposta.raise_for_status()

    with open(
        caminho,
        "wb"
    ) as arquivo:

        arquivo.write(
            resposta.content
        )


# ============================================================
# PREPARAR IMAGEM 9:16
# ============================================================

def preparar_imagem(caminho):

    imagem = Image.open(
        caminho
    ).convert("RGB")

    largura, altura = imagem.size

    proporcao_destino = (
        WIDTH / HEIGHT
    )

    proporcao_atual = (
        largura / altura
    )

    # ========================================================
    # CORTE CENTRAL
    # ========================================================

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

    # ========================================================
    # RESIZE
    # ========================================================

    imagem = imagem.resize(
        (WIDTH, HEIGHT),
        Image.Resampling.LANCZOS
    )

    imagem.save(
        caminho,
        "JPEG",
        quality=94,
        optimize=True
    )

    imagem.close()


# ============================================================
# CRIAR VÍDEO DE 60 SEGUNDOS
# ============================================================

def criar_video(caminho_imagem):

    ffmpeg = get_ffmpeg_exe()

    nome_saida = (
        f"paisagem_{uuid.uuid4().hex}.mp4"
    )

    caminho_saida = os.path.join(
        VIDEOS_DIR,
        nome_saida
    )

    total_frames = (
        DURACAO_TOTAL * FPS
    )

    # ========================================================
    # MOVIMENTO CINEMATOGRÁFICO
    #
    # Começa em 1.00x
    # Termina em aproximadamente 1.25x
    #
    # Além do zoom existe um pequeno
    # deslocamento horizontal/vertical.
    # ========================================================

    filtro = (
        "zoompan="
        "z='min(zoom+0.00022,1.25)':"
        "x='iw/2-(iw/zoom/2)+sin(on/90)*18':"
        "y='ih/2-(ih/zoom/2)+cos(on/110)*12':"
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
        str(DURACAO_TOTAL),

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

        caminho_saida
    ]

    print(
        "🎥 Criando vídeo de 60 segundos..."
    )

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
            "Erro ao criar o vídeo."
        )

    return caminho_saida


# ============================================================
# LIMPAR
# ============================================================

def limpar_arquivo(caminho):

    try:

        if caminho and os.path.exists(
            caminho
        ):
            os.remove(caminho)

    except Exception:
        pass


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

<title>Lagos & Cachoeiras</title>

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

</style>

</head>

<body>

<div class="container">

<h1>💧 Lagos & Cachoeiras</h1>

<div class="subtitulo">

Uma única paisagem natural durante todo o vídeo,
com movimento cinematográfico realista.

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

💧 Lagos cristalinos<br>
🌊 Cachoeiras naturais<br>
🏔️ Montanhas e natureza<br>
🖼️ Uma única paisagem<br>
🎥 Movimento cinematográfico<br>
🔍 Zoom suave<br>
⏱️ 60 segundos<br>
📱 1080 × 1920<br>
🔇 Sem música<br>
🔇 Sem narração<br>
🚫 Sem texto

</div>

</div>

</body>

</html>
"""


# ============================================================
# HOME
# ============================================================

@app.route(
    "/",
    methods=["GET"]
)
def inicio():

    return render_template_string(
        HTML,
        paises=PAISES
    )


# ============================================================
# CRIAR VÍDEO
# ============================================================

@app.route(
    "/criar",
    methods=["POST"]
)
def criar():

    pais = request.form.get(
        "pais"
    )

    if not pais:

        return "Escolha um país."

    caminho_imagem = None
    caminho_video = None

    try:

        print(
            "===================================="
        )

        print(
            f"🌎 País escolhido: {pais}"
        )

        print(
            "💧 Procurando UMA paisagem natural..."
        )

        # ====================================================
        # BUSCAR UMA ÚNICA IMAGEM
        # ====================================================

        url_imagem = buscar_imagem(
            pais
        )

        # ====================================================
        # BAIXAR
        # ====================================================

        caminho_imagem = os.path.join(
            IMAGES_DIR,
            f"{uuid.uuid4().hex}.jpg"
        )

        print(
            "📥 Baixando imagem..."
        )

        baixar_imagem(
            url_imagem,
            caminho_imagem
        )

        # ====================================================
        # PREPARAR
        # ====================================================

        print(
            "🖼️ Preparando imagem vertical..."
        )

        preparar_imagem(
            caminho_imagem
        )

        # ====================================================
        # CRIAR VÍDEO
        # ====================================================

        caminho_video = criar_video(
            caminho_imagem
        )

        # ====================================================
        # APAGAR IMAGEM TEMPORÁRIA
        # ====================================================

        limpar_arquivo(
            caminho_imagem
        )

        caminho_imagem = None

        print(
            "===================================="
        )

        print(
            "✅ VÍDEO PRONTO!"
        )

        print(
            "🎥 60 segundos"
        )

        print(
            "🖼️ Uma única paisagem"
        )

        print(
            "🔇 Sem áudio"
        )

        print(
            "===================================="
        )

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
            "❌ ERRO:"
        )

        print(
            erro
        )

        limpar_arquivo(
            caminho_imagem
        )

        limpar_arquivo(
            caminho_video
        )

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