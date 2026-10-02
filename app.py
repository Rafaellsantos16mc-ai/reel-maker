import os
import random
import uuid
import shutil
import subprocess
import requests

from flask import Flask, request, render_template_string, send_file
import imageio_ffmpeg


# ============================================================
# APP
# ============================================================

app = Flask(__name__)

PORT = int(os.getenv("PORT", "8080"))


# ============================================================
# CONFIGURAÇÕES
# ============================================================

WIDTH = 1080
HEIGHT = 1920

PROCESS_WIDTH = 540
PROCESS_HEIGHT = 960

FPS = 24

# Cada lugar fornece 2 trechos
CLIP_DURATION = 15

# 2 lugares x 2 trechos = 4 clipes
CLIP_COUNT = 4

FINAL_DURATION = 60

# Queremos vídeos longos o suficiente para pegar
# dois momentos diferentes do mesmo vídeo.
MIN_SOURCE_DURATION = 32

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

TEMP_DIR = "temp"
OUTPUT_DIR = "outputs"

os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# FFmpeg
# ============================================================

try:
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG = shutil.which("ffmpeg")

if not FFMPEG:
    raise RuntimeError("FFmpeg não encontrado.")


print("=" * 70)
print("🌎 MUNDO AFORA")
print("FFMPEG:", FFMPEG)
print("=" * 70)


# ============================================================
# LOCAIS
# ============================================================

LOCAIS = {

    "Suíça": [
        "Swiss Alps chalet mountain lake",
        "Swiss mountain cabin Alps",
        "Swiss Alps alpine chalet",
        "Swiss mountain cabin snowy landscape",
        "Swiss Alps chalet valley",
        "Swiss alpine lake mountain cabin",
        "Swiss Alps mountain meadow chalet",
        "Swiss mountain waterfall landscape"
    ],

    "Áustria": [
        "Austrian Alps chalet mountain lake",
        "Austria mountain cabin Alps",
        "Austrian alpine chalet snowy mountains",
        "Austria mountain cabin lake",
        "Austrian Alps valley chalet",
        "Austria alpine lake mountains",
        "Austrian mountain meadow cabin",
        "Austria mountain waterfall landscape"
    ],

    "Noruega": [
        "Norway mountain cabin fjord",
        "Norway cabin mountains lake",
        "Norway snowy mountain cabin",
        "Norway fjord mountain landscape",
        "Norway mountain waterfall",
        "Norway peaceful mountain valley",
        "Norway alpine cabin nature",
        "Norway dramatic mountain lake"
    ],

    "Ilhas Faroé": [
        "Faroe Islands mountain waterfall",
        "Faroe Islands green mountains",
        "Faroe Islands valley waterfall",
        "Faroe Islands dramatic landscape",
        "Faroe Islands remote cabin",
        "Faroe Islands green valley",
        "Faroe Islands misty mountains",
        "Faroe Islands scenic nature"
    ],

    "Islândia": [
        "Iceland mountain cabin waterfall",
        "Iceland waterfall mountains",
        "Iceland snowy mountain lake",
        "Iceland mountain valley waterfall",
        "Iceland remote cabin nature",
        "Iceland glacier mountain lake",
        "Iceland dramatic landscape",
        "Iceland peaceful mountain scenery"
    ],

    "Canadá": [
        "Canadian Rockies mountain cabin lake",
        "Canada mountain chalet lake",
        "Canadian Rockies snowy cabin",
        "Canada mountain waterfall",
        "Canada alpine lake cabin",
        "Canadian Rockies valley",
        "Canada mountain forest lake",
        "Canada dramatic mountains"
    ],

    "Nova Zelândia": [
        "New Zealand mountain cabin lake",
        "New Zealand alpine mountain lake",
        "New Zealand mountain waterfall",
        "New Zealand mountain valley",
        "New Zealand snowy mountain lake",
        "New Zealand remote cabin",
        "New Zealand dramatic mountains",
        "New Zealand scenic landscape"
    ],

    "Eslovênia": [
        "Slovenia mountain cabin lake",
        "Slovenia alpine chalet",
        "Slovenia mountain waterfall",
        "Slovenia alpine lake mountains",
        "Slovenia peaceful mountain valley",
        "Slovenia snowy Alps cabin",
        "Slovenia mountain meadow",
        "Slovenia cinematic landscape"
    ],

    "França": [
        "French Alps chalet mountain lake",
        "French Alps mountain cabin",
        "French Alps snowy chalet",
        "French Alps mountain valley",
        "French Alps waterfall",
        "French Alps alpine lake",
        "French mountain meadow chalet",
        "French Alps landscape"
    ],

    "Itália": [
        "Italian Dolomites chalet mountain lake",
        "Dolomites mountain cabin",
        "Italian Alps snowy cabin",
        "Dolomites mountain valley",
        "Dolomites alpine lake",
        "Italian mountain waterfall",
        "Dolomites meadow chalet",
        "Dolomites landscape"
    ],

    "Japão": [
        "Japan mountain cabin lake",
        "Japan snowy mountain cabin",
        "Japan mountain waterfall",
        "Japanese alpine valley",
        "Japan mountain lake",
        "Japan peaceful mountain landscape",
        "Japan forest waterfall mountains",
        "Japanese mountain cabin"
    ],

    "Chile": [
        "Patagonia mountain cabin lake",
        "Chile Patagonia mountains waterfall",
        "Patagonia snowy mountain landscape",
        "Chile mountain lake valley",
        "Torres del Paine mountains lake",
        "Patagonia remote cabin",
        "Chile dramatic mountains",
        "Patagonia scenic landscape"
    ],

    "Argentina": [
        "Patagonia mountain cabin lake",
        "Argentina Patagonia snowy mountains",
        "Argentina mountain waterfall",
        "Patagonia alpine lake",
        "Argentina mountain valley cabin",
        "Patagonia dramatic mountains",
        "Argentina mountain landscape",
        "Patagonia scenic nature"
    ],

    "Brasil": [
        "Brazil mountain cabin lake",
        "Brazil mountain waterfall",
        "Brazil beautiful mountain valley",
        "Brazil mountain lake landscape",
        "Brazil countryside mountain cabin",
        "Brazil waterfall mountain landscape",
        "Brazil green mountains valley",
        "Brazil scenic nature"
    ]
}


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

    background:
        radial-gradient(
            circle at top,
            #26384a 0%,
            #111 45%,
            #080808 100%
        );

    color: white;

    font-family: Arial, sans-serif;

    min-height: 100vh;
}

