import os
import random
import uuid
import requests
import textwrap

from flask import Flask, request, render_template_string, send_file
from moviepy import ImageClip, CompositeVideoClip, vfx
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)

WIDTH = 1080
HEIGHT = 1920
FPS = 30

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

VIDEOS_DIR = "videos"
IMAGES_DIR = "imagens"
LEGENDAS_DIR = "legendas"

os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(LEGENDAS_DIR, exist_ok=True)

TOPICOS = {
"Pontos positivos e negativos": [
"Pontos positivos",
"Pontos negativos",
"Consumo",
"Manutencao",
"Conforto",
"Desempenho"
],
"Dicas de carros": [
"Dicas importantes para proprietarios",
"Como economizar combustivel",
"Cuidados com manutencao",
"Cuidados com pneus",
"O que observar no carro"
],
"Problemas comuns": [
"Problemas que podem aparecer",
"Sinais de defeito",
"Itens que precisam de atencao",
"Custos de manutencao",
"O que verificar"
],
"Antes de comprar": [
"O que verificar antes de comprar",
"Motor",
"Cambio",
"Suspensao",
"Documentacao",
"Historico de manutencao"
],
"Comparacao": [
"Consumo",
"Manutencao",
"Desempenho",
"Conforto",
"Espaco",
"Custo de propriedade"
],
"Curiosidades": [
"Curiosidades sobre o modelo",
"Historia do carro",
"Motor",
"Tecnologia",
"Versoes",
"Detalhes pouco conhecidos"
],
"Manutencao e mecanica": [
"Motor",
"Oleo",
"Freios",
"Suspensao",
"Bateria",
"Pneus"
],
"Pergunta para o publico": [
"Voce compraria esse carro?",
"Voce ja teve esse modelo?",
"Qual versao voce escolheria?",
"Voce prefere esse ou outro modelo?",
"Qual carro devemos analisar depois?"
]
}

VISUAIS = [
"car",
"modern car",
"car interior",
"car engine",
"car dashboard",
"car wheel",
"car maintenance",
"car dealership",
"car mechanic",
"sports car"
]

def criar_roteiro(modelo, topico, duracao):

    if topico == "Pontos positivos e negativos":
        partes = [
            f"Hoje vamos falar sobre o {modelo}.",
            "Pontos positivos: bom nivel de conforto, boa dirigibilidade e um conjunto que pode agradar bastante.",
            "Pontos negativos: manutencao, consumo e custo de algumas pecas precisam ser avaliados.",
            "Antes de comprar, confira o historico de manutencao e o estado geral do carro.",
            "Voce compraria esse carro?"
        ]
    elif topico == "Dicas de carros":
        partes = [
            f"Se voce tem um {modelo}, confira estas dicas.",
            "Mantenha as revisoes em dia e nao ignore barulhos ou luzes no painel.",
            "Confira regularmente pneus, oleo, freios e fluidos.",
            "Uma manutencao preventiva pode evitar problemas maiores.",
            "Voce cuida do seu carro dessa forma?"
        ]
    elif topico == "Problemas comuns":
        partes = [
            f"Antes de comprar um {modelo}, fique atento.",
            "Verifique se existem sinais de problemas no motor, cambio e suspensao.",
            "Observe barulhos diferentes, vazamentos e luzes de advertencia no painel.",
            "Tambem vale conferir o historico de manutencao.",
            "Voce teria esse carro?"
        ]
    elif topico == "Antes de comprar":
        partes = [
            f"Pensando em comprar um {modelo} usado?",
            "Primeiro confira o estado do motor e do cambio.",
            "Depois verifique suspensao, pneus, freios e parte eletrica.",
            "Confira tambem documentos e historico de manutencao.",
            "Nunca compre apenas pela aparencia."
        ]
    elif topico == "Comparacao":
        partes = [
            f"Vamos comparar o {modelo}.",
            "Antes de escolher, compare consumo, manutencao e desempenho.",
            "Tambem vale analisar conforto, espaco e disponibilidade de pecas.",
            "O carro mais barato nem sempre possui o menor custo de propriedade.",
            "Qual modelo voce colocaria para comparar?"
        ]
    elif topico == "Curiosidades":
        partes = [
            f"Voce conhece bem o {modelo}?",
            "Esse modelo possui detalhes que muitas pessoas acabam nao conhecendo.",
            "Motor, versoes, equipamentos e historia podem mudar bastante de uma configuracao para outra.",
            "Por isso, conhecer a versao exata e importante antes de comprar.",
            "Voce ja conhecia essas informacoes?"
        ]
    elif topico == "Manutencao e mecanica":
        partes = [
            f"Quer manter seu {modelo} em boas condicoes?",
            "Comece pelas revisoes preventivas.",
            "Confira oleo, filtros, freios, pneus, bateria e suspensao.",
            "Nao espere aparecer um problema para fazer a manutencao.",
            "Manutencao preventiva pode evitar gastos maiores."
        ]
    else:
        partes = [
            f"O que voce acha do {modelo}?",
            "Voce compraria esse carro?",
            "Voce ja teve experiencia com esse modelo?",
            "Qual versao voce escolheria?",
            "Comente sua opiniao e diga qual carro devemos analisar no proximo video."
        ]
    texto = " ".join(partes)
    palavras = texto.split()
    if duracao <= 10:
        texto = " ".join(palavras[:42])
    elif duracao <= 15:
        texto = " ".join(palavras[:58])
    else:
        texto = " ".join(palavras[:105])
    return texto

