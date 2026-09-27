import os
import random
import uuid
import requests

from flask import Flask, request, render_template_string, send_file
from moviepy import ImageClip, CompositeVideoClip, concatenate_videoclips, vfx
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)

# ============================================================
# CONFIGURAÇÕES
# ============================================================

WIDTH = 1080
HEIGHT = 1920
FPS = 30
DURACAO = 60

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

VIDEOS_DIR = "videos"
IMAGES_DIR = "imagens"
LEGENDAS_DIR = "legendas"

os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(LEGENDAS_DIR, exist_ok=True)

# ============================================================
# PAÍSES
# ============================================================

PAISES = [
    "Brasil",
    "Suíça",
    "Noruega",
    "Islândia",
    "Itália",
    "França",
    "Portugal",
    "Espanha",
    "Grécia",
    "Alemanha",
    "Áustria",
    "Holanda",
    "Inglaterra",
    "Escócia",
    "Irlanda",
    "Dinamarca",
    "Suécia",
    "Finlândia",
    "Croácia",
    "Eslovênia",
    "Turquia",
    "Japão",
    "Coreia do Sul",
    "China",
    "Tailândia",
    "Indonésia",
    "Maldivas",
    "Filipinas",
    "Vietnã",
    "Austrália",
    "Nova Zelândia",
    "Canadá",
    "Estados Unidos",
    "México",
    "Argentina",
    "Chile",
    "Peru",
    "Colômbia",
    "África do Sul",
    "Marrocos",
    "Egito",
    "Emirados Árabes Unidos",
    "Jordânia"
]

# ============================================================
# NOMES EM INGLÊS
# Ajuda o Pexels a encontrar mais imagens
# ============================================================

PAISES_INGLES = {
    "Brasil": "Brazil",
    "Suíça": "Switzerland",
    "Noruega": "Norway",
    "Islândia": "Iceland",
    "Itália": "Italy",
    "França": "France",
    "Portugal": "Portugal",
    "Espanha": "Spain",
    "Grécia": "Greece",
    "Alemanha": "Germany",
    "Áustria": "Austria",
    "Holanda": "Netherlands",
    "Inglaterra": "England",
    "Escócia": "Scotland",
    "Irlanda": "Ireland",
    "Dinamarca": "Denmark",
    "Suécia": "Sweden",
    "Finlândia": "Finland",
    "Croácia": "Croatia",
    "Eslovênia": "Slovenia",
    "Turquia": "Turkey",
    "Japão": "Japan",
    "Coreia do Sul": "South Korea",
    "China": "China",
    "Tailândia": "Thailand",
    "Indonésia": "Indonesia",
    "Maldivas": "Maldives",
    "Filipinas": "Philippines",
    "Vietnã": "Vietnam",
    "Austrália": "Australia",
    "Nova Zelândia": "New Zealand",
    "Canadá": "Canada",
    "Estados Unidos": "United States",
    "México": "Mexico",
    "Argentina": "Argentina",
    "Chile": "Chile",
    "Peru": "Peru",
    "Colômbia": "Colombia",
    "África do Sul": "South Africa",
    "Marrocos": "Morocco",
    "Egito": "Egypt",
    "Emirados Árabes Unidos": "United Arab Emirates",
    "Jordânia": "Jordan"
}

# ============================================================
# BUSCAR IMAGENS DO PAÍS
# ============================================================

