import os
import random
import uuid
import requests

from flask import Flask, request, render_template_string, send_file
from moviepy import ImageClip, concatenate_videoclips
from PIL import Image

app = Flask(name)

CONFIGURACOES

PORT = int(os.environ.get(“PORT”, “8080”))

WIDTH = 540
HEIGHT = 960
FPS = 15

PEXELS_API_KEY = os.environ.get(“PEXELS_API_KEY”)

VIDEOS_DIR = “videos”
IMAGES_DIR = “imagens”

os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

ROTEIROS

ROTEIROS = {
“Motivacional”: [
“Nunca desista dos seus objetivos. Cada pequeno passo conta. Continue trabalhando e acreditando nos seus sonhos.”,
“Voce nao precisa ser perfeito para comecar. Precisa apenas comecar. Todos os dias sao uma nova oportunidade para evoluir.”,
“Acredite no seu potencial. Mesmo quando ninguem estiver vendo seu esforco, continue. A persistencia faz a diferenca.”
],

"Dinheiro": [
    "Cuidar do dinheiro comeca com pequenas decisoes. Evite gastos desnecessarios, organize suas financas e procure aumentar sua renda.",
    "Construir uma vida financeira melhor exige planejamento, disciplina e paciencia. Pequenas economias podem fazer diferenca no futuro.",
    "Dinheiro nao e apenas sobre ganhar mais. Tambem e sobre aprender a administrar melhor aquilo que voce ja ganha."
],
"Curiosidades": [
    "O mundo esta cheio de fatos surpreendentes. Algumas coisas que parecem impossiveis realmente existem.",
    "A natureza e cheia de fenomenos incriveis. Quanto mais aprendemos, mais percebemos o quanto ainda existe para descobrir.",
    "Todos os dias podemos descobrir algo novo sobre ciencia, natureza, animais e historia."
],
"Futebol": [
    "No futebol, cada segundo pode mudar completamente uma partida. Um gol, uma defesa ou uma decisao podem transformar o jogo.",
    "O futebol e muito mais do que marcar gols. Estrategia, preparacao, concentracao e trabalho em equipe fazem parte do jogo.",
    "Grandes jogadores nao chegaram ao topo apenas pelo talento. Treinamento, disciplina e dedicacao tambem fazem parte da trajetoria."
],
"Historia": [
    "A historia e formada por acontecimentos que mudaram o mundo. Conhecer o passado ajuda a entender melhor o presente.",
    "Grandes acontecimentos historicos influenciaram sociedades inteiras e deixaram marcas que continuam presentes.",
    "Muitas coisas da nossa vida atual comecaram com acontecimentos de centenas ou milhares de anos atras."
],
"Humor": [
    "A vida seria muito mais facil se viesse com manual de instrucoes. Como nao veio, so nos resta aprender na pratica.",
    "Tem dias em que tudo parece dar errado. Mas pelo menos podemos rir depois e transformar tudo em uma boa historia.",
    "A melhor parte de alguns problemas e poder contar a historia depois e perceber que virou motivo para rir."
],
"Desenvolvimento pessoal": [
    "Melhorar um pouco todos os dias pode gerar grandes mudancas ao longo do tempo. Tenha paciencia com seu processo.",
    "Aprender, praticar e corrigir fazem parte do crescimento. Nao tenha medo de errar.",
    "Seu futuro e construido pelas decisoes que voce toma hoje. Comece com pequenas mudancas e mantenha a constancia."
]

}

CRIAR ROTEIRO

def criar_roteiro(tema, estilo, duracao):

textos = ROTEIROS.get(
    tema,
    ROTEIROS["Motivacional"]
)
texto = random.choice(textos)
introducoes = [
    "Confira essa ideia: ",
    "Voce precisa saber disso: ",
    "Olha so isso: "
]
texto = random.choice(introducoes) + texto
if duracao == 10:
    limite = 35
elif duracao == 15:
    limite = 50
elif duracao == 30:
    limite = 90
else:
    limite = 170
palavras = texto.split()
if len(palavras) > limite:
    texto = " ".join(palavras[:limite])
return texto

BUSCAR IMAGENS

def buscar_imagens(tema, quantidade=6):

if not PEXELS_API_KEY:
    raise Exception(
        "PEXELS_API_KEY nao esta configurada no Railway."
    )
url = "https://api.pexels.com/v1/search"
headers = {
    "Authorization": PEXELS_API_KEY
}
params = {
    "query": tema,
    "orientation": "portrait",
    "per_page": quantidade
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
    raise Exception(
        f"Nenhuma imagem encontrada para: {tema}"
    )
imagens = []
for foto in fotos:
    src = foto.get("src", {})
    link = (
        src.get("large2x")
        or src.get("large")
        or src.get("original")
    )
    if link:
        imagens.append(link)
if not imagens:
    raise Exception(
        "Pexels nao retornou imagens."
    )
return imagens

PREPARAR IMAGEM

def preparar_imagem(url, caminho):

resposta = requests.get(
    url,
    timeout=30
)
resposta.raise_for_status()
arquivo_temp = caminho + ".download"
with open(arquivo_temp, "wb") as arquivo:
    arquivo.write(resposta.content)
imagem = Image.open(
    arquivo_temp
).convert("RGB")
largura, altura = imagem.size
proporcao_destino = WIDTH / HEIGHT
proporcao_original = largura / altura
if proporcao_original > proporcao_destino:
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
    Image.LANCZOS
)
imagem.save(
    caminho,
    "JPEG",
    quality=90
)
try:
    os.remove(arquivo_temp)
