import os
import random
import uuid
import shutil
import subprocess
import requests
import time

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

CLIP_DURATION = 15
CLIP_COUNT = 4
FINAL_DURATION = 60

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

VIDEO_DIR = "videos"
TEMP_DIR = "temp"
OUTPUT_DIR = "outputs"

os.makedirs(VIDEO_DIR, exist_ok=True)
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
# PAÍSES / LOCAIS
#
# As buscas foram pensadas para:
#
# - chalés
# - cabanas
# - montanhas
# - lagos
# - neve
# - cachoeiras
# - vales
# - paisagens cinematográficas
#
# Evitamos termos relacionados a:
# pessoas, cidades, carros, ruas e turismo urbano.
# ============================================================

LOCAIS = {

    "Suíça": [

        "Swiss Alps chalet mountain lake",
        "Swiss mountain cabin Alps landscape",
        "Switzerland alpine village chalet mountains",
        "Swiss Alps snowy mountain cabin",
        "Swiss Alps lake chalet cinematic",
        "Switzerland mountain valley waterfall",
        "Swiss mountain meadow chalet",
        "Swiss Alps sunrise landscape"
    ],


    "Áustria": [

        "Austrian Alps chalet mountain lake",
        "Austria mountain cabin Alps landscape",
        "Austrian Alps snowy cabin",
        "Austria alpine lake mountains",
        "Austria mountain valley chalet",
        "Austrian Alps waterfall landscape",
        "Austria meadow mountain cabin",
        "Austrian Alps sunrise"
    ],


    "Noruega": [

        "Norway mountain cabin fjord landscape",
        "Norway fjord mountain cabin",
        "Norway snowy mountains lake",
        "Norway mountain waterfall landscape",
        "Norway peaceful mountain valley",
        "Norway alpine cabin nature",
        "Norway dramatic mountains lake",
        "Norway scenic fjord mountains"
    ],


    "Ilhas Faroé": [

        "Faroe Islands mountain waterfall landscape",
        "Faroe Islands green mountains ocean",
        "Faroe Islands valley waterfall",
        "Faroe Islands dramatic cliffs landscape",
        "Faroe Islands remote cabin landscape",
        "Faroe Islands green valley mountains",
        "Faroe Islands misty mountains",
        "Faroe Islands scenic nature"
    ],


    "Islândia": [

        "Iceland mountain cabin waterfall",
        "Iceland waterfall mountains landscape",
        "Iceland snowy mountains lake",
        "Iceland dramatic valley waterfall",
        "Iceland peaceful mountain landscape",
        "Iceland glacier mountains lake",
        "Iceland remote cabin nature",
        "Iceland cinematic landscape"
    ],


    "Canadá": [

        "Canadian Rockies mountain cabin lake",
        "Canada mountain chalet lake",
        "Canadian Rockies snowy mountains",
        "Canada mountain waterfall landscape",
        "Canada alpine lake cabin",
        "Canadian Rockies valley landscape",
        "Canada mountain forest lake",
        "Canada dramatic mountain landscape"
    ],


    "Nova Zelândia": [

        "New Zealand mountain cabin lake",
        "New Zealand alpine mountains lake",
        "New Zealand waterfall mountains",
        "New Zealand mountain valley landscape",
        "New Zealand snowy mountain lake",
        "New Zealand remote cabin nature",
        "New Zealand dramatic mountains",
        "New Zealand cinematic landscape"
    ],


    "Eslovênia": [

        "Slovenia mountain cabin lake",
        "Slovenia alpine chalet mountains",
        "Slovenia mountain waterfall landscape",
        "Slovenia alpine lake mountains",
        "Slovenia peaceful mountain valley",
        "Slovenia snowy Alps cabin",
        "Slovenia mountain meadow landscape",
        "Slovenia cinematic nature"
    ],


    "França": [

        "French Alps chalet mountain lake",
        "French Alps mountain cabin",
        "French Alps snowy chalet",
        "French Alps mountain valley",
        "French Alps waterfall landscape",
        "French Alps alpine lake",
        "French mountain meadow chalet",
        "French Alps cinematic landscape"
    ],


    "Itália": [

        "Italian Dolomites chalet mountain lake",
        "Dolomites mountain cabin landscape",
        "Italian Alps snowy cabin",
        "Dolomites mountain valley",
        "Dolomites alpine lake",
        "Italian mountain waterfall landscape",
        "Dolomites meadow chalet",
        "Dolomites cinematic landscape"
    ],


    "Japão": [

        "Japan mountain cabin lake nature",
        "Japan snowy mountain cabin",
        "Japan mountain waterfall landscape",
        "Japanese alpine valley",
        "Japan mountain lake cinematic",
        "Japan peaceful mountain landscape",
        "Japan forest waterfall mountains",
        "Japanese mountain cabin nature"
    ],


    "Chile": [

        "Patagonia mountain cabin lake",
        "Chile Patagonia mountains waterfall",
        "Patagonia snowy mountain landscape",
        "Chile mountain lake valley",
        "Torres del Paine mountains lake",
        "Patagonia remote cabin nature",
        "Chile dramatic mountain landscape",
        "Patagonia cinematic landscape"
    ],


    "Argentina": [

        "Patagonia mountain cabin lake",
        "Argentina Patagonia snowy mountains",
        "Argentina mountain waterfall landscape",
        "Patagonia alpine lake",
        "Argentina mountain valley cabin",
        "Patagonia dramatic mountains",
        "Argentina peaceful mountain landscape",
        "Patagonia cinematic landscape"
    ],


    "Brasil": [

        "Brazil mountain cabin lake landscape",
        "Brazil mountain waterfall nature",
        "Brazil beautiful mountain valley",
        "Brazil mountain lake cinematic",
        "Brazil countryside mountain cabin",
        "Brazil waterfall mountain landscape",
        "Brazil green mountains valley",
        "Brazil scenic nature landscape"
    ]
}


