import os
import random
import uuid
import requests

from flask import Flask, request, render_template_string, send_file
from moviepy import ImageClip, concatenate_videoclips
from PIL import Image

app = Flask(name)

============================================================

CONFIGURAÇÕES

============================================================

PORT = int(os.environ.get(“PORT”, “8080”))

WIDTH = 540
HEIGHT = 960
FPS = 15

PEXELS_API_KEY = os.environ.get(“PEXELS_API_KEY”)

VIDEOS_DIR = “videos”
IMAGES_DIR = “imagens”

os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

============================================================

ROTEIROS / TEMAS

============================================================

ROTEIROS = {
“Motivacional”: [
“Nunca desista dos seus objetivos. Cada pequeno passo conta. Continue trabalhando, continue acreditando e lembre-se: resultados levam tempo.”,
“Você não precisa ser perfeito para começar. Precisa apenas começar. Todos os dias são uma nova oportunidade para evoluir e chegar mais perto dos seus sonhos.”,
“Acredite no seu potencial. Mesmo quando ninguém estiver vendo seu esforço, continue. O resultado de hoje pode ser consequência da sua persistência de ontem.”
],

"Dinheiro": [
    "Cuidar do dinheiro começa com pequenas decisões. Evite gastos desnecessários, organize suas finanças e procure maneiras de aumentar sua renda.",
    "Construir uma vida financeira melhor exige planejamento, disciplina e paciência. Pequenas economias feitas todos os dias podem fazer diferença no futuro.",
    "Dinheiro não é apenas sobre ganhar mais. Também é sobre aprender a administrar melhor aquilo que você já ganha."
],
"Curiosidades": [
    "Você sabia que existem milhares de curiosidades incríveis sobre o mundo? Todos os dias podemos descobrir algo novo sobre ciência, natureza e história.",
    "O mundo está cheio de fatos surpreendentes. Algumas coisas que parecem impossíveis realmente existem e fazem parte da nossa realidade.",
    "A natureza é cheia de fenômenos incríveis. Quanto mais aprendemos, mais percebemos o quanto ainda existe para descobrir."
],
"Futebol": [
    "No futebol, cada segundo pode mudar completamente uma partida. Um gol, uma defesa ou uma decisão podem transformar toda a história do jogo.",
    "O futebol é muito mais do que apenas marcar gols. Estratégia, preparação, concentração e trabalho em equipe fazem parte do caminho para a vitória.",
    "Grandes jogadores não chegaram ao topo apenas pelo talento. Treinamento, disciplina e dedicação também fazem parte da trajetória."
],
"História": [
    "A história é formada por acontecimentos que mudaram o mundo. Conhecer o passado ajuda a entender melhor o presente.",
    "Grandes acontecimentos históricos influenciaram sociedades inteiras e deixaram marcas que continuam presentes até os dias de hoje.",
    "Muitas coisas que fazem parte da nossa vida atualmente começaram com acontecimentos que ocorreram há centenas ou até milhares de anos."
],
"Humor": [
    "A vida seria muito mais fácil se viesse com manual de instruções. Mas como não veio, só nos resta aprender na prática e rir dos nossos próprios erros.",
    "Tem dias em que tudo parece dar errado. Mas pelo menos podemos rir depois e transformar aquela situação em uma boa história.",
    "A melhor parte de alguns problemas é poder contar a história depois e perceber que, no final, tudo acabou virando motivo para rir."
],
"Desenvolvimento pessoal": [
    "Melhorar um pouco todos os dias pode gerar grandes mudanças ao longo do tempo. Tenha paciência com seu processo e continue avançando.",
    "Aprender, praticar e corrigir fazem parte do crescimento. Não tenha medo de errar, porque os erros também podem ensinar.",
    "Seu futuro é construído pelas decisões que você toma hoje. Comece com pequenas mudanças e mantenha a constância."
]

}

============================================================

CRIAR ROTEIRO

============================================================

def criar_roteiro(tema, estilo, duracao):

