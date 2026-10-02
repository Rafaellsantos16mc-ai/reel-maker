import os
import random
import uuid
import shutil
import requests
import subprocess
import imageio_ffmpeg

from flask import Flask, request, render_template_string, send_file


# ============================================================
# APP
# ============================================================

app = Flask(__name__)

PORT = int(os.getenv("PORT", "8080"))

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")


# ============================================================
# CONFIGURAÇÕES
# ============================================================

WIDTH = 1080
HEIGHT = 1920

PROCESS_WIDTH = 540
PROCESS_HEIGHT = 960

FPS = 24

DURATION = 60

CLIP_COUNT = 4
CLIP_DURATION = 15


# ============================================================
# FFmpeg
# ============================================================

try:
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG = shutil.which("ffmpeg")

if not FFMPEG:
    raise RuntimeError(
        "FFmpeg não encontrado. Instale imageio-ffmpeg no requirements.txt"
    )


print("=" * 70)
print("[FFMPEG ENCONTRADO]")
print(FFMPEG)
print("=" * 70)


# ============================================================
# DIRETÓRIOS
# ============================================================

VIDEO_DIR = "videos"
TEMP_DIR = "temp"
OUTPUT_DIR = "outputs"

os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# PAÍSES / LOCAIS
# ============================================================

PAISES = {

    "Brasil": [
        "Brazil waterfall nature landscape",
        "Brazil mountains nature",
        "Brazil lake landscape",
        "Brazil river nature",
        "Brazil rainforest waterfall",
        "Brazil beautiful landscape"
    ],

    "Ilhas Faroé": [
        "Faroe Islands mountains waterfall",
        "Faroe Islands landscape",
        "Faroe Islands cliffs nature",
        "Faroe Islands lake mountains",
        "Faroe Islands waterfall",
        "Faroe Islands scenic landscape"
    ],

    "Suíça": [
        "Switzerland Alps mountains lake",
        "Swiss Alps waterfall",
        "Switzerland mountain cabin",
        "Switzerland alpine lake",
        "Swiss mountain landscape",
        "Switzerland winter mountains"
    ],

    "Noruega": [
        "Norway fjord mountains",
        "Norway waterfall mountains",
        "Norway scenic landscape",
        "Norway lake mountains",
        "Norway winter landscape",
        "Norwegian fjord nature"
    ],

    "Islândia": [
        "Iceland waterfall landscape",
        "Iceland mountains nature",
        "Iceland black beach landscape",
        "Iceland glacier mountains",
        "Iceland lake waterfall",
        "Iceland scenic nature"
    ],

    "Canadá": [
        "Canada mountains lake",
        "Canada waterfall nature",
        "Canadian Rockies landscape",
        "Canada forest lake",
        "Canada winter mountains",
        "Canada scenic landscape"
    ],

    "Nova Zelândia": [
        "New Zealand mountains lake",
        "New Zealand waterfall",
        "New Zealand nature landscape",
        "New Zealand fjord mountains",
        "New Zealand alpine lake",
        "New Zealand scenic landscape"
    ],

    "Áustria": [
        "Austria Alps lake",
        "Austria mountain village nature",
        "Austria waterfall mountains",
        "Austrian Alps landscape",
        "Austria winter mountains",
        "Austria mountain lake"
    ],

    "Eslovênia": [
        "Slovenia Lake Bled mountains",
        "Slovenia waterfall nature",
        "Slovenia alpine lake",
        "Slovenia mountains landscape",
        "Slovenia forest waterfall",
        "Slovenia scenic nature"
    ],

    "França": [
        "French Alps mountains",
        "France waterfall mountains",
        "French Alps lake",
        "France nature landscape",
        "French mountain lake",
        "French Alps winter"
    ],

    "Itália": [
        "Italian Alps mountains",
        "Dolomites Italy landscape",
        "Italy mountain lake",
        "Italy waterfall nature",
        "Dolomites lake",
        "Italian Alps scenic"
    ],

    "Estados Unidos": [
        "USA mountain lake nature",
        "Yosemite waterfall landscape",
        "Rocky Mountains lake",
        "Alaska mountains lake",
        "USA waterfall nature",
        "American mountains landscape"
    ],

    "Japão": [
        "Japan mountain waterfall",
        "Japan lake mountains",
        "Japan nature landscape",
        "Japan forest waterfall",
        "Japanese mountains",
        "Japan scenic nature"
    ],

    "Peru": [
        "Peru Andes mountains lake",
        "Peru mountain landscape",
        "Peru waterfall nature",
        "Peruvian Andes landscape",
        "Peru lake mountains",
        "Peru scenic nature"
    ],

    "Chile": [
        "Chile Patagonia mountains",
        "Chile waterfall nature",
        "Chile mountain lake",
        "Patagonia landscape",
        "Chile Andes mountains",
        "Chile scenic landscape"
    ],

    "Argentina": [
        "Argentina Patagonia mountains",
        "Argentina waterfall nature",
        "Argentina mountain lake",
        "Patagonia lake landscape",
        "Argentina Andes mountains",
        "Argentina scenic nature"
    ]
}


