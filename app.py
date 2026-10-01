import os
import random
import uuid
import requests
import subprocess
import html
import shutil

from concurrent.futures import ThreadPoolExecutor, as_completed

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
OUTPUT_DIR = "outputs"

os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

WATERMARK = "mundo.afora0"


# ============================================================
# PAÍSES / DESTINOS
# ============================================================

PAISES = {

    "🇧🇷 Brasil": [
        "Brazil ocean cliffs",
        "Brazil sea cliffs",
        "Brazil mountains lake",
        "Brazil mountain lake",
        "Brazil green valley mountains",
        "Brazil mountain valley",
        "Brazil mountain cabin",
        "Brazil lake mountains",
        "Brazil scenic mountains",
        "Brazil dramatic nature",
        "Brazil coastline cliffs",
        "Brazil green mountains",
        "Brazil fjord landscape"
    ],

    "🇫🇴 Ilhas Faroé": [
        "Faroe Islands ocean cliffs",
        "Faroe Islands sea cliffs",
        "Faroe Islands mountains ocean",
        "Faroe Islands green mountains",
        "Faroe Islands mountain valley",
        "Faroe Islands green valley",
        "Faroe Islands fjord",
        "Faroe Islands fjord mountains",
        "Faroe Islands lake mountains",
        "Faroe Islands mountain lake",
        "Faroe Islands dramatic landscape",
        "Faroe Islands ocean landscape",
        "Faroe Islands cliffs ocean",
        "Faroe Islands green valley cabin",
        "Faroe Islands mountain cabin"
    ],

    "🇨🇭 Suíça": [
        "Switzerland mountain lake",
        "Swiss Alps lake",
        "Switzerland green valley mountains",
        "Swiss mountain valley",
        "Switzerland mountain cabin",
        "Swiss Alps cabin",
        "Switzerland scenic mountains",
        "Swiss Alps landscape",
        "Switzerland lake mountains",
        "Swiss Alps green valley",
        "Switzerland dramatic mountains"
    ],

    "🇳🇴 Noruega": [
        "Norway fjord mountains",
        "Norway ocean cliffs",
        "Norway mountain lake",
        "Norway green valley",
        "Norway mountain cabin",
        "Norwegian fjord landscape",
        "Norway dramatic landscape",
        "Norway sea cliffs",
        "Norway mountains lake"
    ],

    "🇮🇸 Islândia": [
        "Iceland mountain lake",
        "Iceland ocean cliffs",
        "Iceland green valley",
        "Iceland mountain valley",
        "Iceland dramatic mountains",
        "Iceland coastline cliffs",
        "Iceland fjord landscape",
        "Iceland mountain waterfall"
    ],

    "🇨🇦 Canadá": [
        "Canada mountain lake",
        "Canadian Rockies lake",
        "Canada green valley mountains",
        "Canada mountain cabin",
        "Canadian Rockies cabin",
        "Canada ocean cliffs",
        "Canada dramatic landscape",
        "Canada mountain valley"
    ],

    "🇳🇿 Nova Zelândia": [
        "New Zealand mountain lake",
        "New Zealand green valley",
        "New Zealand mountain cabin",
        "New Zealand fjord mountains",
        "New Zealand ocean cliffs",
        "New Zealand dramatic landscape",
        "New Zealand lake mountains"
    ],

    "🇦🇹 Áustria": [
        "Austria mountain lake",
        "Austrian Alps lake",
        "Austria mountain cabin",
        "Austrian Alps cabin",
        "Austria green valley",
        "Austria mountain valley",
        "Austria scenic mountains"
    ],

    "🇸🇮 Eslovênia": [
        "Slovenia mountain lake",
        "Slovenia green valley",
        "Slovenia mountain cabin",
        "Slovenia Alps lake",
        "Slovenia mountain landscape"
    ],

    "🇫🇷 França": [
        "French Alps mountain lake",
        "France mountain valley",
        "French Alps cabin",
        "France green mountains",
        "French Alps landscape",
        "France lake mountains"
    ],

    "🇮🇹 Itália": [
        "Italian Alps mountain lake",
        "Dolomites mountain lake",
        "Dolomites valley",
        "Dolomites mountain cabin",
        "Italy mountain valley",
        "Italian Alps landscape"
    ],

    "🇺🇸 Estados Unidos": [
        "USA mountain lake",
        "Rocky Mountains lake",
        "United States mountain cabin",
        "USA green valley mountains",
        "USA ocean cliffs",
        "California ocean cliffs",
        "Alaska mountain lake",
        "Alaska dramatic landscape"
    ],

    "🇯🇵 Japão": [
        "Japan mountain lake",
        "Japan green valley mountains",
        "Japan mountain cabin",
        "Japan mountain landscape",
        "Japan lake mountains"
    ],

    "🇵🇪 Peru": [
        "Peru mountain lake",
        "Peru green mountain valley",
        "Peru dramatic mountains",
        "Peru mountain landscape",
        "Peru Andes lake"
    ],

    "🇨🇱 Chile": [
        "Chile Patagonia mountains lake",
        "Chile mountain lake",
        "Patagonia green valley",
        "Chile fjord mountains",
        "Chile dramatic landscape",
        "Patagonia mountain cabin"
    ],

    "🇦🇷 Argentina": [
        "Argentina Patagonia mountain lake",
        "Argentina mountain valley",
        "Patagonia lake mountains",
        "Argentina mountain cabin",
        "Argentina dramatic landscape"
    ]
}


