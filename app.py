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

# Processamento interno mais leve
PROC_WIDTH = 540
PROC_HEIGHT = 960

FPS = 24

CLIP_COUNT = 4
CLIP_DURATION = 15

TOTAL_DURATION = CLIP_COUNT * CLIP_DURATION


# ============================================================
# FFMPEG
# ============================================================

try:
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG = shutil.which("ffmpeg")

if not FFMPEG:
    raise RuntimeError(
        "FFmpeg não encontrado. "
        "Adicione imageio-ffmpeg ao requirements.txt."
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
# PAÍSES E LOCAIS
# ============================================================

PAISES = {

    "Brasil": [
        "Brazil waterfall nature landscape",
        "Iguazu Falls Brazil",
        "Lençóis Maranhenses Brazil",
        "Chapada Diamantina waterfall",
        "Fernando de Noronha landscape",
        "Brazil mountain lake",
        "Brazil rainforest waterfall"
    ],

    "Ilhas Faroé": [
        "Faroe Islands waterfall",
        "Faroe Islands mountains",
        "Faroe Islands cliffs",
        "Faroe Islands fjord",
        "Faroe Islands lake",
        "Faroe Islands scenic landscape"
    ],

    "Suíça": [
        "Swiss Alps mountains lake",
        "Lauterbrunnen Switzerland",
        "Grindelwald Switzerland",
        "Swiss Alps waterfall",
        "Swiss mountain cabin",
        "Swiss alpine lake",
        "Swiss Alps winter"
    ],

    "Noruega": [
        "Norway fjord mountains",
        "Geirangerfjord Norway",
        "Lofoten Norway",
        "Norway waterfall",
        "Norway mountain lake",
        "Norway winter mountains",
        "Norwegian landscape"
    ],

    "Islândia": [
        "Iceland waterfall",
        "Iceland glacier",
        "Iceland mountains",
        "Iceland black beach",
        "Iceland river waterfall",
        "Iceland winter landscape",
        "Iceland scenic nature"
    ],

    "Canadá": [
        "Canadian Rockies lake",
        "Banff Canada mountains",
        "Jasper Canada lake",
        "Canada waterfall",
        "Canada mountain river",
        "Canada winter mountains",
        "Canada forest lake"
    ],

    "Nova Zelândia": [
        "Milford Sound New Zealand",
        "New Zealand waterfall",
        "New Zealand mountain lake",
        "New Zealand fjord",
        "New Zealand Alps",
        "New Zealand river mountains",
        "New Zealand landscape"
    ],

    "Áustria": [
        "Austrian Alps lake",
        "Hallstatt Austria mountains",
        "Austria waterfall",
        "Austria mountain cabin",
        "Austria winter Alps",
        "Austria alpine lake",
        "Austria mountains"
    ],

    "Eslovênia": [
        "Lake Bled Slovenia",
        "Lake Bohinj Slovenia",
        "Slovenia waterfall",
        "Slovenia Alps",
        "Slovenia mountain lake",
        "Slovenia forest river",
        "Slovenia landscape"
    ],

    "França": [
        "French Alps lake",
        "Chamonix France mountains",
        "French Alps waterfall",
        "Annecy France mountains",
        "French mountain landscape",
        "French Alps winter"
    ],

    "Itália": [
        "Dolomites Italy",
        "Lake Como mountains",
        "Lake Garda mountains",
        "Italian Alps waterfall",
        "Dolomites lake",
        "Italian mountain cabin",
        "Italian Alps winter"
    ],

    "Estados Unidos": [
        "Yosemite waterfall",
        "Yellowstone waterfall",
        "Rocky Mountains lake",
        "Alaska mountains lake",
        "Grand Teton mountains",
        "USA mountain waterfall",
        "USA scenic lake"
    ],

    "Japão": [
        "Japan mountain waterfall",
        "Mount Fuji lake",
        "Japanese Alps",
        "Japan forest waterfall",
        "Japan mountain lake",
        "Japan winter mountains",
        "Japan scenic nature"
    ],

    "Peru": [
        "Peru Andes mountains",
        "Peru mountain lake",
        "Peru waterfall",
        "Sacred Valley Peru",
        "Peru glacier mountain",
        "Peruvian Andes lake"
    ],

    "Chile": [
        "Torres del Paine Chile",
        "Patagonia Chile lake",
        "Chile waterfall",
        "Chile Andes mountains",
        "Patagonia mountains",
        "Chile glacier lake",
        "Chile landscape"
    ],

    "Argentina": [
        "Patagonia Argentina mountains",
        "Bariloche Argentina lake",
        "Perito Moreno glacier",
        "Argentina waterfall",
        "Argentina Andes mountains",
        "Patagonia lake",
        "Argentina landscape"
    ]
}


# ============================================================
# PALAVRAS QUE QUEREMOS EVITAR
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
    "street",
    "city",
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
    background: #0b0b0b;
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
    font-size: 32px;
    margin-bottom: 5px;
}

