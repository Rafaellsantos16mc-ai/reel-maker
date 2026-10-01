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
# DESTINOS
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
        "Faroe Islands dramatic landscape"
    ],

    "🇨🇭 Suíça": [
        "Switzerland mountain lake",
        "Swiss Alps lake",
        "Switzerland green valley",
        "Swiss mountain valley",
        "Switzerland mountain cabin",
        "Swiss Alps cabin",
        "Switzerland scenic mountains",
        "Swiss Alps landscape"
    ],

    "🇳🇴 Noruega": [
        "Norway fjord mountains",
        "Norway ocean cliffs",
        "Norway mountain lake",
        "Norway green valley",
        "Norway mountain cabin",
        "Norwegian fjord landscape"
    ],

    "🇮🇸 Islândia": [
        "Iceland mountain lake",
        "Iceland ocean cliffs",
        "Iceland green valley",
        "Iceland mountain valley",
        "Iceland dramatic mountains",
        "Iceland coastline cliffs"
    ],

    "🇨🇦 Canadá": [
        "Canada mountain lake",
        "Canadian Rockies lake",
        "Canada green valley mountains",
        "Canada mountain cabin",
        "Canadian Rockies cabin",
        "Canada ocean cliffs"
    ],

    "🇳🇿 Nova Zelândia": [
        "New Zealand mountain lake",
        "New Zealand green valley",
        "New Zealand mountain cabin",
        "New Zealand fjord mountains",
        "New Zealand ocean cliffs"
    ],

    "🇦🇹 Áustria": [
        "Austria mountain lake",
        "Austrian Alps lake",
        "Austria mountain cabin",
        "Austrian Alps cabin",
        "Austria green valley",
        "Austria mountain valley"
    ],

    "🇸🇮 Eslovênia": [
        "Slovenia mountain lake",
        "Slovenia green valley",
        "Slovenia mountain cabin",
        "Slovenia Alps lake"
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
        "Italian Alps landscape"
    ],

    "🇺🇸 Estados Unidos": [
        "USA mountain lake",
        "Rocky Mountains lake",
        "United States mountain cabin",
        "USA green valley mountains",
        "USA ocean cliffs",
        "Alaska mountain lake"
    ],

    "🇯🇵 Japão": [
        "Japan mountain lake",
        "Japan green valley mountains",
        "Japan mountain cabin",
        "Japan mountain landscape"
    ],

    "🇵🇪 Peru": [
        "Peru mountain lake",
        "Peru green mountain valley",
        "Peru dramatic mountains",
        "Peru Andes lake"
    ],

    "🇨🇱 Chile": [
        "Chile Patagonia mountains lake",
        "Chile mountain lake",
        "Patagonia green valley",
        "Chile fjord mountains",
        "Patagonia mountain cabin"
    ],

    "🇦🇷 Argentina": [
        "Argentina Patagonia mountain lake",
        "Argentina mountain valley",
        "Patagonia lake mountains",
        "Argentina mountain cabin"
    ]
}


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

<strong>Configuração:</strong><br>

📱 1080 × 1920<br>
🎞️ 24 FPS<br>
⏱️ 60 segundos<br>
🔇 Sem áudio<br>
💧 mundo.afora0<br>
🎥 Pexels

</div>

</div>

</body>

