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
# PAÍSES
# ============================================================

PAISES = {

    "🇧🇷 Brasil": [
        "Brazil mountains lake",
        "Brazil mountain lake",
        "Brazil green valley",
        "Brazil mountain valley",
        "Brazil ocean cliffs",
        "Brazil sea cliffs",
        "Brazil lake mountains",
        "Brazil mountain cabin",
        "Brazil scenic mountains",
        "Brazil coastline cliffs"
    ],

    "🇫🇴 Ilhas Faroé": [
        "Faroe Islands mountains",
        "Faroe Islands ocean cliffs",
        "Faroe Islands sea cliffs",
        "Faroe Islands green valley",
        "Faroe Islands mountain valley",
        "Faroe Islands fjord",
        "Faroe Islands fjord mountains",
        "Faroe Islands lake mountains",
        "Faroe Islands green mountains",
        "Faroe Islands dramatic landscape",
        "Faroe Islands coastline"
    ],

    "🇨🇭 Suíça": [
        "Switzerland mountain lake",
        "Swiss Alps lake",
        "Switzerland green valley",
        "Swiss mountain valley",
        "Switzerland mountain cabin",
        "Swiss Alps cabin",
        "Switzerland scenic mountains",
        "Swiss Alps landscape",
        "Switzerland lake mountains"
    ],

    "🇳🇴 Noruega": [
        "Norway fjord mountains",
        "Norway ocean cliffs",
        "Norway mountain lake",
        "Norway green valley",
        "Norway mountain cabin",
        "Norwegian fjord landscape",
        "Norway dramatic landscape",
        "Norway sea cliffs"
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
        "New Zealand dramatic landscape"
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
        "French Alps landscape"
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
# PALAVRAS BOAS
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
    "andes",
    "rocky mountains",

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
    "people",
    "person",
    "man",
    "woman",
    "child",
    "children",
    "face",
    "selfie",
    "portrait",

    "city",
    "street",
    "road",
    "highway",
    "traffic",
    "downtown",
    "building",
    "skyscraper",

    "car",
    "cars",
    "vehicle",
    "truck",
    "bus",
    "motorcycle",
    "train",
    "airport",

    "hotel",
    "restaurant",
    "house",
    "home",
    "office",
    "indoor",
    "room",

    "boat",
    "boats",
    "ship",
    "cruise",
    "yacht",
    "sailboat",

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

    "concert",
    "party",
    "wedding",
    "festival",

    "pool",
    "swimming pool"
]


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

<title>Mundo Afora</title>

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
}

.container {
    width: 100%;
    max-width: 600px;
    margin: auto;
}

h1 {
    text-align: center;
    margin-top: 20px;
    margin-bottom: 5px;
}

.subtitle {
    text-align: center;
    color: #999;
    margin-bottom: 30px;
}

label {
    display: block;
    margin-bottom: 8px;
    font-weight: bold;
}

select {
    width: 100%;
    padding: 15px;
    background: #222;
    color: white;
    border: 1px solid #333;
    border-radius: 10px;
    font-size: 16px;
    margin-bottom: 20px;
}

button {
    width: 100%;
    padding: 16px;
    background: white;
    color: black;
    border: none;
    border-radius: 10px;
    font-size: 17px;
    font-weight: bold;
    cursor: pointer;
}

.info {
    margin-top: 25px;
    padding: 18px;
    background: #1b1b1b;
    border-radius: 12px;
    color: #bbb;
    line-height: 1.7;
}

</style>

</head>

<body>

<div class="container">

<h1>🌎 Mundo Afora</h1>

<div class="subtitle">
Paisagens incríveis pelo mundo
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

<strong>Vídeo:</strong><br>

📱 1080 × 1920<br>
🎞️ 24 FPS<br>
⏱️ 60 segundos<br>
🔇 Sem áudio<br>
🚫 Sem textos<br>
💧 @mundo.afora0<br>
🎥 Vídeos reais do Pexels

</div>

</div>

</body>