# ============================================================
# TERMOS DE SEGURANÇA VISUAL
#
# São adicionados às pesquisas para reforçar o tipo
# de resultado que queremos.
# ============================================================

TERMOS_NATUREZA = [
    "cinematic landscape",
    "scenic nature",
    "beautiful landscape",
    "peaceful nature",
    "dramatic landscape"
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

    background:
        radial-gradient(
            circle at top,
            #243447 0%,
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

    transform: scale(1.01);
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

Paisagens que parecem de outro planeta

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

❄️ Neve e paisagens naturais
<br>

📱 1080 × 1920
<br>

⏱️ 60 segundos
<br>

🔇 Sem áudio
<br>

🚫 Sem legenda
<br>

🚫 Sem pessoas

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

🏔️ GERAR PAISAGEM

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
# BUSCAR VÍDEO NO PEXELS
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


    # --------------------------------------------------------
    # NOVO ENDPOINT DA PEXELS
    # --------------------------------------------------------

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
        "[PEXELS SEARCH]",
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
            "[SEM RESULTADO]",
            query
        )

        return None


    # Embaralha para não pegar sempre os mesmos
    random.shuffle(videos)


    candidatos = []


    for video in videos:

        video_id = video.get("id")


        if not video_id:

            continue


        # Não repetir vídeo
        if video_id in usados:

            continue


        # ----------------------------------------------------
        # DURAÇÃO
        # ----------------------------------------------------

        duration = video.get(
            "duration",
            0
        )


        # Preferimos vídeos com pelo menos 15 segundos
        if duration < CLIP_DURATION:

            continue


        # ----------------------------------------------------
        # ARQUIVOS
        # ----------------------------------------------------

        files = video.get(
            "video_files",
            []
        )


        if not files:

            continue


        melhores = []


        for arquivo in files:

            link = arquivo.get(
                "link"
            )


            if not link:

                continue


            width = (
                arquivo.get(
                    "width"
                ) or 0
            )


            height = (
                arquivo.get(
                    "height"
                ) or 0
            )


            fps = (
                arquivo.get(
                    "fps"
                ) or 0
            )


            # Ignorar arquivos pequenos demais
            if width < 720:

                continue


            if height < 400:

                continue


            # ------------------------------------------------
            # Pontuação de qualidade
            # ------------------------------------------------

            pixels = width * height


            score = pixels


            # Preferência por vídeos horizontais
            if width > height:

                score += 1000000


            # Preferência por 24/25/30/60 FPS
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
            "[NENHUM CLIPE COMPATÍVEL]"
        )

        return None


    candidatos.sort(
        reverse=True
    )


    # --------------------------------------------------------
    # Escolhe aleatoriamente entre os melhores
    # --------------------------------------------------------

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
        "[VIDEO ESCOLHIDO]",
        "ID:", video_id,
        "| duração:", duration,
        "| resolução:",
        f"{width}x{height}",
        "| FPS:", fps
    )


    return link


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
            "Download ficou pequeno/inválido."
        )


    return destino


# ============================================================
# PROCESSAR CLIPE
# ============================================================

