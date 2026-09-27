import os
import random
import uuid
import requests
import subprocess

from flask import Flask, request, render_template_string, send_file
import imageio_ffmpeg


app = Flask(__name__)


# ============================================================
# CONFIGURAÇÕES
# ============================================================

WIDTH = 1080
HEIGHT = 1920
FPS = 24
DURATION = 60

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

VIDEO_DIR = "videos"
TEMP_DIR = "temp"

os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


# ============================================================
# PAÍSES
# ============================================================

PAISES = {
    "Brasil": "Brazil",
    "Estados Unidos": "United States",
    "Canadá": "Canada",
    "México": "Mexico",
    "Argentina": "Argentina",
    "Chile": "Chile",
    "Peru": "Peru",
    "Colômbia": "Colombia",
    "Costa Rica": "Costa Rica",
    "Islândia": "Iceland",
    "Noruega": "Norway",
    "Suíça": "Switzerland",
    "França": "France",
    "Itália": "Italy",
    "Portugal": "Portugal",
    "Espanha": "Spain",
    "Escócia": "Scotland",
    "Irlanda": "Ireland",
    "Inglaterra": "England",
    "Alemanha": "Germany",
    "Áustria": "Austria",
    "Nova Zelândia": "New Zealand",
    "Austrália": "Australia",
    "Japão": "Japan",
    "China": "China",
    "Coreia do Sul": "South Korea",
    "Indonésia": "Indonesia",
    "Tailândia": "Thailand",
    "Filipinas": "Philippines",
    "Índia": "India",
    "Nepal": "Nepal",
    "África do Sul": "South Africa",
    "Quênia": "Kenya",
    "Marrocos": "Morocco",
    "Tanzânia": "Tanzania",
    "Turquia": "Turkey",
    "Grécia": "Greece",
    "Croácia": "Croatia",
    "Eslovênia": "Slovenia",
    "Finlândia": "Finland",
    "Suécia": "Sweden",
    "Polônia": "Poland"
}


# ============================================================
# INTERFACE
# ============================================================

HTML = """
<!DOCTYPE html>

<html lang="pt-BR">

<head>

<meta charset="UTF-8">

<meta
name="viewport"
content="width=device-width, initial-scale=1.0"
>

<title>Nature Reel Maker</title>

<style>

body {
    margin: 0;
    padding: 20px;
    background: #111;
    color: white;
    font-family: Arial, sans-serif;
}

.container {
    max-width: 500px;
    margin: auto;
}

h1 {
    text-align: center;
    margin-bottom: 8px;
}

.subtitle {
    text-align: center;
    color: #aaa;
    margin-bottom: 25px;
}

.card {
    background: #1c1c1c;
    padding: 20px;
    border-radius: 18px;
}

label {
    display: block;
    margin-bottom: 8px;
    font-weight: bold;
}

select {
    width: 100%;
    padding: 15px;
    border-radius: 10px;
    border: none;
    font-size: 16px;
    margin-bottom: 20px;
    box-sizing: border-box;
}

button {
    width: 100%;
    padding: 16px;
    border: none;
    border-radius: 12px;
    background: white;
    color: #111;
    font-size: 17px;
    font-weight: bold;
    cursor: pointer;
}

button:hover {
    opacity: 0.9;
}

.info {
    margin-top: 20px;
    padding: 15px;
    background: #252525;
    border-radius: 12px;
    color: #bbb;
    font-size: 14px;
    line-height: 1.7;
}

</style>

</head>


<body>

<div class="container">

<h1>🌎 Nature Reel Maker</h1>

<div class="subtitle">
Vídeos reais de lagos e cachoeiras
</div>


<div class="card">

<form method="POST">

<label>Escolha o país</label>

<select name="pais" required>

{% for nome in paises %}

<option value="{{ nome }}">
{{ nome }}
</option>

{% endfor %}

</select>


<button type="submit">
🎬 Criar Reel
</button>

</form>


<div class="info">

🌊 Lagos e cachoeiras<br>
🎥 Um único vídeo real<br>
🌎 Paisagens naturais<br>
📱 1080 x 1920<br>
⏱️ Até 60 segundos<br>
🔇 Sem música<br>
🔇 Sem narração<br>
🚫 Sem texto<br>
🚫 Sem zoom artificial

</div>

</div>

</div>

</body>

</html>
"""


