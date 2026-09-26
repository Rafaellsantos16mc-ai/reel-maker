import os
import random
import uuid
import requests
from flask import Flask, request, render_template_string, send_file
from moviepy import ImageClip, CompositeVideoClip, vfx
from PIL import Image
app = Flask(__name__)
# ============================================================
# CONFIGURAÇÕES
# ============================================================
WIDTH = 1080
HEIGHT = 1920
FPS = 30
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")
VIDEOS_DIR = "videos"
IMAGES_DIR = "imagens"
os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)
# ============================================================
# ROTEIROS
# ============================================================
ROTEIROS = {
    "Motivacional": [
        "Não espere o momento perfeito para começar. Comece com o que você tem e melhore todos os dias.",
        "A diferença entre quem sonha e quem conquista está na constância. Faça um pouco todos os dias.",
        "Você não precisa ser perfeito. Precisa apenas continuar, mesmo quando estiver difícil."
    ],
    "Dinheiro": [
        "Dinheiro não muda apenas a vida. A forma como você administra o dinheiro também muda o seu futuro.",
        "Aprender a guardar dinheiro é tão importante quanto aprender a ganhar dinheiro.",
        "Pequenas decisões financeiras tomadas todos os dias podem criar grandes resultados no futuro."
    ],
    "Curiosidades": [
        "Você sabia que existem fatos incríveis sobre o mundo que parecem mentira, mas são completamente reais?",
        "O mundo está cheio de curiosidades que poucas pessoas conhecem. Algumas delas são realmente impressionantes.",
        "Existem acontecimentos históricos e científicos que parecem coisa de filme, mas realmente aconteceram."
    ],
    "Futebol": [
        "O futebol é muito mais do que um jogo. É paixão, estratégia, história e emoção.",
        "Grandes jogadores não chegaram ao topo apenas pelo talento. Treino, disciplina e dedicação fizeram parte da jornada.",
        "No futebol, alguns segundos podem mudar completamente o resultado de uma partida."
    ],
    "História": [
        "A história é cheia de acontecimentos que mudaram completamente o mundo.",
        "Muitas coisas que fazem parte da nossa vida hoje começaram com acontecimentos de centenas de anos atrás.",
        "Conhecer a história ajuda a entender melhor como o mundo chegou até aqui."
    ],
    "Humor": [
        "A vida seria muito mais fácil se algumas situações viessem com manual de instruções.",
        "Tem dias em que tudo parece dar errado, mas pelo menos depois podemos rir da situação.",
        "Algumas situações são tão inesperadas que só resta respirar fundo e continuar."
    ],
    "Desenvolvimento pessoal": [
        "Melhorar um pouco todos os dias pode parecer pouco, mas depois de meses o resultado pode ser enorme.",
        "Seu futuro é construído pelas pequenas decisões que você toma todos os dias.",
        "Disciplina significa continuar fazendo aquilo que precisa ser feito mesmo quando a motivação desaparece."
    ]
}
# ============================================================
# CRIAR ROTEIRO
# ============================================================
def criar_roteiro(tema, estilo, duracao):
    lista = ROTEIROS.get(
        estilo,
        ROTEIROS["Motivacional"]
    )
    texto = random.choice(lista)
    introducoes = [
        f"Falando sobre {tema}, existe uma coisa importante para entender.",
        f"Se você está pensando em {tema}, preste atenção nisso.",
        f"Quando o assunto é {tema}, muita gente esquece de uma coisa."
    ]
    texto_final = (
        random.choice(introducoes)
        + " "
        + texto
    )
    palavras = texto_final.split()
    if duracao <= 10:
        texto_final = " ".join(palavras[:42])
    elif duracao <= 15:
        texto_final = " ".join(palavras[:58])
    else:
        texto_final = " ".join(palavras[:105])
    return texto_final
# ============================================================
# BUSCAR IMAGENS NO PEXELS
# ============================================================
def buscar_imagens(tema):
    if not PEXELS_API_KEY:
        raise Exception(
            "PEXELS_API_KEY não configurada nas variáveis de ambiente."
        )
    resposta = requests.get(
        "https://api.pexels.com/v1/search",
        headers={
            "Authorization": PEXELS_API_KEY
        },
        params={
            "query": tema,
            "per_page": 10,
            "orientation": "portrait"
        },
        timeout=30
    )
    if resposta.status_code != 200:
        raise Exception(
            f"Erro Pexels: status {resposta.status_code}"
        )
    dados = resposta.json()
    imagens = []
    for foto in dados.get("photos", []):
        src = foto.get("src", {})
        # Prioriza imagens maiores
        link = (
            src.get("original")
            or src.get("large2x")
            or src.get("large")
            or src.get("medium")
        )
        if link:
            imagens.append(link)
    if not imagens:
        raise Exception(
            "Nenhuma imagem encontrada no Pexels para esse tema."
        )
    random.shuffle(imagens)
    return imagens[:5]
