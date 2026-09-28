import os
import random
import uuid
import requests
import subprocess
import html

from flask import Flask, request, render_template_string, send_file
import imageio_ffmpeg


app = Flask(__name__)


# ============================================================
# CONFIGURAÇÕES
# ============================================================

WIDTH = 1080
HEIGHT = 1920
FPS = 24

# Duração final
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

<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>Cliff & Nature Reel</title>

<style>

body {
    margin: 0;
    padding: 20px;
    background: #101010;
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

<h1>🏔️ Cliff & Nature Reel</h1>

<div class="subtitle">
Paisagens naturais, penhascos e vistas impressionantes
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

🏔️ Penhascos e desfiladeiros<br>
🌊 Cachoeiras e oceanos<br>
🏞️ Montanhas e lagos<br>
👁️ Sensação de POV / viewpoint<br>
🎥 Vários clipes no mesmo vídeo<br>
📱 1080 x 1920 vertical<br>
🔎 Zoom progressivo e aproximado<br>
⏱️ Até 60 segundos<br>
🔇 Sem áudio<br>
🚫 Sem texto

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
        "orientation": "portrait",
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
# ESCOLHER ARQUIVO VERTICAL
# ============================================================

def escolher_arquivo(video):

    arquivos = video.get("video_files", [])

    candidatos = []

    for arquivo in arquivos:

        link = arquivo.get("link")

        if not link:
            continue

        tipo = arquivo.get("file_type")

        if tipo and tipo != "video/mp4":
            continue

        largura = int(arquivo.get("width") or 0)
        altura = int(arquivo.get("height") or 0)

        if largura <= 0 or altura <= 0:
            continue

        # Preferir vídeo realmente vertical
        proporcao = altura / largura

        if proporcao < 1.35:
            continue

        candidatos.append(arquivo)

    if not candidatos:
        return None

    # Melhor resolução primeiro
    candidatos.sort(
        key=lambda x: x.get("width", 0) * x.get("height", 0),
        reverse=True
    )

    # Evitar arquivos exageradamente grandes
    for arquivo in candidatos:

        largura = int(arquivo.get("width") or 0)
        altura = int(arquivo.get("height") or 0)

        if largura <= 2160 and altura <= 3840:
            return arquivo

    return candidatos[0]


# ============================================================
# PALAVRAS
# ============================================================

PALAVRAS_BOAS = [

    "cliff",
    "cliffs",
    "cliffside",
    "cliff edge",
    "edge",
    "mountain",
    "mountains",
    "mountain view",
    "waterfall",
    "waterfalls",
    "canyon",
    "canyons",
    "gorge",
    "valley",
    "landscape",
    "nature",
    "nature landscape",
    "scenic",
    "viewpoint",
    "view",
    "panorama",
    "panoramic",
    "ocean",
    "sea",
    "coast",
    "coastline",
    "lake",
    "river",
    "rocks",
    "rocky",
    "peak",
    "summit",
    "hiking",
    "trail",
    "dramatic",
    "wild",
    "wilderness",
    "aerial",
    "look down",
    "height",
    "high",
    "beautiful nature"

]


PALAVRAS_RUINS = [

    "city",
    "street",
    "road",
    "highway",
    "car",
    "cars",
    "vehicle",
    "building",
    "hotel",
    "restaurant",
    "house",
    "home",
    "indoor",
    "room",
    "office",
    "pool",
    "swimming pool",
    "boat",
    "boats",
    "ship",
    "cruise",
    "people",
    "person",
    "man",
    "woman",
    "face",
    "selfie",
    "concert",
    "party",
    "wedding",
    "airport",
    "train",
    "bus",
    "traffic",
    "skyscraper"

]


# ============================================================
# ESCOLHER MELHORES VÍDEOS
# ============================================================

def pontuar_video(video):

    texto = ""

    texto += str(video.get("url", "")).lower()
    texto += " "
    texto += str(video.get("user", {}).get("name", "")).lower()

    score = 0

    for palavra in PALAVRAS_BOAS:

        if palavra in texto:
            score += 5

    for palavra in PALAVRAS_RUINS:

        if palavra in texto:
            score -= 20

    duracao = float(video.get("duration") or 0)

    if duracao >= 10:
        score += 10

    if duracao >= 20:
        score += 10

    if duracao >= 40:
        score += 15

    if duracao >= 60:
        score += 20

    return score


def selecionar_melhores_videos(videos, quantidade=8):

    candidatos = []

    vistos = set()

    for video in videos:

        video_id = video.get("id")

        if not video_id:
            continue

        if video_id in vistos:
            continue

        vistos.add(video_id)

        duracao = float(video.get("duration") or 0)

        if duracao < 5:
            continue

        arquivo = escolher_arquivo(video)

        if not arquivo:
            continue

        score = pontuar_video(video)

        candidatos.append({
            "video": video,
            "arquivo": arquivo,
            "score": score,
            "duracao": duracao
        })

    if not candidatos:
        return []

    candidatos.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    # Pegar uma quantidade maior para dar variedade
    melhores = candidatos[:25]

    random.shuffle(melhores)

    return melhores[:quantidade]


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
            "O vídeo baixado ficou muito pequeno."
        )