# ============================================================
# BUSCAR VÍDEOS NO PEXELS
# ============================================================

def buscar_videos(query):

    if not PEXELS_API_KEY:
        raise Exception(
            "A variável PEXELS_API_KEY não está configurada no Railway."
        )

    url = "https://api.pexels.com/videos/search"

    headers = {
        "Authorization": PEXELS_API_KEY
    }

    params = {
        "query": query,
        "orientation": "landscape",
        "size": "large",
        "per_page": 80
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=40
    )

    if response.status_code != 200:
        raise Exception(
            f"Erro Pexels {response.status_code}: {response.text}"
        )

    data = response.json()

    return data.get("videos", [])


# ============================================================
# ESCOLHER ARQUIVO DO VÍDEO
# ============================================================

def escolher_arquivo(video):

    arquivos = video.get("video_files", [])

    candidatos = []

    for arquivo in arquivos:

        link = arquivo.get("link")

        if not link:
            continue

        file_type = arquivo.get("file_type")

        if file_type and file_type != "video/mp4":
            continue

        largura = int(
            arquivo.get("width") or 0
        )

        altura = int(
            arquivo.get("height") or 0
        )

        if largura <= 0 or altura <= 0:
            continue

        candidatos.append(arquivo)

    if not candidatos:
        return None

    # Preferimos arquivos grandes,
    # mas evitamos arquivos absurdamente pesados.
    candidatos.sort(
        key=lambda x: (
            x.get("width", 0) * x.get("height", 0)
        ),
        reverse=True
    )

    # Primeiro tenta um arquivo 4K ou Full HD.
    for arquivo in candidatos:

        largura = int(
            arquivo.get("width") or 0
        )

        altura = int(
            arquivo.get("height") or 0
        )

        if largura <= 3840 and altura <= 2160:
            return arquivo

    return candidatos[0]


# ============================================================
# ESCOLHER O MELHOR VÍDEO
# ============================================================

def escolher_video(videos):

    candidatos = []

    palavras_boas = [
        "landscape",
        "scenic",
        "nature",
        "waterfall",
        "lake",
        "mountain",
        "river",
        "valley",
        "aerial",
        "drone",
        "panoramic",
        "view",
        "nature"
    ]

    palavras_ruins = [
        "person",
        "people",
        "man",
        "woman",
        "city",
        "street",
        "road",
        "car",
        "building",
        "hotel",
        "pool",
        "boat",
        "ship",
        "restaurant",
        "house",
        "office"
    ]

    for video in videos:

        duracao = float(
            video.get("duration") or 0
        )

        if duracao < 5:
            continue

        arquivo = escolher_arquivo(video)

        if not arquivo:
            continue

        texto = str(
            video.get("url", "")
        ).lower()

        score = 0

        for palavra in palavras_boas:

            if palavra in texto:
                score += 3

        for palavra in palavras_ruins:

            if palavra in texto:
                score -= 6

        # Grande preferência para vídeos
        # que conseguem fornecer os 60 segundos.
        if duracao >= DURATION:
            score += 50

        # Preferência por vídeos longos.
        score += min(duracao, 120) / 4

        largura = int(
            arquivo.get("width") or 0
        )

        altura = int(
            arquivo.get("height") or 0
        )

        # Boa resolução.
        if largura >= 1920 and altura >= 1080:
            score += 10

        candidatos.append({
            "video": video,
            "arquivo": arquivo,
            "score": score,
            "duracao": duracao
        })

    if not candidatos:
        return None

    candidatos.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    # Escolhe aleatoriamente entre alguns dos melhores
    # para não gerar sempre exatamente o mesmo vídeo.
    melhores = candidatos[:8]

    return random.choice(melhores)


