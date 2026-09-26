import os
import random
import uuid
import requests
from flask import Flask, request, render_template_string, send_file
from moviepy import ImageClip, CompositeVideoClip, vfx
from PIL import Image
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
os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)
# =========================
# ROTEIROS
# =========================
ROTEIROS = {
    "Motivacional": [
        "Você não precisa mudar sua vida inteira hoje. Precisa apenas começar. Pequenas decisões repetidas todos os dias podem mudar completamente o seu futuro. Enquanto muita gente espera a oportunidade perfeita, quem começa agora já está criando a própria oportunidade. Não pare.",
        "Talvez você esteja mais perto do seu objetivo do que imagina. O problema é que resultados grandes quase nunca aparecem rapidamente. Continue trabalhando, continue aprendendo e continue tentando. Um dia você vai olhar para trás e perceber que cada pequeno passo valeu a pena.",
        "Não espere sentir vontade para começar. A disciplina aparece justamente nos dias em que a motivação desaparece. Faça um pouco hoje, faça novamente amanhã e continue. O segredo não é ser perfeito. É não desistir."
    ],
    "Dinheiro": [
        "Se você quer melhorar sua vida financeira, comece pelo básico. Gaste menos do que ganha, evite dívidas desnecessárias e aprenda uma habilidade que possa aumentar sua renda. Dinheiro não muda uma pessoa do dia para a noite. Mas bons hábitos financeiros podem mudar seu futuro.",
        "Ganhar mais dinheiro é importante, mas saber administrar o que você ganha é fundamental. Antes de procurar a próxima forma de ganhar dinheiro, descubra para onde está indo o seu dinheiro hoje. Pequenas despesas repetidas podem consumir uma grande parte da sua renda.",
        "Quer começar a construir uma vida financeira melhor? Pare de pensar apenas em economizar e comece também a pensar em aumentar sua capacidade de ganhar dinheiro. Aprenda, desenvolva habilidades e procure novas oportunidades. Sua renda pode crescer junto com o seu conhecimento."
    ],
    "Curiosidades": [
        "Você sabia que o cérebro humano é capaz de consumir uma quantidade enorme de energia mesmo quando estamos parados? Isso acontece porque ele trabalha continuamente, controlando pensamentos, movimentos, memória e diversas funções do corpo. É uma das estruturas mais impressionantes da natureza.",
        "Existe uma curiosidade sobre o sono que muita gente desconhece. Enquanto você dorme, seu cérebro continua trabalhando. Ele organiza informações, consolida memórias e participa de vários processos importantes para o funcionamento do organismo.",
        "Você já percebeu como uma música pode trazer uma lembrança antiga quase instantaneamente? Isso acontece porque música, emoção e memória estão fortemente conectadas no cérebro. Por isso algumas músicas conseguem nos transportar para momentos específicos da nossa vida."
    ],
    "Futebol": [
        "No futebol, uma partida pode mudar completamente em poucos minutos. Um gol muda a estratégia, um cartão pode alterar o comportamento de um jogador e uma substituição pode transformar o jogo. É justamente essa imprevisibilidade que faz milhões de pessoas acompanharem o esporte.",
        "Você já reparou como os melhores jogadores parecem tomar decisões muito rapidamente? Isso acontece porque eles treinam repetidamente situações de jogo. Com experiência, muitas decisões deixam de ser pensadas conscientemente e passam a acontecer quase automaticamente.",
        "No futebol, talento ajuda, mas preparação também faz diferença. Treinamento, posicionamento, leitura de jogo e tomada de decisão podem transformar completamente o desempenho de um jogador. Muitas vezes, o que parece facilidade é resultado de milhares de horas de treino."
    ],
    "História": [
        "A história está cheia de acontecimentos que parecem inacreditáveis hoje. Impérios surgiram e desapareceram, cidades foram reconstruídas e invenções mudaram completamente a maneira como as pessoas viviam. Conhecer o passado ajuda a entender por que o mundo atual é como é.",
        "Muitas das coisas que usamos diariamente possuem uma história muito mais antiga do que imaginamos. Algumas invenções passaram por décadas de mudanças até chegarem ao formato que conhecemos hoje. A tecnologia atual é resultado de muitas gerações de descobertas.",
        "Grandes acontecimentos históricos raramente acontecem de uma hora para outra. Normalmente são resultado de pequenas decisões, conflitos, descobertas e mudanças que acontecem ao longo de muitos anos. Por isso estudar história é também entender como pequenas mudanças podem produzir grandes consequências."
    ],
    "Humor": [
        "Eu prometi que hoje ia economizar dinheiro. Aí entrei em uma loja só para olhar. Cinco minutos depois estava pensando se realmente precisava daquele produto. Conclusão: meu dinheiro saiu mais rápido do que eu entrei na loja.",
        "Você já percebeu que quando estamos com pressa tudo dá errado? A chave desaparece, o celular fica sem bateria e justamente naquele momento aparece um trânsito enorme. Parece que o universo escolheu aquele dia para testar nossa paciência.",
        "O despertador toca e você pensa: só mais cinco minutos. Quando percebe, já passou meia hora. Aí você levanta correndo, procurando roupa, celular, chave e tentando lembrar por que decidiu dormir tarde. Todo dia é uma nova aventura."
    ],
    "Desenvolvimento pessoal": [
        "Uma das melhores coisas que você pode fazer por você mesmo é aprender a dizer não. Não para tudo, mas para aquilo que tira seu tempo, sua energia e seu foco. Quando você aprende a escolher melhor onde coloca sua atenção, sua vida começa a mudar.",
        "Você não precisa se comparar com todo mundo. Cada pessoa está vivendo uma realidade diferente. Compare você de hoje com quem você era ontem. Se estiver aprendendo, melhorando e avançando, mesmo que lentamente, já existe progresso.",
        "Aprender uma habilidade nova pode parecer difícil no começo. Você erra, esquece e pensa em desistir. Mas depois de repetir várias vezes, aquilo começa a ficar natural. O segredo é aceitar ser iniciante antes de tentar ser bom."
    ]
}
# =========================
# CRIAR ROTEIRO
# =========================
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
    texto_final = random.choice(introducoes) + " " + texto
    palavras = texto_final.split()
    if duracao <= 10:
        texto_final = " ".join(palavras[:42])
    elif duracao <= 15:
        texto_final = " ".join(palavras[:58])
    else:
        texto_final = " ".join(palavras[:105])
    return texto_final