</html>
"""


# ============================================================
# BUSCAR PEXELS
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
        timeout=40
    )

    resposta.raise_for_status()

    return resposta.json().get(
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

        tipo = str(
            arquivo.get(
                "file_type",
                ""
            )
        ).lower()

        if "mp4" not in tipo:
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

        if proporcao < 1.30:
            continue

        # ====================================================
        # PRIORIZA 1080x1920 / 1440x2560
        # Evita arquivos de 400+ MB
        # ====================================================

        if largura == 1080 and altura == 1920:

            prioridade = 1

        elif largura == 1440 and altura == 2560:

            prioridade = 2

        elif largura == 720 and altura == 1280:

            prioridade = 3

        elif largura == 2160 and altura == 3840:

            prioridade = 4

        else:

            prioridade = 5

        candidatos.append(
            (
                prioridade,
                abs(
                    (largura / altura)
                    - (1080 / 1920)
                ),
                link,
                largura,
                altura
            )
        )

    if not candidatos:
        return None

    # Menor prioridade = melhor
    candidatos.sort(
        key=lambda x: (
            x[0],
            x[1]
        )
    )

    _, _, link, largura, altura = candidatos[0]

    return (
        link,
        largura,
        altura
    )


# ============================================================
# PONTUAR
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

    for palavra in PALAVRAS_RUINS:

        if palavra in texto:

            pontos -= 100

    return pontos


# ============================================================
# SELECIONAR VÍDEOS
# ============================================================

def selecionar_videos(videos):

    candidatos = []

    ids_usados = set()

    for video in videos:

        video_id = video.get(
            "id"
        )

        if not video_id:
            continue

        if video_id in ids_usados:
            continue

        ids_usados.add(
            video_id
        )

        arquivo = escolher_arquivo_video(
            video
        )

        if not arquivo:
            continue

        pontos = pontuar_video(
            video
        )

        if pontos < 0:
            continue

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

    candidatos = candidatos[:50]

    random.shuffle(
        candidatos
    )

    return candidatos[:15]


# ============================================================
# DOWNLOAD
# ============================================================

def baixar_video(
    item,
    numero
):

    _, video, arquivo = item

    link, largura, altura = arquivo

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
                "Arquivo vazio."
            )

        print(
            f"[OK DOWNLOAD] {numero} "
            f"{tamanho / 1024 / 1024:.1f} MB"
        )

        return caminho

    except Exception as erro:

        print(
            f"[ERRO DOWNLOAD] "
            f"{numero}: {erro}"
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
                    f"[ERRO THREAD] "
                    f"{erro}"
                )

    return caminhos


# ============================================================
# VERIFICAR VÍDEO
# ============================================================

def verificar_video(
    caminho
):

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
            "[ERRO AO LER VÍDEO]"
        )

        print(
            resultado.stderr
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

    # ========================================================
    # IMPORTANTE:
    #
    # NÃO TEM CROP
    # NÃO TEM ZOOMPAN
    # NÃO TEM EXPRESSÃO COM t
    #
    # Os vídeos selecionados já são verticais.
    # Apenas reduzimos para 1080x1920.
    # ========================================================

    filtro = (
        "scale=1080:1920,"
        "fps=24,"
        "setsar=1"
    )

    comando = [

        FFMPEG,

        "-y",

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
        "ultrafast",

        "-crf",
        "28",

        "-pix_fmt",
        "yuv420p",

        "-r",
        "24",

        "-movflags",
        "+faststart",

        output_path
    ]

    print(
        "[FFMPEG] Iniciando..."
    )

    resultado = subprocess.run(
        comando,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if resultado.returncode != 0:

        print(
            "======================================"
        )

        print(
            f"[ERRO FFMPEG CLIPE {numero}]"
        )

        print(
            f"Return code: "
            f"{resultado.returncode}"
        )

        print(
            resultado.stderr[-10000:]
        )

        print(
            "======================================"
        )

        return False

    if not os.path.exists(
        output_path
    ):

        print(
            "[ERRO] FFmpeg não criou o arquivo."
        )

        return False

    tamanho = os.path.getsize(
        output_path
    )

    if tamanho < 50000:

        print(
            "[ERRO] Arquivo final muito pequeno."
        )

        return False

    print(
        f"[OK PROCESSADO] Clipe {numero} "
        f"{tamanho / 1024 / 1024:.1f} MB"
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

        print(
            ""
        )

        print(
            "--------------------------------------"
        )

        print(
            f"CLipe {numero}"
        )

        print(
            caminho
        )

        # Verificação
        if not verificar_video(
            caminho
        ):

            print(
                "[PULANDO] Vídeo inválido."
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
# JUNTAR
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

            absoluto = os.path.abspath(
                caminho
            )

            absoluto = absoluto.replace(
                "\\",
                "/"
            )

            arquivo.write(
                f"file '{absoluto}'\n"
            )

    print(
        f"[JUNTANDO] "
        f"{len(caminhos)} clipes"
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
            "[ERRO AO JUNTAR]"
        )

        print(
            resultado.stderr
        )

        raise RuntimeError(
            "Erro ao juntar os clipes."
        )

    print(
        "[OK] Clipes unidos."
    )


# ============================================================
# MARCA D'ÁGUA
# ============================================================

def aplicar_marca_dagua(
    input_path,
    output_path
):

    print(
        "[MARCA D'ÁGUA]"
    )

    filtro = (
        "drawtext="
        "text='mundo.afora0':"
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

        "-i",
        input_path,

        "-vf",
        filtro,

        "-an",

        "-c:v",
        "libx264",

        "-preset",
        "ultrafast",

        "-crf",
        "28",

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
            "======================================"
        )

        print(
            "[ERRO MARCA D'ÁGUA]"
        )

        print(
            resultado.stderr[-10000:]
        )

        print(
            "======================================"
        )

        raise RuntimeError(
            "Erro ao aplicar marca d'água."
        )

    print(
        "[OK] Marca d'água aplicada."
    )


# ============================================================
# LIMPAR
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
                    f"[LIMPEZA] {erro}"
                )


# ============================================================
# CRIAR REEL
# ============================================================

def criar_reel(
    pais
):

    print("")
    print(
        "======================================"
    )
    print(
        "          MUNDO AFORA"
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
            "Destino inválido."
        )

    consultas = consultas.copy()

    random.shuffle(
        consultas
    )

    todos_videos = []

    # ========================================================
    # PESQUISAR
    # ========================================================

    for query in consultas[:8]:

        try:

            print(
                f"[PEXELS] {query}"
            )

            resultados = buscar_videos(
                query
            )

            print(
                f"[PEXELS] "
                f"{len(resultados)} resultados"
            )

            todos_videos.extend(
                resultados
            )

        except Exception as erro:

            print(
                f"[ERRO PEXELS] "
                f"{erro}"
            )

    if not todos_videos:

        raise RuntimeError(
            "Nenhum vídeo encontrado."
        )

    # ========================================================
    # DUPLICADOS
    # ========================================================

    unicos = {}

    for video in todos_videos:

        video_id = video.get(
            "id"
        )

        if video_id:
            unicos[
                video_id
            ] = video

    todos_videos = list(
        unicos.values()
    )

    print(
        f"[TOTAL] "
        f"{len(todos_videos)} vídeos únicos"
    )

    # ========================================================
    # SELEÇÃO
    # ========================================================

    selecionados = selecionar_videos(
        todos_videos
    )

    print(
        f"[SELECIONADOS] "
        f"{len(selecionados)}"
    )

    if not selecionados:

        raise RuntimeError(
            "Nenhum vídeo vertical adequado."
        )

    # ========================================================
    # DOWNLOAD
    # ========================================================

    caminhos = baixar_videos_paralelo(
        selecionados
    )

    print(
        f"[BAIXADOS] "
        f"{len(caminhos)}"
    )

    if not caminhos:

        raise RuntimeError(
            "Nenhum vídeo pôde ser baixado."
        )

    # ========================================================
    # PROCESSAMENTO
    # ========================================================

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

    # ========================================================
    # JUNTAR
    # ========================================================

    base = os.path.join(
        TEMP_DIR,
        f"base_{uuid.uuid4().hex}.mp4"
    )

    juntar_clipes(
        processados,
        base
    )

    # ========================================================
    # MARCA D'ÁGUA
    # ========================================================

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
        ""
    )

    print(
        "======================================"
    )

    print(
        "        VÍDEO PRONTO"
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
                "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
            )
            print(
                "ERRO GERAL"
            )
            print(
                str(erro)
            )
            print(
                "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
            )

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

<h2>❌ Erro ao gerar vídeo</h2>

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
# HEALTH CHECK
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