# ============================================================
# PROCESSAR UM CLIPE
# ============================================================

def processar_clipe(
    input_path,
    output_path,
    duracao,
    zoom_inicio=1.0,
    zoom_final=1.45
):

    frames = max(
        1,
        int(float(duracao) * FPS)
    )

    # Zoom progressivo.
    # O centro permanece fixo.
    filtro = (
        f"scale={WIDTH}:{HEIGHT}:"
        f"force_original_aspect_ratio=increase,"
        f"crop={WIDTH}:{HEIGHT},"
        f"zoompan="
        f"z='min({zoom_inicio}+"
        f"({zoom_final}-{zoom_inicio})*on/"
        f"{frames},"
        f"{zoom_final})':"
        f"x='iw/2-(iw/zoom/2)':"
        f"y='ih/2-(ih/zoom/2)':"
        f"d=1:"
        f"s={WIDTH}x{HEIGHT}:"
        f"fps={FPS}"
    )

    comando = [

        FFMPEG,

        "-y",

        "-hide_banner",

        "-loglevel",
        "error",

        "-i",
        input_path,

        "-vf",
        filtro,

        "-t",
        str(duracao),

        "-an",

        "-c:v",
        "libx264",

        "-preset",
        "veryfast",

        "-crf",
        "23",

        "-pix_fmt",
        "yuv420p",

        "-threads",
        "2",

        output_path
    ]

    processo = subprocess.run(
        comando,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=300
    )

    if processo.returncode != 0:

        erro = (
            processo.stderr.strip()
            or "Erro desconhecido."
        )

        raise Exception(
            "Erro processando clipe:\n\n"
            + erro[-6000:]
        )


# ============================================================
# JUNTAR CLIPES
# ============================================================

def juntar_clipes(clipes, output_path):

    lista_path = os.path.join(
        TEMP_DIR,
        f"{uuid.uuid4().hex}_lista.txt"
    )

    try:

        with open(
            lista_path,
            "w",
            encoding="utf-8"
        ) as arquivo:

            for clipe in clipes:

                caminho = os.path.abspath(clipe)

                caminho = caminho.replace(
                    "\\",
                    "/"
                )

                arquivo.write(
                    "file '"
                    + caminho.replace("'", "'\\''")
                    + "'\n"
                )

        comando = [

            FFMPEG,

            "-y",

            "-hide_banner",

            "-loglevel",
            "error",

            "-f",
            "concat",

            "-safe",
            "0",

            "-i",
            lista_path,

            "-c",
            "copy",

            "-an",

            "-movflags",
            "+faststart",

            output_path
        ]

        processo = subprocess.run(
            comando,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=300
        )

        if processo.returncode != 0:

            erro = (
                processo.stderr.strip()
                or "Erro desconhecido."
            )

            raise Exception(
                "Erro juntando os clipes:\n\n"
                + erro[-6000:]
            )

    finally:

        if os.path.exists(lista_path):

            try:
                os.remove(lista_path)
            except Exception:
                pass


# ============================================================
# CRIAR REEL
# ============================================================

