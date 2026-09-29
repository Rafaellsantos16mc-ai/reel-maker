import os
import random
import uuid
import requests
import subprocess
import html

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


# ============================================================
# PAÍSES / DESTINOS
# ============================================================

PAISES = {
    "🇧🇷 Brasil": [
        "Brazil landscape",
        "Brazil mountains",
        "Brazil waterfalls",
        "Brazil cliffs",
        "Brazil nature",
        "Brazil scenic",
        "Brazil canyon",
        "Brazil lake",
        "Brazil viewpoint"
    ],

    "🇺🇸 Estados Unidos": [
        "USA landscape",
        "USA mountains",
        "USA waterfalls",
        "USA cliffs",
        "USA canyon",
        "USA nature",
        "USA scenic",
        "USA viewpoint"
    ],

    "🇨🇦 Canadá": [
        "Canada landscape",
        "Canada mountains",
        "Canada waterfalls",
        "Canada cliffs",
        "Canada lake",
        "Canada nature",
        "Canada scenic",
        "Canada viewpoint"
    ],

    "🇲🇽 México": [
        "Mexico landscape",
        "Mexico mountains",
        "Mexico waterfalls",
        "Mexico canyon",
        "Mexico cliffs",
        "Mexico nature",
        "Mexico scenic"
    ],

    "🇦🇷 Argentina": [
        "Argentina landscape",
        "Argentina mountains",
        "Patagonia landscape",
        "Argentina waterfalls",
        "Argentina cliffs",
        "Argentina nature",
        "Argentina scenic"
    ],

    "🇨🇱 Chile": [
        "Chile landscape",
        "Chile mountains",
        "Patagonia Chile",
        "Chile waterfalls",
        "Chile cliffs",
        "Chile nature",
        "Chile scenic"
    ],

    "🇵🇪 Peru": [
        "Peru landscape",
        "Peru mountains",
        "Peru canyon",
        "Peru waterfalls",
        "Peru cliffs",
        "Peru nature",
        "Peru scenic"
    ],

    "🇨🇴 Colômbia": [
        "Colombia landscape",
        "Colombia mountains",
        "Colombia waterfalls",
        "Colombia cliffs",
        "Colombia nature",
        "Colombia scenic"
    ],

    "🇨🇷 Costa Rica": [
        "Costa Rica landscape",
        "Costa Rica waterfalls",
        "Costa Rica mountains",
        "Costa Rica jungle",
        "Costa Rica nature",
        "Costa Rica scenic"
    ],

    "🇮🇸 Islândia": [
        "Iceland landscape",
        "Iceland mountains",
        "Iceland waterfalls",
        "Iceland cliffs",
        "Iceland canyon",
        "Iceland nature",
        "Iceland scenic",
        "Iceland viewpoint"
    ],

    "🇳🇴 Noruega": [
        "Norway landscape",
        "Norway mountains",
        "Norway waterfalls",
        "Norway cliffs",
        "Norway fjord",
        "Norway nature",
        "Norway scenic"
    ],

    "🇨🇭 Suíça": [
        "Switzerland landscape",
        "Swiss Alps",
        "Switzerland mountains",
        "Switzerland waterfall",
        "Switzerland lake mountains",
        "Swiss Alps viewpoint",
        "Switzerland nature",
        "Swiss scenic"
    ],

    "🇫🇷 França": [
        "France landscape",
        "French Alps",
        "France mountains",
        "France waterfalls",
        "France cliffs",
        "France nature",
        "France scenic"
    ],

    "🇮🇹 Itália": [
        "Italy landscape",
        "Italian Alps",
        "Italy mountains",
        "Italy waterfalls",
        "Italy cliffs",
        "Italy lake mountains",
        "Italy nature"
    ],

    "🇵🇹 Portugal": [
        "Portugal landscape",
        "Portugal mountains",
        "Portugal waterfalls",
        "Portugal cliffs",
        "Portugal nature",
        "Portugal scenic"
    ],

    "🇪🇸 Espanha": [
        "Spain landscape",
        "Spain mountains",
        "Spain waterfalls",
        "Spain cliffs",
        "Spain canyon",
        "Spain nature"
    ],

    "🏴 Escócia": [
        "Scotland landscape",
        "Scotland mountains",
        "Scotland waterfalls",
        "Scotland cliffs",
        "Scottish Highlands",
        "Scotland nature",
        "Scotland scenic"
    ],

    "🇮🇪 Irlanda": [
        "Ireland landscape",
        "Ireland cliffs",
        "Ireland waterfalls",
        "Ireland mountains",
        "Ireland nature",
        "Ireland scenic"
    ],

    "🇬🇧 Inglaterra": [
        "England landscape",
        "England mountains",
        "England waterfalls",
        "England cliffs",
        "England nature"
    ],

    "🇩🇪 Alemanha": [
        "Germany landscape",
        "Germany mountains",
        "Germany waterfalls",
        "Germany cliffs",
        "Germany nature",
        "Germany scenic"
    ],

    "🇦🇹 Áustria": [
        "Austria landscape",
        "Austrian Alps",
        "Austria mountains",
        "Austria waterfalls",
        "Austria lake mountains",
        "Austria nature"
    ],

    "🇳🇿 Nova Zelândia": [
        "New Zealand landscape",
        "New Zealand mountains",
        "New Zealand waterfalls",
        "New Zealand cliffs",
        "New Zealand fjord",
        "New Zealand nature",
        "New Zealand scenic"
    ],

    "🇦🇺 Austrália": [
        "Australia landscape",
        "Australia mountains",
        "Australia waterfalls",
        "Australia cliffs",
        "Australia canyon",
        "Australia nature"
    ],

    "🇯🇵 Japão": [
        "Japan landscape",
        "Japan mountains",
        "Japan waterfalls",
        "Japan cliffs",
        "Japan lake mountains",
        "Japan nature",
        "Japan scenic"
    ],

    "🇨🇳 China": [
        "China landscape",
        "China mountains",
        "China waterfalls",
        "China cliffs",
        "China canyon",
        "China nature"
    ],

    "🇰🇷 Coreia do Sul": [
        "South Korea landscape",
        "South Korea mountains",
        "South Korea waterfalls",
        "South Korea cliffs",
        "South Korea nature"
    ],

    "🇮🇩 Indonésia": [
        "Indonesia landscape",
        "Indonesia waterfalls",
        "Indonesia mountains",
        "Indonesia cliffs",
        "Indonesia nature",
        "Indonesia scenic"
    ],

    "🇹🇭 Tailândia": [
        "Thailand landscape",
        "Thailand waterfalls",
        "Thailand mountains",
        "Thailand cliffs",
        "Thailand nature"
    ],

    "🇵🇭 Filipinas": [
        "Philippines landscape",
        "Philippines waterfalls",
        "Philippines cliffs",
        "Philippines mountains",
        "Philippines nature"
    ],

    "🇮🇳 Índia": [
        "India landscape",
        "India mountains",
        "India waterfalls",
        "India cliffs",
        "India nature"
    ],

    "🇳🇵 Nepal": [
        "Nepal landscape",
        "Nepal mountains",
        "Himalayas Nepal",
        "Nepal waterfalls",
        "Nepal nature",
        "Nepal viewpoint"
    ],

    "🇿🇦 África do Sul": [
        "South Africa landscape",
        "South Africa mountains",
        "South Africa waterfalls",
        "South Africa cliffs",
        "South Africa nature"
    ],

    "🇰🇪 Quênia": [
        "Kenya landscape",
        "Kenya mountains",
        "Kenya waterfalls",
        "Kenya cliffs",
        "Kenya nature"
    ],

    "🇲🇦 Marrocos": [
        "Morocco landscape",
        "Morocco mountains",
        "Morocco waterfalls",
        "Morocco canyon",
        "Morocco cliffs",
        "Morocco nature"
    ],

    "🇹🇿 Tanzânia": [
        "Tanzania landscape",
        "Tanzania mountains",
        "Tanzania waterfalls",
        "Tanzania cliffs",
        "Tanzania nature"
    ],

    "🇹🇷 Turquia": [
        "Turkey landscape",
        "Turkey mountains",
        "Turkey waterfalls",
        "Turkey cliffs",
        "Turkey canyon",
        "Turkey nature"
    ],

    "🇬🇷 Grécia": [
        "Greece landscape",
        "Greece mountains",
        "Greece cliffs",
        "Greece waterfalls",
        "Greece nature",
        "Greece scenic"
    ],

    "🇭🇷 Croácia": [
        "Croatia landscape",
        "Croatia waterfalls",
        "Croatia mountains",
        "Croatia cliffs",
        "Croatia nature"
    ],

    "🇸🇮 Eslovênia": [
        "Slovenia landscape",
        "Slovenia mountains",
        "Slovenia waterfalls",
        "Slovenia lake mountains",
        "Slovenia nature"
    ],

    "🇫🇮 Finlândia": [
        "Finland landscape",
        "Finland lakes",
        "Finland forest lake",
        "Finland waterfalls",
        "Finland nature"
    ],

    "🇸🇪 Suécia": [
        "Sweden landscape",
        "Sweden mountains",
        "Sweden waterfalls",
        "Sweden lake",
        "Sweden nature"
    ],

    "🇵🇱 Polônia": [
        "Poland landscape",
        "Poland mountains",
        "Poland waterfalls",
        "Poland cliffs",
        "Poland nature"
    ],

    "🇫🇴 Ilhas Faroé": [
        "Faroe Islands",
        "Faroe Islands landscape",
        "Faroe Islands mountains",
        "Faroe Islands cliffs",
        "Faroe Islands waterfalls",
        "Faroe Islands ocean cliffs",
        "Faroe Islands coastline",
        "Faroe Islands fjord",
        "Faroe Islands valley",
        "Faroe Islands nature",
        "Faroe Islands scenic",
        "Faroe Islands viewpoint",
        "Faroe Islands dramatic landscape",
        "Faroe Islands green mountains",
        "Faroe Islands waterfall mountain",
        "Faroe Islands sea cliffs",
        "Faroe Islands hiking",
        "Faroe Islands remote landscape",
        "Faroe Islands aerial landscape"
    ]
}