def buscar_imagem_pexels(busca):

    if not PEXELS_API_KEY:
        raise Exception(
            "PEXELS_API_KEY nao configurada."
        )
    resposta = requests.get(
        "https://api.pexels.com/v1/search",
        headers={
            "Authorization": PEXELS_API_KEY
        },
        params={
            "query": busca,
            "per_page": 10,
            "orientation": "portrait"
        },
        timeout=30
    )
    if resposta.status_code != 200:
        return None
    dados = resposta.json()
    fotos = dados.get("photos", [])
    if not fotos:
        return None
    random.shuffle(fotos)
    for foto in fotos:
        src = foto.get("src", {})
        link = (
            src.get("original")
            or src.get("large2x")
            or src.get("large")
            or src.get("medium")
        )
        if link:
            return link
    return None

def buscar_imagens(modelo):

    imagens = []
    visuais = VISUAIS.copy()
    random.shuffle(visuais)
    for visual in visuais:
        busca = f"{modelo} {visual}"
        link = buscar_imagem_pexels(
            busca
        )
        if link and link not in imagens:
            imagens.append(link)
        if len(imagens) >= 5:
            break
    if len(imagens) < 5:
        link = buscar_imagem_pexels(
            modelo
        )
        if link and link not in imagens:
            imagens.append(link)
    if not imagens:
        raise Exception(
            "Nenhuma imagem encontrada no Pexels."
        )
    return imagens[:5]

def preparar_imagem(url, session_id, numero):

    resposta = requests.get(
        url,
        timeout=60
    )
    if resposta.status_code != 200:
        raise Exception(
            "Erro ao baixar imagem do Pexels."
        )
    caminho_original = os.path.join(
        IMAGES_DIR,
        f"orig_{session_id}_{numero}.jpg"
    )
    caminho_final = os.path.join(
        IMAGES_DIR,
        f"img_{session_id}_{numero}.jpg"
    )
    with open(caminho_original, "wb") as arquivo:
        arquivo.write(resposta.content)
    with Image.open(caminho_original) as imagem:
        imagem = imagem.convert("RGB")
        margem_zoom = 1.07
        largura_alvo = int(
            WIDTH * margem_zoom
        )
        altura_alvo = int(
            HEIGHT * margem_zoom
        )
        proporcao_alvo = (
            largura_alvo / altura_alvo
        )
        proporcao_imagem = (
            imagem.width / imagem.height
        )
        if proporcao_imagem > proporcao_alvo:
            nova_altura = altura_alvo
            nova_largura = int(
                imagem.width
                * nova_altura
                / imagem.height
            )
        else:
            nova_largura = largura_alvo
            nova_altura = int(
                imagem.height
                * nova_largura
                / imagem.width
            )
        imagem = imagem.resize(
            (
                nova_largura,
                nova_altura
            ),
            Image.Resampling.LANCZOS
        )
        esquerda = max(
            0,
            (imagem.width - largura_alvo) // 2
        )
        topo = max(
            0,
            (imagem.height - altura_alvo) // 2
        )
        imagem = imagem.crop(
            (
                esquerda,
                topo,
                esquerda + largura_alvo,
                topo + altura_alvo
            )
        )
        imagem.save(
            caminho_final,
            "JPEG",
            quality=95,
            optimize=True,
            progressive=True
        )
    if os.path.exists(
        caminho_original
    ):
        os.remove(
            caminho_original
        )
    return caminho_final

def criar_clip_com_zoom(
    caminho_img,
    duracao,
    zoom_in=True
):

    clip = ImageClip(
        caminho_img
    )
    if zoom_in:
        def zoom(t):
            progresso = t / duracao
            return 1.0 + (
                0.07 * progresso
            )
    else:
        def zoom(t):
            progresso = t / duracao
            return 1.07 - (
                0.07 * progresso
            )
    clip = clip.resized(
        zoom
    )
    clip = clip.with_position(
        "center"
    )
    clip = clip.with_duration(
        duracao
    )
    return clip

