import os
import random
import requests

from flask import Flask, request, render_template_string, send_file
from gtts import gTTS
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips

app = Flask(__name__)

# =========================
# CONFIGURAÇÕES
# =========================

WIDTH = 540
HEIGHT = 960
FPS = 15

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

VIDEOS_DIR = "videos"
IMAGES_DIR = "imagens"
AUDIO_DIR = "audios"

os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)


# =========================
# ROTEIROS
# =========================

def criar_roteiro(tema, estilo):

    if estilo == "Motivacional":
        return [
            f"Hoje vamos falar sobre {tema}.",
            f"Quando o assunto é {tema}, muita gente acaba desistindo cedo demais.",
            "Mas os resultados aparecem quando você mantém a constância.",
            "Continue avançando um passo de cada vez."
        ]

    if estilo == "Dinheiro":
        return [
            f"Hoje vamos falar sobre {tema}.",
            "Antes de buscar resultados, é importante entender como as coisas funcionam.",
            "Conhecimento e planejamento podem ajudar nas suas decisões.",
            "Aprenda, pratique e evolua todos os dias."
        ]

    if estilo == "Curiosidades":
        return [
            f"Você conhece essas curiosidades sobre {tema}?",
            "Existem informações muito interessantes que poucas pessoas conhecem.",
            f"Quando pesquisamos mais sobre {tema}, encontramos detalhes surpreendentes.",
            "Agora você já conhece mais uma curiosidade."
        ]

    if estilo == "Futebol":
        return [
            f"Hoje vamos falar sobre {tema}.",
            "O futebol é cheio de histórias e momentos marcantes.",
            f"Quando pesquisamos sobre {tema}, encontramos fatos muito interessantes.",
            "Você já conhecia essa história?"
        ]

    if estilo == "História":
        return [
            f"Hoje vamos conhecer um pouco da história de {tema}.",
            "O passado guarda acontecimentos que ajudam a entender o presente.",
            f"A história de {tema} possui momentos muito interessantes.",
            "Essa é mais uma história que merece ser conhecida."
        ]

    return [
        f"Hoje vamos falar sobre {tema}.",
        f"Existem muitas informações interessantes sobre {tema}.",
        "Continue acompanhando para descobrir mais.",
        "Até o próximo vídeo."
    ]


# =========================
# BUSCAR IMAGENS
# =========================

def buscar_imagens(tema):

    if not PEXELS_API_KEY:
        raise Exception("PEXELS_API_KEY não encontrada.")

    url = "https://api.pexels.com/v1/search"

    headers = {
        "Authorization": PEXELS_API_KEY
    }

    params = {
        "query": tema,
        "per_page": 4,
        "orientation": "portrait"
    }

    resposta = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=30
    )

    if resposta.status_code != 200:
        raise Exception(
            f"Erro Pexels: {resposta.status_code}"
        )

    dados = resposta.json()

    fotos = dados.get("photos", [])

    if not fotos:
        raise Exception("Nenhuma imagem encontrada.")

    links = []

    for foto in fotos:

        src = foto.get("src", {})

        link = (
            src.get("large")
            or src.get("medium")
            or src.get("original")
        )

        if link:
            links.append(link)

    if not links:
        raise Exception("Nenhuma imagem disponível.")

    return links[:4]


# =========================
# PREPARAR IMAGEM
# =========================

def preparar_imagem(url, numero):

    caminho = os.path.join(
        IMAGES_DIR,
        f"imagem_{numero}.jpg"
    )

    resposta = requests.get(
        url,
        timeout=30
    )

    if resposta.status_code != 200:
        raise Exception("Erro ao baixar imagem.")

    with open(caminho, "wb") as arquivo:
        arquivo.write(resposta.content)

    from PIL import Image

    imagem = Image.open(caminho).convert("RGB")

    # Tamanho vertical 9:16
    imagem.thumbnail(
        (WIDTH, HEIGHT),
        Image.Resampling.LANCZOS
    )

    fundo = Image.new(
        "RGB",
        (WIDTH, HEIGHT),
        "black"
    )

    x = (WIDTH - imagem.width) // 2
    y = (HEIGHT - imagem.height) // 2

    fundo.paste(
        imagem,
        (x, y)
    )

    fundo.save(
        caminho,
        "JPEG",
        quality=85
    )

    return caminho


# =========================
# GERAR VOZ
# =========================

def gerar_narracao(roteiro):

    texto = " ".join(roteiro)

    caminho = os.path.join(
        AUDIO_DIR,
        "narracao.mp3"
    )

    print("Gerando narração...")

    voz = gTTS(
        text=texto,
        lang="pt-br",
        slow=False
    )

    voz.save(caminho)

    if not os.path.exists(caminho):
        raise Exception("A narração não foi criada.")

    return caminho


# =========================
# CRIAR VÍDEO
# =========================

def criar_video(tema, estilo, duracao):

    print("Criando roteiro...")

    roteiro = criar_roteiro(
        tema,
        estilo
    )

    print("Buscando imagens...")

    imagens = buscar_imagens(
        tema
    )

    print("Gerando narração...")

    caminho_audio = gerar_narracao(
        roteiro
    )

    audio = AudioFileClip(
        caminho_audio
    )

    duracao_audio = float(
        audio.duration
    )

    # O vídeo acompanha a narração.
    duracao_video = max(
        float(duracao),
        duracao_audio
    )

    # Limite de segurança
    if duracao_video > duracao + 5:
        duracao_video = float(duracao + 5)

    tempo_por_imagem = (
        duracao_video / len(imagens)
    )

    clips = []

    for i, url in enumerate(imagens):

        print(
            f"Preparando imagem {i + 1}..."
        )

        caminho = preparar_imagem(
            url,
            i
        )

        clip = ImageClip(
            caminho
        ).with_duration(
            tempo_por_imagem
        )

        clips.append(clip)

    print("Montando vídeo...")

    video = concatenate_videoclips(
        clips,
        method="compose"
    )

    # Ajustar o áudio ao vídeo
    if audio.duration > video.duration:

        audio = audio.subclipped(
            0,
            video.duration
        )

    # SOMENTE NARRAÇÃO
    video = video.with_audio(
        audio
    )

    nome = (
        "reel_"
        + str(random.randint(10000, 99999))
        + ".mp4"
    )

    caminho_final = os.path.join(
        VIDEOS_DIR,
        nome
    )

    print("Renderizando MP4...")

    video.write_videofile(
        caminho_final,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        threads=1,
        logger=None
    )

    try:
        video.close()
    except:
        pass

    try:
        audio.close()
    except:
        pass

    return caminho_final


# =========================
# PÁGINA
# =========================

HTML = """
<!DOCTYPE html>

<html lang="pt-br">

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>Reel Maker</title>

<style>

body {
    background: #111;
    color: white;
    font-family: Arial, sans-serif;
    text-align: center;
    padding: 30px;
}

.container {
    max-width: 500px;
    margin: auto;
}

input,
select,
button {

    width: 100%;
    box-sizing: border-box;

    padding: 15px;
    margin: 10px 0;

    border-radius: 8px;
    border: none;

    font-size: 16px;
}

button {

    background: #00c853;
    color: white;

    font-weight: bold;

    cursor: pointer;
}

.info {

    margin-top: 20px;
    padding: 15px;

    background: #222;
    border-radius: 10px;
}

</style>

</head>

<body>

<div class="container">

<h1>🎬 Reel Maker</h1>

<p>
Imagens + narração automática
</p>

<form method="POST">

<input
    type="text"
    name="tema"
    placeholder="Digite o tema"
    required
>

<select name="estilo">

<option value="Motivacional">
Motivacional
</option>

<option value="Dinheiro">
Dinheiro
</option>

<option value="Curiosidades">
Curiosidades
</option>

<option value="Futebol">
Futebol
</option>

<option value="História">
História
</option>

</select>

<select name="duracao">

<option value="10">
10 segundos
</option>

<option value="15">
15 segundos
</option>

<option value="30">
30 segundos
</option>

</select>

<button type="submit">
🎙️ Criar Reel
</button>

</form>

{% if mensagem %}

<div class="info">

<p>{{ mensagem }}</p>

{% if video %}

<a href="/download/{{ video }}">

<button>
⬇️ Baixar vídeo
</button>

</a>

{% endif %}

</div>

{% endif %}

</div>

</body>

</html>
"""


# =========================
# ROTA PRINCIPAL
# =========================

@app.route("/", methods=["GET", "POST"])
def index():

    mensagem = ""
    video = None

    if request.method == "POST":

        tema = request.form.get(
            "tema",
            ""
        ).strip()

        estilo = request.form.get(
            "estilo",
            "Motivacional"
        )

        try:
            duracao = int(
                request.form.get(
                    "duracao",
                    10
                )
            )
        except:
            duracao = 10

        if not tema:

            mensagem = "Digite um tema."

        else:

            try:

                mensagem = (
                    "🎙️ Criando seu vídeo..."
                )

                caminho = criar_video(
                    tema,
                    estilo,
                    duracao
                )

                video = os.path.basename(
                    caminho
                )

                mensagem = (
                    "✅ Vídeo criado com sucesso!"
                )

            except Exception as erro:

                mensagem = (
                    "❌ Erro: "
                    + str(erro)
                )

                print(
                    "ERRO:",
                    erro
                )

    return render_template_string(
        HTML,
        mensagem=mensagem,
        video=video
    )


# =========================
# DOWNLOAD
# =========================

@app.route("/download/<nome>")
def download(nome):

    caminho = os.path.join(
        VIDEOS_DIR,
        nome
    )

    if not os.path.exists(caminho):
        return "Vídeo não encontrado.", 404

    return send_file(
        caminho,
        as_attachment=True
    )


# =========================
# SERVIDOR
# =========================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                8080
            )
        )
    )