# ============================================================
# DOWNLOAD
# ============================================================

def baixar_video(url, destino):

    print("⬇️ Baixando vídeo...")

    response = requests.get(
        url,
        stream=True,
        timeout=180
    )

    if response.status_code != 200:

        raise Exception(
            f"Erro ao baixar vídeo: HTTP {response.status_code}"
        )

    tamanho = 0

    with open(destino, "wb") as arquivo:

        for bloco in response.iter_content(
            chunk_size=1024 * 1024
        ):

            if bloco:

                arquivo.write(bloco)

                tamanho += len(bloco)

    print(
        f"✅ Download concluído: "
        f"{tamanho / 1024 / 1024:.1f} MB"
    )

    if tamanho < 100000:

        raise Exception(
            "O vídeo baixado ficou muito pequeno ou está inválido."
        )


# ============================================================
# CRIAR REEL
# ============================================================

def criar_reel(video_path, output_path):

    print("🎬 Iniciando conversão...")

    # O vídeo original normalmente é horizontal.
    #
    # Aqui ele é ampliado até preencher a tela vertical
    # e depois cortado no centro.
    #
    # Não existe zoom artificial ao longo do vídeo.
    filtro = (
        "scale=1080:1920:"
        "force_original_aspect_ratio=increase,"
        "crop=1080:1920:"
        "(iw-1080)/2:"
        "(ih-1920)/2,"
        "setsar=1"
    )

    comando = [

        FFMPEG,

        "-y",

        "-hide_banner",

        "-loglevel",
        "error",

        "-i",
        video_path,

        "-map",
        "0:v:0",

        "-vf",
        filtro,

        "-t",
        str(DURATION),

        "-r",
        str(FPS),

        "-an",

        "-c:v",
        "libx264",

        "-preset",
        "veryfast",

        "-crf",
        "22",

        "-pix_fmt",
        "yuv420p",

        "-movflags",
        "+faststart",

        "-threads",
        "2",

        output_path
    ]

    processo = subprocess.run(
        comando,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=600
    )

    if processo.returncode != 0:

        erro = processo.stderr.strip()

        if not erro:
            erro = "Erro desconhecido do FFmpeg."

        raise Exception(
            "FFmpeg não conseguiu converter o vídeo:\n\n"
            + erro[-8000:]
        )

    if not os.path.exists(output_path):

        raise Exception(
            "O FFmpeg terminou, mas o arquivo não foi criado."
        )

    tamanho = os.path.getsize(output_path)

    print(
        f"✅ Reel criado: "
        f"{tamanho / 1024 / 1024:.1f} MB"
    )

    if tamanho < 100000:

        raise Exception(
            "O arquivo final ficou muito pequeno."
        )


# ============================================================
# GERAR VÍDEO
# ============================================================