# ============================================================
# PALAVRAS ACEITAS
# ============================================================

PALAVRAS_BOAS = [
    "cliff",
    "cliffs",
    "cliffside",
    "sea cliff",
    "sea cliffs",
    "ocean",
    "ocean cliffs",
    "ocean landscape",
    "sea",
    "coast",
    "coastline",

    "mountain",
    "mountains",
    "mountain view",
    "mountain landscape",
    "alps",
    "rocky mountains",
    "andes",

    "lake",
    "lakes",
    "mountain lake",
    "lake mountains",

    "valley",
    "green valley",
    "mountain valley",

    "fjord",
    "fjords",

    "waterfall",
    "waterfalls",
    "mountain waterfall",

    "cabin",
    "mountain cabin",
    "chalet",
    "mountain chalet",

    "landscape",
    "nature",
    "scenic",
    "scenery",
    "view",
    "viewpoint",
    "panorama",
    "panoramic",
    "dramatic",
    "wilderness",

    "faroe",
    "faroe islands",
    "switzerland",
    "swiss alps",
    "norway",
    "iceland",
    "patagonia",
    "dolomites",
    "new zealand"
]


# ============================================================
# PALAVRAS PROIBIDAS
# ============================================================

PALAVRAS_RUINS = [
    # Pessoas
    "people",
    "person",
    "man",
    "woman",
    "child",
    "children",
    "face",
    "selfie",
    "portrait",

    # Cidades
    "city",
    "street",
    "road",
    "highway",
    "traffic",
    "downtown",
    "building",
    "skyscraper",

    # Veículos
    "car",
    "cars",
    "vehicle",
    "truck",
    "bus",
    "motorcycle",
    "train",
    "airport",

    # Construções
    "hotel",
    "restaurant",
    "house",
    "home",
    "office",
    "indoor",
    "room",

    # Embarcações
    "boat",
    "boats",
    "ship",
    "cruise",
    "yacht",
    "sailboat",

    # Trilhas / caminhada
    "hiking",
    "hike",
    "trail",
    "trails",
    "trekking",
    "trek",
    "walking",
    "walking trail",
    "walking path",
    "footpath",
    "path",

    # Eventos
    "concert",
    "party",
    "wedding",
    "festival",

    # Piscinas
    "pool",
    "swimming pool"
]


# ============================================================
# HTML
# ============================================================