def buscar_imagens_pexels(pais, quantidade=15):

    if not PEXELS_API_KEY:
        raise Exception(
            "PEXELS_API_KEY não configurada no Railway."
        )

    pais_ingles = PAISES_INGLES.get(
        pais,
        pais
    )

    url = "https://api.pexels.com/v1/search"

    headers = {
        "Authorization": PEXELS_API_KEY
    }

    # --------------------------------------------------------
    # BUSCAS ESPECÍFICAS
    # --------------------------------------------------------

    buscas = [
        f"{pais_ingles} landscape",
        f"{pais_ingles} nature",
        f"{pais_ingles} beautiful places",
        f"{pais_ingles} mountains",
        f"{pais_ingles} tourism",
        f"{pais_ingles} travel",
        f"{pais_ingles} scenic",
        f"{pais_ingles} beautiful landscape"
    ]

    fotos = []
    ids = set()

    for busca in buscas:

        if len(fotos) >= quantidade:
            break

        try:

            params = {
                "query": busca,
                "orientation": "portrait",
                "size": "large",
                "per_page": 40
            }

            resposta = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=30
            )

            if resposta.status_code != 200:
                continue

            dados = resposta.json()

            for foto in dados.get("photos", []):

                foto_id = foto.get("id")

                if not foto_id:
                    continue

                if foto_id in ids:
                    continue

                src = foto.get("src", {})

                imagem_url = (
                    src.get("large2x")
                    or src.get("large")
                    or src.get("original")
                )

                if not imagem_url:
                    continue

                ids.add(foto_id)

                fotos.append({
                    "id": foto_id,
                    "url": imagem_url,
                    "pais": pais,
                    "query": busca
                })

                if len(fotos) >= quantidade:
                    break

        except Exception:
            continue

    # --------------------------------------------------------
    # NÃO USAR IMAGEM GENÉRICA
    # --------------------------------------------------------

    if not fotos:

        raise Exception(
            f"Não foram encontradas imagens suficientes "
            f"para {pais}."
        )

    return fotos

# ============================================================
# DOWNLOAD
# ============================================================

def baixar_imagem(url, caminho):

    resposta = requests.get(
        url,
        timeout=40
    )

    resposta.raise_for_status()

    with open(caminho, "wb") as arquivo:
        arquivo.write(resposta.content)

    return caminho

# ============================================================
# PREPARAR IMAGEM
# ============================================================

def preparar_imagem(caminho):

    imagem = Image.open(caminho).convert("RGB")

    proporcao_destino = WIDTH / HEIGHT

    largura, altura = imagem.size

    proporcao_atual = largura / altura

    if proporcao_atual > proporcao_destino:

        nova_largura = int(
            altura * proporcao_destino
        )

        esquerda = (
            largura - nova_largura
        ) // 2

        imagem = imagem.crop(
            (
                esquerda,
                0,
                esquerda + nova_largura,
                altura
            )
        )

    else:

        nova_altura = int(
            largura / proporcao_destino
        )

        topo = (
            altura - nova_altura
        ) // 2

        imagem = imagem.crop(
            (
                0,
                topo,
                largura,
                topo + nova_altura
            )
        )

    imagem = imagem.resize(
        (WIDTH, HEIGHT),
        Image.Resampling.LANCZOS
    )

    imagem.save(
        caminho,
        quality=95
    )

    return caminho

# ============================================================
# FONTE
# ============================================================

def encontrar_fonte(tamanho=60):

    caminhos = [

        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",

        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",

        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"
    ]

    for caminho in caminhos:

        if os.path.exists(caminho):

            return ImageFont.truetype(
                caminho,
                tamanho
            )

    return ImageFont.load_default()

# ============================================================
# LEGENDA
# ============================================================

def criar_legenda(pais):

    caminho = os.path.join(
        LEGENDAS_DIR,
        f"legenda_{uuid.uuid4().hex}.png"
    )

    imagem = Image.new(
        "RGBA",
        (WIDTH, 240),
        (0, 0, 0, 0)
    )

    desenho = ImageDraw.Draw(imagem)

    fonte = encontrar_fonte(58)

    texto = pais

    caixa = desenho.textbbox(
        (0, 0),
        texto,
        font=fonte
    )

    largura_texto = (
        caixa[2] - caixa[0]
    )

    altura_texto = (
        caixa[3] - caixa[1]
    )

    x = (
        WIDTH - largura_texto
    ) // 2

    y = 65

    # Fundo transparente escuro
    desenho.rounded_rectangle(
        (
            x - 35,
            y - 20,
            x + largura_texto + 35,
            y + altura_texto + 25
        ),
        radius=25,
        fill=(0, 0, 0, 180)
    )

    desenho.text(
        (x, y),
        texto,
        font=fonte,
        fill=(255, 255, 255, 255)
    )

    imagem.save(caminho)

    return caminho