# ============================================================
# PALAVRAS PARA FILTRAR OS VÍDEOS
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
    "beautiful nature",
    "faroe",
    "faroe islands",
    "fjord",
    "green mountains",
    "sea cliffs"
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
# INTERFACE
# ============================================================

HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>Cliff & Nature Reel</title>

<style>

body {
    margin: 0;
    padding: 0;
    background: #101010;
    color: white;
    font-family: Arial, sans-serif;
}

.container {
    max-width: 600px;
    margin: auto;
    padding: 25px;
}

h1 {
    text-align: center;
    margin-bottom: 8px;
}

.subtitle {
    text-align: center;
    color: #aaa;
    margin-bottom: 30px;
}

label {
    display: block;
    margin-top: 18px;
    margin-bottom: 8px;
}

select,
button {
    width: 100%;
    padding: 15px;
    border-radius: 10px;
    border: none;
    font-size: 16px;
    box-sizing: border-box;
}

select {
    background: #222;
    color: white;
}

button {
    margin-top: 25px;
    background: #ffffff;
    color: #000;
    font-weight: bold;
    cursor: pointer;
}

button:hover {
    opacity: 0.85;
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

<h1>🌎 Cliff & Nature Reel</h1>

<div class="subtitle">
Vídeos verticais de paisagens naturais
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
🎬 Criar vídeo
</button>

</form>

<div class="info">

<b>Configurações:</b><br><br>

📱 1080 × 1920<br>
🎞️ 24 FPS<br>
⏱️ Aproximadamente 60 segundos<br>
🔇 Sem áudio<br>
📝 Sem texto<br>
🎥 Vídeos reais do Pexels<br>
🔍 Zoom suave

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

def escolher_arquivo(video):

    arquivos = video.get("video_files", [])

    candidatos = []

    for arquivo in arquivos:

        link = arquivo.get("link")

        largura = arquivo.get("width") or 0
        altura = arquivo.get("height") or 0

        if not link:
            continue

        if largura <= 0 or altura <= 0:
            continue

        if not link.lower().endswith(".mp4"):
            continue

        proporcao = altura / largura

        # Precisa ser vertical
        if proporcao < 1.35:
            continue

        area = largura * altura

        candidatos.append({
            "link": link,
            "width": largura,
            "height": altura,
            "area": area
        })

    if not candidatos:
        return None

    # Prioriza vídeos grandes
    candidatos.sort(
        key=lambda x: x["area"],
        reverse=True
    )

    # Evita arquivos absurdamente grandes
    adequados = [
        x for x in candidatos
        if x["width"] <= 2160
        and x["height"] <= 3840
    ]

    if adequados:
        return adequados[0]

    return candidatos[0]


# ============================================================
# PONTUAÇÃO DO VÍDEO
# ============================================================

def pontuar_video(video):

    texto = ""

    texto += str(video.get("url", ""))
    texto += " "
    texto += str(video.get("user", {}).get("name", ""))

    texto = texto.lower()

    score = 0

    for palavra in PALAVRAS_BOAS:

        if palavra.lower() in texto:
            score += 5

    for palavra in PALAVRAS_RUINS:

        if palavra.lower() in texto:
            score -= 10

    return score


# ============================================================
# SELECIONAR MELHORES
# ============================================================

def selecionar_melhores_videos(videos, quantidade=12):

    unicos = {}

    for video in videos:

        video_id = video.get("id")

        if not video_id:
            continue

        if video_id in unicos:
            continue

        duracao = video.get("duration", 0)

        if duracao < 5:
            continue

        arquivo = escolher_arquivo(video)

        if not arquivo:
            continue

        video["_arquivo_escolhido"] = arquivo
        video["_score"] = pontuar_video(video)

        unicos[video_id] = video

    lista = list(unicos.values())

    lista.sort(
        key=lambda x: x.get("_score", 0),
        reverse=True
    )

    # Pegamos uma quantidade maior para variar
    lista = lista[:30]

    random.shuffle(lista)

    return lista[:quantidade]


# ============================================================
# BAIXAR UM VÍDEO
# ============================================================

def baixar_video(video):

    arquivo = video["_arquivo_escolhido"]

    url = arquivo["link"]

    nome = f"{uuid.uuid4().hex}.mp4"

    caminho = os.path.join(
        VIDEO_DIR,
        nome
    )

    resposta = requests.get(
        url,
        stream=True,
        timeout=60
    )

    resposta.raise_for_status()

    with open(caminho, "wb") as f:

        for bloco in resposta.iter_content(
            chunk_size=1024 * 1024
        ):

            if bloco:
                f.write(bloco)

    return caminho


# ============================================================
# DOWNLOAD PARALELO
# ============================================================

def baixar_videos_paralelo(videos):

    resultados = []

    with ThreadPoolExecutor(
        max_workers=3
    ) as executor:

        tarefas = [
            executor.submit(
                baixar_video,
                video
            )
            for video in videos
        ]

        for tarefa in as_completed(tarefas):

            try:

                caminho = tarefa.result()

                resultados.append(caminho)

            except Exception as e:

                print(
                    "Erro ao baixar vídeo:",
                    e
                )

    return resultados


# ============================================================
# PROCESSAR CLIPE
# ============================================================

def processar_clipe_zoom(
    input_path,
    output_path,
    duracao,
    zoom_final=1.12
):

    """
    Processamento estável para Railway.

    NÃO usa zoompan.

    O vídeo é convertido para vertical
    1080x1920 e recebe um zoom suave
    através de crop + scale.
    """

    duracao = max(
        1.0,
        float(duracao)
    )

    velocidade_zoom = (
        zoom_final - 1.0
    ) / duracao

    # Mantemos uma área maior para permitir
    # o movimento de zoom.
    #
    # A expressão usa o tempo do vídeo (t).
    #
    # O tamanho do crop vai diminuindo
    # gradualmente, criando o efeito de aproximação.

    largura_crop = (
        f"2160/(1+{velocidade_zoom:.6f}*t)"
    )

    altura_crop = (
        f"3840/(1+{velocidade_zoom:.6f}*t)"
    )

    x_crop = (
        f"(iw-2160/(1+{velocidade_zoom:.6f}*t))/2"
    )

    y_crop = (
        f"(ih-3840/(1+{velocidade_zoom:.6f}*t))/2"
    )

    filtro = (
        "scale=2160:3840:force_original_aspect_ratio=increase,"
        "crop=2160:3840,"
        f"crop={largura_crop}:{altura_crop}:{x_crop}:{y_crop},"
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

    print("\n==============================")
    print("PROCESSANDO CLIPE")
    print("==============================")
    print("Entrada:", input_path)
    print("Saída:", output_path)
    print("Duração:", duracao)
    print("Zoom final:", zoom_final)
    print("==============================\n")

    resultado = subprocess.run(
        comando,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if resultado.returncode != 0:

        print(
            "ERRO COMPLETO DO FFMPEG:"
        )

        print(
            resultado.stderr
        )

        raise RuntimeError(
            "Erro real do FFmpeg ao processar o clipe:\n\n"
            + resultado.stderr[-6000:]
        )

    return output_path


# ============================================================
# JUNTAR CLIPES
# ============================================================

def juntar_clipes(
    clipes,
    output_path
):

    lista_path = os.path.join(
        TEMP_DIR,
        f"concat_{uuid.uuid4().hex}.txt"
    )

    with open(
        lista_path,
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
        lista_path,

        "-c",
        "copy",

        "-an",

        "-movflags",
        "+faststart",

        output_path
    ]

    print("\n==============================")
    print("JUNTANDO CLIPES")
    print("==============================\n")

    resultado = subprocess.run(
        comando,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    try:
        os.remove(lista_path)
    except Exception:
        pass

    if resultado.returncode != 0:

        print(
            "ERRO AO JUNTAR:"
        )

        print(
            resultado.stderr
        )

        raise RuntimeError(
            "Erro ao juntar os clipes:\n\n"
            + resultado.stderr[-6000:]
        )

    return output_path


# ============================================================
# CRIAR REEL
# ============================================================

def criar_reel(
    videos,
    output_path
):

    clipes_processados = []

    tempo_restante = DURATION

    try:

        for index, video_path in enumerate(
            videos
        ):

            if tempo_restante <= 0:
                break

            # Cada cena fica entre 7 e 11 segundos.
            duracao_clipe = random.uniform(
                7.0,
                11.0
            )

            duracao_clipe = min(
                duracao_clipe,
                tempo_restante
            )

            nome_clipe = (
                f"{uuid.uuid4().hex}.mp4"
            )

            caminho_clipe = os.path.join(
                TEMP_DIR,
                nome_clipe
            )

            zoom = random.uniform(
                1.08,
                1.14
            )

            processar_clipe_zoom(
                video_path,
                caminho_clipe,
                duracao_clipe,
                zoom_final=zoom
            )

            clipes_processados.append(
                caminho_clipe
            )

            tempo_restante -= (
                duracao_clipe
            )

            print(
                f"Clipe {index + 1} concluído"
            )

            print(
                "Tempo restante:",
                round(
                    tempo_restante,
                    2
                )
            )

        if not clipes_processados:

            raise RuntimeError(
                "Nenhum clipe foi processado."
            )

        juntar_clipes(
            clipes_processados,
            output_path
        )

    finally:

        # Remove vídeos originais
        for caminho in videos:

            try:
                os.remove(caminho)
            except Exception:
                pass

        # Remove clipes temporários
        for caminho in clipes_processados:

            try:
                os.remove(caminho)
            except Exception:
                pass

    return output_path


# ============================================================
# GERAR VÍDEO
# ============================================================

def gerar_video(pais):

    if pais not in PAISES:

        raise ValueError(
            "Destino inválido."
        )

    consultas = PAISES[pais]

    todos_videos = []

    print("\n==============================")
    print("BUSCANDO VÍDEOS")
    print("==============================")

    # Limita a quantidade de consultas
    # para não exagerar na API.

    for query in consultas[:10]:

        try:

            print(
                "Pesquisa:",
                query
            )

            encontrados = buscar_videos(
                query
            )

            todos_videos.extend(
                encontrados
            )

            print(
                "Encontrados:",
                len(encontrados)
            )

            if len(todos_videos) >= 150:

                break

        except Exception as e:

            print(
                "Erro na pesquisa:",
                query,
                e
            )

    if not todos_videos:

        raise RuntimeError(
            "Nenhum vídeo encontrado no Pexels."
        )

    print(
        "Total encontrado:",
        len(todos_videos)
    )

    videos_selecionados = (
        selecionar_melhores_videos(
            todos_videos,
            quantidade=12
        )
    )

    if not videos_selecionados:

        raise RuntimeError(
            "Nenhum vídeo vertical adequado foi encontrado."
        )

    print(
        "Vídeos selecionados:",
        len(videos_selecionados)
    )

    # ========================================================
    # DOWNLOAD
    # ========================================================

    videos_baixados = (
        baixar_videos_paralelo(
            videos_selecionados
        )
    )

    if not videos_baixados:

        raise RuntimeError(
            "Não foi possível baixar os vídeos."
        )

    print(
        "Downloads concluídos:",
        len(videos_baixados)
    )

    # ========================================================
    # OUTPUT
    # ========================================================

    nome_saida = (
        "cliff_reel_"
        + uuid.uuid4().hex
        + ".mp4"
    )

    output_path = os.path.join(
        OUTPUT_DIR,
        nome_saida
    )

    # ========================================================
    # PROCESSAMENTO
    # ========================================================

    criar_reel(
        videos_baixados,
        output_path
    )

    return output_path


# ============================================================
# HOME
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
                download_name="cliff_nature_reel.mp4",
                mimetype="video/mp4"
            )

        except Exception as e:

            print(
                "\nERRO FINAL:"
            )

            print(
                str(e)
            )

            return f"""
            <html>
            <body style="
                background:#111;
                color:white;
                font-family:Arial;
                padding:30px;
            ">

            <h2>❌ Erro ao criar vídeo</h2>

            <pre style="
                white-space:pre-wrap;
                background:#222;
                padding:20px;
                border-radius:10px;
            ">{html.escape(str(e))}</pre>

            <br>

            <a href="/"
               style="
               color:white;
               background:#333;
               padding:12px 20px;
               border-radius:8px;
               text-decoration:none;
               ">

               ← Voltar

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
        "status": "online",
        "app": "Cliff & Nature Reel",
        "type": "nature_vertical_video",
        "duration": DURATION,
        "resolution": f"{WIDTH}x{HEIGHT}",
        "fps": FPS,
        "zoom": True,
        "audio": False,
        "text": False
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