HTML = """
<!DOCTYPE html>
<html lang="pt-BR">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>Mundo Afora</title>

<style>

body {
    margin: 0;
    padding: 20px;
    background: #111;
    color: white;
    font-family: Arial, sans-serif;
}

.container {
    max-width: 600px;
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

label {
    display: block;
    margin-bottom: 8px;
    font-weight: bold;
}

select,
button {
    width: 100%;
    padding: 15px;
    margin-bottom: 18px;
    border-radius: 10px;
    border: none;
    font-size: 16px;
}

select {
    background: #222;
    color: white;
}

button {
    background: white;
    color: black;
    font-weight: bold;
    cursor: pointer;
}

.info {
    background: #1d1d1d;
    padding: 15px;
    border-radius: 10px;
    line-height: 1.6;
    color: #ccc;
}

</style>

</head>

<body>

<div class="container">

<h1>🌎 Mundo Afora</h1>

<div class="subtitle">
Paisagens incríveis do mundo
</div>

<form method="POST">

<label>Escolha o destino</label>

<select name="pais" required>

{% for pais in paises %}

<option value="{{ pais }}">
{{ pais }}
</option>

{% endfor %}

</select>

<button type="submit">
🎬 GERAR VÍDEO
</button>

</form>

<div class="info">

<strong>Configuração:</strong><br>

📱 1080 × 1920<br>
🎞️ 24 FPS<br>
⏱️ Aproximadamente 60 segundos<br>
🔇 Sem áudio<br>
🚫 Sem textos<br>
💧 Marca d'água: mundo.afora0<br>
🎥 Vídeos reais do Pexels

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
        raise RuntimeError(
            "PEXELS_API_KEY não configurada."
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

    resposta = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=30
    )

    resposta.raise_for_status()

    dados = resposta.json()

    return dados.get("videos", [])


# ============================================================
# ESCOLHER ARQUIVO DO VÍDEO
# ============================================================

def escolher_arquivo_video(video):

    arquivos = video.get("video_files", [])

    candidatos = []

    for arquivo in arquivos:

        link = arquivo.get("link")

        if not link:
            continue

        tipo = arquivo.get("file_type", "")

        if "mp4" not in tipo.lower():
            continue

        largura = arquivo.get("width") or 0
        altura = arquivo.get("height") or 0

        if largura <= 0 or altura <= 0:
            continue

        proporcao = altura / largura

        # Queremos vídeo vertical
        if proporcao < 1.35:
            continue

        # Evita arquivos gigantes
        if largura > 2160 or altura > 3840:
            continue

        candidatos.append(
            (
                largura * altura,
                link,
                largura,
                altura
            )
        )

    if not candidatos:
        return None

    candidatos.sort(
        key=lambda x: x[0],
        reverse=True
    )

    return candidatos[0]


# ============================================================
# PONTUAR VÍDEO
# ============================================================

def pontuar_video(video):

    texto = ""

    try:
        texto += " " + str(video.get("url", ""))
        texto += " " + str(video.get("image", ""))
        texto += " " + str(
            video.get("user", {}).get("name", "")
        )
    except Exception:
        pass

    texto = texto.lower()

    pontos = 0

    for palavra in PALAVRAS_BOAS:

        if palavra in texto:
            pontos += 5

    for palavra in PALAVRAS_RUINS:

        if palavra in texto:
            pontos -= 20

    return pontos


# ============================================================
# SELECIONAR VÍDEOS
# ============================================================

def selecionar_videos(videos):

    candidatos = []

    for video in videos:

        arquivo = escolher_arquivo_video(video)

        if not arquivo:
            continue

        pontuacao = pontuar_video(video)

        candidatos.append(
            (
                pontuacao,
                video,
                arquivo
            )
        )

    candidatos.sort(
        key=lambda x: x[0],
        reverse=True
    )

    # Pega os melhores
    candidatos = candidatos[:40]

    # Mistura um pouco para não ficar sempre igual
    random.shuffle(candidatos)

    selecionados = candidatos[:12]

    return selecionados


# ============================================================
# BAIXAR UM VÍDEO
# ============================================================

def baixar_video(item, index):

    _, video, arquivo = item

    _, link, largura, altura = arquivo

    nome = f"{uuid.uuid4().hex}_{index}.mp4"

    caminho = os.path.join(
        VIDEO_DIR,
        nome
    )

    try:

        resposta = requests.get(
            link,
            stream=True,
            timeout=60
        )

        resposta.raise_for_status()

        with open(caminho, "wb") as arquivo_saida:

            for bloco in resposta.iter_content(
                chunk_size=1024 * 1024
            ):

                if bloco:
                    arquivo_saida.write(bloco)

        if os.path.getsize(caminho) < 10000:

            try:
                os.remove(caminho)
            except:
                pass

            return None

        return caminho

    except Exception as erro:

        print(
            f"Erro baixando vídeo {index}: {erro}"
        )

        try:
            if os.path.exists(caminho):
                os.remove(caminho)
        except:
            pass

        return None


# ============================================================
# DOWNLOAD PARALELO
# ============================================================

def baixar_videos_paralelo(selecionados):

    caminhos = []

    with ThreadPoolExecutor(
        max_workers=3
    ) as executor:

        tarefas = []

        for index, item in enumerate(
            selecionados
        ):

            tarefas.append(
                executor.submit(
                    baixar_video,
                    item,
                    index
                )
            )

        for tarefa in as_completed(tarefas):

            resultado = tarefa.result()

            if resultado:
                caminhos.append(resultado)

    return caminhos


# ============================================================
# PROCESSAR CLIPE
# ============================================================

def processar_clipe_zoom(
    input_path,
    output_path,
    duracao,
    zoom_final=1.10
):

    """
    Processamento ESTÁVEL.

    Não usa crop dinâmico.
    Não usa zoompan.

    O vídeo recebe um pequeno zoom fixo
    para preencher a tela vertical.
    """

    try:

        zoom_final = float(zoom_final)

    except:

        zoom_final = 1.10

    if zoom_final < 1.0:
        zoom_final = 1.0

    if zoom_final > 1.20:
        zoom_final = 1.20

    # Tamanho maior proporcional ao zoom
    largura_base = int(
        WIDTH * zoom_final
    )

    altura_base = int(
        HEIGHT * zoom_final
    )

    filtro = (
        f"scale={largura_base}:{altura_base}:"
        "force_original_aspect_ratio=increase,"
        f"crop={largura_base}:{altura_base},"
        f"scale={WIDTH}:{HEIGHT},"
        "fps=24,"
        "setsar=1"
    )

    comando = [

        FFMPEG,

        "-y",

        "-i",
        input_path,

        "-t",
        str(duracao),

        "-vf",
        filtro,

        "-an",

        "-c:v",
        "libx264",

        "-preset",
        "veryfast",

        "-crf",
        "23",

        "-pix_fmt",
        "yuv420p",

        "-movflags",
        "+faststart",

        output_path
    ]

    resultado = subprocess.run(
        comando,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if resultado.returncode != 0:

        print(
            "ERRO FFmpeg PROCESSANDO CLIPE:"
        )

        print(
            resultado.stderr[-5000:]
        )

        raise RuntimeError(
            "Falha ao processar clipe."
        )


# ============================================================
# PROCESSAR TODOS OS CLIPES
# ============================================================

def preparar_clipes(caminhos):

    processados = []

    for index, caminho in enumerate(
        caminhos
    ):

        saida = os.path.join(
            TEMP_DIR,
            f"clip_{uuid.uuid4().hex}.mp4"
        )

        # Varia discretamente o zoom
        zoom = random.uniform(
            1.04,
            1.12
        )

        try:

            processar_clipe_zoom(
                caminho,
                saida,
                duracao=8,
                zoom_final=zoom
            )

            processados.append(saida)

        except Exception as erro:

            print(
                f"Erro no clipe {index}: {erro}"
            )

    return processados


# ============================================================
# JUNTAR CLIPES
# ============================================================

def juntar_clipes(
    caminhos,
    output_path
):

    if not caminhos:
        raise RuntimeError(
            "Nenhum clipe disponível."
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

        for caminho in caminhos:

            caminho_absoluto = os.path.abspath(
                caminho
            )

            caminho_ffmpeg = (
                caminho_absoluto
                .replace("\\", "/")
                .replace("'", "'\\''")
            )

            arquivo.write(
                f"file '{caminho_ffmpeg}'\n"
            )

    comando = [

        FFMPEG,

        "-y",

        "-f",
        "concat",

        "-safe",
        "0",

        "-i",
        lista,

        "-t",
        str(DURATION),

        "-c",
        "copy",

        "-movflags",
        "+faststart",

        output_path
    ]

    resultado = subprocess.run(
        comando,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    try:
        os.remove(lista)
    except:
        pass

    if resultado.returncode != 0:

        print(
            "ERRO FFmpeg JUNTANDO CLIPES:"
        )

        print(
            resultado.stderr[-5000:]
        )

        raise RuntimeError(
            "Falha ao juntar os vídeos."
        )


# ============================================================
# MARCA D'ÁGUA
# ============================================================

def aplicar_marca_dagua(
    input_path,
    output_path
):

    texto = WATERMARK.replace(
        "'",
        "\\'"
    )

    filtro = (
        "drawtext="
        f"text='{texto}':"
        "font='DejaVu Sans':"
        "fontcolor=white@0.75:"
        "fontsize=32:"
        "x=w-tw-45:"
        "y=h-th-55:"
        "shadowcolor=black@0.55:"
        "shadowx=2:"
        "shadowy=2"
    )

    comando = [

        FFMPEG,

        "-y",

        "-i",
        input_path,

        "-vf",
        filtro,

        "-an",

        "-c:v",
        "libx264",

        "-preset",
        "veryfast",

        "-crf",
        "23",

        "-pix_fmt",
        "yuv420p",

        "-movflags",
        "+faststart",

        output_path
    ]

    resultado = subprocess.run(
        comando,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if resultado.returncode != 0:

        print(
            "ERRO FFmpeg MARCA D'ÁGUA:"
        )

        print(
            resultado.stderr[-5000:]
        )

        raise RuntimeError(
            "Falha ao aplicar marca d'água."
        )


# ============================================================
# LIMPEZA
# ============================================================

def limpar_temporarios():

    for pasta in [
        VIDEO_DIR,
        TEMP_DIR
    ]:

        if not os.path.exists(pasta):
            continue

        for nome in os.listdir(pasta):

            caminho = os.path.join(
                pasta,
                nome
            )

            try:

                if os.path.isfile(caminho):
                    os.remove(caminho)

                elif os.path.isdir(caminho):
                    shutil.rmtree(caminho)

            except Exception as erro:

                print(
                    f"Erro limpando {caminho}: {erro}"
                )


# ============================================================
# CRIAR REEL
# ============================================================

def criar_reel(pais):

    limpar_temporarios()

    consultas = PAISES.get(
        pais,
        []
    )

    if not consultas:

        raise RuntimeError(
            "Destino inválido."
        )

    todos_videos = []

    # Faz várias pesquisas
    consultas_embaralhadas = consultas.copy()

    random.shuffle(
        consultas_embaralhadas
    )

    for query in consultas_embaralhadas[:8]:

        try:

            print(
                f"Pesquisando: {query}"
            )

            videos = buscar_videos(
                query
            )

            todos_videos.extend(
                videos
            )

        except Exception as erro:

            print(
                f"Erro pesquisando {query}: {erro}"
            )

    if not todos_videos:

        raise RuntimeError(
            "O Pexels não retornou vídeos."
        )

    # Remove duplicados
    unicos = {}

    for video in todos_videos:

        video_id = video.get("id")

        if video_id:
            unicos[video_id] = video

    todos_videos = list(
        unicos.values()
    )

    print(
        f"Vídeos encontrados: {len(todos_videos)}"
    )

    selecionados = selecionar_videos(
        todos_videos
    )

    if not selecionados:

        raise RuntimeError(
            "Nenhum vídeo vertical adequado foi encontrado."
        )

    print(
        f"Vídeos selecionados: {len(selecionados)}"
    )

    caminhos = baixar_videos_paralelo(
        selecionados
    )

    if not caminhos:

        raise RuntimeError(
            "Não foi possível baixar os vídeos."
        )

    print(
        f"Vídeos baixados: {len(caminhos)}"
    )

    processados = preparar_clipes(
        caminhos
    )

    if not processados:

        raise RuntimeError(
            "Nenhum clipe pôde ser processado."
        )

    print(
        f"Clipes processados: {len(processados)}"
    )

    base = os.path.join(
        TEMP_DIR,
        f"base_{uuid.uuid4().hex}.mp4"
    )

    juntar_clipes(
        processados,
        base
    )

    nome_final = (
        f"mundo_afora_"
        f"{uuid.uuid4().hex}.mp4"
    )

    final = os.path.join(
        OUTPUT_DIR,
        nome_final
    )

    aplicar_marca_dagua(
        base,
        final
    )

    return final


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

        try:

            print(
                f"Gerando vídeo: {pais}"
            )

            arquivo = criar_reel(
                pais
            )

            return send_file(
                arquivo,
                as_attachment=True,
                download_name=os.path.basename(
                    arquivo
                ),
                mimetype="video/mp4"
            )

        except Exception as erro:

            print(
                "ERRO GERAL:"
            )

            print(
                str(erro)
            )

            mensagem = html.escape(
                str(erro)
            )

            return f"""
            <html>
            <body style="
                background:#111;
                color:white;
                font-family:Arial;
                padding:30px;
            ">

            <h2>❌ Erro ao gerar vídeo</h2>

            <p>{mensagem}</p>

            <br>

            <a
                href="/"
                style="
                    color:white;
                    background:#333;
                    padding:12px 20px;
                    border-radius:8px;
                    text-decoration:none;
                "
            >
                Voltar
            </a>

            </body>
            </html>
            """

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
        "project": "Mundo Afora",
        "resolution": "1080x1920",
        "fps": FPS,
        "duration": DURATION,
        "audio": False,
        "watermark": WATERMARK
    }


# ============================================================
# START
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