# ============================================================
# PALAVRAS PARA EVITAR
# ============================================================

PALAVRAS_RUINS = [
    "people",
    "person",
    "man",
    "woman",
    "girl",
    "boy",
    "hiker",
    "hiking",
    "tourist",
    "crowd",
    "car",
    "cars",
    "vehicle",
    "road",
    "highway",
    "city",
    "street",
    "building",
    "house",
    "hotel",
    "resort",
    "airport",
    "train",
    "boat",
    "ship",
    "event",
    "festival",
    "concert",
    "restaurant",
    "urban"
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
    max-width: 600px;
    margin: auto;
}

h1 {
    text-align: center;
    margin-bottom: 8px;
}

.sub {
    text-align: center;
    color: #aaa;
    margin-bottom: 25px;
}

label {
    display: block;
    margin-top: 15px;
    margin-bottom: 6px;
}

select,
button {
    width: 100%;
    padding: 14px;
    border-radius: 10px;
    border: none;
    font-size: 16px;
}

select {
    background: #202020;
    color: white;
}

button {
    margin-top: 25px;
    background: #ffffff;
    color: #000;
    font-weight: bold;
    cursor: pointer;
}

.info {
    margin-top: 25px;
    padding: 15px;
    background: #1c1c1c;
    border-radius: 10px;
    line-height: 1.6;
}

</style>

</head>

<body>

<div class="container">

<h1>🌎 Mundo Afora</h1>

<div class="sub">
Paisagens incríveis pelo mundo
</div>

<form method="POST">

<label>Escolha o país</label>

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

<b>Configuração:</b><br>

🎥 4 clipes<br>
⏱️ 15 segundos cada<br>
📱 1080 × 1920<br>
🚫 Sem pessoas<br>
🚫 Sem áudio<br>
🚫 Sem música<br>
🚫 Sem narração<br>
🚫 Sem marca-d'água

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
            "PEXELS_API_KEY não configurada no Railway."
        )

    url = "https://api.pexels.com/videos/search"

    headers = {
        "Authorization": PEXELS_API_KEY
    }

    params = {
        "query": query,

        # Não obrigamos portrait.
        # Assim também aceitamos vídeos horizontais.
        "size": "large",

        "per_page": 80,

        "page": random.randint(1, 5)
    }

    try:

        resposta = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=30
        )

        print("[PEXELS STATUS]", resposta.status_code)

        if resposta.status_code != 200:

            print(
                "[PEXELS ERRO]",
                resposta.text[:500]
            )

            return []

        dados = resposta.json()

        videos = dados.get("videos", [])

        print(
            "[PEXELS]",
            len(videos),
            "vídeos encontrados"
        )

        return videos

    except Exception as e:

        print(
            "[ERRO PEXELS]",
            repr(e)
        )

        return []


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

        tipo = str(
            arquivo.get("file_type", "")
        ).lower()

        if tipo and "mp4" not in tipo:
            continue

        largura = int(
            arquivo.get("width") or 0
        )

        altura = int(
            arquivo.get("height") or 0
        )

        tamanho = int(
            arquivo.get("file_size") or 0
        )

        if largura <= 0 or altura <= 0:
            continue

        # Precisamos de uma resolução razoável.
        if largura < 540 and altura < 540:
            continue

        candidatos.append({
            "link": link,
            "width": largura,
            "height": altura,
            "size": tamanho
        })

    if not candidatos:
        return None

    # Preferimos arquivos que não sejam gigantes.
    def pontuacao(item):

        largura = item["width"]
        altura = item["height"]

        pixels = largura * altura

        # Quanto mais próximo de 720p/1080p,
        # melhor para processamento.
        diferenca = abs(pixels - (1280 * 720))

        # Penaliza arquivos enormes.
        penalidade = 0

        if pixels > 1920 * 1080:
            penalidade += 5000000

        return diferenca + penalidade

    candidatos.sort(
        key=pontuacao
    )

    return candidatos[0]