def criar_reel(videos_selecionados, output_path):

    print("======================================")
    print("🎬 MONTANDO REEL")
    print("======================================")

    clipes_processados = []

    tempo_restante = DURATION

    try:

        for indice, item in enumerate(
            videos_selecionados
        ):

            if tempo_restante <= 0:
                break

            video = item["video"]
            arquivo = item["arquivo"]

            duracao_original = float(
                item["duracao"]
            )

            # Cada cena terá entre 6 e 12 segundos
            duracao_clipe = min(
                tempo_restante,
                random.uniform(7, 12),
                duracao_original
            )

            if duracao_clipe < 4:
                continue

            video_id = video.get(
                "id",
                uuid.uuid4().hex
            )

            original_path = os.path.join(
                TEMP_DIR,
                f"{video_id}_{uuid.uuid4().hex[:8]}.mp4"
            )

            processado_path = os.path.join(
                TEMP_DIR,
                f"processed_{uuid.uuid4().hex}.mp4"
            )

            try:

                print(
                    f"🎥 Clipe {indice + 1}"
                    f" | {duracao_clipe:.1f}s"
                )

                baixar_video(
                    arquivo["link"],
                    original_path
                )

                # Zoom diferente em cada cena
                zoom_final = random.uniform(
                    1.35,
                    1.60
                )

                processar_clipe(
                    original_path,
                    processado_path,
                    duracao_clipe,
                    1.0,
                    zoom_final
                )

                clipes_processados.append(
                    processado_path
                )

                tempo_restante -= duracao_clipe

            finally:

                if os.path.exists(original_path):

                    try:
                        os.remove(original_path)
                    except Exception:
                        pass

        if not clipes_processados:

            raise Exception(
                "Não foi possível processar nenhum clipe."
            )

        print(
            f"🎞️ Total de clipes: "
            f"{len(clipes_processados)}"
        )

        juntar_clipes(
            clipes_processados,
            output_path
        )

        if not os.path.exists(output_path):

            raise Exception(
                "O arquivo final não foi criado."
            )

        tamanho = os.path.getsize(
            output_path
        )

        print(
            f"✅ Reel final: "
            f"{tamanho / 1024 / 1024:.1f} MB"
        )

        if tamanho < 100000:

            raise Exception(
                "O vídeo final ficou muito pequeno."
            )

    finally:

        for clipe in clipes_processados:

            if os.path.exists(clipe):

                try:
                    os.remove(clipe)
                except Exception:
                    pass


# ============================================================
# GERAR VÍDEO
# ============================================================

def gerar_video(pais):

    nome_pais = PAISES.get(
        pais,
        pais
    )

    # Consultas diferentes para aumentar a chance
    # de encontrar paisagens realmente relacionadas
    # ao país selecionado.
    consultas = [

        f"{nome_pais} nature landscape",

        f"{nome_pais} mountain waterfall",

        f"{nome_pais} cliff viewpoint",

        f"{nome_pais} dramatic mountain",

        f"{nome_pais} canyon waterfall",

        f"{nome_pais} ocean cliff",

        f"{nome_pais} scenic nature",

        f"{nome_pais} mountain lake",

        f"{nome_pais} waterfall landscape",

        f"{nome_pais} beautiful landscape"

    ]

    random.shuffle(consultas)

    todos_videos = []

    print("")
    print("======================================")
    print("🏔️ CLIFF & NATURE REEL")
    print("🌎 PAÍS:", pais)
    print("======================================")

    # Fazer várias pesquisas
    for consulta in consultas[:8]:

        print(
            "🔎 Busca:",
            consulta
        )

        try:

            videos = buscar_videos(
                consulta
            )

            print(
                "   Encontrados:",
                len(videos)
            )

            todos_videos.extend(
                videos
            )

        except Exception as erro:

            print(
                "⚠️ Erro na busca:",
                erro
            )

        if len(todos_videos) >= 300:
            break

    if not todos_videos:

        raise Exception(
            "Nenhum vídeo encontrado no Pexels."
        )

    print(
        "🎥 Total de resultados:",
        len(todos_videos)
    )

    selecionados = selecionar_melhores_videos(
        todos_videos,
        quantidade=12
    )

    if not selecionados:

        raise Exception(
            "Não encontrei vídeos verticais adequados "
            "para paisagens naturais."
        )

    print(
        "✅ Vídeos selecionados:",
        len(selecionados)
    )

    identificador = uuid.uuid4().hex

    output_name = (
        "cliff_reel_"
        + pais.lower().replace(" ", "_")
        + "_"
        + identificador[:8]
        + ".mp4"
    )

    output_path = os.path.join(
        VIDEO_DIR,
        output_name
    )

    criar_reel(
        selecionados,
        output_path
    )

    return output_path


# ============================================================
# ROTA PRINCIPAL
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

                download_name=(
                    "cliff_nature_reel.mp4"
                ),

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
            O vídeo demorou muito para ser processado.
            Tente novamente.
            </p>

            <br>

            <a href="/" style="color:white;">
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

            erro_html = html.escape(
                str(erro)
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
            ">{erro_html}</pre>

            <br>

            <a href="/" style="color:white;">
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

        "app": "Cliff & Nature Reel",

        "type": "multi clip nature video",

        "theme":
            "cliffs, waterfalls, mountains, lakes and viewpoints",

        "duration":
            DURATION,

        "resolution":
            f"{WIDTH}x{HEIGHT}",

        "audio":
            False,

        "text":
            False

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