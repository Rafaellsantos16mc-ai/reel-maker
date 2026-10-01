import os
import re
import uuid
import random
import shutil
import subprocess

import requests
import imageio_ffmpeg

from flask import Flask, request, render_template_string, send_file


# ============================================================
# CONFIGURAÇÕES
# ============================================================

app = Flask(__name__)

PORT = int(os.getenv("PORT", "8080"))

WIDTH = 1080
HEIGHT = 1920
FPS = 24

DURATION = 60

CLIP_COUNT = 8
CLIP_DURATION = 7.5

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

VIDEO_DIR = "videos"
TEMP_DIR = "temp"
OUTPUT_DIR = "outputs"

os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# PAÍSES
# ============================================================

PAISES = {

    "Brasil": [
        "Brazil mountains lake",
        "Brazil sea cliffs",
        "Brazil mountain cabin",
        "Brazil mountain valley",
        "Brazil scenic mountains",
        "Brazil mountain lake",
        "Brazil lake mountains",
        "Brazil ocean cliffs",
    ],

    "Ilhas Faroé": [
        "Faroe Islands mountains ocean",
        "Faroe Islands cliffs",
        "Faroe Islands lake mountains",
        "Faroe Islands green valley",
        "Faroe Islands waterfall mountains",
        "Faroe Islands scenic landscape",
    ],

    "Suíça": [
        "Switzerland mountains lake",
        "Swiss Alps lake",
        "Switzerland mountain cabin",
        "Swiss mountain valley",
        "Swiss Alps chalet",
        "Switzerland green valley",
        "Swiss lake mountains",
    ],

    "Noruega": [
        "Norway fjord mountains",
        "Norway mountain lake",
        "Norway cliffs ocean",
        "Norway green valley",
        "Norway mountain cabin",
        "Norwegian fjord landscape",
    ],

    "Islândia": [
        "Iceland mountains waterfall",
        "Iceland lake mountains",
        "Iceland cliffs ocean",
        "Iceland green valley",
        "Iceland scenic landscape",
        "Iceland waterfall mountains",
    ],

    "Canadá": [
        "Canada Rocky Mountains lake",
        "Canada mountain lake",
        "Canada mountain cabin",
        "Canada green valley",
        "Canadian Rockies landscape",
        "Canada turquoise lake mountains",
    ],

    "Nova Zelândia": [
        "New Zealand mountains lake",
        "New Zealand mountain valley",
        "New Zealand mountain cabin",
        "New Zealand green valley",
        "New Zealand lake mountains",
        "New Zealand scenic landscape",
    ],

    "Áustria": [
        "Austria Alps lake",
        "Austria mountain cabin",
        "Austria mountain valley",
        "Austrian Alps landscape",
        "Austria green valley",
        "Austria lake mountains",
    ],

    "Eslovênia": [
        "Slovenia mountains lake",
        "Slovenia Lake Bled mountains",
        "Slovenia mountain valley",
        "Slovenia green valley",
        "Slovenia mountain waterfall",
    ],

    "França": [
        "French Alps lake",
        "France mountain valley",
        "French Alps cabin",
        "France mountain lake",
        "French Alps landscape",
    ],

    "Itália": [
        "Italian Alps lake",
        "Dolomites lake mountains",
        "Dolomites mountain cabin",
        "Italy green mountain valley",
        "Dolomites landscape",
    ],

    "Estados Unidos": [
        "USA mountain lake",
        "Rocky Mountains lake",
        "USA mountain cabin",
        "USA mountain valley",
        "Yosemite mountains lake",
        "Alaska mountains lake",
    ],

    "Japão": [
        "Japan mountain lake",
        "Japan mountain valley",
        "Japan scenic mountains",
        "Japan lake mountains",
        "Japan green valley",
    ],

    "Peru": [
        "Peru Andes mountains lake",
        "Peru mountain valley",
        "Peru green mountains",
        "Peru scenic mountain lake",
    ],

    "Chile": [
        "Chile Patagonia mountains lake",
        "Chile mountain lake",
        "Patagonia mountains",
        "Chile green valley",
        "Chile scenic landscape",
    ],

    "Argentina": [
        "Argentina Patagonia mountains lake",
        "Argentina mountain lake",
        "Patagonia mountain valley",
        "Argentina green valley",
        "Argentina scenic mountains",
    ],
}