def encontrar_fonte():

    fontes = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"
    ]
    for fonte in fontes:
        if os.path.exists(fonte):
            return fonte
    return None

def criar_imagem_legenda(
    texto,
    session_id,
    numero
):

    largura = 1000
    altura = 230
    imagem = Image.new(
        "RGBA",
        (
            largura,
            altura
        ),
        (
            0,
            0,
            0,
            0
        )
    )
    desenho = ImageDraw.Draw(
        imagem
    )
    fonte_path = encontrar_fonte()
    if fonte_path:
        fonte = ImageFont.truetype(
            fonte_path,
            52
        )
    else:
        fonte = ImageFont.load_default()
    linhas = textwrap.wrap(
        texto,
        width=34
    )
    if len(linhas) > 3:
        linhas = linhas[:3]
    caixas = []
    for linha in linhas:
        caixa = desenho.textbbox(
            (0, 0),
            linha,
            font=fonte,
            stroke_width=2
        )
        largura_texto = (
            caixa[2] - caixa[0]
        )
        altura_texto = (
            caixa[3] - caixa[1]
        )
        caixas.append(
            (
                linha,
                largura_texto,
                altura_texto
            )
        )
    altura_total = sum(
        item[2]
        for item in caixas
    ) + (
        (len(caixas) - 1) * 12
    )
    y = (
        altura - altura_total
    ) // 2
    margem_x = 30
    margem_y = 20
    desenho.rounded_rectangle(
        (
            margem_x,
            max(
                5,
                y - margem_y
            ),
            largura - margem_x,
            min(
                altura - 5,
                y + altura_total + margem_y
            )
        ),
        radius=28,
        fill=(
            0,
            0,
            0,
            175
        )
    )
    for (
        linha,
        largura_texto,
        altura_texto
    ) in caixas:
        x = (
            largura - largura_texto
        ) // 2
        desenho.text(
            (
                x,
                y
            ),
            linha,
            font=fonte,
            fill=(
                255,
                255,
                255,
                255
            ),
            stroke_width=3,
            stroke_fill=(
                0,
                0,
                0,
                255
            )
        )
        y += (
            altura_texto + 12
        )
    caminho = os.path.join(
        LEGENDAS_DIR,
        f"legenda_{session_id}_{numero}.png"
    )
    imagem.save(
        caminho,
        "PNG"
    )
    return caminho

def criar_legendas(
    roteiro,
    duracao,
    session_id
):

    palavras = roteiro.split()
    if not palavras:
        return []
    tamanho_bloco = 6
    blocos = []
    for i in range(
        0,
        len(palavras),
        tamanho_bloco
    ):
        bloco = " ".join(
            palavras[
                i:i + tamanho_bloco
            ]
        )
        if bloco:
            blocos.append(
                bloco
            )
    if not blocos:
        return []
    tempo_por_bloco = (
        float(duracao)
        / len(blocos)
    )
    legendas = []
    for i, bloco in enumerate(
        blocos
    ):
        caminho = criar_imagem_legenda(
            bloco,
            session_id,
            i
        )
        clip = ImageClip(
            caminho
        )
        clip = clip.with_duration(
            tempo_por_bloco
        )
        clip = clip.with_position(
            (
                "center",
                HEIGHT - 430
            )
        )
        clip = clip.with_start(
            i * tempo_por_bloco
        )
        legendas.append(
            clip
        )
    return legendas

def criar_video(
    modelo,
    topico,
    duracao
):

    session_id = str(
        uuid.uuid4()
    )[:8]
    roteiro = criar_roteiro(
        modelo,
        topico,
        duracao
    )
    links = buscar_imagens(
        modelo
    )
    clips = []
    clips_legendas = []
    video = None
    try:
        quantidade = min(
            len(links),
            5
        )
        duracao_imagem = (
            float(duracao)
            / quantidade
        )
        transicao = min(
            0.5,
            duracao_imagem / 3
        )
        tempo_atual = 0
        for i in range(
            quantidade
        ):
            caminho_img = preparar_imagem(
                links[i],
                session_id,
                i
            )
            clip = criar_clip_com_zoom(
                caminho_img,
                duracao_imagem,
                zoom_in=(
                    i % 2 == 0
                )
            )
            if i > 0:
                tempo_atual -= transicao
                clip = clip.with_effects(
                    [
                        vfx.CrossFadeIn(
                            transicao
                        )
                    ]
                )
            clip = clip.with_start(
                tempo_atual
            )
            clips.append(
                clip
            )
            tempo_atual += (
                duracao_imagem
            )
        clips_legendas = criar_legendas(
            roteiro,
            duracao,
            session_id
        )
        video = CompositeVideoClip(
            clips + clips_legendas,
            size=(
                WIDTH,
                HEIGHT
            )
        )
        video = video.with_duration(
            float(duracao)
        )
        video = video.without_audio()
        nome_video = (
            f"reel_{session_id}.mp4"
        )
        caminho_video = os.path.join(
            VIDEOS_DIR,
            nome_video
        )
        video.write_videofile(
            caminho_video,
            fps=FPS,
            codec="libx264",
            audio=False,
            preset="faster",
            bitrate="8M",
            threads=2,
            logger=None
        )
        return (
            nome_video,
            roteiro
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
        for clip in clips_legendas:
            try:
                clip.close()
            except:
                pass

HTML = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">

<meta
name="viewport"
content="width=device-width, initial-scale=1.0">

<title>Auto Reel Maker</title>
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
    background: #1c1c1c;
    padding: 20px;
    border-radius: 15px;
}
label {
    display: block;
    margin-top: 15px;
    font-weight: bold;
}
input,
select,
button {
    width: 100%;
    box-sizing: border-box;
    padding: 14px;
    margin-top: 10px;
    border-radius: 10px;
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
    background: #222;
    padding: 15px;
    border-radius: 10px;
    line-height: 1.6;
}
a {
    color: #00e676;
    font-weight: bold;
}
</style>
</head>
<body>
<div class="container">
<h1>Auto Reel Maker</h1>
<div class="card">
<form method="POST">
<label>
Modelo do carro
</label>

<input
type="text"
name="modelo"
placeholder="Ex: Honda Civic 2015"
required>

<label>
Tipo de conteudo
</label>
<select name="topico">
<option>
Pontos positivos e negativos
</option>
<option>
Dicas de carros
</option>
<option>
Problemas comuns
</option>
<option>
Antes de comprar
</option>
<option>
Comparacao
</option>
<option>
Curiosidades
</option>
<option>
Manutencao e mecanica
</option>
<option>
Pergunta para o publico
</option>
</select>
<label>
Duracao
</label>
<select name="duracao">
<option value="10">
10 segundos
</option>
<option value="15">
15 segundos
</option>
<option value="20">
20 segundos
</option>
<option value="30">
30 segundos
</option>
</select>
<button type="submit">
CRIAR REEL
</button>
</form>
<div class="info">

Canal:
Automotivo

<br>

Formato:
Vertical 1080 x 1920

<br>

FPS:
30

<br>

Imagens:
Pexels

<br>

Zoom:
Suave

<br>

Transicoes:
Suaves

<br>

Narracao:
Nao

<br>

Musica:
Nao

<br>

Legendas:
Automaticas

</div>

{% if mensagem %}

<div class="info">

{{ mensagem|safe }}

</div>

{% endif %}

</div>
</div>
</body>
</html>
"""

@app.route(
    "/",
    methods=["GET", "POST"]
)
def index():

    mensagem = ""
    if request.method == "POST":
        try:
            modelo = request.form.get(
                "modelo",
                "carro"
            )
            topico = request.form.get(
                "topico",
                "Pontos positivos e negativos"
            )
            duracao = int(
                request.form.get(
                    "duracao",
                    "15"
                )
            )
            nome_video, roteiro = criar_video(
                modelo,
                topico,
                duracao
            )
            mensagem = f"""
            <h3>Reel criado!</h3>
            <p>
            Modelo: {modelo}
            </p>
            <p>
            Tipo: {topico}
            </p>
            <p>
            Video 1080 x 1920.
            </p>
            <p>
            Legendas automaticas.
            </p>
            <p>
            Sem narracao ou musica.
            </p>
            <p>
            <a href="/download/{nome_video}">
            BAIXAR VIDEO
            </a>
            </p>
            """
        except Exception as erro:
            mensagem = f"""
            <h3>Erro ao criar o video</h3>
            <p>
            {erro}
            </p>
            """
    return render_template_string(
        HTML,
        mensagem=mensagem
    )

@app.route(
    "/download/<nome>"
)
def download(nome):

    caminho = os.path.join(
        VIDEOS_DIR,
        nome
    )
    if not os.path.exists(
        caminho
    ):
        return (
            "Video nao encontrado.",
            404
        )
    return send_file(
        caminho,
        as_attachment=True
    )

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
