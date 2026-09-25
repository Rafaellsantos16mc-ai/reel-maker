import os
import random
import uuid
import requests
from flask import Flask, request, render_template_string, send_file
from gtts import gTTS
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
from PIL import Image
# ============================================================
# FLASK
# ============================================================
app = Flask(__name__)
# ============================================================
# CONFIGURAÇÕES
# ============================================================
PORT = int(os.environ.get("PORT", "8080"))
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
# ============================================================
# ROTEIROS
# ============================================================
ROTEIROS = {
    "Motivacional": [
        "Você não precisa mudar sua vida inteira hoje. "
        "Precisa apenas começar. Pequenas decisões repetidas "
        "todos os dias podem mudar completamente o seu futuro. "
        "Enquanto muita gente espera a oportunidade perfeita, "
        "quem começa agora já está criando a própria oportunidade. "
        "Não pare.",
        "Talvez você esteja mais perto do seu objetivo do que imagina. "
        "O problema é que resultados grandes quase nunca aparecem rapidamente. "
        "Continue trabalhando, continue aprendendo e continue tentando. "
        "Um dia você vai olhar para trás e perceber que cada pequeno passo "
        "valeu a pena.",
        "Não espere sentir vontade para começar. "
        "A disciplina aparece justamente nos dias em que a motivação desaparece. "
        "Faça um pouco hoje, faça novamente amanhã e continue. "
        "O segredo não é ser perfeito. "
        "É não desistir."
    ],
    "Dinheiro": [
        "Se você quer melhorar sua vida financeira, comece pelo básico. "
        "Gaste menos do que ganha, evite dívidas desnecessárias "
        "e aprenda uma habilidade que possa aumentar sua renda. "
        "Dinheiro não muda uma pessoa do dia para a noite. "
        "Mas bons hábitos financeiros podem mudar seu futuro.",
        "Ganhar mais dinheiro é importante, mas saber administrar "
        "o que você ganha é fundamental. "
        "Antes de procurar a próxima forma de ganhar dinheiro, "
        "descubra para onde está indo o seu dinheiro hoje. "
        "Pequenas despesas repetidas podem consumir uma grande parte "
        "da sua renda.",
        "Quer começar a construir uma vida financeira melhor? "
        "Pare de pensar apenas em economizar e comece também "
        "a pensar em aumentar sua capacidade de ganhar dinheiro. "
        "Aprenda, desenvolva habilidades e procure novas oportunidades. "
        "Sua renda pode crescer junto com o seu conhecimento."
    ],
    "Curiosidades": [
        "Você sabia que o cérebro humano é capaz de consumir "
        "uma quantidade enorme de energia mesmo quando estamos parados? "
        "Isso acontece porque ele trabalha continuamente, "
        "controlando pensamentos, movimentos, memória e diversas funções "
        "do corpo. É uma das estruturas mais impressionantes da natureza.",
        "Existe uma curiosidade sobre o sono que muita gente desconhece. "
        "Enquanto você dorme, seu cérebro continua trabalhando. "
        "Ele organiza informações, consolida memórias e participa "
        "de vários processos importantes para o funcionamento do organismo.",
        "Você já percebeu como uma música pode trazer uma lembrança antiga "
        "quase instantaneamente? Isso acontece porque música, emoção "
        "e memória estão fortemente conectadas no cérebro. "
        "Por isso algumas músicas conseguem nos transportar "
        "para momentos específicos da nossa vida."
    ],
    "Futebol": [
        "No futebol, uma partida pode mudar completamente em poucos minutos. "
        "Um gol muda a estratégia, um cartão pode alterar o comportamento "
        "de um jogador e uma substituição pode transformar o jogo. "
        "É justamente essa imprevisibilidade que faz milhões de pessoas "
        "acompanharem o esporte.",
        "Você já reparou como os melhores jogadores parecem tomar decisões "
        "muito rapidamente? Isso acontece porque eles treinam repetidamente "
        "situações de jogo. Com experiência, muitas decisões deixam "
        "de ser pensadas conscientemente e passam a acontecer "
        "quase automaticamente.",
        "No futebol, talento ajuda, mas preparação também faz diferença. "
        "Treinamento, posicionamento, leitura de jogo e tomada de decisão "
        "podem transformar completamente o desempenho de um jogador. "
        "Muitas vezes, o que parece facilidade é resultado "
        "de milhares de horas de treino."
    ],
    "História": [
        "A história está cheia de acontecimentos que parecem inacreditáveis hoje. "
        "Impérios surgiram e desapareceram, cidades foram reconstruídas "
        "e invenções mudaram completamente a maneira como as pessoas viviam. "
        "Conhecer o passado ajuda a entender por que o mundo atual é como é.",
        "Muitas das coisas que usamos diariamente possuem uma história "
        "muito mais antiga do que imaginamos. "
        "Algumas invenções passaram por décadas de mudanças "
        "até chegarem ao formato que conhecemos hoje. "
        "A tecnologia atual é resultado de muitas gerações de descobertas.",
        "Grandes acontecimentos históricos raramente acontecem de uma hora para outra. "
        "Normalmente são resultado de pequenas decisões, conflitos, descobertas "
        "e mudanças que acontecem ao longo de muitos anos. "
        "Por isso estudar história é também entender como pequenas mudanças "
        "podem produzir grandes consequências."
    ],
    "Humor": [
        "Eu prometi que hoje ia economizar dinheiro. "
        "Aí entrei em uma loja só para olhar. "
        "Cinco minutos depois estava pensando se realmente precisava daquele produto. "
        "Conclusão: meu dinheiro saiu mais rápido do que eu entrei na loja.",
        "Você já percebeu que quando estamos com pressa tudo dá errado? "
        "A chave desaparece, o celular fica sem bateria "
        "e justamente naquele momento aparece um trânsito enorme. "
        "Parece que o universo escolheu aquele dia "
        "para testar nossa paciência.",
        "O despertador toca e você pensa: só mais cinco minutos. "
        "Quando percebe, já passou meia hora. "
        "Aí você levanta correndo, procurando roupa, celular, chave "
        "e tentando lembrar por que decidiu dormir tarde. "
        "Todo dia é uma nova aventura."
    ],
    "Desenvolvimento pessoal": [
        "Uma das melhores coisas que você pode fazer por você mesmo "
        "é aprender a dizer não. Não para tudo, mas para aquilo "
        "que tira seu tempo, sua energia e seu foco. "
        "Quando você aprende a escolher melhor onde coloca sua atenção, "
        "sua vida começa a mudar.",
        "Você não precisa se comparar com todo mundo. "
        "Cada pessoa está vivendo uma realidade diferente. "
        "Compare você de hoje com quem você era ontem. "
        "Se estiver aprendendo, melhorando e avançando, "
        "mesmo que lentamente, já existe progresso.",
        "Aprender uma habilidade nova pode parecer difícil no começo. "
        "Você erra, esquece e pensa em desistir. "
        "Mas depois de repetir várias vezes, aquilo começa a ficar natural. "
        "O segredo é aceitar ser iniciante antes de tentar ser bom."
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
    introducao = random.choice(introducoes)
    texto_final = introducao + " " + texto
    palavras = texto_final.split()
    if duracao <= 10:
        texto_final = " ".join(
            palavras[:42]
        )
    elif duracao <= 15:
        texto_final = " ".join(
            palavras[:58]
        )
    else:
        texto_final = " ".join(
            palavras[:105]
        )
    return texto_final
# ============================================================
# GERAR NARRAÇÃO
# ============================================================
def gerar_narracao(texto, session_id):
    caminho = os.path.join(
        AUDIO_DIR,
        f"narracao_{session_id}.mp3"
    )
    voz = gTTS(
        text=texto,
        lang="pt-br",
        slow=False
    )
    voz.save(caminho)
    return caminho
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
# ============================================================
# PREPARAR IMAGEM
# ============================================================
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
    with open(
        caminho_original,
        "wb"
    ) as arquivo:
        arquivo.write(
            resposta.content
        )
    with Image.open(
        caminho_original
    ) as imagem:
        imagem = imagem.convert("RGB")
        proporcao_destino = WIDTH / HEIGHT
        proporcao_imagem = (
            imagem.width / imagem.height
        )
        if proporcao_imagem > proporcao_destino:
            nova_altura = HEIGHT
            nova_largura = int(
                imagem.width
                * nova_altura
                / imagem.height
            )
        else:
            nova_largura = WIDTH
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
            quality=85
        )
    if os.path.exists(
        caminho_original
    ):
        os.remove(
            caminho_original
        )
    return caminho_final
# ============================================================
# CRIAR VÍDEO
# ============================================================
def criar_video(tema, estilo, duracao):
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
    caminho_audio = gerar_narracao(
        roteiro,
        session_id
    )
    audio = None
    audio_final = None
    video = None
    clips = []
    audio_cortado = False
    try:
        # =========================
        # CARREGAR NARRAÇÃO
        # =========================
        audio = AudioFileClip(
            caminho_audio
        )
        duracao_audio = float(
            audio.duration
        )
        duracao_final = max(
            float(duracao),
            duracao_audio
        )
        duracao_final = min(
            duracao_final,
            float(duracao) + 5
        )
        # =========================
        # IMAGENS
        # =========================
        quantidade = min(
            len(links),
            5
        )
        if quantidade <= 0:
            raise Exception(
                "Nenhuma imagem disponível."
            )
        duracao_imagem = (
            duracao_final
            / quantidade
        )
        for i in range(quantidade):
            caminho_img = preparar_imagem(
                links[i],
                session_id,
                i
            )
            clip = ImageClip(
                caminho_img
            ).with_duration(
                duracao_imagem
            )
            clips.append(
                clip
            )
        # =========================
        # JUNTAR IMAGENS
        # =========================
        video = concatenate_videoclips(
            clips,
            method="compose"
        )
        if video.duration > duracao_final:
            video = video.subclipped(
                0,
                duracao_final
            )
        # =========================
        # AJUSTAR NARRAÇÃO
        # =========================
        if audio.duration > video.duration:
            audio_final = audio.subclipped(
                0,
                video.duration
            )
            audio_cortado = True
        else:
            audio_final = audio
        # =========================
        # COLOCAR SOMENTE NARRAÇÃO
        # =========================
        video = video.with_audio(
            audio_final
        )
        # =========================
        # SALVAR VÍDEO
        # =========================
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
            audio_codec="aac",
            preset="ultrafast",
            threads=1,
            logger=None
        )
        return nome_video, roteiro
    finally:
        # =========================
        # FECHAR VÍDEO
        # =========================
        if video is not None:
            try:
                video.close()
            except Exception:
                pass
        # =========================
        # FECHAR ÁUDIO CORTADO
        # =========================
        if (
            audio_cortado
            and audio_final is not None
        ):
            try:
                audio_final.close()
            except Exception:
                pass
        # =========================
        # FECHAR ÁUDIO ORIGINAL
        # =========================
        if audio is not None:
            try:
                audio.close()
            except Exception:
                pass
        # =========================
        # FECHAR CLIPS
        # =========================
        for clip in clips:
            try:
                clip.close()
            except Exception:
                pass
        # =========================
        # APAGAR MP3 TEMPORÁRIO
        # =========================
        if os.path.exists(
            caminho_audio
        ):
            try:
                os.remove(
                    caminho_audio
                )
            except Exception:
                pass
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
<title>🎬 Gerador de Reels</title>
<style>
body {
    font-family: Arial, sans-serif;
    background:
        linear-gradient(
            135deg,
            #111827,
            #1f2937
        );
    color: white;
    margin: 0;
    padding: 20px;
}
.container {
    max-width: 600px;
    margin: auto;
}
.card {
    background: #ffffff;
    color: #111827;
    padding: 25px;
    border-radius: 20px;
    box-shadow:
        0 10px 30px
        rgba(0,0,0,0.3);
}
h1 {
    text-align: center;
    margin-bottom: 25px;
}
label {
    display: block;
    margin-top: 15px;
    font-weight: bold;
}
input,
select {
    width: 100%;
    box-sizing: border-box;
    padding: 14px;
    margin-top: 7px;
    border-radius: 10px;
    border: 1px solid #ccc;
    font-size: 16px;
}
button {
    width: 100%;
    padding: 16px;
    margin-top: 25px;
    border: none;
    border-radius: 12px;
    background: #111827;
    color: white;
    font-size: 18px;
    font-weight: bold;
    cursor: pointer;
}
button:hover {
    opacity: 0.9;
}
.aviso {
    background: #f3f4f6;
    padding: 15px;
    border-radius: 10px;
    margin-top: 20px;
    font-size: 14px;
}
.sucesso {
    background: #dcfce7;
    color: #166534;
    padding: 15px;
    border-radius: 10px;
    margin-top: 20px;
}
.erro {
    background: #fee2e2;
    color: #991b1b;
    padding: 15px;
    border-radius: 10px;
    margin-top: 20px;
}
.download {
    display: block;
    text-align: center;
    background: #16a34a;
    color: white;
    text-decoration: none;
    padding: 15px;
    border-radius: 10px;
    margin-top: 15px;
    font-weight: bold;
}
.roteiro {
    background: #f9fafb;
    padding: 15px;
    border-radius: 10px;
    margin-top: 15px;
    line-height: 1.6;
}
</style>
</head>
<body>
<div class="container">
<div class="card">
<h1>🎬 Gerador de Reels</h1>
<form method="POST">
<label>
Tema
</label>
<input
    type="text"
    name="tema"
    placeholder="Ex: dinheiro, futebol, motivação..."
    required>