# ============================================================
# PREPARAR IMAGEM EM ALTA QUALIDADE
# ============================================================
def preparar_imagem(url, session_id, numero):
    resposta = requests.get(
        url,
        timeout=60
    )
    if resposta.status_code != 200:
        raise Exception(
            "Erro ao baixar a imagem do Pexels."
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
        proporcao_destino = WIDTH / HEIGHT
        proporcao_imagem = imagem.width / imagem.height
        # ----------------------------------------------------
        # RESERVA 7% PARA O ZOOM
        # ----------------------------------------------------
        margem_zoom = 1.07
        largura_alvo = int(WIDTH * margem_zoom)
        altura_alvo = int(HEIGHT * margem_zoom)
        proporcao_alvo = largura_alvo / altura_alvo
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
            (nova_largura, nova_altura),
            Image.Resampling.LANCZOS
        )
        # ----------------------------------------------------
        # RECORTE CENTRAL
        # ----------------------------------------------------
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
        # ----------------------------------------------------
        # SALVAR COM QUALIDADE ALTA
        # ----------------------------------------------------
        imagem.save(
            caminho_final,
            "JPEG",
            quality=95,
            optimize=True,
            progressive=True
        )
    # Remove arquivo original
    if os.path.exists(caminho_original):
        os.remove(caminho_original)
    return caminho_final
# ============================================================
# CRIAR CLIP COM ZOOM
# ============================================================
def criar_clip_com_zoom(
    caminho_img,
    duracao,
    zoom_in=True
):
    clip = ImageClip(caminho_img)
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
    clip = clip.resized(zoom)
    clip = clip.with_position("center")
    clip = clip.with_duration(
        duracao
    )
    return clip
# ============================================================
# CRIAR VÍDEO
# ============================================================
def criar_video(
    tema,
    estilo,
    duracao
):
    session_id = str(
        uuid.uuid4()
    )[:8]
    roteiro = criar_roteiro(
        tema,
        estilo,
        duracao
    )
    links = buscar_imagens(
        tema
    )
    clips = []
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
        # ----------------------------------------------------
        # CRIAR CADA CENA
        # ----------------------------------------------------
        for i in range(quantidade):
            caminho_img = preparar_imagem(
                links[i],
                session_id,
                i
            )
            clip = criar_clip_com_zoom(
                caminho_img,
                duracao_imagem,
                zoom_in=(i % 2 == 0)
            )
            # ------------------------------------------------
            # TRANSIÇÃO
            # ------------------------------------------------
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
        # ----------------------------------------------------
        # MONTAR VÍDEO FULL HD
        # ----------------------------------------------------
        video = CompositeVideoClip(
            clips,
            size=(WIDTH, HEIGHT)
        )
        video = video.with_duration(
            float(duracao)
        )
        # ----------------------------------------------------
        # SEM ÁUDIO
        # ----------------------------------------------------
        video = video.without_audio()
        nome_video = (
            f"reel_{session_id}.mp4"
        )
        caminho_video = os.path.join(
            VIDEOS_DIR,
            nome_video
        )
        # ----------------------------------------------------
        # EXPORTAÇÃO DE ALTA QUALIDADE
        # ----------------------------------------------------
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
# ============================================================
# INTERFACE
# ============================================================
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
<h1>🎬 Reel Maker</h1>
<div class="card">
<form method="POST">
<label>Tema do vídeo</label>
<input
type="text"
name="tema"
placeholder="Ex: dinheiro, academia, futebol..."
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
<option value="20">20 segundos</option>
<option value="30">30 segundos</option>
</select>
<button type="submit">
🎬 CRIAR REEL FULL HD
</button>
</form>
<div class="info">
<b>Qualidade:</b> 1080 × 1920 Full HD<br>
<b>FPS:</b> 30<br>
<b>Imagens:</b> alta resolução<br>
<b>Zoom:</b> suave<br>
<b>Transições:</b> suaves<br>
<b>Narração:</b> não<br>
<b>Música:</b> não<br>
<b>Texto na tela:</b> não
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
# ============================================================
# ROTA PRINCIPAL
# ============================================================
@app.route(
    "/",
    methods=["GET", "POST"]
)
def index():
    mensagem = ""
    if request.method == "POST":
        try:
            tema = request.form.get(
                "tema",
                "motivacional"
            )
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
            nome_video, roteiro = criar_video(
                tema,
                estilo,
                duracao
            )
            mensagem = f"""
            <h3>✅ Reel criado!</h3>
            <p>
            Vídeo em Full HD 1080×1920.
            </p>
            <p>
            Sem narração, sem música e sem texto.
            </p>
            <p>
            <a href="/download/{nome_video}">
            ⬇️ BAIXAR VÍDEO
            </a>
            </p>
            """
        except Exception as erro:
            mensagem = f"""
            <h3>❌ Erro ao criar o vídeo</h3>
            <p>{erro}</p>
            """
    return render_template_string(
        HTML,
        mensagem=mensagem
    )
# ============================================================
# DOWNLOAD
# ============================================================
@app.route(
    "/download/<nome>"
)
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
# ============================================================
# EXECUÇÃO
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