# ============================================================
# SELECIONAR VÍDEOS
# ============================================================

def selecionar_videos(pais):

    queries = PAISES.get(
        pais,
        ["beautiful nature landscape"]
    )

    todos = []

    consultas = queries[:]

    random.shuffle(consultas)

    # Fazemos várias consultas para aumentar
    # a chance de encontrar vídeos válidos.
    for query in consultas[:4]:

        print()
        print(
            "[BUSCANDO]",
            query
        )

        videos = buscar_videos(query)

        for video in videos:

            titulo = str(
                video.get("url", "")
            ).lower()

            # Alguns vídeos podem trazer texto
            # desnecessário na URL.
            ruim = 0

            for palavra in PALAVRAS_RUINS:

                if palavra in titulo:
                    ruim += 1

            arquivo = escolher_arquivo_video(
                video
            )

            if not arquivo:
                continue

            todos.append({
                "video": video,
                "arquivo": arquivo,
                "ruim": ruim
            })

    # Ordena primeiro pelos menos problemáticos.
    todos.sort(
        key=lambda x: x["ruim"]
    )

    # Remove duplicados.
    resultado = []

    links_usados = set()

    for item in todos:

        link = item["arquivo"]["link"]

        if link in links_usados:
            continue

        links_usados.add(link)

        resultado.append(item)

    random.shuffle(resultado)

    # Mantemos uma quantidade maior de candidatos
    # para que vídeos que falhem sejam substituídos.
    return resultado[:60]


# ============================================================
# DOWNLOAD
# ============================================================

def baixar_video(item):

    arquivo = item["arquivo"]

    link = arquivo["link"]

    nome = (
        str(uuid.uuid4())
        + ".mp4"
    )

    caminho = os.path.join(
        VIDEO_DIR,
        nome
    )

    print(
        "[DOWNLOAD]",
        arquivo["width"],
        "x",
        arquivo["height"]
    )

    headers = {
        "User-Agent":
        "Mozilla/5.0"
    }

    try:

        resposta = requests.get(
            link,
            headers=headers,
            stream=True,
            timeout=90
        )

        resposta.raise_for_status()

        tamanho = 0

        with open(
            caminho,
            "wb"
        ) as f:

            for bloco in resposta.iter_content(
                chunk_size=1024 * 1024
            ):

                if bloco:

                    f.write(bloco)

                    tamanho += len(bloco)

        print(
            "[OK DOWNLOAD]",
            round(
                tamanho / 1024 / 1024,
                2
            ),
            "MB"
        )

        # Arquivo muito pequeno provavelmente
        # não é um vídeo válido.
        if tamanho < 10000:

            print(
                "[DOWNLOAD INVALIDO]"
            )

            try:
                os.remove(caminho)
            except:
                pass

            return None

        return caminho

    except Exception as e:

        print(
            "[ERRO DOWNLOAD]",
            repr(e)
        )

        try:
            os.remove(caminho)
        except:
            pass

        return None


# ============================================================
# EXECUTAR FFMPEG
# ============================================================