</html>
"""


# ============================================================
# BUSCAR NO PEXELS
# ============================================================

def buscar_videos(query):

    if not PEXELS_API_KEY:

        raise RuntimeError(
            "PEXELS_API_KEY não configurada no Railway."
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
        timeout=40
    )

    resposta.raise_for_status()

    dados = resposta.json()

    return dados.get(
        "videos",
        []
    )


# ============================================================
# ESCOLHER ARQUIVO
# ============================================================

def escolher_arquivo_video(video):

    arquivos = video.get(
        "video_files",
        []
    )

    candidatos = []

    for arquivo in arquivos:

        link = arquivo.get("link")

        if not link:
            continue

        file_type = str(
            arquivo.get(
                "file_type",
                ""
            )
        ).lower()

        if "mp4" not in file_type:
            continue

        largura = int(
            arquivo.get(
                "width",
                0
            ) or 0
        )

        altura = int(
            arquivo.get(
                "height",
                0
            ) or 0
        )

        if largura <= 0 or altura <= 0:
            continue

        proporcao = altura / largura

        # Vertical
        if proporcao < 1.30:
            continue

        # Evita arquivos absurdamente grandes
        if largura > 3840 or altura > 7680:
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

    # Melhor resolução disponível
    candidatos.sort(
        key=lambda x: x[0],
        reverse=True
    )

    return candidatos[0]


# ============================================================
# PONTUAÇÃO
# ============================================================

def pontuar_video(video):

    texto = ""

    texto += str(
        video.get(
            "url",
            ""
        )
    )

    texto += " "

    texto += str(
        video.get(
            "image",
            ""
        )
    )

    try:

        texto += " "

        texto += str(
            video.get(
                "user",
                {}
            ).get(
                "name",
                ""
            )
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
            pontos -= 30

    return pontos


# ============================================================
# SELECIONAR
# ============================================================

def selecionar_videos(videos):

    candidatos = []

    for video in videos:

        arquivo = escolher_arquivo_video(
            video
        )

        if not arquivo:
            continue

        pontos = pontuar_video(
            video
        )

        candidatos.append(
            (
                pontos,
                video,
                arquivo
            )
        )

    candidatos.sort(
        key=lambda x: x[0],
        reverse=True
    )

    # Mantém os melhores
    candidatos = candidatos[:50]

    random.shuffle(
        candidatos
    )

    # Até 15 clipes
    return candidatos[:15]


# ============================================================
# DOWNLOAD
# ============================================================

def baixar_video(item, numero):

    _, video, arquivo = item

    _, link, largura, altura = arquivo

    nome = (
        f"{uuid.uuid4().hex}_"
        f"{numero}.mp4"
    )

    caminho = os.path.join(
        VIDEO_DIR,
        nome
    )

    try:

        print(
            f"[DOWNLOAD] {numero} "
            f"{largura}x{altura}"
        )

        resposta = requests.get(
            link,
            stream=True,
            timeout=90
        )

        resposta.raise_for_status()

        with open(
            caminho,
            "wb"
        ) as saida:

            for bloco in resposta.iter_content(
                chunk_size=1024 * 1024
            ):

                if bloco:

                    saida.write(
                        bloco
                    )

        tamanho = os.path.getsize(
            caminho
        )

        if tamanho < 10000:

            raise RuntimeError(
                "Arquivo baixado está vazio."
            )

        print(
            f"[OK DOWNLOAD] {numero} "
            f"{tamanho / 1024 / 1024:.1f} MB"
        )

        return caminho

    except Exception as erro:

        print(
            f"[ERRO DOWNLOAD] {numero}: "
            f"{erro}"
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

def baixar_videos_paralelo(
    selecionados
):

    caminhos = []

    with ThreadPoolExecutor(
        max_workers=3
    ) as executor:

        tarefas = []

        for numero, item in enumerate(
            selecionados
        ):

            tarefas.append(
                executor.submit(
                    baixar_video,
                    item,
                    numero
                )
            )

        for tarefa in as_completed(
            tarefas
        ):

            try:

                resultado = tarefa.result()

                if resultado:
                    caminhos.append(
                        resultado
                    )

            except Exception as erro:

                print(
                    f"Erro em download paralelo: "
                    f"{erro}"
                )

    return caminhos


# ============================================================
# VERIFICAR VÍDEO COM FFPROBE
# ============================================================

def verificar_video(caminho):

    comando = [

        FFMPEG,

        "-v",
        "error",

        "-i",
        caminho,

        "-f",
        "null",

        "-"
    ]

    resultado = subprocess.run(
        comando,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if resultado.returncode != 0:

        print(
            "[VÍDEO INVÁLIDO]"
        )

        print(
            resultado.stderr[-3000:]
        )

        return False

    return True


# ============================================================
# PROCESSAR CLIPE
# ============================================================

def processar_clipe(
    input_path,
    output_path,
    numero
):

    print(
        f"[PROCESSANDO] Clipe {numero}"
    )

    # --------------------------------------------------------
    # FILTRO SIMPLES E ESTÁVEL
    # --------------------------------------------------------
    #
    # Primeiro aumenta o vídeo o suficiente para preencher
    # 1080x1920.
    #
    # Depois corta o excesso no centro.
    #
    # Não existe expressão com "t".
    # Não existe zoompan.
    # Não existe crop dinâmico.
    #
    # --------------------------------------------------------

    filtro = (
        "scale="
        "1080:1920:"
        "force_original_aspect_ratio=increase,"
        "crop=1080:1920:"
        "(iw-1080)/2:"
        "(ih-1920)/2,"
        "setsar=1,"
        "fps=24"
    )

    comando = [

        FFMPEG,

        "-y",

        "-hide_banner",

        "-loglevel",
        "error",

        "-i",
        input_path,

        "-t",
        "8",

        "-vf",
        filtro,

        "-an",

        "-c:v",
        "libx264",

        "-preset",
        "veryfast",

        "-crf",
        "24",

        "-pix_fmt",
        "yuv420p",

        "-r",
        "24",

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
            "===================================="
        )

        print(
            f"[ERRO PROCESSANDO CLIPE {numero}]"
        )

        print(
            resultado.stderr
        )

        print(
            "===================================="
        )

        return False

    if not os.path.exists(
        output_path
    ):

        print(
            f"[ERRO] Arquivo não criado: "
            f"{output_path}"
        )

        return False

    tamanho = os.path.getsize(
        output_path
    )

    if tamanho < 50000:

        print(
            f"[ERRO] Arquivo processado "
            f"muito pequeno: {tamanho}"
        )

        return False

    print(
        f"[OK PROCESSADO] Clipe {numero}"
    )

    return True


# ============================================================
# PREPARAR CLIPES
# ============================================================

def preparar_clipes(
    caminhos
):

    processados = []

    for numero, caminho in enumerate(
        caminhos
    ):

        # Verifica arquivo original
        if not verificar_video(
            caminho
        ):

            print(
                f"[PULANDO] Vídeo inválido "
                f"{numero}"
            )

            continue

        saida = os.path.join(
            TEMP_DIR,
            f"clip_{numero}_"
            f"{uuid.uuid4().hex}.mp4"
        )

        sucesso = processar_clipe(
            caminho,
            saida,
            numero
        )

        if sucesso:

            processados.append(
                saida
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
            "Não existem clipes para juntar."
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

            absoluto = os.path.abspath(
                caminho
            )

            absoluto = absoluto.replace(
                "\\",
                "/"
            )

            arquivo.write(
                "file '"
                + absoluto.replace(
                    "'",
                    "'\\''"
                )
                + "'\n"
            )

    print(
        f"[JUNTANDO] {len(caminhos)} clipes"
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
            "[ERRO JUNTANDO]"
        )

        print(
            resultado.stderr
        )

        raise RuntimeError(
            "Erro ao juntar os clipes."
        )

    if not os.path.exists(
        output_path
    ):

        raise RuntimeError(
            "Arquivo final não foi criado."
        )

    print(
        "[OK] Clipes juntados"
    )


# ============================================================
# MARCA D'ÁGUA
# ============================================================

def aplicar_marca_dagua(
    input_path,
    output_path
):

    print(
        "[MARCA D'ÁGUA] Aplicando..."
    )

    texto = WATERMARK

    filtro = (
        "drawtext="
        f"text='{texto}':"
        "fontcolor=white@0.72:"
        "fontsize=30:"
        "x=w-tw-40:"
        "y=h-th-45:"
        "shadowcolor=black@0.50:"
        "shadowx=2:"
        "shadowy=2"
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

        "-an",

        "-c:v",
        "libx264",

        "-preset",
        "veryfast",

        "-crf",
        "24",

        "-pix_fmt",
        "yuv420p",

        "-r",
        "24",

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
            "[ERRO MARCA D'ÁGUA]"
        )

        print(
            resultado.stderr
        )

        raise RuntimeError(
            "Erro ao aplicar a marca d'água."
        )

    if not os.path.exists(
        output_path
    ):

        raise RuntimeError(
            "Vídeo final não foi criado."
        )

    print(
        "[OK] Marca d'água aplicada"
    )


# ============================================================
# LIMPAR TEMPORÁRIOS
# ============================================================

def limpar_temporarios():

    for pasta in [
        VIDEO_DIR,
        TEMP_DIR
    ]:

        if not os.path.exists(
            pasta
        ):
            continue

        for nome in os.listdir(
            pasta
        ):

            caminho = os.path.join(
                pasta,
                nome
            )

            try:

                if os.path.isfile(
                    caminho
                ):

                    os.remove(
                        caminho
                    )

                elif os.path.isdir(
                    caminho
                ):

                    shutil.rmtree(
                        caminho
                    )

            except Exception as erro:

                print(
                    f"Erro limpando "
                    f"{caminho}: {erro}"
                )


# ============================================================
# CRIAR VÍDEO
# ============================================================

def criar_reel(
    pais
):

    print("")
    print(
        "======================================"
    )
    print(
        "        MUNDO AFORA"
    )
    print(
        "======================================"
    )

    print(
        f"Destino: {pais}"
    )

    limpar_temporarios()

    consultas = PAISES.get(
        pais
    )

    if not consultas:

        raise RuntimeError(
            "Destino não encontrado."
        )

    # --------------------------------------------------------
    # PESQUISA
    # --------------------------------------------------------

    consultas = consultas.copy()

    random.shuffle(
        consultas
    )

    todos = []

    for query in consultas[:8]:

        try:

            print(
                f"[PEXELS] {query}"
            )

            resultados = buscar_videos(
                query
            )

            todos.extend(
                resultados
            )

            print(
                f"[PEXELS] "
                f"{len(resultados)} resultados"
            )

        except Exception as erro:

            print(
                f"[ERRO PEXELS] "
                f"{query}: {erro}"
            )

    if not todos:

        raise RuntimeError(
            "Nenhum vídeo retornado pelo Pexels."
        )

    # --------------------------------------------------------
    # REMOVER DUPLICADOS
    # --------------------------------------------------------

    unicos = {}

    for video in todos:

        video_id = video.get(
            "id"
        )

        if video_id:
            unicos[
                video_id
            ] = video

    todos = list(
        unicos.values()
    )

    print(
        f"[TOTAL] {len(todos)} vídeos únicos"
    )

    # --------------------------------------------------------
    # SELEÇÃO
    # --------------------------------------------------------

    selecionados = selecionar_videos(
        todos
    )

    print(
        f"[SELECIONADOS] "
        f"{len(selecionados)}"
    )

    if not selecionados:

        raise RuntimeError(
            "Nenhum vídeo vertical adequado foi encontrado."
        )

    # --------------------------------------------------------
    # DOWNLOAD
    # --------------------------------------------------------

    caminhos = baixar_videos_paralelo(
        selecionados
    )

    print(
        f"[BAIXADOS] {len(caminhos)}"
    )

    if not caminhos:

        raise RuntimeError(
            "Nenhum vídeo pôde ser baixado."
        )

    # --------------------------------------------------------
    # PROCESSAMENTO
    # --------------------------------------------------------

    processados = preparar_clipes(
        caminhos
    )

    print(
        f"[PROCESSADOS] "
        f"{len(processados)}"
    )

    if not processados:

        raise RuntimeError(
            "Nenhum clipe pôde ser processado."
        )

    # --------------------------------------------------------
    # JUNTAR
    # --------------------------------------------------------

    base = os.path.join(
        TEMP_DIR,
        f"base_{uuid.uuid4().hex}.mp4"
    )

    juntar_clipes(
        processados,
        base
    )

    # --------------------------------------------------------
    # MARCA D'ÁGUA
    # --------------------------------------------------------

    nome_final = (
        "mundo_afora_"
        + uuid.uuid4().hex
        + ".mp4"
    )

    final = os.path.join(
        OUTPUT_DIR,
        nome_final
    )

    aplicar_marca_dagua(
        base,
        final
    )

    print(
        "======================================"
    )

    print(
        "[SUCESSO] VÍDEO PRONTO"
    )

    print(
        final
    )

    print(
        "======================================"
    )

    return final


# ============================================================
# ROTA
# ============================================================

@app.route(
    "/",
    methods=[
        "GET",
        "POST"
    ]
)
def index():

    if request.method == "POST":

        pais = request.form.get(
            "pais"
        )

        try:

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

            print("")
            print(
                "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
            )
            print(
                "ERRO GERAL:"
            )
            print(
                str(erro)
            )
            print(
                "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
            )
            print("")

            mensagem = html.escape(
                str(erro)
            )

            return f"""
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>Erro</title>

</head>

<body style="
background:#111;
color:white;
font-family:Arial;
padding:30px;
">

<h2>❌ Não foi possível gerar o vídeo</h2>

<p>{mensagem}</p>

<br>

<a
href="/"
style="
background:white;
color:black;
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
# HEALTH
# ============================================================

@app.route(
    "/health"
)
def health():

    return {
        "status": "ok",
        "project": "Mundo Afora",
        "resolution": "1080x1920",
        "fps": 24,
        "duration": 60,
        "audio": False,
        "watermark": WATERMARK
    }


# ============================================================
# START LOCAL
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