.container {

    max-width: 600px;

    margin: auto;
}

h1 {

    text-align: center;

    margin-bottom: 8px;

    font-size: 32px;
}

.subtitle {

    text-align: center;

    color: #aaa;

    margin-bottom: 30px;

    line-height: 1.5;
}

label {

    display: block;

    margin-bottom: 8px;

    font-weight: bold;
}

select,
button {

    width: 100%;

    padding: 16px;

    margin-bottom: 20px;

    border-radius: 12px;

    border: none;

    font-size: 16px;
}

select {

    background: #222;

    color: white;

    border: 1px solid #333;
}

button {

    background: white;

    color: #111;

    font-weight: bold;

    cursor: pointer;
}

button:hover {

    opacity: 0.9;
}

.info {

    background: rgba(30,30,30,0.95);

    padding: 18px;

    border-radius: 14px;

    margin-bottom: 25px;

    color: #ccc;

    line-height: 1.7;

    border: 1px solid #333;
}

.destaque {

    color: white;

    font-weight: bold;
}

.credito {

    text-align: center;

    color: #777;

    font-size: 12px;

    margin-top: 20px;
}

</style>

</head>

<body>

<div class="container">

<h1>🏔️ Mundo Afora</h1>

<div class="subtitle">

Paisagens de sonho pelo mundo

</div>

<div class="info">

<span class="destaque">
🎬 Vídeos cinematográficos
</span>

<br>

🏔️ Montanhas e Alpes
<br>

🏡 Chalés e cabanas
<br>