# =========================
# PEXELS
# =========================
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
            "per_page": 8,
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
        link = (
            src.get("large")
            or src.get("medium")
            or src.get("original")
        )
        if link:
            imagens.append(link)
    if not imagens:
        raise Exception(
            "Nenhuma imagem encontrada no Pexels para esse tema."
        )
    random.shuffle(imagens)
    return imagens[:5]
# =========================
# PREPARAR IMAGEM
# =========================
def preparar_imagem(url, session_id, numero):
    resposta = requests.get(
        url,
        timeout=30
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
        if proporcao_imagem > proporcao_destino:
            nova_altura = HEIGHT
            nova_largura = int(
                imagem.width *
                nova_altura /
                imagem.height
            )
        else:
            nova_largura = WIDTH
            nova_altura = int(
                imagem.height *
                nova_largura /
                imagem.width
            )
        # Deixa um pouco maior para permitir o zoom
        margem_zoom = 1.15
        nova_largura = int(
            nova_largura * margem_zoom
        )
        nova_altura = int(
            nova_altura * margem_zoom
        )
        imagem = imagem.resize(
            (nova_largura, nova_altura),
            Image.LANCZOS
        )
        esquerda = max(
            0,
            (imagem.width - WIDTH) // 2
        )
        topo = max(
            0,
            (imagem.height - HEIGHT) // 2
        )
        imagem = imagem.crop(
            (
                esquerda,
                topo,
                esquerda + WIDTH,
                topo + HEIGHT
            )
        )
        imagem.save(
            caminho_final,
            "JPEG",
            quality=88
        )
    if os.path.exists(caminho_original):
        os.remove(caminho_original)
    return caminho_final
# =========================
# CRIAR CLIP COM ZOOM
# =========================
def criar_clip_com_zoom(
    caminho_img,
    duracao,
    zoom_in=True
):
    clip = ImageClip(caminho_img)
    # Pequeno zoom progressivo
    if zoom_in:
        def zoom(t):
            return 1.0 + (0.07 * (t / duracao))
    else:
        def zoom(t):
            return 1.07 - (0.07 * (t / duracao))
    clip = clip.resized(zoom)
    # Mantém a imagem centralizada
    clip = clip.with_position("center")
    clip = clip.with_duration(duracao)
    return clip
# =========================
# CRIAR VÍDEO
# =========================
def criar_video(tema, estilo, duracao):
    session_id = str(uuid.uuid4())[:8]
    roteiro = criar_roteiro(
        tema,
        estilo,
        duracao
    )
    links = buscar_imagens(tema)
    clips = []
    video = None
    try:
        quantidade = min(
            len(links),
            5
        )
        # Tempo de cada imagem
        duracao_imagem = (
            float(duracao) / quantidade
        )
        # Transição entre imagens
        transicao = min(
            0.5,
            duracao_imagem / 3
        )
        tempo_atual = 0
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
            # Cada imagem começa um pouco antes
            # da anterior terminar.
            if i > 0:
                tempo_atual -= transicao
                clip = clip.with_effects([
                    vfx.CrossFadeIn(transicao)
                ])
            clip = clip.with_start(
                tempo_atual
            )
            clips.append(clip)
            tempo_atual += duracao_imagem
        # Monta o vídeo vertical
        video = CompositeVideoClip(
            clips,
            size=(WIDTH, HEIGHT)
        )
        # Garante exatamente a duração escolhida
        video = video.with_duration(
            float(duracao)
        )
        # =================================
        # SEM NARRAÇÃO
        # SEM MÚSICA
        # SEM ÁUDIO
        # =================================
        video = video.without_audio()
        nome_video = f"reel_{session_id}.mp4"
        caminho_video = os.path.join(
            VIDEOS_DIR,
            nome_video
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
        return nome_video, roteiro
    finally:
        if video is not None:
            try:
                video.close()
            except Exception:
                pass
        for clip in clips:
            try:
                clip.close()
            except Exception:
                pass
# =========================
# INTERFACE
# =========================
HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>
<title>Gerador de Reels</title>
<style>
body {
    font-family: Arial, sans-serif;
    background: #111;
    color: white;
    padding: 20px;
}
.container {
    max-width: 500px;
    margin: auto;
}
.caixa {
    background: #1e1e1e;
    padding: 20px;
    border-radius: 15px;
}
h1 {
    text-align: center;
}
input,
select,
button {
    width: 100%;
    padding: 14px;
    margin-top: 8px;
    margin-bottom: 15px;
    border: none;
    border-radius: 8px;
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
    background: #00e676;
}
.resultado {
    background: #292929;
    padding: 15px;
    border-radius: 10px;
    margin-top: 15px;
    word-wrap: break-word;
}
a {
    display: block;
    background: #2196f3;
    color: white;
    padding: 15px;
    margin-top: 15px;
    text-align: center;
    border-radius: 8px;
    text-decoration: none;
    font-weight: bold;
}
a:hover {
    background: #42a5f5;
}
.aviso {
    background: #333;
    padding: 10px;
    border-radius: 8px;
    font-size: 13px;
    margin-bottom: 15px;
    color: #ddd;
}
</style>
</head>
<body>
<div class="container">
<h1>🎬 Gerador de Reels</h1>
<div class="caixa">
<div class="aviso">
🎬 Vídeo vertical profissional.
<br>
🔍 Zoom suave nas imagens.
<br>
✨ Transições entre as imagens.
<br>
🔇 Sem narração.
<br>
🔇 Sem música.
<br>
📝 Sem texto sobre o vídeo.
</div>
<form method="POST">
<label>Tema</label>
<input
    name="tema"
    placeholder="Ex: Como juntar dinheiro"
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
<option value="10">
10 segundos
</option>
<option value="15" selected>
15 segundos
</option>
<option value="30">
30 segundos
</option>
</select>
<button type="submit">
🎬 CRIAR REEL PROFISSIONAL
</button>
</form>
{% if mensagem %}
<div class="resultado">
{{ mensagem }}
</div>
{% endif %}
{% if download %}
<a href="/download/{{ download }}">
⬇️ BAIXAR REEL
</a>
{% endif %}
{% if roteiro %}
<div class="resultado">
<strong>Roteiro:</strong>
<p>{{ roteiro }}</p>
</div>
{% endif %}
</div>
</div>
</body>
</html>
"""
# =========================
# ROTAS
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
                    "Digite um tema válido."
                )
            download, roteiro = criar_video(
                tema,
                estilo,
                duracao
            )
            mensagem = (
                "✅ Reel profissional criado com sucesso!"
            )
        except Exception as erro:
            mensagem = (
                f"❌ Erro ao criar o vídeo: {erro}"
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
    nome = os.path.basename(nome)
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
# =========================
# EXECUÇÃO
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