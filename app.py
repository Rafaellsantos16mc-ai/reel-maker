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

CLIP_COUNT = 4
CLIP_DURATION = 15

VIDEO_DURATION = CLIP_COUNT * CLIP_DURATION


# ============================================================
# FFMPEG
# ============================================================

try:
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG = shutil.which("ffmpeg")

if not FFMPEG:
    raise RuntimeError(
        "FFmpeg não encontrado. Instale imageio-ffmpeg."
    )

print("=" * 70)
print("[FFMPEG]")
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
# LOCAIS
# ============================================================

PAISES = {

    "Brasil": [
        "Lençóis Maranhenses Brazil",
        "Iguazu Falls Brazil",
        "Chapada Diamantina waterfall",
        "Fernando de Noronha landscape",
        "Serra da Mantiqueira mountains",
        "Brazil rainforest waterfall",
        "Brazil mountain lake"
    ],

    "Ilhas Faroé": [
        "Faroe Islands waterfall",
        "Faroe Islands fjord",
        "Faroe Islands cliffs",
        "Faroe Islands mountains",
        "Faroe Islands lake",
        "Faroe Islands village mountains",
        "Faroe Islands scenic landscape"
    ],

    "Suíça": [
        "Swiss Alps lake",
        "Swiss Alps waterfall",
        "Lauterbrunnen Switzerland",
        "Interlaken Switzerland mountains",
        "Grindelwald Switzerland",
        "Swiss mountain cabin",
        "Swiss Alps winter"
    ],

    "Noruega": [
        "Norway fjord",
        "Geirangerfjord Norway",
        "Lofoten Norway mountains",
        "Norway waterfall",
        "Norway mountain lake",
        "Norway winter mountains",
        "Norwegian scenic landscape"
    ],

    "Islândia": [
        "Iceland waterfall",
        "Iceland glacier",
        "Iceland black beach",
        "Iceland mountains",
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
        "New Zealand scenic landscape"
    ],

    "Áustria": [
        "Austrian Alps lake",
        "Hallstatt Austria mountains",
        "Austria waterfall",
        "Austria mountain cabin",
        "Austria winter Alps",
        "Austria alpine lake",
        "Austria scenic mountains"
    ],

    "Eslovênia": [
        "Lake Bled Slovenia",
        "Lake Bohinj Slovenia",
        "Slovenia waterfall",
        "Slovenia Alps",
        "Slovenia mountain lake",
        "Slovenia forest river",
        "Slovenia scenic landscape"
    ],

    "França": [
        "French Alps lake",
        "Chamonix France mountains",
        "French Alps waterfall",
        "Annecy France mountains",
        "French mountain landscape",
        "French Alps winter",
        "France alpine lake"
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
        "Sacred Valley Peru mountains",
        "Peru glacier mountain",
        "Peru scenic landscape",
        "Peruvian Andes lake"
    ],

    "Chile": [
        "Torres del Paine Chile",
        "Patagonia Chile lake",
        "Chile waterfall",
        "Chile Andes mountains",
        "Patagonia mountains",
        "Chile glacier lake",
        "Chile scenic landscape"
    ],

    "Argentina": [
        "Patagonia Argentina mountains",
        "Bariloche Argentina lake",
        "Perito Moreno glacier",
        "Argentina waterfall",
        "Argentina Andes mountains",
        "Patagonia lake",
        "Argentina scenic landscape"
    ]
}


# ============================================================
# PALAVRAS A EVITAR
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
    color: #aaa;
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
    background: #242424;
    color: white;
    border: 1px solid #333;
    border-radius: 10px;
    font-size: 16px;
}