🏞️ Lagos e vales
<br>

💧 Cachoeiras
<br>

❄️ Neve e natureza
<br>

🎥 Dois momentos do mesmo lugar
<br>

📱 1080 × 1920
<br>

⏱️ 60 segundos
<br>

🔇 Sem áudio
<br>

🚫 Sem legenda
<br>

🚫 Sem pessoas como foco

</div>

<form method="POST" action="/gerar">

<label>
Escolha o destino
</label>

<select name="local" required>

{% for local in locais %}

<option value="{{ local }}">
{{ local }}
</option>

{% endfor %}

</select>

<button type="submit">

🏔️ GERAR VÍDEO

</button>

</form>

<div class="credito">

Vídeos fornecidos pelo Pexels

</div>

</div>

</body>

</html>
"""


# ============================================================
# REMOVER ARQUIVO
# ============================================================

def remover_arquivo(path):

    try:

        if os.path.exists(path):

            os.remove(path)

    except Exception as e:

        print(
            "[ERRO REMOVENDO]",
            e
        )


# ============================================================
# BUSCAR VÍDEO LONGO
# ============================================================

def buscar_video(
    query,
    usados=None
):

    if not PEXELS_API_KEY:

        raise RuntimeError(
            "PEXELS_API_KEY não configurada."
        )

    if usados is None:

        usados = set()

    url = (
        "https://api.pexels.com/"
        "v1/videos/search"
    )

    headers = {
        "Authorization":
            PEXELS_API_KEY
    }

    params = {

        "query": query,

        "per_page": 80,

        "orientation": "landscape",

        "size": "large",

        "locale": "en-US",

        "page": 1
    }

    print("=" * 60)

    print(
        "[PEXELS]",
        query
    )

    try:

        response = requests.get(

            url,

            headers=headers,

            params=params,

            timeout=40
        )

        response.raise_for_status()

    except Exception as e:

        print(
            "[ERRO PEXELS]",
            repr(e)
        )

        return None

    data = response.json()

    videos = data.get(
        "videos",
        []
    )

    if not videos:

        print(
            "[SEM RESULTADOS]"
        )

        return None

    random.shuffle(videos)

    candidatos = []

    for video in videos:

        video_id = video.get("id")

        if not video_id:

            continue

        if video_id in usados:

            continue

        duration = float(
            video.get(
                "duration",
                0
            ) or 0
        )

        # Precisamos de pelo menos 32 segundos
        if duration < MIN_SOURCE_DURATION:

            continue

        files = video.get(
            "video_files",
            []
        )

        melhores = []

        for arquivo in files:

            link = arquivo.get(
                "link"
            )

            if not link:

                continue

            width = int(
                arquivo.get(
                    "width",
                    0
                ) or 0
            )

            height = int(
                arquivo.get(
                    "height",
                    0
                ) or 0
            )

            fps = float(
                arquivo.get(
                    "fps",
                    0
                ) or 0
            )

            if width < 720:

                continue

            if height < 400:

                continue

            pixels = width * height

            score = pixels

            # Preferimos horizontal
            if width > height:

                score += 1000000

            # Preferimos 24 FPS ou mais
            if fps >= 24:

                score += 500000

            melhores.append(
                (
                    score,
                    width,
                    height,
                    fps,
                    link
                )
            )

        if not melhores:

            continue

        melhores.sort(
            reverse=True
        )

        (
            score,
            width,
            height,
            fps,
            link
        ) = melhores[0]

        candidatos.append(
            (
                score,
                video_id,
                duration,
                width,
                height,
                fps,
                link
            )
        )

    if not candidatos:

        print(
            "[NENHUM VÍDEO LONGO COMPATÍVEL]"
        )

        return None

    # Ordena por qualidade
    candidatos.sort(
        reverse=True
    )

    # Escolhe entre os 10 melhores
    melhores = candidatos[
        :min(10, len(candidatos))
    ]

    escolhido = random.choice(
        melhores
    )

    (
        score,
        video_id,
        duration,
        width,
        height,
        fps,
        link
    ) = escolhido

    usados.add(
        video_id
    )

    print(
        "[VÍDEO ESCOLHIDO]",
        "ID:", video_id,
        "| duração:",
        duration,
        "| resolução:",
        f"{width}x{height}",
        "| FPS:",
        fps
    )

    return {
        "id": video_id,
        "duration": duration,
        "url": link
    }


# ============================================================
# DOWNLOAD
# ============================================================

def baixar_video(
    url,
    destino
):

    headers = {
        "User-Agent":
            "Mozilla/5.0"
    }

    print(
        "[DOWNLOAD]",
        url
    )

    with requests.get(

        url,

        headers=headers,

        stream=True,

        timeout=120

    ) as response:

        response.raise_for_status()

        with open(
            destino,
            "wb"
        ) as f:

            for chunk in response.iter_content(

                chunk_size=
                    1024 * 1024

            ):

                if chunk:

                    f.write(
                        chunk
                    )

    tamanho = os.path.getsize(
        destino
    )

    print(
        "[DOWNLOAD OK]",
        round(
            tamanho /
            1024 /
            1024,
            2
        ),
        "MB"
    )

    if tamanho < 50000:

        remover_arquivo(
            destino
        )

        raise RuntimeError(
            "Download inválido."
        )

    return destino


# ============================================================
# PROCESSAR TRECHO
# ============================================================

def processar_trecho(
    entrada,
    saida,
    inicio
):

    print("=" * 60)

    print(
        "[PROCESSANDO TRECHO]"
    )

    print(
        "Início:",
        inicio
    )

    print(
        "Duração:",
        CLIP_DURATION
    )

    print("=" * 60)

    comando = [

        FFMPEG,

        "-hide_banner",

        "-loglevel",
        "error",

        "-y",

        "-ss",
        str(inicio),

        "-i",
        entrada,

        "-t",
        str(CLIP_DURATION),

        "-vf",

        (
            f"scale={PROCESS_WIDTH}:{PROCESS_HEIGHT}:"
            "force_original_aspect_ratio=increase,"
            f"crop={PROCESS_WIDTH}:{PROCESS_HEIGHT},"
            f"fps={FPS},"
            "format=yuv420p"
        ),

        # SEM ÁUDIO
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
        str(FPS),

        "-movflags",
        "+faststart",

        saida
    ]

    result = subprocess.run(

        comando,

        stdout=subprocess.PIPE,

        stderr=subprocess.PIPE,

        text=True
    )

    if result.returncode != 0:

        print(
            "[ERRO TRECHO]"
        )

        print(
            result.stderr
        )

        raise RuntimeError(
            "Falha ao processar trecho."
        )

    if not os.path.exists(
        saida
    ):

        raise RuntimeError(
            "Trecho não foi criado."
        )

    tamanho = os.path.getsize(
        saida
    )

    if tamanho < 10000:

        raise RuntimeError(
            "Trecho inválido."
        )

    print(
        "[TRECHO OK]",
        round(
            tamanho /
            1024 /
            1024,
            2
        ),
        "MB"
    )

    return saida


# ============================================================
# CONCATENAR
# ============================================================

def concatenar_clipes(
    clipes,
    saida
):

    lista = os.path.join(

        TEMP_DIR,

        f"concat_"
        f"{uuid.uuid4().hex}.txt"
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
                    "\\",
                    "/"
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

            "-hide_banner",

            "-loglevel",
            "error",

            "-y",

            "-f",
            "concat",

            "-safe",
            "0",

            "-i",
            lista,

            "-an",

            "-c",
            "copy",

            saida
        ]

        result = subprocess.run(

            comando,

            stdout=subprocess.PIPE,

            stderr=subprocess.PIPE,

            text=True
        )

        if result.returncode != 0:

            print(
                "[ERRO CONCAT]"
            )

            print(
                result.stderr
            )

            raise RuntimeError(
                "Falha na concatenação."
            )

        if not os.path.exists(
            saida
        ):

            raise RuntimeError(
                "Concatenação não criada."
            )

        return saida

    finally:

        remover_arquivo(
            lista
        )


# ============================================================
# FINALIZAR
# ============================================================

def finalizar_video(
    entrada,
    saida
):

    print("=" * 60)

    print(
        "[FINALIZANDO]"
    )

    print("=" * 60)

    comando = [

        FFMPEG,

        "-hide_banner",

        "-loglevel",
        "error",

        "-y",

        "-i",
        entrada,

        "-vf",

        (
            f"scale={WIDTH}:{HEIGHT}:"
            "force_original_aspect_ratio=increase,"
            f"crop={WIDTH}:{HEIGHT},"
            f"fps={FPS},"
            "format=yuv420p"
        ),

        # GARANTIA DE SEM ÁUDIO
        "-an",

        "-c:v",
        "libx264",

        "-preset",
        "ultrafast",

        "-crf",
        "29",

        "-pix_fmt",
        "yuv420p",

        "-r",
        str(FPS),

        "-t",
        str(FINAL_DURATION),

        "-movflags",
        "+faststart",

        saida
    ]

    result = subprocess.run(

        comando,

        stdout=subprocess.PIPE,

        stderr=subprocess.PIPE,

        text=True
    )

    print(
        "[FFMPEG RETURN CODE]",
        result.returncode
    )

    if result.returncode != 0:

        print(
            result.stderr
        )

        raise RuntimeError(
            "FFmpeg falhou na finalização."
        )

    if not os.path.exists(
        saida
    ):

        raise RuntimeError(
            "Vídeo final não criado."
        )

    tamanho = os.path.getsize(
        saida
    )

    if tamanho < 100000:

        raise RuntimeError(
            "Vídeo final inválido."
        )

    print(
        "[VIDEO FINAL OK]",
        round(
            tamanho /
            1024 /
            1024,
            2
        ),
        "MB"
    )

    return saida


# ============================================================
# GERAR VÍDEO
# ============================================================

def gerar_video(
    local
):

    if local not in LOCAIS:

        raise ValueError(
            "Local inválido."
        )

    trabalho = os.path.join(

        TEMP_DIR,

        uuid.uuid4().hex
    )

    os.makedirs(
        trabalho,
        exist_ok=True
    )

    clipes = []

    videos_usados = set()

    try:

        queries = list(
            LOCAIS[local]
        )

        random.shuffle(
            queries
        )

        # ====================================================
        # 2 LUGARES
        # ====================================================

        lugares_encontrados = 0

        for lugar in range(2):

            if lugar >= len(queries):

                break

            query = queries[lugar]

            print("=" * 70)

            print(
                "🏔️ LUGAR",
                lugar + 1,
                "/ 2"
            )

            print(
                "[BUSCA]",
                query
            )

            print("=" * 70)

            video = None

            # Tenta várias pesquisas caso a primeira
            # não tenha um vídeo longo.
            tentativas = 0

            while (
                video is None
                and tentativas < 5
            ):

                tentativas += 1

                if tentativas > 1:

                    query_tentativa = random.choice(
                        queries
                    )

                else:

                    query_tentativa = query

                video = buscar_video(

                    query_tentativa,

                    videos_usados
                )

            if not video:

                print(
                    "[SEM VÍDEO PARA ESTE LUGAR]"
                )

                continue

            lugares_encontrados += 1

            original = os.path.join(

                trabalho,

                f"lugar_{lugar}.mp4"
            )

            baixar_video(

                video["url"],

                original
            )

            # =================================================
            # DOIS TRECHOS DO MESMO VÍDEO
            # =================================================

            duracao = float(
                video["duration"]
            )

            # Primeiro trecho:
            # início do vídeo
            inicio_1 = 0

            # Segundo trecho:
            # pega outra parte do mesmo vídeo.
            #
            # Nunca deixa ultrapassar a duração disponível.
            max_inicio = max(
                1,
                int(
                    duracao
                    - CLIP_DURATION
                    - 1
                )
            )

            if max_inicio <= 5:

                inicio_2 = 8

            else:

                inicio_2 = random.randint(
                    5,
                    max_inicio
                )

            # Garantia para não ficar praticamente
            # no mesmo ponto.
            if inicio_2 < 8:

                inicio_2 = 8

            # -----------------------------------------------
            # TRECHO 1
            # -----------------------------------------------

            trecho_1 = os.path.join(

                trabalho,

                f"trecho_{lugar}_1.mp4"
            )

            processar_trecho(

                original,

                trecho_1,

                inicio_1
            )

            clipes.append(
                trecho_1
            )

            # -----------------------------------------------
            # TRECHO 2
            # -----------------------------------------------

            trecho_2 = os.path.join(

                trabalho,

                f"trecho_{lugar}_2.mp4"
            )

            processar_trecho(

                original,

                trecho_2,

                inicio_2
            )

            clipes.append(
                trecho_2
            )

            print("=" * 70)

            print(
                "🏔️ MESMO LUGAR"
            )

            print(
                "Trecho 1:",
                inicio_1,
                "segundos"
            )

            print(
                "Trecho 2:",
                inicio_2,
                "segundos"
            )

            print("=" * 70)

            # Remove vídeo original
            remover_arquivo(
                original
            )

        # ====================================================
        # VERIFICAR
        # ====================================================

        if len(clipes) < 4:

            raise RuntimeError(

                "Não foi possível encontrar "
                "2 vídeos longos de paisagens "
                "para montar os 4 trechos."
            )

        # ====================================================
        # CONCAT
        # ====================================================

        concatenado = os.path.join(

            trabalho,

            "concatenado.mp4"
        )

        concatenar_clipes(

            clipes,

            concatenado
        )

        # ====================================================
        # FINAL
        # ====================================================

        nome_final = (

            "mundo_afora_"

            + uuid.uuid4().hex[:10]

            + ".mp4"
        )

        saida_final = os.path.join(

            OUTPUT_DIR,

            nome_final
        )

        finalizar_video(

            concatenado,

            saida_final
        )

        print("=" * 70)

        print(
            "🌎 VÍDEO CONCLUÍDO"
        )

        print(
            saida_final
        )

        print("=" * 70)

        return saida_final

    finally:

        shutil.rmtree(

            trabalho,

            ignore_errors=True
        )


# ============================================================
# HOME
# ============================================================

@app.route(
    "/",
    methods=["GET"]
)
def index():

    return render_template_string(

        HTML,

        locais=LOCAIS.keys()
    )


# ============================================================
# GERAR
# ============================================================

@app.route(
    "/gerar",
    methods=["POST"]
)
def gerar():

    local = request.form.get(
        "local",
        ""
    ).strip()

    try:

        arquivo = gerar_video(
            local
        )

        return send_file(

            arquivo,

            as_attachment=True,

            download_name=
                os.path.basename(
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

<!DOCTYPE html>

<html lang="pt-BR">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width,initial-scale=1">

<style>

body {{

    background:#111;

    color:white;

    font-family:Arial;

    padding:30px;

    text-align:center;
}}

.erro {{

    background:#222;

    padding:25px;

    border-radius:14px;

    max-width:600px;

    margin:auto;
}}

a {{

    display:block;

    margin-top:20px;

    color:white;
}}

</style>

</head>

<body>

<div class="erro">

<h2>
❌ Erro ao gerar
</h2>

<p>
Não foi possível gerar o vídeo.
</p>

<p>
Tente novamente.
</p>

<a href="/">
← Voltar
</a>

</div>

</body>

</html>

""", 500


# ============================================================
# HEALTH
# ============================================================

@app.route(
    "/health"
)
def health():

    return {

        "status":
            "ok",

        "ffmpeg":
            FFMPEG,

        "clips":
            4,

        "source_videos":
            2,

        "duration":
            FINAL_DURATION,

        "resolution":
            f"{WIDTH}x{HEIGHT}",

        "audio":
            False,

        "captions":
            False,

        "style":
            "cinematic landscape",

        "same_location_segments":
            True
    }


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=PORT
    )