<label>
Estilo
</label>
<select name="estilo">
<option>Motivacional</option>
<option>Dinheiro</option>
<option>Curiosidades</option>
<option>Futebol</option>
<option>História</option>
<option>Humor</option>
<option>Desenvolvimento pessoal</option>
</select>
<label>
Duração
</label>
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
🎙️ CRIAR REEL
</button>
</form>
<div class="aviso">
🎙️ Narração automática em português.<br>
🎵 Sem música de fundo.<br>
📝 Sem texto sobre o vídeo.
</div>
{% if mensagem %}
{% if download %}
<div class="sucesso">
{{ mensagem }}
</div>
<a
    class="download"
    href="/download/{{ download }}">
⬇️ BAIXAR REEL
</a>
{% else %}
<div class="erro">
{{ mensagem }}
</div>
{% endif %}
{% endif %}
{% if roteiro %}
<div class="roteiro">
<strong>📝 Roteiro utilizado:</strong>
<br><br>
{{ roteiro }}
</div>
{% endif %}
</div>
</div>
</body>
</html>
"""
# ============================================================
# PÁGINA PRINCIPAL
# ============================================================
@app.route(
    "/",
    methods=["GET", "POST"]
)
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
            if duracao not in [10, 15, 30]:
                raise Exception(
                    "Duração inválida."
                )
            download, roteiro = criar_video(
                tema,
                estilo,
                duracao
            )
            mensagem = (
                "✅ Reel criado com sucesso!"
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
# ============================================================
# DOWNLOAD
# ============================================================
@app.route(
    "/download/<nome>"
)
def download_video(nome):
    nome = os.path.basename(
        nome
    )
    caminho = os.path.join(
        VIDEOS_DIR,
        nome
    )
    if not os.path.exists(
        caminho
    ):
        return (
            "Vídeo não encontrado.",
            404
        )
    return send_file(
        caminho,
        as_attachment=True
    )
# ============================================================
# EXECUÇÃO LOCAL
# ============================================================
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=PORT
    )

requirements.txt

Confira se o seu está assim:

Flask>=3.0.0
gunicorn>=23.0.0
gTTS>=2.5.0
moviepy>=2.0.0
Pillow>=10.0.0
requests>=2.31.0
imageio-ffmpeg>=0.5.1

E no Railway, o Start Command:

gunicorn app:app --bind 0.0.0.0:$PORT

Depois de salvar o app.py, faça o Deploy/Commit novamente.

Importante: agora o arquivo obrigatoriamente contém app = Flask(__name__) logo no começo, então o erro Failed to find attribute 'app' in 'app' deve ser eliminado.