# ============================================================
# CLIP COM ZOOM
# ============================================================

def criar_clip_com_zoom(
    caminho,
    duracao
):

    clip = ImageClip(caminho)

    clip = clip.with_duration(
        duracao
    )

    clip = clip.resized(
        lambda t:
        1.0 + (
            0.05 *
            (t / duracao)
        )
    )

    clip = clip.with_position(
        "center"
    )

    return clip

# ============================================================
# CRIAR VÍDEO
# ============================================================

def criar_video(
    imagens,
    pais
):

    if not imagens:

        raise Exception(
            "Nenhuma imagem disponível."
        )

    nome_video = (
        f"paisagem_"
        f"{uuid.uuid4().hex}.mp4"
    )

    caminho_video = os.path.join(
        VIDEOS_DIR,
        nome_video
    )

    quantidade = len(imagens)

    duracao_por_imagem = (
        DURACAO / quantidade
    )

    clips = []

    # --------------------------------------------------------
    # IMAGENS
    # --------------------------------------------------------

    for indice, caminho in enumerate(imagens):

        clip = criar_clip_com_zoom(
            caminho,
            duracao_por_imagem
        )

        if indice > 0:

            clip = clip.with_effects([
                vfx.CrossFadeIn(0.7)
            ])

        clips.append(clip)

    # --------------------------------------------------------
    # VÍDEO
    # --------------------------------------------------------

    video = CompositeVideoClip(
        clips,
        size=(WIDTH, HEIGHT)
    )

    video = video.with_duration(
        DURACAO
    )

    # --------------------------------------------------------
    # NOME DO PAÍS
    # --------------------------------------------------------

    caminho_legenda = criar_legenda(
        pais
    )

    legenda = ImageClip(
        caminho_legenda
    )

    legenda = legenda.with_duration(
        DURACAO
    )

    legenda = legenda.with_position(
        ("center", HEIGHT - 420)
    )

    video_final = CompositeVideoClip(
        [
            video,
            legenda
        ],
        size=(WIDTH, HEIGHT)
    )

    # --------------------------------------------------------
    # SEM ÁUDIO
    # --------------------------------------------------------

    video_final = (
        video_final.without_audio()
    )

    # --------------------------------------------------------
    # EXPORTAR
    # --------------------------------------------------------

    video_final.write_videofile(
        caminho_video,
        fps=FPS,
        codec="libx264",
        audio=False,
        preset="faster",
        bitrate="8M",
        threads=2,
        logger=None
    )

    # Liberar memória

    try:
        video.close()
        video_final.close()

        for clip in clips:
            clip.close()

    except Exception:
        pass

    return nome_video

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

<title>World Landscapes</title>

<style>

body {

    background: #101010;

    color: white;

    font-family: Arial, sans-serif;

    padding: 20px;

}

.container {

    max-width: 600px;

    margin: auto;

}

h1 {

    text-align: center;

    font-size: 28px;

}

.subtitulo {

    text-align: center;

    color: #bbb;

    margin-bottom: 25px;

}

label {

    display: block;

    margin-top: 18px;

    margin-bottom: 7px;

    font-weight: bold;

}

select,
button {

    width: 100%;

    padding: 16px;

    font-size: 17px;

    border-radius: 10px;

    border: none;

    box-sizing: border-box;

}

select {

    background: #222;

    color: white;

}

button {

    margin-top: 25px;

    background: #1687ff;

    color: white;

    font-weight: bold;

    cursor: pointer;

}

button:hover {

    opacity: 0.9;

}

.status {

    margin-top: 20px;

    padding: 15px;

    background: #222;

    border-radius: 10px;

    line-height: 1.5;

}

.download {

    display: block;

    margin-top: 20px;

    padding: 16px;

    background: #18a558;

    color: white;

    text-align: center;

    text-decoration: none;

    border-radius: 10px;

    font-weight: bold;

}

.info {

    margin-top: 20px;

    background: #1d1d1d;

    padding: 18px;

    border-radius: 10px;

    line-height: 1.6;

}