def gerar_video(pais):

    nome_pais = PAISES.get(
        pais,
        pais
    )

    consultas = [

        f"{nome_pais} waterfall landscape",

        f"{nome_pais} beautiful waterfall nature",

        f"{nome_pais} lake landscape",

        f"{nome_pais} beautiful lake nature",

        f"{nome_pais} scenic waterfall",

        f"{nome_pais} scenic lake",

        f"{nome_pais} panoramic nature landscape",

        f"{nome_pais} mountain lake"

    ]

    consultas_embaralhadas = consultas[:]

    random.shuffle(
        consultas_embaralhadas
    )

    todos_videos = []

    print("======================================")
    print("🌎 PAÍS:", pais)
    print("🔎 Procurando vídeos reais...")
    print("======================================")

    # Faz algumas buscas diferentes.
    for consulta in consultas_embaralhadas[:5]:

        print(
            "🔎 Busca:",
            consulta
        )

        try:

            videos = buscar_videos(
                consulta
            )

            todos_videos.extend(
                videos
            )

        except Exception as erro:

            print(
                "⚠️ Erro nessa busca:",
                erro
            )

        if len(todos_videos) >= 100:

            break

    if not todos_videos:

        raise Exception(
            "Nenhum vídeo encontrado para esse país."
        )

    escolhido = escolher_video(
        todos_videos
    )

    if not escolhido:

        raise Exception(
            "Não encontrei um vídeo adequado de lago ou cachoeira."
        )

    video = escolhido["video"]

    arquivo = escolhido["arquivo"]

    video_id = video.get(
        "id",
        "desconhecido"
    )

    duracao = video.get(
        "duration",
        0
    )

    largura = arquivo.get(
        "width",
        0
    )

    altura = arquivo.get(
        "height",
        0
    )

    url_video = arquivo.get(
        "link"
    )

    if not url_video:

        raise Exception(
            "O Pexels não forneceu o arquivo do vídeo."
        )

    print("======================================")
    print("🎥 VÍDEO ESCOLHIDO:", video_id)
    print("⏱️ DURAÇÃO:", duracao, "segundos")
    print(
        "📐 RESOLUÇÃO:",
        largura,
        "x",
        altura
    )
    print("======================================")

    identificador = uuid.uuid4().hex

    temp_path = os.path.join(
        TEMP_DIR,
        f"{identificador}_original.mp4"
    )

    output_name = (
        f"nature_"
        f"{pais.lower().replace(' ', '_')}_"
        f"{identificador[:8]}.mp4"
    )

    output_path = os.path.join(
        VIDEO_DIR,
        output_name
    )

    try:

        baixar_video(
            url_video,
            temp_path
        )

        criar_reel(
            temp_path,
            output_path
        )

        return output_path

    finally:

        # Apaga o vídeo original baixado
        # depois de criar o Reel.
        if os.path.exists(temp_path):

            try:

                os.remove(
                    temp_path
                )

                print(
                    "🗑️ Arquivo temporário removido."
                )

            except Exception as erro:

                print(
                    "⚠️ Não foi possível remover temporário:",
                    erro
                )


# ============================================================
# PÁGINA PRINCIPAL
# ============================================================

@app.route(
    "/",
    methods=["GET", "POST"]
)
def index():

    if request.method == "POST":

        pais = request.form.get(
            "pais"
        )

        if not pais:

            return (
                "Selecione um país.",
                400
            )

        try:

            caminho = gerar_video(
                pais
            )

            return send_file(
                caminho,
                as_attachment=True,
                download_name="nature_reel.mp4",
                mimetype="video/mp4"
            )

        except subprocess.TimeoutExpired:

            return """
            <html>

            <body style="
                background:#111;
                color:white;
                font-family:Arial;
                padding:30px;
            ">

            <h2>❌ Tempo excedido</h2>

            <p>
            O processamento demorou mais do que o esperado.
            Tente novamente.
            </p>

            <br>

            <a
            href="/"
            style="color:white;"
            >
            ← Voltar
            </a>

            </body>

            </html>
            """, 500

        except Exception as erro:

            print(
                "❌ ERRO:",
                erro
            )

            return f"""

            <html>

            <body style="
                background:#111;
                color:white;
                font-family:Arial;
                padding:25px;
            ">

            <h2>❌ Erro ao criar vídeo</h2>

            <pre style="
                white-space:pre-wrap;
                background:#222;
                padding:15px;
                border-radius:10px;
                overflow:auto;
            ">{str(erro)}</pre>

            <br>

            <a
            href="/"
            style="color:white;"
            >
            ← Voltar
            </a>

            </body>

            </html>

            """, 500

    return render_template_string(
        HTML,
        paises=PAISES.keys()
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health")
def health():

    return {
        "status": "ok",
        "app": "Nature Reel Maker",
        "type": "real videos",
        "duration": DURATION,
        "resolution": f"{WIDTH}x{HEIGHT}"
    }


# ============================================================
# INICIAR
# ============================================================

if __name__ == "__main__":

    port = int(
        os.getenv(
            "PORT",
            "8080"
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )