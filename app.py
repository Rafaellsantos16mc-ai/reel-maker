import os
import random
import requests

from flask import Flask, request, render_template_string, send_file
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
from PIL import Image

app = Flask(__name__)

# =========================
# CONFIGURAÇÕES
# =========================

WIDTH = 540
HEIGHT = 960
FPS = 15

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

VIDEOS_DIR = "videos"
IMAGES_DIR = "imagens"
AUDIO_DIR = "audios"

os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)


# =========================
# GERAR ROTEIRO COM IA
# =========================

def gerar_roteiro_ia(tema, estilo, duracao):

    if not OPENAI_API_KEY:
        raise Exception("OPENAI_API_KEY não configurada no Railway.")

    prompt = f"""
Crie um roteiro curto para um vídeo vertical de Instagram Reels/TikTok.

Tema: {tema}
Estilo: {estilo}
Duração aproximada: {duracao} segundos.

Regras:
- Escreva em português do Brasil.
- Comece com um gancho muito forte.
- O texto precisa prender a atenção.
- Use frases naturais, como uma pessoa falando.
- Não use títulos.
- Não use emojis.
- Não use tópicos.
- Não diga "neste vídeo".
- Não diga "curta e compartilhe".
- Não invente estatísticas.
- Termine com uma frase marcante.
- Escreva somente o texto que será narrado.
"""

    resposta = requests.post(
        "https://api.openai.com/v1/responses",
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-5.6-luna",
            "input": prompt
        },
        timeout=60
    )

    if resposta.status_code != 200:
        raise Exception(
            f"Erro OpenAI: {resposta.status_code} - {resposta.text[:500]}"
        )

    dados = resposta.json()

    texto = dados.get("output_text")

    if not texto:
        # Fallback para estruturas diferentes da resposta
        partes = []

        for item in dados.get("output", []):
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    partes.append(content.get("text", ""))

        texto = " ".join(partes)

    texto = texto.strip()

    if not texto:
        raise Exception("A IA não retornou um roteiro.")

    return texto


# =========================
# GERAR NARRAÇÃO
# =========================

def gerar_narracao(texto):

    if not OPENAI_API_KEY:
        raise Exception("OPENAI_API_KEY não configurada.")

    caminho = os.path.join(AUDIO_DIR, "narracao.mp3")

    resposta = requests.post(
        "https://api.openai.com/v1/audio/speech",
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-4o-mini-tts",
            "voice": "coral",
            "input": texto,
            "instructions": (
                "Fale em português do Brasil. "
                "Use uma voz natural, clara e envolvente, "
                "com ritmo de narrador de vídeos curtos para redes sociais. "
                "Faça pausas naturais e dê ênfase às partes importantes."
            ),
            "response_format": "mp3"
        },
        timeout=120
    )

    if resposta.status_code != 200:
        raise Exception(
            f"Erro TTS: {resposta.status_code} - {resposta.text[:500]}"
        )

    with open(caminho, "wb") as arquivo:
        arquivo.write(resposta.content)

    return caminho


# =========================
# BUSCAR IMAGENS NO PEXELS
# =========================

def buscar_imagens(tema):

    if not PEXELS_API_KEY:
        raise Exception("PEXELS_API_KEY não configurada no Railway.")

    url = "https://api.pexels.com/v1/search"

    headers = {
        "Authorization": PEXELS_API_KEY
    }

    params = {
        "query": tema,
        "per_page": 8,
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
            f"Erro Pexels: {resposta.status_code} - {resposta.text[:500]}"
        )

    dados = resposta.json()

    imagens = []

    for foto in dados.get("photos", []):

        src = foto.get("src", {})

        link = (
            src.get("large2x")
            or src.get("large")
            or src.get("medium")
            or src.get("original")
        )

        if link:
            imagens.append(link)

    if not imagens:
        raise Exception("Nenhuma imagem encontrada no Pexels.")

    random.shuffle(imagens)

    return imagens[:5]


# =========================
# PREPARAR IMAGEM
# =========================

def preparar_imagem(url, numero):

    resposta = requests.get(
        url,
        timeout=30
    )

    if resposta.status_code != 200:
        raise Exception("Não foi possível baixar uma imagem do Pexels.")

    original = os.path.join(
        IMAGES_DIR,
        f"original_{numero}.jpg"
    )

    preparada = os.path.join(
        IMAGES_DIR,
        f"imagem_{numero}.jpg"
    )

    with open(original, "wb") as arquivo:
        arquivo.write(resposta.content)

    imagem = Image.open(original).convert("RGB")

    # Ajusta para o formato vertical
    proporcao_destino = WIDTH / HEIGHT
    proporcao_original = imagem.width / imagem.height

    if proporcao_original > proporcao_destino:

        nova_altura = HEIGHT

        nova_largura = int(
            imagem.width * nova_altura / imagem.height
        )

    else:

        nova_largura = WIDTH

        nova_altura = int(
            imagem.height * nova_largura / imagem.width
        )

    imagem = imagem.resize(
        (nova_largura, nova_altura),
        Image.LANCZOS
    )

    # Recorte central
    esquerda = max(
        0,
        (imagem.width - WIDTH) // 2
    )

    topo = max(
        0,
        (imagem.height - HEIGHT) // 2
    )

    direita = esquerda + WIDTH
    baixo = topo + HEIGHT

    imagem = imagem.crop(
        (esquerda, topo, direita, baixo)
    )

    imagem.save(
        preparada,
        "JPEG",
        quality=85
    )

    return preparada


# =========================
# CRIAR VÍDEO
# =========================