# ============================================================
# TERMOS QUE NÃO QUEREMOS
# ============================================================

PALAVRAS_RUINS = [
    "person",
    "people",
    "man",
    "woman",
    "men",
    "women",
    "hiker",
    "hiking",
    "trail",
    "trekking",
    "trek",
    "walking",
    "walk",
    "runner",
    "running",
    "road",
    "street",
    "highway",
    "car",
    "vehicle",
    "city",
    "urban",
    "building",
    "house",
    "hotel",
    "boat",
    "ship",
    "yacht",
    "pool",
    "swimming",
    "event",
    "festival",
    "concert",
    "party",
    "crowd",
    "airport",
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

    min-height: 100vh;

    background:
        linear-gradient(
            180deg,
            #06151f 0%,
            #0b2633 50%,
            #06151f 100%
        );

    color: white;

    font-family:
        Arial,
        Helvetica,
        sans-serif;

    display: flex;

    align-items: center;

    justify-content: center;

    padding: 20px;
}

.container {

    width: 100%;

    max-width: 500px;

    background:
        rgba(255,255,255,0.07);

    border:
        1px solid
        rgba(255,255,255,0.12);

    border-radius: 22px;

    padding: 28px;

    box-shadow:
        0 20px 60px
        rgba(0,0,0,0.35);
}

h1 {

    text-align: center;

    margin-top: 0;

    margin-bottom: 8px;

    font-size: 30px;
}

.subtitle {

    text-align: center;

    color: #b9cbd2;

    margin-bottom: 28px;
}

label {

    display: block;

    margin-top: 18px;

    margin-bottom: 8px;

    font-weight: bold;
}

select,
button {

    width: 100%;

    border-radius: 12px;

    padding: 15px;

    font-size: 16px;
}

select {

    background: #102f3d;

    color: white;

    border:
        1px solid
        rgba(255,255,255,0.15);
}

button {

    margin-top: 24px;

    border: 0;

    background: white;

    color: #09202b;

    font-weight: bold;

    cursor: pointer;
}

button:hover {

    opacity: 0.9;
}

.info {

    margin-top: 20px;

    padding: 15px;

    border-radius: 12px;

    background:
        rgba(255,255,255,0.05);

    color: #b9cbd2;

    font-size: 14px;

    line-height: 1.6;
}

</style>

</head>

<body>

<div class="container">

<h1>🌎 MUNDO AFORA</h1>

<div class="subtitle">
Paisagens incríveis pelo mundo
</div>

<form method="POST">

<label>Destino</label>

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

📱 Formato: 1080 × 1920<br>
⏱️ Duração: aproximadamente 60 segundos<br>
🎞️ FPS: 24<br>
🔇 Sem música e sem narração<br>
🌎 Apenas paisagens<br>
✨ Marca: mundo.afora0

</div>

</div>

</body>

</html>
"""


# ============================================================
# EXECUTAR COMANDO
# ============================================================

def executar(comando):

    try:

        print("")
        print("[COMANDO]")
        print(" ".join(str(x) for x in comando))
        print("")

        resultado = subprocess.run(
            comando,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        print(
            f"[RETURN CODE] "
            f"{resultado.returncode}"
        )

        if resultado.stdout:

            print("[STDOUT]")
            print(
                resultado.stdout[-3000:]
            )

        if resultado.stderr:

            print("[STDERR]")
            print(
                resultado.stderr[-5000:]
            )

        return resultado

    except Exception as e:

        print(
            "[ERRO SUBPROCESS]"
        )

        print(
            repr(e)
        )

        return None


# ============================================================
# LIMPAR DIRETÓRIO
# ============================================================

def limpar_diretorio(diretorio):

    os.makedirs(
        diretorio,
        exist_ok=True
    )

    for nome in os.listdir(
        diretorio
    ):

        caminho = os.path.join(
            diretorio,
            nome
        )

        try:

            if os.path.isdir(
                caminho
            ):

                shutil.rmtree(
                    caminho
                )

            else:

                os.remove(
                    caminho
                )

        except Exception as e:

            print(
                f"[ERRO LIMPEZA] "
                f"{caminho}: {e}"
            )


# ============================================================
# BUSCAR NO PEXELS
# ============================================================

def buscar_videos(query):

    if not PEXELS_API_KEY:

        print(
            "[ERRO] "
            "PEXELS_API_KEY não configurada."
        )

        return []

    url = (
        "https://api.pexels.com/videos/search"
    )

    headers = {
        "Authorization":
            PEXELS_API_KEY
    }

    params = {

        "query": query,

        "orientation":
            "portrait",

        "size":
            "large",

        "per_page":
            80,
    }

    try:

        resposta = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=30
        )

        resposta.raise_for_status()

        dados = resposta.json()

        videos = dados.get(
            "videos",
            []
        )

        print(
            f"[PEXELS] {query}"
        )

        print(
            f"[PEXELS] "
            f"{len(videos)} resultados"
        )

        return videos

    except Exception as e:

        print(
            f"[ERRO PEXELS] {e}"
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

        largura = arquivo.get(
            "width"
        ) or 0

        altura = arquivo.get(
            "height"
        ) or 0

        if largura <= 0 or altura <= 0:
            continue

        proporcao = (
            altura / largura
        )

        if proporcao < 1.35:
            continue

        tipo = (
            arquivo.get(
                "file_type"
            )
            or ""
        ).lower()

        if "mp4" not in tipo:
            continue

        candidatos.append(
            (
                largura,
                altura,
                link
            )
        )

    if not candidatos:

        return None

    preferencias = [

        (1080, 1920),

        (1440, 2560),

        (720, 1280),

        (2160, 3840),
    ]

    for largura_pref, altura_pref in preferencias:

        for largura, altura, link in candidatos:

            if (
                largura == largura_pref
                and
                altura == altura_pref
            ):

                return {

                    "link": link,

                    "width": largura,

                    "height": altura
                }

    candidatos.sort(
        key=lambda x:
            abs(x[0] - 1080)
            +
            abs(x[1] - 1920)
    )

    largura, altura, link = candidatos[0]

    return {

        "link": link,

        "width": largura,

        "height": altura
    }


# ============================================================
# PONTUAÇÃO
# ============================================================

def pontuar_video(video):

    score = 0

    texto = ""

    texto += str(
        video.get(
            "url",
            ""
        )
    ).lower()

    texto += " "

    texto += str(
        video.get(
            "image",
            ""
        )
    ).lower()

    for palavra in PALAVRAS_RUINS:

        if palavra in texto:

            score -= 20

    largura = video.get(
        "width"
    ) or 0

    altura = video.get(
        "height"
    ) or 0

    if largura and altura:

        proporcao = (
            altura / largura
        )

        if proporcao >= 1.7:

            score += 10

        elif proporcao >= 1.45:

            score += 5

    return score


# ============================================================
# SELECIONAR VÍDEOS
# ============================================================

def selecionar_videos(pais):

    consultas = PAISES.get(
        pais,
        []
    )

    encontrados = {}

    for consulta in consultas:

        resultados = buscar_videos(
            consulta
        )

        for video in resultados:

            video_id = video.get(
                "id"
            )

            if not video_id:
                continue

            if video_id in encontrados:
                continue

            arquivo = escolher_arquivo_video(
                video
            )

            if not arquivo:
                continue

            video[
                "_arquivo_escolhido"
            ] = arquivo

            encontrados[
                video_id
            ] = video

    print("")

    print(
        f"[TOTAL] "
        f"{len(encontrados)} "
        f"vídeos únicos"
    )

    videos = list(
        encontrados.values()
    )

    videos.sort(
        key=pontuar_video,
        reverse=True
    )

    selecionados = videos[:20]

    random.shuffle(
        selecionados
    )

    print(
        f"[SELECIONADOS] "
        f"{len(selecionados)}"
    )

    return selecionados


# ============================================================
# DOWNLOAD
# ============================================================

def baixar_video(video, indice):

    arquivo = video.get(
        "_arquivo_escolhido"
    )

    if not arquivo:

        print(
            "[ERRO] "
            "Arquivo não encontrado."
        )

        return None

    url = arquivo[
        "link"
    ]

    nome = (
        f"{uuid.uuid4().hex}.mp4"
    )

    caminho = os.path.join(
        VIDEO_DIR,
        nome
    )

    print("")

    print(
        f"[DOWNLOAD] {indice} "
        f"{arquivo['width']}x"
        f"{arquivo['height']}"
    )

    try:

        with requests.get(
            url,
            stream=True,
            timeout=(20, 120)
        ) as resposta:

            resposta.raise_for_status()

            with open(
                caminho,
                "wb"
            ) as arquivo_saida:

                for bloco in resposta.iter_content(
                    chunk_size=1024 * 1024
                ):

                    if bloco:

                        arquivo_saida.write(
                            bloco
                        )

        tamanho = (
            os.path.getsize(
                caminho
            )
            / 1024
            / 1024
        )

        print(
            f"[OK DOWNLOAD] "
            f"{tamanho:.1f} MB"
        )

        return caminho

    except Exception as e:

        print(
            f"[ERRO DOWNLOAD] "
            f"{e}"
        )

        try:

            if os.path.exists(
                caminho
            ):

                os.remove(
                    caminho
                )

        except Exception:
            pass

        return None


# ============================================================
# VERIFICAR VÍDEO
# ============================================================

def verificar_video(caminho):

    if not caminho:
        return False

    if not os.path.exists(
        caminho
    ):

        return False

    tamanho = os.path.getsize(
        caminho
    )

    if tamanho < 10000:

        print(
            "[ERRO] "
            "Arquivo muito pequeno."
        )

        return False

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

    resultado = executar(
        comando
    )

    if resultado is None:

        return False

    if resultado.returncode != 0:

        print(
            "[ERRO] "
            "Vídeo inválido."
        )

        return False

    return True


# ============================================================
# PROCESSAR CLIPE + MARCA D'ÁGUA
# ============================================================

def processar_clipe(
    input_path,
    output_path,
    duracao=CLIP_DURATION
):

    # --------------------------------------------------------
    # ESCAPAMOS O TEXTO PARA O FILTRO DO FFMPEG
    # --------------------------------------------------------

    texto = "mundo.afora0"

    texto = (
        texto
        .replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\\'")
        .replace("[", "\\[")
        .replace("]", "\\]")
    )

    # --------------------------------------------------------
    # FILTRO
    # --------------------------------------------------------
    #
    # 1. Ajusta para 1080x1920
    # 2. 24 FPS
    # 3. Coloca marca d'água
    #
    # A marca fica centralizada horizontalmente
    # e em aproximadamente 58% da altura.
    #
    # --------------------------------------------------------

    filtro = (
        "scale=1080:1920,"
        "fps=24,"
        "setsar=1,"
        f"drawtext="
        f"text='{texto}':"
        "fontcolor=white@0.72:"
        "fontsize=38:"
        "x=(w-text_w)/2:"
        "y=h*0.58:"
        "shadowcolor=black@0.35:"
        "shadowx=2:"
        "shadowy=2"
    )

    comando = [

        FFMPEG,

        "-y",

        "-hide_banner",

        "-loglevel",
        "warning",

        "-threads",
        "1",

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
        "ultrafast",

        "-crf",
        "30",

        "-pix_fmt",
        "yuv420p",

        "-r",
        "24",

        "-movflags",
        "+faststart",

        output_path
    ]

    print("")
    print(
        "===================================="
    )

    print(
        "[FFMPEG] Processando clipe"
    )

    print(
        f"Entrada: {input_path}"
    )

    print(
        f"Saída: {output_path}"
    )

    print(
        "[WATERMARK] mundo.afora0"
    )

    print(
        "===================================="
    )

    resultado = executar(
        comando
    )

    if resultado is None:

        return False

    if resultado.returncode != 0:

        print(
            "[ERRO PROCESSANDO CLIPE]"
        )

        return False

    if not os.path.exists(
        output_path
    ):

        print(
            "[ERRO] "
            "Arquivo de saída não existe."
        )

        return False

    tamanho = (
        os.path.getsize(
            output_path
        )
        / 1024
        / 1024
    )

    print(
        f"[OK PROCESSAMENTO] "
        f"{tamanho:.1f} MB"
    )

    return True


# ============================================================
# CONCATENAR
# ============================================================

def criar_lista_concat(
    clipes,
    lista_path
):

    with open(
        lista_path,
        "w",
        encoding="utf-8"
    ) as arquivo:

        for clipe in clipes:

            caminho = os.path.abspath(
                clipe
            )

            caminho = (
                caminho
                .replace("\\", "/")
            )

            caminho = (
                caminho
                .replace(
                    "'",
                    "'\\''"
                )
            )

            arquivo.write(
                f"file '{caminho}'\n"
            )


def juntar_clipes(
    clipes,
    output_path
):

    lista_path = os.path.join(
        TEMP_DIR,
        "lista_concat.txt"
    )

    criar_lista_concat(
        clipes,
        lista_path
    )

    comando = [

        FFMPEG,

        "-y",

        "-hide_banner",

        "-loglevel",
        "warning",

        "-f",
        "concat",

        "-safe",
        "0",

        "-i",
        lista_path,

        "-c",
        "copy",

        output_path
    ]

    print("")
    print(
        "[CONCAT] "
        "Juntando clipes..."
    )

    resultado = executar(
        comando
    )

    try:

        if os.path.exists(
            lista_path
        ):

            os.remove(
                lista_path
            )

    except Exception:
        pass

    if resultado is None:

        return False

    if resultado.returncode != 0:

        print(
            "[ERRO CONCAT]"
        )

        return False

    if not os.path.exists(
        output_path
    ):

        return False

    return True


# ============================================================
# GARANTIR 60 SEGUNDOS
# ============================================================

def limitar_duracao(
    input_path,
    output_path
):

    comando = [

        FFMPEG,

        "-y",

        "-hide_banner",

        "-loglevel",
        "warning",

        "-threads",
        "1",

        "-i",
        input_path,

        "-t",
        str(DURATION),

        "-an",

        "-c:v",
        "libx264",

        "-preset",
        "ultrafast",

        "-crf",
        "30",

        "-pix_fmt",
        "yuv420p",

        "-r",
        "24",

        output_path
    ]

    resultado = executar(
        comando
    )

    if resultado is None:

        return False

    if resultado.returncode != 0:

        return False

    return os.path.exists(
        output_path
    )


# ============================================================
# GERAR VÍDEO
# ============================================================

def gerar_video(pais):

    print("")
    print(
        "===================================="
    )

    print(
        "🌎 MUNDO AFORA"
    )

    print(
        "===================================="
    )

    print(
        f"Destino: {pais}"
    )

    # --------------------------------------------------------
    # LIMPAR
    # --------------------------------------------------------

    limpar_diretorio(
        VIDEO_DIR
    )

    limpar_diretorio(
        TEMP_DIR
    )

    # --------------------------------------------------------
    # BUSCAR
    # --------------------------------------------------------

    videos = selecionar_videos(
        pais
    )

    if not videos:

        raise Exception(
            "Nenhum vídeo encontrado."
        )

    # --------------------------------------------------------
    # PROCESSAR UM POR VEZ
    # --------------------------------------------------------

    clipes = []

    for indice, video in enumerate(
        videos
    ):

        if len(clipes) >= CLIP_COUNT:

            break

        original = None

        numero = len(clipes)

        clip_path = os.path.join(
            TEMP_DIR,
            f"clip_{numero:02d}.mp4"
        )

        try:

            # ----------------------------------------------
            # DOWNLOAD
            # ----------------------------------------------

            original = baixar_video(
                video,
                indice
            )

            if not original:

                print(
                    "[PULAR] "
                    "Falha no download."
                )

                continue

            # ----------------------------------------------
            # VERIFICAR
            # ----------------------------------------------

            if not verificar_video(
                original
            ):

                print(
                    "[PULAR] "
                    "Vídeo inválido."
                )

                continue

            # ----------------------------------------------
            # PROCESSAR
            # ----------------------------------------------

            print("")
            print(
                f"[PROCESSANDO] "
                f"Clipe {numero}"
            )

            sucesso = processar_clipe(
                original,
                clip_path,
                CLIP_DURATION
            )

            if not sucesso:

                print(
                    "[PULAR] "
                    "Falha no processamento."
                )

                continue

            clipes.append(
                clip_path
            )

            print(
                f"[CLIPES OK] "
                f"{len(clipes)}/"
                f"{CLIP_COUNT}"
            )

        except Exception as e:

            print(
                "[ERRO CLIPE]"
            )

            print(
                repr(e)
            )

        finally:

            # ----------------------------------------------
            # APAGA O ORIGINAL
            # ----------------------------------------------

            if original:

                try:

                    if os.path.exists(
                        original
                    ):

                        os.remove(
                            original
                        )

                        print(
                            "[LIMPO] "
                            "Original removido."
                        )

                except Exception as e:

                    print(
                        "[ERRO AO APAGAR]"
                    )

                    print(
                        repr(e)
                    )

    # --------------------------------------------------------
    # VERIFICAR
    # --------------------------------------------------------

    print("")

    print(
        f"[CLIPES FINALIZADOS] "
        f"{len(clipes)}"
    )

    if len(clipes) < 4:

        raise Exception(
            "Não foi possível processar "
            "vídeos suficientes."
        )

    # --------------------------------------------------------
    # JUNTAR
    # --------------------------------------------------------

    base = os.path.join(
        TEMP_DIR,
        f"base_{uuid.uuid4().hex}.mp4"
    )

    sucesso = juntar_clipes(
        clipes,
        base
    )

    if not sucesso:

        raise Exception(
            "Erro ao juntar os clipes."
        )

    # --------------------------------------------------------
    # ARQUIVO FINAL
    # --------------------------------------------------------

    nome_pais = re.sub(
        r"[^a-zA-Z0-9]+",
        "_",
        pais
    )

    nome_final = (
        f"mundo_afora_"
        f"{nome_pais}_"
        f"{uuid.uuid4().hex[:8]}.mp4"
    )

    final_path = os.path.join(
        OUTPUT_DIR,
        nome_final
    )

    # --------------------------------------------------------
    # GARANTIR 60 SEGUNDOS
    # --------------------------------------------------------

    sucesso = limitar_duracao(
        base,
        final_path
    )

    if not sucesso:

        raise Exception(
            "Erro ao finalizar o vídeo."
        )

    # --------------------------------------------------------
    # LIMPAR TEMPORÁRIOS
    # --------------------------------------------------------

    try:

        limpar_diretorio(
            VIDEO_DIR
        )

        limpar_diretorio(
            TEMP_DIR
        )

    except Exception as e:

        print(
            "[ERRO LIMPEZA FINAL]"
        )

        print(
            repr(e)
        )

    if not os.path.exists(
        final_path
    ):

        raise Exception(
            "Vídeo final não foi criado."
        )

    tamanho = (
        os.path.getsize(
            final_path
        )
        / 1024
        / 1024
    )

    print("")
    print(
        "===================================="
    )

    print(
        "🎉 VÍDEO FINALIZADO"
    )

    print(
        f"Arquivo: {final_path}"
    )

    print(
        f"Tamanho: {tamanho:.1f} MB"
    )

    print(
        "===================================="
    )

    return final_path


# ============================================================
# ROTA PRINCIPAL
# ============================================================

@app.route(
    "/",
    methods=["GET", "POST"]
)

def index():

    if request.method == "GET":

        return render_template_string(
            HTML,
            paises=list(
                PAISES.keys()
            )
        )

    pais = request.form.get(
        "pais"
    )

    if not pais:

        return (
            "Selecione um destino.",
            400
        )

    try:

        caminho = gerar_video(
            pais
        )

        return send_file(
            caminho,

            as_attachment=True,

            download_name=os.path.basename(
                caminho
            ),

            mimetype="video/mp4"
        )

    except Exception as e:

        print("")
        print(
            "===================================="
        )

        print(
            "[ERRO GERAL]"
        )

        print(
            repr(e)
        )

        print(
            "===================================="
        )

        return f"""
<!DOCTYPE html>

<html lang="pt-BR">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width,
      initial-scale=1.0">

<style>

body {{

    background: #081820;

    color: white;

    font-family: Arial;

    padding: 30px;
}}

.box {{

    max-width: 600px;

    margin: auto;

    background: #102b36;

    padding: 25px;

    border-radius: 18px;
}}

</style>

</head>

<body>

<div class="box">

<h2>
❌ Não foi possível gerar o vídeo
</h2>

<p>
{str(e)}
</p>

<p>
Volte e tente novamente.
</p>

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
        "status": "ok",
        "app": "Mundo Afora"
    }


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=PORT
    )