.sub {
    text-align: center;
    color: #999;
    margin-bottom: 30px;
}

.box {
    background: #171717;
    padding: 20px;
    border-radius: 16px;
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
    border: 1px solid #333;
    background: #242424;
    color: white;
    font-size: 16px;
}

button {
    width: 100%;
    margin-top: 20px;
    padding: 16px;
    border: none;
    border-radius: 10px;
    background: white;
    color: black;
    font-size: 17px;
    font-weight: bold;
}

.info {
    margin-top: 20px;
    padding: 18px;
    background: #171717;
    border-radius: 15px;
    line-height: 1.7;
    color: #ddd;
}

</style>

</head>

<body>

<div class="container">

<h1>🌎 Mundo Afora</h1>

<div class="sub">
Paisagens incríveis pelo mundo
</div>

<div class="box">

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

</div>

<div class="info">

<b>🎥 Configuração</b><br><br>

🌎 Paisagens reais<br>
🎬 4 cenas<br>
⏱️ 15 segundos por cena<br>
⏱️ 60 segundos no total<br>
📱 1080 × 1920<br>
🎞️ 24 FPS<br>
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
# BUSCAR PEXELS
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

        print(
            "[PEXELS]",
            resposta.status_code,
            query
        )

        if resposta.status_code != 200:

            print(
                "[PEXELS ERRO]",
                resposta.text[:1000]
            )

            return []

        dados = resposta.json()

        return dados.get(
            "videos",
            []
        )

    except Exception as e:

        print(
            "[ERRO PEXELS]",
            repr(e)
        )

        return []


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

        if tipo and "mp4" not in tipo:
            continue

        largura = int(
            arquivo.get("width") or 0
        )

        altura = int(
            arquivo.get("height") or 0
        )

        if largura <= 0 or altura <= 0:
            continue

        if largura < 540 and altura < 540:
            continue

        pixels = largura * altura

        candidatos.append({
            "link": link,
            "width": largura,
            "height": altura,
            "pixels": pixels
        })

    if not candidatos:
        return None

    # Preferimos arquivos até 1080p.
    candidatos.sort(
        key=lambda x: (
            0 if x["pixels"] <= 1920 * 1080 else 1,
            abs(x["pixels"] - 1280 * 720)
        )
    )

    return candidatos[0]


# ============================================================
# SELECIONAR CANDIDATOS
# ============================================================

def selecionar_videos(pais):

    consultas = PAISES.get(
        pais,
        ["beautiful nature landscape"]
    )

    consultas = consultas[:]
    random.shuffle(consultas)

    candidatos = []
    links_usados = set()

    for query in consultas[:5]:

        print()
        print(
            "[BUSCANDO]",
            query
        )

        videos = buscar_videos(
            query
        )

        for video in videos:

            arquivo = escolher_arquivo_video(
                video
            )

            if not arquivo:
                continue

            link = arquivo["link"]

            if link in links_usados:
                continue

            links_usados.add(link)

            url_video = str(
                video.get("url", "")
            ).lower()

            problemas = 0

            for palavra in PALAVRAS_RUINS:

                if palavra in url_video:
                    problemas += 1

            candidatos.append({
                "arquivo": arquivo,
                "problemas": problemas
            })

    candidatos.sort(
        key=lambda x: x["problemas"]
    )

    # Mantém bastante opção para substituir
    # vídeos que eventualmente falharem.
    candidatos = candidatos[:40]

    random.shuffle(candidatos)

    return candidatos


# ============================================================
# DOWNLOAD
# ============================================================

def baixar_video(item):

    arquivo = item["arquivo"]

    link = arquivo["link"]

    nome = (
        uuid.uuid4().hex
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

    try:

        resposta = requests.get(
            link,
            headers={
                "User-Agent":
                "Mozilla/5.0"
            },
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

        if tamanho < 10000:

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
# FFMPEG
# ============================================================

def executar_ffmpeg(comando):

    print()
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

    print(
        "[FFMPEG RETURN CODE]",
        resultado.returncode
    )

    if resultado.returncode != 0:

        print()
        print("=" * 70)
        print("[FFMPEG ERRO COMPLETO]")
        print("=" * 70)

        print(
            resultado.stderr
        )

        print("=" * 70)

        raise RuntimeError(
            "FFmpeg falhou. "
            f"Return code: {resultado.returncode}"
        )

    return resultado


# ============================================================
# VALIDAR VÍDEO
# ============================================================

def verificar_video(caminho):

    comando = [
        FFMPEG,

        "-hide_banner",

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
        "clip_"
        + uuid.uuid4().hex
        + ".mp4"
    )

    filtro = (
        f"scale={PROC_WIDTH}:"
        f"{PROC_HEIGHT}:"
        "force_original_aspect_ratio=increase,"
        f"crop={PROC_WIDTH}:"
        f"{PROC_HEIGHT},"
        f"fps={FPS}"
    )

    comando = [

        FFMPEG,

        "-hide_banner",

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
        "31",

        "-pix_fmt",
        "yuv420p",

        saida
    ]

    try:

        executar_ffmpeg(
            comando
        )

        if not os.path.exists(
            saida
        ):
            return None

        tamanho = os.path.getsize(
            saida
        )

        print(
            "[OK CLIPE]",
            numero,
            "-",
            round(
                tamanho / 1024 / 1024,
                2
            ),
            "MB"
        )

        return saida

    except Exception as e:

        print(
            "[ERRO CLIPE]",
            repr(e)
        )

        try:
            os.remove(saida)
        except:
            pass

        return None


# ============================================================
# GERAR VÍDEO FINAL
#
# IMPORTANTE:
# Em vez de usar concat -c copy,
# usamos um segundo FFmpeg para juntar
# os 4 clipes e gerar o arquivo final.
# ============================================================

def juntar_e_finalizar(
    clipes,
    saida
):

    if len(clipes) != CLIP_COUNT:

        raise Exception(
            "Quantidade incorreta de clipes."
        )

    comando = [
        FFMPEG,

        "-hide_banner",

        "-y"
    ]

    # --------------------------------------------------------
    # INPUTS
    # --------------------------------------------------------

    for clipe in clipes:

        comando.extend([
            "-i",
            clipe
        ])

    # --------------------------------------------------------
    # FILTRO
    # --------------------------------------------------------

    partes = []

    for i in range(
        CLIP_COUNT
    ):

        partes.append(
            f"[{i}:v]"
            f"setpts=PTS-STARTPTS"
            f"[v{i}]"
        )

    entradas = "".join(
        f"[v{i}]"
        for i in range(
            CLIP_COUNT
        )
    )

    filtro_concat = (
        entradas
        + f"concat=n={CLIP_COUNT}:"
          "v=1:a=0,"
          f"scale={WIDTH}:{HEIGHT}:"
          "force_original_aspect_ratio=increase,"
          f"crop={WIDTH}:{HEIGHT},"
          f"fps={FPS},"
          "format=yuv420p"
        + "[outv]"
    )

    filtro = ";".join(
        partes
    ) + ";" + filtro_concat

    comando.extend([

        "-filter_complex",
        filtro,

        "-map",
        "[outv]",

        "-an",

        "-c:v",
        "libx264",

        "-preset",
        "ultrafast",

        "-crf",
        "30",

        "-pix_fmt",
        "yuv420p",

        "-t",
        str(TOTAL_DURATION),

        "-movflags",
        "+faststart",

        saida
    ])

    try:

        executar_ffmpeg(
            comando
        )

        if not os.path.exists(
            saida
        ):

            raise Exception(
                "Arquivo final não foi criado."
            )

        tamanho = os.path.getsize(
            saida
        )

        print()
        print(
            "[VÍDEO FINAL]",
            round(
                tamanho / 1024 / 1024,
                2
            ),
            "MB"
        )

        return True

    except Exception as e:

        print(
            "[ERRO FINAL]",
            repr(e)
        )

        return False


# ============================================================
# LIMPAR
# ============================================================

def limpar(arquivos):

    for arquivo in arquivos:

        try:

            if arquivo and os.path.exists(
                arquivo
            ):

                os.remove(
                    arquivo
                )

        except:
            pass


# ============================================================
# GERAR VÍDEO
# ============================================================

def gerar_video(pais):

    print()
    print("=" * 70)
    print(
        "[INICIANDO MUNDO AFORA]",
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

    indice = 0

    while len(clipes) < CLIP_COUNT:

        if indice >= len(candidatos):

            break

        item = candidatos[indice]

        indice += 1

        numero = len(clipes) + 1

        print()
        print("-" * 70)

        print(
            "[TENTANDO VÍDEO]",
            numero,
            "/",
            CLIP_COUNT
        )

        original = baixar_video(
            item
        )

        if not original:

            print(
                "[PULAR] Falha no download."
            )

            continue

        originais.append(
            original
        )

        # ----------------------------------------------------
        # VALIDAR
        # ----------------------------------------------------

        if not verificar_video(
            original
        ):

            print(
                "[PULAR] Vídeo inválido."
            )

            continue

        # ----------------------------------------------------
        # PROCESSAR
        # ----------------------------------------------------

        clipe = processar_clipe(
            original,
            numero
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

    # --------------------------------------------------------
    # VERIFICAR QUANTIDADE
    # --------------------------------------------------------

    if len(clipes) < CLIP_COUNT:

        limpar(
            originais
            + clipes
        )

        raise Exception(
            "Não foi possível processar "
            "vídeos suficientes. "
            f"Obtidos: {len(clipes)}/"
            f"{CLIP_COUNT}"
        )

    # --------------------------------------------------------
    # ARQUIVO FINAL
    # --------------------------------------------------------

    nome = (
        "mundo_afora_"
        + uuid.uuid4().hex
        + ".mp4"
    )

    saida = os.path.join(
        OUTPUT_DIR,
        nome
    )

    try:

        sucesso = juntar_e_finalizar(
            clipes,
            saida
        )

        if not sucesso:

            raise Exception(
                "Não foi possível gerar "
                "o vídeo final."
            )

        print()
        print("=" * 70)
        print(
            "[SUCESSO]",
            saida
        )
        print("=" * 70)

        return saida

    finally:

        limpar(
            originais
            + clipes
        )


# ============================================================
# ROTA
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

            print()
            print(
                "[ERRO GERAL]",
                repr(e)
            )

            return f"""
            <!DOCTYPE html>

            <html lang="pt-BR">

            <head>

            <meta charset="UTF-8">

            <meta name="viewport"
            content="width=device-width, initial-scale=1.0">

            <title>Erro</title>

            </head>

            <body style="
                background:#0b0b0b;
                color:white;
                font-family:Arial;
                padding:30px;
            ">

            <div style="
                max-width:700px;
                margin:auto;
                background:#171717;
                padding:25px;
                border-radius:15px;
            ">

            <h2>❌ Erro ao gerar vídeo</h2>

            <p>
            {str(e)}
            </p>

            <br>

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
        paises=list(
            PAISES.keys()
        )
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
        TOTAL_DURATION,
        "segundos"
    )

    print(
        "Resolução:",
        WIDTH,
        "x",
        HEIGHT
    )

    print(
        "Áudio: DESATIVADO"
    )

    print("=" * 70)

    app.run(
        host="0.0.0.0",
        port=PORT
    )