button {
    width: 100%;
    padding: 16px;
    margin-top: 20px;
    border: 0;
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

• 4 cenas diferentes<br>
• 15 segundos por cena<br>
• 60 segundos no total<br>
• 1080 × 1920<br>
• 24 FPS<br>
• Paisagens reais<br>
• Sem pessoas<br>
• Sem música<br>
• Sem narração<br>
• Sem marca-d'água<br>
• Transições suaves

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
        raise Exception(
            "PEXELS_API_KEY não configurada."
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
                resposta.text[:500]
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

        link = arquivo.get(
            "link"
        )

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
            arquivo.get(
                "width"
            ) or 0
        )

        altura = int(
            arquivo.get(
                "height"
            ) or 0
        )

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

    # Preferimos 720p/1080p.
    candidatos.sort(
        key=lambda x: (
            0
            if x["pixels"] <= 1920 * 1080
            else 1,
            abs(
                x["pixels"]
                - 1280 * 720
            )
        )
    )

    return candidatos[0]


# ============================================================
# SELECIONAR CANDIDATOS
# ============================================================

def selecionar_videos(pais):

    queries = PAISES.get(
        pais,
        ["beautiful nature landscape"]
    )

    consultas = queries[:]

    random.shuffle(
        consultas
    )

    candidatos = []

    usados = set()

    for query in consultas[:5]:

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

            if link in usados:
                continue

            usados.add(link)

            titulo = str(
                video.get(
                    "url",
                    ""
                )
            ).lower()

            problemas = 0

            for palavra in PALAVRAS_RUINS:

                if palavra in titulo:
                    problemas += 1

            candidatos.append({
                "arquivo": arquivo,
                "problemas": problemas,
                "query": query
            })

    candidatos.sort(
        key=lambda x: x["problemas"]
    )

    # Mistura um pouco para não gerar
    # sempre os mesmos vídeos.
    melhores = candidatos[:30]

    random.shuffle(
        melhores
    )

    return melhores


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

                    tamanho += len(
                        bloco
                    )

        print(
            "[OK DOWNLOAD]",
            round(
                tamanho / 1024 / 1024,
                2
            ),
            "MB"
        )

        if tamanho < 10000:

            os.remove(
                caminho
            )

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
            resultado.stderr[-4000:]
        )

        raise RuntimeError(
            "FFmpeg falhou."
        )

    return resultado


# ============================================================
# VERIFICAR
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

    # Corte central.
    # Isso permite usar vídeos horizontais,
    # verticais ou quadrados.

    filtro = (
        f"scale={PROCESS_WIDTH}:"
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
            return None

        print(
            "[OK CLIPE]",
            numero
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

                f.write(
                    "file '"
                    + caminho.replace(
                        "'",
                        "'\\''"
                    )
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

        return os.path.exists(
            saida
        )

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
# FINALIZAR
# ============================================================

def finalizar_video(
    entrada,
    saida
):

    filtro = (
        f"scale={WIDTH}:"
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

    return os.path.exists(
        saida
    )


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
# GERAR
# ============================================================

def gerar_video(pais):

    candidatos = selecionar_videos(
        pais
    )

    if not candidatos:

        raise Exception(
            "Nenhum vídeo encontrado."
        )

    clipes = []
    originais = []

    indice = 0

    while len(clipes) < CLIP_COUNT:

        if indice >= len(candidatos):

            break

        item = candidatos[
            indice
        ]

        indice += 1

        print()
        print(
            "[TENTATIVA]",
            len(clipes) + 1,
            "/",
            CLIP_COUNT
        )

        original = baixar_video(
            item
        )

        if not original:
            continue

        originais.append(
            original
        )

        if not verificar_video(
            original
        ):

            print(
                "[PULAR] Vídeo inválido"
            )

            continue

        clipe = processar_clipe(
            original,
            len(clipes) + 1
        )

        if not clipe:
            continue

        clipes.append(
            clipe
        )

    if len(clipes) < CLIP_COUNT:

        limpar(
            originais + clipes
        )

        raise Exception(
            "Não foi possível processar "
            f"vídeos suficientes. "
            f"Obtidos: {len(clipes)}/"
            f"{CLIP_COUNT}"
        )

    # --------------------------------------------------------
    # JUNÇÃO
    # --------------------------------------------------------

    unido = os.path.join(
        TEMP_DIR,
        f"unido_{uuid.uuid4().hex}.mp4"
    )

    if not juntar_clipes(
        clipes,
        unido
    ):

        limpar(
            originais + clipes
        )

        raise Exception(
            "Erro ao juntar os clipes."
        )

    # --------------------------------------------------------
    # FINAL
    # --------------------------------------------------------

    nome = (
        "mundo_afora_"
        + uuid.uuid4().hex
        + ".mp4"
    )

    final = os.path.join(
        OUTPUT_DIR,
        nome
    )

    try:

        if not finalizar_video(
            unido,
            final
        ):

            raise Exception(
                "Erro ao finalizar vídeo."
            )

        print(
            "[FINAL]",
            final
        )

    finally:

        limpar(
            originais
            + clipes
            + [unido]
        )

    return final


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

            # O vídeo agora fica disponível
            # para download.

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
            <body style="
                background:#0b0b0b;
                color:white;
                font-family:Arial;
                padding:30px;
            ">

            <h2>❌ Erro ao gerar vídeo</h2>

            <p>{str(e)}</p>

            <a
                href="/"
                style="color:white"
            >
                ← Voltar
            </a>

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
        "FFmpeg:",
        FFMPEG
    )
    print(
        "Clipes:",
        CLIP_COUNT
    )
    print(
        "Duração:",
        VIDEO_DURATION,
        "segundos"
    )
    print("=" * 70)

    app.run(
        host="0.0.0.0",
        port=PORT
    )