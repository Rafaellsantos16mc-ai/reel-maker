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
DURACAO_IMAGEM = 30

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
# BUSCA DE DUAS IMAGENS
# ============================================================

def buscar_duas_imagens(pais):

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

    # Mantemos a busca no mesmo tema/localidade.
    # Assim as duas imagens tendem a mostrar o mesmo
    # tipo de paisagem e, quando o catálogo possui,
    # diferentes ângulos do mesmo lugar.

    buscas = [
        f"{pais_ingles} waterfall lake",
        f"{pais_ingles} waterfall turquoise lake",
        f"{pais_ingles} beautiful waterfall lake",
        f"{pais_ingles} crystal clear lake waterfall"
    ]

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
                "per_page": 30
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

                    candidatos.append({
                        "url": imagem_url,
                        "alt": alt,
                        "id": foto.get("id")
                    })

        except Exception as erro:

            print(
                f"Erro na busca: {erro}"
            )

    if len(candidatos) < 2:

        raise Exception(
            f"Não encontrei duas imagens naturais para {pais}."
        )

    # Remove imagens duplicadas
    unicos = {}

    for foto in candidatos:
        unicos[foto["id"]] = foto

    candidatos = list(
        unicos.values()
    )

    # Mistura para não gerar sempre as mesmas fotos
    random.shuffle(candidatos)

    # Tenta encontrar duas imagens que tenham
    # palavras semelhantes na descrição.
    primeira = candidatos[0]

    palavras_primeira = set(
        primeira["alt"].split()
    )

    segunda = None

    for foto in candidatos[1:]:

        palavras_segunda = set(
            foto["alt"].split()
        )

        semelhanca = (
            len(
                palavras_primeira
                & palavras_segunda
            )
        )

        if semelhanca >= 2:

            segunda = foto
            break

    # Se não encontrou uma descrição semelhante,
    # usa outra foto da mesma busca temática.
    if segunda is None:
        segunda = candidatos[1]

    return [
        primeira["url"],
        segunda["url"]
    ]


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
# PREPARAR IMAGEM 9:16
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
        quality=92,
        optimize=True
    )

    imagem.close()


# ============================================================
# CRIAR UM CLIPE DE 30 SEGUNDOS
# ============================================================

def criar_clipe_zoom(caminho_imagem, numero):

    ffmpeg = get_ffmpeg_exe()

    caminho_saida = os.path.join(
        TEMP_DIR,
        f"parte_{numero}_{uuid.uuid4().hex}.mp4"
    )

    total_frames = DURACAO_IMAGEM * FPS

    # Zoom um pouco mais rápido.
    #
    # Começa em 1.00x
    # Termina aproximadamente em 1.18x
    #
    # O movimento continua suave, mas agora
    # fica mais perceptível.

    filtro = (
        "zoompan="
        "z='min(zoom+0.00025,1.18)':"
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
        str(DURACAO_IMAGEM),

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
            "Erro ao criar uma das partes do vídeo."
        )

    return caminho_saida


# ============================================================
# JUNTAR OS DOIS VÍDEOS
# ============================================================

def juntar_videos(video1, video2):

    ffmpeg = get_ffmpeg_exe()

    nome_final = (
        f"paisagem_{uuid.uuid4().hex}.mp4"
    )

    caminho_final = os.path.join(
        VIDEOS_DIR,
        nome_final
    )

    lista = os.path.join(
        TEMP_DIR,
        f"lista_{uuid.uuid4().hex}.txt"
    )

    with open(
        lista,
        "w",
        encoding="utf-8"
    ) as arquivo:

        arquivo.write(
            f"file '{os.path.abspath(video1)}'\n"
        )

        arquivo.write(
            f"file '{os.path.abspath(video2)}'\n"
        )

    comando = [
        ffmpeg,

        "-y",

        "-f",
        "concat",

        "-safe",
        "0",

        "-i",
        lista,

        "-c",
        "copy",

        "-movflags",
        "+faststart",

        caminho_final
    ]

    resultado = subprocess.run(
        comando,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    try:
        os.remove(lista)
    except Exception:
        pass

    if resultado.returncode != 0:

        print(
            resultado.stderr[-5000:]
        )

        raise Exception(
            "Erro ao juntar os dois vídeos."
        )

    return caminho_final


# ============================================================
# LIMPAR ARQUIVOS TEMPORÁRIOS
# ============================================================

def limpar_temp(arquivos):

    for arquivo in arquivos:

        try:

            if arquivo and os.path.exists(
                arquivo
            ):
                os.remove(arquivo)

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

<title>Lagos e Cachoeiras</title>

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

Paisagens naturais incríveis,
com duas imagens do mesmo cenário
e movimento de zoom cinematográfico.

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
🌊 Cachoeiras<br>
🏞️ Natureza intocada<br>
📸 2 imagens<br>
🎥 Zoom mais rápido e suave<br>
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
# CRIAR
# ============================================================

@app.route("/criar", methods=["POST"])
def criar():

    pais = request.form.get(
        "pais"
    )

    if not pais:
        return "Escolha um país."

    imagens = []
    partes = []

    try:

        print(
            f"🌎 País escolhido: {pais}"
        )

        print(
            "💧 Procurando duas imagens de "
            "lagos/cachoeiras..."
        )

        urls = buscar_duas_imagens(
            pais
        )

        # ====================================================
        # BAIXAR AS DUAS IMAGENS
        # ====================================================

        for i, url in enumerate(urls, start=1):

            caminho = os.path.join(
                IMAGES_DIR,
                f"{uuid.uuid4().hex}.jpg"
            )

            print(
                f"📥 Baixando imagem {i}/2..."
            )

            baixar_imagem(
                url,
                caminho
            )

            print(
                f"🖼️ Preparando imagem {i}/2..."
            )

            preparar_imagem(
                caminho
            )

            imagens.append(
                caminho
            )

        # ====================================================
        # CRIAR PRIMEIRO VÍDEO
        # ====================================================

        print(
            "🎥 Criando primeira parte..."
        )

        video1 = criar_clipe_zoom(
            imagens[0],
            1
        )

        partes.append(video1)

        # Libera a primeira imagem
        try:
            os.remove(imagens[0])
        except Exception:
            pass

        # ====================================================
        # CRIAR SEGUNDO VÍDEO
        # ====================================================

        print(
            "🎥 Criando segunda parte..."
        )

        video2 = criar_clipe_zoom(
            imagens[1],
            2
        )

        partes.append(video2)

        # Libera segunda imagem
        try:
            os.remove(imagens[1])
        except Exception:
            pass

        # ====================================================
        # JUNTAR
        # ====================================================

        print(
            "🎬 Juntando as duas partes..."
        )

        caminho_final = juntar_videos(
            video1,
            video2
        )

        print(
            "✅ VÍDEO DE 60 SEGUNDOS PRONTO!"
        )

        limpar_temp(
            partes
        )

        return send_file(
            caminho_final,
            as_attachment=True,
            download_name=os.path.basename(
                caminho_final
            ),
            mimetype="video/mp4"
        )

    except Exception as erro:

        print(
            f"❌ ERRO: {erro}"
        )

        limpar_temp(
            imagens + partes
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