except:
    pass

CRIAR VIDEO

def criar_video(tema, estilo, duracao):

sessao = str(uuid.uuid4())[:8]
nome_video = (
    f"reel_{sessao}_{duracao}s.mp4"
)
caminho_video = os.path.join(
    VIDEOS_DIR,
    nome_video
)
roteiro = criar_roteiro(
    tema,
    estilo,
    duracao
)
imagens_urls = buscar_imagens(
    tema,
    quantidade=6
)
caminhos_imagens = []
for i, url in enumerate(imagens_urls):
    caminho = os.path.join(
        IMAGES_DIR,
        f"{sessao}_{i}.jpg"
    )
    preparar_imagem(
        url,
        caminho
    )
    caminhos_imagens.append(caminho)
quantidade = len(caminhos_imagens)
tempo_por_imagem = (
    duracao / quantidade
)
clips = []
video = None
try:
    for caminho in caminhos_imagens:
        clip = (
            ImageClip(caminho)
            .with_duration(
                tempo_por_imagem
            )
        )
        clips.append(clip)
    video = concatenate_videoclips(
        clips,
        method="compose"
    )
    video.write_videofile(
        caminho_video,
        fps=FPS,
        codec="libx264",
        audio=False,
        preset="ultrafast",
        threads=1,
        logger=None
    )
finally:
    if video is not None:
        try:
            video.close()
        except:
            pass
    for clip in clips:
        try:
            clip.close()
        except:
            pass
    for caminho in caminhos_imagens:
        try:
            os.remove(caminho)
        except:
            pass
return nome_video, roteiro

HTML

HTML = “””

<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Reel Maker</title>
<style>
body {
    font-family: Arial, sans-serif;
    background: #111;
    color: white;
    margin: 0;
    padding: 20px;
}
.container {
    max-width: 600px;
    margin: auto;
}
h1 {
    text-align: center;
}
.card {
    background: #1d1d1d;
    padding: 20px;
    border-radius: 15px;
}
label {
    display: block;
    margin-top: 15px;
    margin-bottom: 7px;
}
input,
select,
button {
    width: 100%;
    box-sizing: border-box;
    padding: 14px;
    border-radius: 10px;
    border: none;
    font-size: 16px;
}
button {
    margin-top: 20px;
    background: #00c853;
    color: white;
    font-weight: bold;
    cursor: pointer;
}
.info {
    margin-top: 15px;
    padding: 12px;
    background: #292929;
    border-radius: 10px;
    font-size: 14px;
}
.success {
    margin-top: 20px;
    background: #123d20;
    padding: 15px;
    border-radius: 10px;
}
a {
    color: #00e676;
    font-weight: bold;
}
.roteiro {
    margin-top: 15px;
    background: #222;
    padding: 15px;
    border-radius: 10px;
    line-height: 1.5;
}
</style>
</head>
<body>
<div class="container">
<h1>🎬 Reel Maker</h1>
<div class="card">
<form method="POST">

Tema

<select name="tema">
<option>Motivacional</option>
<option>Dinheiro</option>
<option>Curiosidades</option>
<option>Futebol</option>
<option>Historia</option>
<option>Humor</option>
<option>Desenvolvimento pessoal</option>
</select>

Estilo

<select name="estilo">
<option>Viral</option>
<option>Informativo</option>
<option>Emocionante</option>
<option>Rapido</option>
</select>

Duracao

<select name="duracao">
<option value="10">10 segundos</option>
<option value="15">15 segundos</option>
<option value="30">30 segundos</option>
<option value="60">60 segundos</option>
</select>
<button type="submit">
🎬 CRIAR REEL
</button>
</form>
<div class="info">

🖼️ Imagens automaticas do Pexels
🎵 Sem musica
🎙️ Sem narracao
📝 Sem texto sobre o video
📱 Formato vertical 540x960
⏱️ Ate 60 segundos

</div>

{% if resultado %}

<div class="success">
<h3>✅ Video criado!</h3>
<p>
<a href="/download/{{ resultado }}">
⬇️ BAIXAR VIDEO
</a>
</p>
</div>
<div class="roteiro">

💡 Ideia usada:

<p>
{{ roteiro }}
</p>
</div>

{% endif %}

{% if erro %}

<div class="success">

❌ Erro:

<p>
{{ erro }}
</p>
</div>

{% endif %}

</div>
</div>
</body>
</html>
"""

ROTA PRINCIPAL

@app.route(”/”, methods=[“GET”, “POST”])
def index():

resultado = None
roteiro = None
erro = None
if request.method == "POST":
    try:
        tema = request.form.get(
            "tema",
            "Motivacional"
        )
        estilo = request.form.get(
            "estilo",
            "Viral"
        )
        duracao = int(
            request.form.get(
                "duracao",
                "30"
            )
        )
        if duracao not in [10, 15, 30, 60]:
            raise Exception(
                "Duracao invalida."
            )
        resultado, roteiro = criar_video(
            tema,
            estilo,
            duracao
        )
    except Exception as e:
        erro = str(e)
return render_template_string(
    HTML,
    resultado=resultado,
    roteiro=roteiro,
    erro=erro
)

DOWNLOAD

@app.route(”/download/”)
def download(nome):

caminho = os.path.join(
    VIDEOS_DIR,
    nome
)
if not os.path.exists(caminho):
    return "Video nao encontrado.", 404
return send_file(
    caminho,
    as_attachment=True
)

INICIAR

if name == “main”:

app.run(
    host="0.0.0.0",
    port=PORT
)