.duracao {

    margin-top: 15px;

    background: #181818;

    padding: 15px;

    border-radius: 10px;

    text-align: center;

}

</style>

</head>

<body>

<div class="container">

<h1>🌎 WORLD LANDSCAPES</h1>

<div class="subtitulo">

Paisagens incríveis do mundo

</div>

<div class="info">

Escolha um país e o sistema irá buscar imagens de paisagens,
natureza, lugares turísticos e cenários relacionados
exclusivamente ao país escolhido.

<br><br>

<strong>Vídeo:</strong> 60 segundos<br>

<strong>Formato:</strong> 1080 × 1920<br>

<strong>Áudio:</strong> sem música e sem narração

</div>

<form method="POST">

<label>

🌍 Escolha o país

</label>

<select name="pais" required>

{% for pais in paises %}

<option value="{{ pais }}">

{{ pais }}

</option>

{% endfor %}

</select>

<div class="duracao">

🎬 Duração fixa: <strong>60 segundos</strong>

</div>

<button type="submit">

CRIAR VÍDEO DE 60 SEGUNDOS

</button>

</form>

{% if mensagem %}

<div class="status">

{{ mensagem }}

</div>

{% endif %}

{% if download %}

<a
href="{{ download }}"
class="download">

⬇️ BAIXAR VÍDEO

</a>

{% endif %}

</div>

</body>

</html>

"""

# ============================================================
# ROTA PRINCIPAL
# ============================================================

@app.route(
    "/",
    methods=["GET", "POST"]
)

def index():

    mensagem = ""

    download = None

    if request.method == "POST":

        try:

            pais = request.form.get(
                "pais",
                ""
            ).strip()

            if not pais:

                raise Exception(
                    "Escolha um país."
                )

            mensagem = (
                f"🌎 Buscando paisagens "
                f"de {pais}..."
            )

            # ------------------------------------------------
            # BUSCAR IMAGENS
            # ------------------------------------------------

            resultados = (
                buscar_imagens_pexels(
                    pais,
                    quantidade=15
                )
            )

            # Embaralhar para variar
            random.shuffle(
                resultados
            )

            imagens = []

            # ------------------------------------------------
            # BAIXAR
            # ------------------------------------------------

            for indice, item in enumerate(
                resultados
            ):

                nome = (
                    f"{uuid.uuid4().hex}_"
                    f"{indice}.jpg"
                )

                caminho = os.path.join(
                    IMAGES_DIR,
                    nome
                )

                try:

                    baixar_imagem(
                        item["url"],
                        caminho
                    )

                    preparar_imagem(
                        caminho
                    )

                    imagens.append(
                        caminho
                    )

                except Exception:

                    continue

            # ------------------------------------------------
            # VERIFICAR
            # ------------------------------------------------

            if not imagens:

                raise Exception(
                    f"Não foi possível baixar "
                    f"imagens de {pais}."
                )

            # ------------------------------------------------
            # CRIAR VÍDEO
            # ------------------------------------------------

            mensagem = (
                f"🎬 Criando vídeo de 60 segundos "
                f"com paisagens de {pais}..."
            )

            nome_video = criar_video(
                imagens,
                pais
            )

            mensagem = (
                f"✅ Vídeo criado com sucesso! "
                f"Pais: {pais}"
            )

            download = (
                f"/download/{nome_video}"
            )

        except Exception as erro:

            mensagem = (
                "❌ Erro ao criar o vídeo: "
                + str(erro)
            )

    return render_template_string(
        HTML,
        paises=PAISES,
        mensagem=mensagem,
        download=download
    )

# ============================================================
# DOWNLOAD
# ============================================================

@app.route(
    "/download/<nome>"
)

def download_video(nome):

    caminho = os.path.join(
        VIDEOS_DIR,
        nome
    )

    if not os.path.exists(caminho):

        return (
            "Vídeo não encontrado.",
            404
        )

    return send_file(
        caminho,
        as_attachment=True
    )

# ============================================================
# RAILWAY
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            "8080"
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )