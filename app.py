import os
import random
import uuid
import requests
import textwrap

from flask import Flask, request, render_template_string, send_file
from moviepy import ImageClip, CompositeVideoClip, vfx
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)

# ============================================================
# CONFIGURACOES
# ============================================================

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

# ============================================================
# TEMAS
# ============================================================

TEMAS = [
    "Pontos positivos e negativos",
    "Dicas de carros",
    "Problemas comuns",
    "Antes de comprar",
    "Comparacao",
    "Curiosidades",
    "Manutencao e mecanica",
    "Pergunta para o publico"
]

# ============================================================
# ROTEIRO
# ============================================================

def criar_roteiro(modelo, topico, duracao):
    if topico == "Pontos positivos e negativos":
        partes = [
            f"Hoje vamos falar sobre o {modelo}.",
            "Entre os pontos positivos estao conforto, dirigibilidade e praticidade.",
            "Nos pontos negativos, e importante observar consumo, manutencao e preco das pecas.",
            "Antes de comprar, confira o historico e o estado real do carro.",
            "Voce compraria esse modelo?"
        ]
    elif topico == "Dicas de carros":
        partes = [
            f"Tem um {modelo}? Entao confira estas dicas.",
            "Nao deixe de fazer as revisoes preventivas.",
            "Confira regularmente oleo, filtros, pneus e freios.",
            "Fique atento a barulhos, vazamentos e luzes no painel.",
            "Qual dica voce acrescentaria?"
        ]
    elif topico == "Problemas comuns":
        partes = [
            f"Vai comprar um {modelo}? Fique atento a alguns pontos.",
            "Confira motor, cambio, suspensao e sistema eletrico.",
            "Observe barulhos diferentes, vazamentos e sinais de desgaste.",
            "O historico de manutencao tambem faz muita diferenca.",
            "Voce ja teve algum problema com esse modelo?"
        ]
    elif topico == "Antes de comprar":
        partes = [
            f"Pensando em comprar um {modelo} usado?",
            "Comece verificando o motor e o cambio.",
            "Depois confira suspensao, pneus, freios e parte eletrica.",
            "Confira tambem documentos e historico de manutencao.",
            "Nunca compre apenas pela aparencia."
        ]
    elif topico == "Comparacao":
        partes = [
            f"Vamos analisar o {modelo}.",
            "Na hora de comparar carros, observe consumo e manutencao.",
            "Tambem compare desempenho, conforto e espaco interno.",
            "Confira o preco das pecas e a disponibilidade de manutencao.",
            "Qual outro carro voce colocaria nessa comparacao?"
        ]
    elif topico == "Curiosidades":
        partes = [
            f"Voce conhece bem o {modelo}?",
            "Esse carro possui detalhes que muita gente acaba nao conhecendo.",
            "Versoes, motores e equipamentos podem mudar bastante.",
            "Por isso, sempre confira a versao exata do carro.",
            "Voce ja conhecia essas informacoes?"
        ]
    elif topico == "Manutencao e mecanica":
        partes = [
            f"Quer manter seu {modelo} em boas condicoes?",
            "Comece pelas revisoes preventivas.",
            "Confira oleo, filtros, freios, pneus, bateria e suspensao.",
            "Nao espere aparecer um problema para fazer manutencao.",
            "A manutencao preventiva pode evitar gastos maiores."
        ]
    else:
        partes = [
            f"O que voce acha do {modelo}?",
            "Voce compraria esse carro?",
            "Voce ja teve experiencia com esse modelo?",
            "Qual versao voce escolheria?",
            "Comente sua opiniao e diga qual carro devemos analisar depois."
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

# ============================================================
# BUSCA DE IMAGENS NO PEXELS
# ============================================================

def buscar_imagens_pexels(modelo, quantidade=5):
    if not PEXELS_API_KEY:
        raise Exception("PEXELS_API_KEY nao configurada no Railway.")
    modelo = modelo.strip()
    if not modelo:
        raise Exception("Digite o modelo do carro.")
    url = "https://api.pexels.com/v1/search"
    headers = {
        "Authorization": PEXELS_API_KEY
    }
    # --------------------------------------------------------
    # BUSCAS PRIORITARIAS
    # --------------------------------------------------------
    buscas = [
        modelo,
        f"{modelo} car",
        f"{modelo} automobile",
        f"{modelo} vehicle"
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
                "per_page": 30
            }
            resposta = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=20
            )
            if resposta.status_code != 200:
                continue
            dados = resposta.json()
            for foto in dados.get("photos", []):
                foto_id = foto.get("id")
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
                    "query": busca
                })
                if len(fotos) >= quantidade:
                    break
        except Exception:
            continue
    # --------------------------------------------------------
    # IMPORTANTE:
    # NAO USAR MAIS IMAGENS GENERICAS DE CARROS.
    # --------------------------------------------------------
    if not fotos:
        raise Exception(
            "Nao foram encontradas imagens para "
            f"'{modelo}'. Tente informar o nome completo do carro."
        )
    return fotos

# ============================================================
# DOWNLOAD DAS IMAGENS
# ============================================================

def baixar_imagem(url, caminho):
    resposta = requests.get(
        url,
        timeout=30
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
        Image.Resampling.LANCZOS
    )
    imagem.save(caminho, quality=95)
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
            return ImageFont.truetype(caminho, tamanho)
    return ImageFont.load_default()

# ============================================================
# CRIAR LEGENDA
# ============================================================

def criar_legenda(texto, indice):
    caminho = os.path.join(
        LEGENDAS_DIR,
        f"legenda_{uuid.uuid4().hex}_{indice}.png"
    )
    imagem = Image.new(
        "RGBA",
        (WIDTH, 260),
        (0, 0, 0, 0)
    )
    desenho = ImageDraw.Draw(imagem)
    fonte = encontrar_fonte(58)
    linhas = textwrap.wrap(
        texto,
        width=30
    )
    y = 30
    for linha in linhas[:3]:
        caixa = desenho.textbbox(
            (0, 0),
            linha,
            font=fonte
        )
        largura_texto = caixa[2] - caixa[0]
        x = (WIDTH - largura_texto) // 2
        # Fundo da legenda
        desenho.rounded_rectangle(
            (
                x - 25,
                y - 10,
                x + largura_texto + 25,
                y + 70
            ),
            radius=20,
            fill=(0, 0, 0, 190)
        )
        desenho.text(
            (x, y),
            linha,
            font=fonte,
            fill=(255, 255, 255, 255)
        )
        y += 75
    imagem.save(caminho)
    return caminho

# ============================================================
# CLIP COM ZOOM
# ============================================================

def criar_clip_com_zoom(caminho, duracao):
    clip = ImageClip(caminho)
    clip = clip.with_duration(duracao)
    # Pequeno zoom para deixar o video mais dinamico
    clip = clip.resized(
        lambda t: 1.0 + (0.06 * (t / duracao))
    )
    clip = clip.with_position("center")
    return clip

# ============================================================
# CRIAR VIDEO
# ============================================================

def criar_video(imagens, texto, duracao):
    nome_video = f"reel_{uuid.uuid4().hex}.mp4"
    caminho_video = os.path.join(
        VIDEOS_DIR,
        nome_video
    )
    quantidade_imagens = len(imagens)
    if quantidade_imagens == 0:
        raise Exception("Nenhuma imagem disponivel.")
    duracao_por_imagem = duracao / quantidade_imagens
    clips = []
    for indice, caminho in enumerate(imagens):
        clip = criar_clip_com_zoom(
            caminho,
            duracao_por_imagem
        )
        if indice > 0:
            clip = clip.with_effects([
                vfx.CrossFadeIn(0.35)
            ])
        clips.append(clip)
    video = CompositeVideoClip(
        clips,
        size=(WIDTH, HEIGHT)
    )
    video = video.with_duration(duracao)
    # --------------------------------------------------------
    # LEGENDAS AUTOMATICAS
    # --------------------------------------------------------
    palavras = texto.split()
    quantidade_blocos = max(
        1,
        min(6, len(palavras) // 5)
    )
    tamanho_bloco = max(
        1,
        len(palavras) // quantidade_blocos
    )
    blocos = []
    for i in range(0, len(palavras), tamanho_bloco):
        bloco = " ".join(
            palavras[i:i + tamanho_bloco]
        )
        if bloco:
            blocos.append(bloco)
    legenda_clips = []
    tempo_por_bloco = duracao / max(
        1,
        len(blocos)
    )
    for indice, bloco in enumerate(blocos):
        caminho_legenda = criar_legenda(
            bloco,
            indice
        )
        legenda = ImageClip(
            caminho_legenda
        )
        legenda = legenda.with_duration(
            tempo_por_bloco
        )
        legenda = legenda.with_start(
            indice * tempo_por_bloco
        )
        legenda = legenda.with_position(
            ("center", HEIGHT - 500)
        )
        legenda_clips.append(legenda)
    if legenda_clips:
        video_final = CompositeVideoClip(
            [video] + legenda_clips,
            size=(WIDTH, HEIGHT)
        )
    else:
        video_final = video
    # Sem musica e sem narracao
    video_final = video_final.without_audio()
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
    return nome_video

# ============================================================
# PAGINA
# ============================================================

HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Reel Maker Automotivo</title>
<style>
body {
    background: #111;
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
}
label {
    display: block;
    margin-top: 18px;
    margin-bottom: 7px;
}
input,
select,
button {
    width: 100%;
    padding: 15px;
    font-size: 17px;
    border-radius: 10px;
    border: none;
    box-sizing: border-box;
}
input,
select {
    background: #222;
    color: white;
}
button {
    margin-top: 25px;
    background: #e50914;
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
}
.download {
    display: block;
    margin-top: 20px;
    padding: 15px;
    background: green;
    color: white;
    text-align: center;
    text-decoration: none;
    border-radius: 10px;
}
.info {
    margin-top: 20px;
    background: #1d1d1d;
    padding: 15px;
    border-radius: 10px;
    line-height: 1.5;
}
</style>
</head>
<body>
<div class="container">
<h1>REEL MAKER AUTOMOTIVO</h1>
<div class="info">

Importante:

Digite o modelo do carro o mais completo possivel.
Exemplos:

Honda Civic 2015
Toyota Corolla 2020
Chevrolet Onix 2022
Volkswagen Golf 2017

</div>
<form method="POST">

Modelo do carro

<input
type="text"
name="modelo"
placeholder="Ex: Honda Civic 2015"
required>

Tipo de conteudo

<select name="topico">

{% for tema in temas %}

<option value="{{ tema }}">
{{ tema }}
</option>

{% endfor %}

</select>

Duracao

<select name="duracao">
<option value="10">10 segundos</option>
<option value="15">15 segundos</option>
<option value="20">20 segundos</option>
<option value="30">30 segundos</option>
</select>
<button type="submit">
CRIAR REEL
</button>
</form>

{% if mensagem %}

<div class="status">
{{ mensagem }}
</div>

{% endif %}

{% if download %}

<a href="{{ download }}" class="download">
BAIXAR VIDEO
</a>

{% endif %}

</div>
</body>
</html>
"""

# ============================================================
# ROTA PRINCIPAL
# ============================================================

@app.route("/", methods=["GET", "POST"])
def index():
    mensagem = ""
    download = None
    if request.method == "POST":
        try:
            modelo = request.form.get(
                "modelo",
                ""
            ).strip()
            topico = request.form.get(
                "topico",
                "Dicas de carros"
            )
            duracao = int(
                request.form.get(
                    "duracao",
                    "15"
                )
            )
            if not modelo:
                raise Exception(
                    "Digite o modelo do carro."
                )
            mensagem = (
                f"Buscando imagens especificas de "
                f"'{modelo}'..."
            )
            # ------------------------------------------------
            # BUSCAR SOMENTE IMAGENS RELACIONADAS AO MODELO
            # ------------------------------------------------
            resultados = buscar_imagens_pexels(
                modelo,
                quantidade=5
            )
            imagens = []
            # ------------------------------------------------
            # BAIXAR IMAGENS
            # ------------------------------------------------
            for indice, item in enumerate(resultados):
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
            if not imagens:
                raise Exception(
                    "Nao foi possivel baixar "
                    "imagens do modelo informado."
                )
            # ------------------------------------------------
            # CRIAR ROTEIRO
            # ------------------------------------------------
            texto = criar_roteiro(
                modelo,
                topico,
                duracao
            )
            # ------------------------------------------------
            # CRIAR VIDEO
            # ------------------------------------------------
            nome_video = criar_video(
                imagens,
                texto,
                duracao
            )
            mensagem = (
                f"Video criado com sucesso para "
                f"{modelo}."
            )
            download = (
                f"/download/{nome_video}"
            )
        except Exception as erro:
            mensagem = (
                "Erro ao criar o video: "
                + str(erro)
            )
    return render_template_string(
        HTML,
        temas=TEMAS,
        mensagem=mensagem,
        download=download
    )

# ============================================================
# DOWNLOAD
# ============================================================

@app.route("/download/<nome>")
def download_video(nome):
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