def processar_clipe(
    entrada,
    saida
):

    print("=" * 60)

    print(
        "[PROCESSANDO CLIPE]"
    )

    print(
        entrada
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


        # Começa do início
        "-ss",
        "0",


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
            "[ERRO CLIPE]"
        )

        print(
            result.stderr
        )

        raise RuntimeError(
            "Falha ao processar clipe."
        )


    if not os.path.exists(
        saida
    ):

        raise RuntimeError(
            "Clipe não foi criado."
        )


    tamanho = os.path.getsize(
        saida
    )


    if tamanho < 10000:

        raise RuntimeError(
            "Clipe processado inválido."
        )


    print(

        "[CLIPE OK]",

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


        print("=" * 60)

        print(
            "[CONCATENANDO]"
        )

        print("=" * 60)


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
                "Falha ao juntar os clipes."
            )


        if not os.path.exists(
            saida
        ):

            raise RuntimeError(
                "Concatenação não criada."
            )


        tamanho = os.path.getsize(
            saida
        )


        print(

            "[CONCAT OK]",

            round(
                tamanho /
                1024 /
                1024,
                2
            ),

            "MB"
        )


        return saida


    finally:

        remover_arquivo(
            lista
        )


# ============================================================
# FINALIZAR VÍDEO
# ============================================================

def finalizar_video(
    entrada,
    saida
):

    print("=" * 60)

    print(
        "[FINALIZANDO VÍDEO]"
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


        # GARANTIA: SEM ÁUDIO
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
            "[FFMPEG ERRO]"
        )

        print(
            result.stderr
        )

        raise RuntimeError(
            "FFmpeg falhou."
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


    clipes_processados = []


    # Guarda IDs dos vídeos já usados
    videos_usados = set()


    try:

        queries = list(
            LOCAIS[local]
        )


        # ----------------------------------------------------
        # Embaralha as buscas
        # ----------------------------------------------------

        random.shuffle(
            queries
        )


        # ----------------------------------------------------
        # Tenta várias pesquisas até conseguir 4 vídeos
        # ----------------------------------------------------

        tentativas = 0

        max_tentativas = 12


        while (

            len(clipes_processados)
            < CLIP_COUNT

            and

            tentativas
            < max_tentativas

        ):


            tentativas += 1


            # Escolhe uma busca
            query = queries[
                (tentativas - 1)
                % len(queries)
            ]


            # ------------------------------------------------
            # Às vezes adiciona termo cinematográfico
            # ------------------------------------------------

            if random.random() < 0.55:

                termo = random.choice(
                    TERMOS_NATUREZA
                )

                query_final = (
                    query
                    + " "
                    + termo
                )

            else:

                query_final = query


            print("=" * 60)

            print(
                "[TENTATIVA]",
                tentativas,
                "/",
                max_tentativas
            )

            print(
                "[BUSCA]",
                query_final
            )

            print("=" * 60)


            url = buscar_video(

                query_final,

                videos_usados
            )


            if not url:

                print(
                    "[PULAR] Nenhum vídeo."
                )

                continue


            indice = len(
                clipes_processados
            )


            original = os.path.join(

                trabalho,

                f"original_{indice}.mp4"
            )


            processado = os.path.join(

                trabalho,

                f"clip_{indice}.mp4"
            )


            try:

                # --------------------------------------------
                # DOWNLOAD
                # --------------------------------------------

                baixar_video(

                    url,

                    original
                )


                # --------------------------------------------
                # PROCESSAMENTO
                # --------------------------------------------

                processar_clipe(

                    original,

                    processado
                )


                clipes_processados.append(
                    processado
                )


                # Remove original imediatamente
                remover_arquivo(
                    original
                )


                print(

                    "[CLIPE ADICIONADO]",

                    len(
                        clipes_processados
                    ),

                    "/",

                    CLIP_COUNT
                )


            except Exception as e:

                print(
                    "[ERRO NO CLIPE]",
                    repr(e)
                )


                remover_arquivo(
                    original
                )

                remover_arquivo(
                    processado
                )


        # ----------------------------------------------------
        # VERIFICAR
        # ----------------------------------------------------

        print("=" * 60)

        print(
            "[CLIPES VÁLIDOS]",
            len(
                clipes_processados
            )
        )

        print("=" * 60)


        if len(
            clipes_processados
        ) < CLIP_COUNT:

            raise RuntimeError(

                "Não foi possível encontrar "
                f"{CLIP_COUNT} vídeos de paisagem "
                "compatíveis."
            )


        # ----------------------------------------------------
        # CONCATENAR
        # ----------------------------------------------------

        concatenado = os.path.join(

            trabalho,

            "concatenado.mp4"
        )


        concatenar_clipes(

            clipes_processados,

            concatenado
        )


        # ----------------------------------------------------
        # ARQUIVO FINAL
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # LIMPAR TEMPORÁRIOS
        # ----------------------------------------------------

        try:

            shutil.rmtree(

                trabalho,

                ignore_errors=True
            )

        except Exception:

            pass


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
# HEALTH CHECK
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
            CLIP_COUNT,

        "duration":
            FINAL_DURATION,

        "resolution":
            f"{WIDTH}x{HEIGHT}",

        "audio":
            False,

        "captions":
            False,

        "style":
            "cinematic mountain landscapes"
    }


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=PORT
    )