def executar_ffmpeg(comando):

    print("=" * 70)

    print("[FFMPEG]")

    print(
        " ".join(
            str(x)
            for x in comando
        )
    )

    print("=" * 70)

    resultado = subprocess.run(
        comando,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if resultado.returncode != 0:

        print(
            "[FFMPEG ERRO]"
        )

        print(
            resultado.stderr[-4000:]
        )

        raise RuntimeError(
            "FFmpeg retornou código "
            + str(resultado.returncode)
        )

    return resultado


# ============================================================
# VERIFICAR VÍDEO
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

    try:

        executar_ffmpeg(
            comando
        )

        return True

    except Exception as e:

        print(
            "[VÍDEO INVÁLIDO]",
            repr(e)
        )

        return False


# ============================================================
# PROCESSAR CLIPE
# ============================================================

def processar_clipe(
    entrada,
    numero
):

    saida = os.path.join(
        TEMP_DIR,
        f"clip_{uuid.uuid4().hex}.mp4"
    )

    # Crop central para vertical.
    filtro = (
        "scale="
        f"{PROCESS_WIDTH}:"
        f"{PROCESS_HEIGHT}:"
        "force_original_aspect_ratio=increase,"
        f"crop={PROCESS_WIDTH}:"
        f"{PROCESS_HEIGHT},"
        f"fps={FPS}"
    )

    comando = [

        FFMPEG,

        "-y",

        "-i",
        entrada,

        "-t",
        str(CLIP_DURATION),

        "-vf",
        filtro,

        "-an",

        "-c:v",
        "libx264",

        "-preset",
        "ultrafast",

        "-crf",
        "30",

        "-pix_fmt",
        "yuv420p",

        "-movflags",
        "+faststart",

        saida
    ]

    try:

        executar_ffmpeg(
            comando
        )

        if not os.path.exists(
            saida
        ):

            raise Exception(
                "Arquivo processado não foi criado."
            )

        tamanho = os.path.getsize(
            saida
        )

        if tamanho < 10000:

            raise Exception(
                "Arquivo processado ficou muito pequeno."
            )

        print(
            "[OK CLIPE]",
            numero,
            round(
                tamanho / 1024 / 1024,
                2
            ),
            "MB"
        )

        return saida

    except Exception as e:

        print(
            "[ERRO PROCESSANDO CLIPE]",
            repr(e)
        )

        try:
            os.remove(saida)
        except:
            pass

        return None


# ============================================================
# JUNTAR CLIPES
# ============================================================

def juntar_clipes(
    clipes,
    saida
):

    lista = os.path.join(
        TEMP_DIR,
        f"lista_{uuid.uuid4().hex}.txt"
    )

    try:

        with open(
            lista,
            "w",
            encoding="utf-8"
        ) as f:

            for clipe in clipes:

                caminho = os.path.abspath(
                    clipe
                )

                caminho = caminho.replace(
                    "'",
                    "'\\''"
                )

                f.write(
                    "file '"
                    + caminho
                    + "'\n"
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

            "-c",
            "copy",

            "-an",

            saida
        ]

        executar_ffmpeg(
            comando
        )

        if not os.path.exists(
            saida
        ):

            raise Exception(
                "Vídeo final não foi criado."
            )

        return True

    except Exception as e:

        print(
            "[ERRO JUNTANDO]",
            repr(e)
        )

        return False

    finally:

        try:
            os.remove(lista)
        except:
            pass


# ============================================================
# FINALIZAR VÍDEO
# ============================================================

def finalizar_video(
    entrada,
    saida
):

    filtro = (
        "scale="
        f"{WIDTH}:"
        f"{HEIGHT}:"
        "force_original_aspect_ratio=increase,"
        f"crop={WIDTH}:"
        f"{HEIGHT},"
        f"fps={FPS}"
    )

    comando = [

        FFMPEG,

        "-y",

        "-i",
        entrada,

        "-vf",
        filtro,

        "-an",

        "-c:v",
        "libx264",

        "-preset",
        "ultrafast",

        "-crf",
        "29",

        "-pix_fmt",
        "yuv420p",

        "-movflags",
        "+faststart",

        saida
    ]

    executar_ffmpeg(
        comando
    )

    if not os.path.exists(
        saida
    ):

        raise Exception(
            "Arquivo final não foi criado."
        )

    return saida


# ============================================================
# LIMPAR
# ============================================================

def limpar_arquivos(
    arquivos
):

    for arquivo in arquivos:

        try:

            if arquivo and os.path.exists(
                arquivo
            ):

                os.remove(
                    arquivo
                )

        except Exception:
            pass


# ============================================================
# GERAR VÍDEO
# ============================================================

def gerar_video(pais):

    print()
    print("=" * 70)
    print(
        "[INICIANDO]",
        pais
    )
    print("=" * 70)

    candidatos = selecionar_videos(
        pais
    )

    if not candidatos:

        raise Exception(
            "Nenhum vídeo encontrado no Pexels."
        )

    clipes = []

    originais = []

    tentativas = 0

    indice = 0

    # Temos vários candidatos para substituir
    # aqueles que eventualmente falharem.
    while len(clipes) < CLIP_COUNT:

        if indice >= len(candidatos):

            break

        item = candidatos[indice]

        indice += 1

        tentativas += 1

        print()
        print("-" * 70)

        print(
            "[TENTANDO VÍDEO]",
            len(clipes) + 1,
            "/",
            CLIP_COUNT
        )

        caminho = baixar_video(
            item
        )

        if not caminho:

            continue

        originais.append(
            caminho
        )

        # Primeiro verifica se o arquivo
        # realmente é um vídeo.
        if not verificar_video(
            caminho
        ):

            print(
                "[PULAR] Vídeo inválido."
            )

            continue

        clipe = processar_clipe(
            caminho,
            len(clipes) + 1
        )

        if not clipe:

            print(
                "[PULAR] Falha no processamento."
            )

            continue

        clipes.append(
            clipe
        )

        print(
            "[PROGRESSO]",
            len(clipes),
            "/",
            CLIP_COUNT
        )

    if len(clipes) < CLIP_COUNT:

        limpar_arquivos(
            originais
        )

        limpar_arquivos(
            clipes
        )

        raise Exception(
            "Não foi possível processar "
            "vídeos suficientes. Obtidos: "
            f"{len(clipes)}/{CLIP_COUNT}"
        )

    # --------------------------------------------------------
    # JUNTAR
    # --------------------------------------------------------

    unido = os.path.join(
        TEMP_DIR,
        f"unido_{uuid.uuid4().hex}.mp4"
    )

    if not juntar_clipes(
        clipes,
        unido
    ):

        limpar_arquivos(
            originais + clipes
        )

        raise Exception(
            "Não foi possível juntar os clipes."
        )

    # --------------------------------------------------------
    # FINAL
    # --------------------------------------------------------

    nome_final = (
        "mundo_afora_"
        + uuid.uuid4().hex
        + ".mp4"
    )

    saida_final = os.path.join(
        OUTPUT_DIR,
        nome_final
    )

    try:

        finalizar_video(
            unido,
            saida_final
        )

        print()
        print("=" * 70)

        print(
            "[VÍDEO FINALIZADO]"
        )

        print(
            saida_final
        )

        print("=" * 70)

    finally:

        limpar_arquivos(
            originais
        )

        limpar_arquivos(
            clipes
        )

        limpar_arquivos(
            [unido]
        )

    return saida_final


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

            arquivo = gerar_video(
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

        except Exception as e:

            print(
                "[ERRO GERAL]",
                repr(e)
            )

            return f"""
            <html>
            <head>
            <meta charset="UTF-8">
            <style>
            body {{
                background:#101010;
                color:white;
                font-family:Arial;
                padding:30px;
            }}
            .erro {{
                max-width:700px;
                margin:auto;
                background:#1d1d1d;
                padding:25px;
                border-radius:15px;
            }}
            </style>
            </head>

            <body>

            <div class="erro">

            <h2>❌ Erro ao gerar vídeo</h2>

            <p>
            {str(e)}
            </p>

            <p>
            Verifique os logs do Railway.
            </p>

            <a
            href="/"
            style="color:white"
            >
            ← Voltar
            </a>

            </div>

            </body>
            </html>
            """, 500

    return render_template_string(
        HTML,
        paises=list(PAISES.keys())
    )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 70)
    print("🌎 MUNDO AFORA")
    print("=" * 70)

    print(
        "Porta:",
        PORT
    )

    print(
        "FFmpeg:",
        FFMPEG
    )

    print(
        "Clipes:",
        CLIP_COUNT
    )

    print(
        "Duração:",
        DURATION,
        "segundos"
    )

    print("=" * 70)

    app.run(
        host="0.0.0.0",
        port=PORT
    )