def criar_video(tema, estilo, duracao):

    # 1. Cria roteiro
    roteiro = gerar_roteiro_ia(
        tema,
        estilo,
        duracao
    )

    # 2. Busca imagens
    links_imagens = buscar_imagens(tema)

    # 3. Cria narração
    caminho_audio = gerar_narracao(roteiro)

    audio = AudioFileClip(caminho_audio)

    duracao_audio = audio.duration

    # Usa a duração da narração.
    # Se for menor que o solicitado, mantém a duração escolhida.
    duracao_final = max(
        float(duracao),
        float(duracao_audio)
    )

    # Limite de segurança
    duracao_final = min(
        duracao_final,
        float(duracao) + 8
    )

    # Quantidade de imagens
    quantidade = min(
        len(links_imagens),
        5
    )

    duracao_por_imagem = (
        duracao_final / quantidade
    )

    clips = []

    for i in range(quantidade):

        caminho_imagem = preparar_imagem(
            links_imagens[i],
            i
        )

        clip = (
            ImageClip(caminho_imagem)
            .with_duration(duracao_por_imagem)
        )

        clips.append(clip)

    video = concatenate_videoclips(
        clips,
        method="compose"
    )

    # Ajusta exatamente à duração final
    if video.duration > duracao_final:
        video = video.subclipped(
            0,
            duracao_final
        )

    # Coloca somente a narração
    audio_final = audio

    if audio.duration > video.duration:
        audio_final = audio.subclipped(
            0,
            video.duration
        )

    video = video.with_audio(
        audio_final
    )

    nome_video = "reel_automatico.mp4"

    caminho_final = os.path.join(
        VIDEOS_DIR,
        nome_video
    )

    video.write_videofile(
        caminho_final,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        threads=1,
        logger=None
    )

    video.close()

    if audio_final != audio:
        audio_final.close()

    audio.close()

    return nome_video, roteiro


# =========================
# INTERFACE
# =========================

HTML = """
<!DOCTYPE html>
<html lang="pt-BR">

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>Gerador de Reels IA</title>

<style>

body {
    font-family: Arial, sans-serif;
    background: #111;
    color: white;
    padding: 25px;
}

.container {
    max-width: 500px;
    margin: auto;
}

h1 {
    text-align: center;
}

input, select, button {
    width: 100%;
    padding: 14px;
    margin-top: 10px;
    margin-bottom: 15px;
    border-radius: 8px;
    border: none;
    box-sizing: border-box;
}

button {
    background: #00c853;
    color: white;
    font-size: 18px;
    font-weight: bold;
    cursor: pointer;
}

button:hover {
    background: #00a844;
}

.caixa {
    background: #1e1e1e;
    padding: 20px;
    border-radius: 15px;
}

.resultado {
    background: #222;
    padding: 15px;
    border-radius: 10px;
    margin-top: 20px;
}

a {
    display: block;
    text-align: center;
    background: #2196f3;
    color: white;
    padding: 14px;
    border-radius: 8px;
    text-decoration: none;
    margin-top: 15px;
}

</style>

</head>

<body>

<div class="container">

<h1>🎬 Gerador de Reels IA</h1>

<div class="caixa">

<form method="POST">

<label>Tema do vídeo</label>

<input
type="text"
name="tema"
placeholder="Ex: Como juntar dinheiro ganhando pouco"
required
>

<label>Estilo</label>

<select name="estilo">

<option>Motivacional</option>
<option>Dinheiro</option>
<option>Curiosidades</option>
<option>Futebol</option>
<option>História</option>
<option>Humor</option>
<option>Desenvolvimento pessoal</option>

</select>

<label>Duração</label>

<select name="duracao">

<option value="10">10 segundos</option>
<option value="15">15 segundos</option>
<option value="30">30 segundos</option>

</select>

<button type="submit">
🎙️ CRIAR REEL
</button>

</form>

{% if mensagem %}

<div class="resultado">

{{ mensagem }}

</div>

{% endif %}

{% if download %}

<a href="/download/{{ download }}">
⬇️ BAIXAR VÍDEO
</a>

{% endif %}

{% if roteiro %}

<div class="resultado">

<strong>Roteiro criado:</strong>

<p>{{ roteiro }}</p>

</div>

{% endif %}

</div>

</div>

</body>

</html>
"""


# =========================
# ROTA PRINCIPAL
# =========================

@app.route("/", methods=["GET", "POST"])
def index():

    mensagem = None
    download = None
    roteiro = None

    if request.method == "POST":

        try:

            tema = request.form.get(
                "tema",
                ""
            ).strip()

            estilo = request.form.get(
                "estilo",
                "Motivacional"
            )

            duracao = int(
                request.form.get(
                    "duracao",
                    "15"
                )
            )

            if not tema:
                raise Exception(
                    "Digite um tema."
                )

            mensagem = (
                "Criando roteiro, "
                "narração, imagens e vídeo..."
            )

            download, roteiro = criar_video(
                tema,
                estilo,
                duracao
            )

            mensagem = (
                "Reel criado com sucesso!"
            )

        except Exception as erro:

            mensagem = (
                "Erro ao criar o vídeo: "
                + str(erro)
            )

    return render_template_string(
        HTML,
        mensagem=mensagem,
        download=download,
        roteiro=roteiro
    )


# =========================
# DOWNLOAD
# =========================

@app.route("/download/<nome>")
def download_video(nome):

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
# INICIAR SERVIDOR
# =========================

if __name__ == "__main__":

    porta = int(
        os.environ.get(
            "PORT",
            8080
        )
    )

    app.run(
        host="0.0.0.0",
        port=porta
    )