textos = ROTEIROS.get(tema, ROTEIROS["Motivacional"])
texto = random.choice(textos)
introducoes = [
    "Confira essa ideia: ",
    "Você precisa saber disso: ",
    "Olha só isso: "
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

============================================================

BUSCAR IMAGENS NO PEXELS

============================================================

def buscar_imagens(tema, quantidade=6):

if not PEXELS_API_KEY:
    raise Exception("PEXELS_API_KEY não está configurada no Railway.")
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
        f"Erro Pexels: {resposta.status_code} - {resposta.text}"
    )
dados = resposta.json()
fotos = dados.get("photos", [])
if not fotos:
    raise Exception(
        f"Nenhuma imagem encontrada para o tema: {tema}"
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
    raise Exception("Pexels não retornou imagens utilizáveis.")
return imagens

============================================================

BAIXAR E PREPARAR IMAGEM

============================================================

def preparar_imagem(url, caminho):

resposta = requests.get(
    url,
    timeout=30
)
resposta.raise_for_status()
arquivo_temp = caminho + ".download"
with open(arquivo_temp, "wb") as arquivo:
    arquivo.write(resposta.content)
imagem = Image.open(arquivo_temp).convert("RGB")
largura, altura = imagem.size
proporcao_destino = WIDTH / HEIGHT
proporcao_original = largura / altura
if proporcao_original > proporcao_destino:
    nova_largura = int(altura * proporcao_destino)
    esquerda = (largura - nova_largura) // 2
    imagem = imagem.crop(
        (
            esquerda,
            0,
            esquerda + nova_largura,
            altura
        )
    )
else:
    nova_altura = int(largura / proporcao_destino)
    topo = (altura - nova_altura) // 2
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

============================================================

CRIAR VÍDEO

============================================================

def criar_video(tema, estilo, duracao):

sessao = str(uuid.uuid4())[:8]
nome_video = f"reel_{sessao}_{duracao}s.mp4"
caminho_video = os.path.join(
    VIDEOS_DIR,
    nome_video
)
roteiro = criar_roteiro(
    tema,
    estilo,
    duracao
)
# --------------------------------------------------------
# BUSCAR IMAGENS
# --------------------------------------------------------
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
# --------------------------------------------------------
# DIVIDIR TEMPO ENTRE AS IMAGENS
# --------------------------------------------------------
quantidade = len(caminhos_imagens)
tempo_por_imagem = duracao / quantidade
clips = []
try:
    for caminho in caminhos_imagens:
        clip = (
            ImageClip(caminho)
            .with_duration(tempo_por_imagem)
        )
        clips.append(clip)
    video = concatenate_videoclips(
        clips,
        method="compose"
    )
    # ----------------------------------------------------
    # EXPORTAR
    # ----------------------------------------------------
    video.write_videofile(
        caminho_video,
        fps=FPS,
        codec="libx264",
        audio=False,
        preset="ultrafast",
        threads=1,
        logger=None
    )
    video.close()
finally:
    for clip in clips:
        try:
            clip.close()
        except:
            pass
    # Limpar imagens temporárias
    for caminho in caminhos_imagens:
        try:
            os.remove(caminho)
        except:
            pass
return nome_video, roteiro

============================================================

HTML

============================================================

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
button:hover {
    opacity: 0.9;
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
<option>História</option>
<option>Humor</option>
<option>Desenvolvimento pessoal</option>
</select>

Estilo

<select name="estilo">
<option>Viral</option>
<option>Informativo</option>
<option>Emocionante</option>
<option>Rápido</option>
</select>

Duração

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

🖼️ Imagens automáticas do Pexels
🎵 Sem música
🎙️ Sem narração
📝 Sem texto sobre o vídeo
📱 Formato vertical 540x960
⏱️ Até 60 segundos

</div>

{% if resultado %}

<div class="success">
<h3>✅ Vídeo criado!</h3>
<p>
<a href="/download/{{ resultado }}">
⬇️ BAIXAR VÍDEO
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

============================================================

ROTA PRINCIPAL

============================================================

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
                "Duração inválida."
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

============================================================

DOWNLOAD

============================================================

@app.route(”/download/”)
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

============================================================

INICIAR

============================================================

if name == “main”:

app.run(
    host="0.0.0.0",
    port=PORT
)