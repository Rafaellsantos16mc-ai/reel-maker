import os
import random
import uuid
import requests
import subprocess

from flask import Flask, request, render_template_string, send_file
import imageio_ffmpeg


app = Flask(__name__)


# ============================================================
# CONFIGURAÇÕES
# ============================================================

WIDTH = 1080
HEIGHT = 1920
FPS = 24
DURATION = 60

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

VIDEO_DIR = "videos"
TEMP_DIR = "temp"

os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


# ============================================================
# PAÍSES
# ============================================================

PAISES = {
    "Brasil": "Brazil",
    "Estados Unidos": "United States",
    "Canadá": "Canada",
    "México": "Mexico",
    "Argentina": "Argentina",
    "Chile": "Chile",
    "Peru": "Peru",
    "Colômbia": "Colombia",
    "Costa Rica": "Costa Rica",
    "Islândia": "Iceland",
    "Noruega": "Norway",
    "Suíça": "Switzerland",
    "França": "France",
    "Itália": "Italy",
    "Portugal": "Portugal",
    "Espanha": "Spain",
    "Escócia": "Scotland",
    "Irlanda": "Ireland",
    "Inglaterra": "England",
    "Alemanha": "Germany",
    "Áustria": "Austria",
    "Nova Zelândia": "New Zealand",
    "Austrália": "Australia",
    "Japão": "Japan",
    "China": "China",
    "Coreia do Sul": "South Korea",
    "Indonésia": "Indonesia",
    "Tailândia": "Thailand",
    "Filipinas": "Philippines",
    "Índia": "India",
    "Nepal": "Nepal",
    "África do Sul": "South Africa",
    "Quênia": "Kenya",
    "Marrocos": "Morocco",
    "Tanzânia": "Tanzania",
    "Turquia": "Turkey",
    "Grécia": "Greece",
    "Croácia": "Croatia",
    "Eslovênia": "Slovenia",
    "Finlândia": "Finland",
    "Suécia": "Sweden",
    "Polônia": "Poland"
}


# ============================================================
# INTERFACE
# ============================================================

HTML = """
<!DOCTYPE html>
<html lang="pt-BR">

<head>

<meta charset="UTF-8">

<meta
name="viewport"
content="width=device-width, initial-scale=1.0"
>

<title>Cliff & Nature Reel</title>

<style>

body {
    margin: 0;
    padding: 20px;
    background: #101010;
    color: white;
    font-family: Arial, sans-serif;
}

.container {
    max-width: 500px;
    margin: auto;
}

h1 {
    text-align: center;
    margin-bottom: 8px;
}

.subtitle {
    text-align: center;
    color: #aaa;
    margin-bottom: 25px;
}

.card {
    background: #1c1c1c;
    padding: 20px;
    border-radius: 18px;
}

label {
    display: block;
    margin-bottom: 8px;
    font-weight: bold;
}

select {
    width: 100%;
    padding: 15px;
    border-radius: 10px;
    border: none;
    font-size: 16px;
    margin-bottom: 20px;
    box-sizing: border-box;
}

button {
    width: 100%;
    padding: 16px;
    border: none;
    border-radius: 12px;
    background: white;
    color: #111;
    font-size: 17px;
    font-weight: bold;
    cursor: pointer;
}

button:hover {
    opacity: 0.9;
}

.info {
    margin-top: 20px;
    padding: 15px;
    background: #252525;
    border-radius: 12px;
    color: #bbb;
    font-size: 14px;
    line-height: 1.7;
}

</style>

</head>

<body>

<div class="container">

<h1>🏔️ Cliff & Nature Reel</h1>

<div class="subtitle">
Visões do topo de desfiladeiros e paisagens dramáticas
</div>

<div class="card">

<form method="POST">

<label>Escolha o país</label>

<select name="pais" required>

{% for nome in paises %}

<option value="{{ nome }}">
{{ nome }}
</option>

{% endfor %}

</select>

<button type="submit">
🎬 Criar Reel
</button>

</form>

<div class="info">

🏔️ Topo de penhascos e montanhas<br>
🌊 Visão panorâmica e mar/cachoeira<br>
👁️ Estilo POV (Primeira pessoa)<br>
📱 Vídeo Nativamente Vertical (1080 x 1920)<br>
🔎 Revelação com zoom lento e fluido<br>
⏱️ Até 60 segundos<br>
🔇 Sem áudio<br>
🚫 Sem texto

</div>

</div>

</div>

</body>

</html>
"""


# ============================================================
# BUSCAR VÍDEOS
# ============================================================

def buscar_videos(query):

    if not PEXELS_API_KEY:
        raise Exception(
            "A variável PEXELS_API_KEY não está configurada no Railway."
        )

    url = "https://api.pexels.com/videos/search"

    headers = {
        "Authorization": PEXELS_API_KEY
    }

    params = {
        "query": query,
        "orientation": "portrait",  # Busca diretamente vídeos verticais
        "size": "large",
        "per_page": 80
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=40
    )

    if response.status_code != 200:
        raise Exception(
            f"Erro Pexels {response.status_code}: {response.text}"
        )

    data = response.json()
    return data.get("videos", [])


# ============================================================
# ESCOLHER ARQUIVO DO VÍDEO
# ============================================================

def escolher_arquivo(video):

    arquivos = video.get("video_files", [])
    candidatos = []

    for arquivo in arquivos:
        link = arquivo.get("link")
        if not link:
            continue

        tipo = arquivo.get("file_type")
        if tipo and tipo != "video/mp4":
            continue

        largura = int(arquivo.get("width") or 0)
        altura = int(arquivo.get("height") or 0)

        if largura <= 0 or altura <= 0:
            continue

        candidatos.append(arquivo)

    if not candidatos:
        return None

    candidatos.sort(
        key=lambda x: x.get("width", 0) * x.get("height", 0),
        reverse=True
    )

    # Preferir até resolução Full HD/4K vertical
    for arquivo in candidatos:
        largura = int(arquivo.get("width") or 0)
        altura = int(arquivo.get("height") or 0)

        if largura <= 2160 and altura <= 3840:
            return arquivo

    return candidatos[0]


# ============================================================
# ESCOLHER VÍDEO
# ============================================================

def escolher_video(videos):

    candidatos = []

    palavras_boas = [
        "cliff",
        "edge",
        "top",
        "view",
        "pov",
        "look down",
        "height",
        "mountain",
        "waterfall",
        "ocean",
        "waves",
        "dramatic",
        "steep",
        "rock",
        "nature",
        "landscape",
        "aerial",
        "scenic"
    ]

    palavras_ruins = [
        "city",
        "street",
        "road",
        "car",
        "building",
        "hotel",
        "restaurant",
        "house",
        "indoor",
        "room",
        "pool",
        "boat",
        "ship",
        "people",
        "person",
        "face",
        "selfie"
    ]

    for video in videos:
        duracao = float(video.get("duration") or 0)

        if duracao < 5:
            continue

        arquivo = escolher_arquivo(video)
        if not arquivo:
            continue

        texto = str(video.get("url", "")).lower()
        score = 0

        # Palavras desejadas
        for palavra in palavras_boas:
            if palavra in texto:
                score += 5

        # Palavras indesejadas
        for palavra in palavras_ruins:
            if palavra in texto:
                score -= 15

        if duracao >= DURATION:
            score += 50

        score += min(duracao, 120) / 4

        candidatos.append({
            "video": video,
            "arquivo": arquivo,
            "score": score,
            "duracao": duracao
        })

    if not candidatos:
        return None

    candidatos.sort(key=lambda x: x["score"], reverse=True)
    melhores = candidatos[:8]

    return random.choice(melhores)


# ============================================================
# DOWNLOAD
# ============================================================

def baixar_video(url, destino):

    print("⬇️ Baixando vídeo vertical...")

    response = requests.get(url, stream=True, timeout=180)

    if response.status_code != 200:
        raise Exception(f"Erro ao baixar vídeo: HTTP {response.status_code}")

    tamanho = 0
    with open(destino, "wb") as arquivo:
        for bloco in response.iter_content(chunk_size=1024 * 1024):
            if bloco:
                arquivo.write(bloco)
                tamanho += len(bloco)

    print(f"✅ Download concluído: {tamanho / 1024 / 1024:.1f} MB")

    if tamanho < 100000:
        raise Exception("O vídeo baixado ficou muito pequeno.")


# ============================================================
# CRIAR REEL COM ZOOM DE REVELAÇÃO
# ============================================================

def criar_reel(video_path, output_path):

    print("🎬 Processando vídeo vertical...")
    print("🔎 Aplicando efeito de movimento suave (Zoom)...")

    # Filtro otimizado para vídeo vertical mantendo a proporção 1080x1920
    # com movimento de zoom progressivo e fluido
    filtro = (
        "scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,"
        "zoompan="
        "z='min(zoom+0.0015,1.35)':"
        "x='iw/2-(iw/zoom/2)':"
        "y='ih/2-(ih/zoom/2)':"
        "d=1:"
        "s=1080x1920:"
        "fps=24"
    )

    comando = [
        FFMPEG,
        "-y",
        "-hide_banner",
        "-loglevel", "error",
        "-i", video_path,
        "-map", "0:v:0",
        "-vf", filtro,
        "-t", str(DURATION),
        "-an",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "22",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-threads", "2",
        output_path
    ]

    processo = subprocess.run(
        comando,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=600
    )

    if processo.returncode != 0:
        erro = processo.stderr.strip() or "Erro desconhecido do FFmpeg."
        raise Exception("FFmpeg não conseguiu criar o Reel:\n\n" + erro[-8000:])

    if not os.path.exists(output_path):
        raise Exception("O arquivo final não foi criado.")

    tamanho = os.path.getsize(output_path)
    print(f"✅ Reel criado: {tamanho / 1024 / 1024:.1f} MB")

    if tamanho < 100000:
        raise Exception("O arquivo final ficou muito pequeno.")


# ============================================================
# GERAR VÍDEO
# ============================================================

def gerar_video(pais):

    nome_pais = PAISES.get(pais, pais)

    # Consultas focadas em vista de penhascos, topo de cachoeiras e paisagens dramáticas
    consultas = [
        f"{nome_pais} cliff view pov",
        f"{nome_pais} edge of cliff waterfall",
        f"{nome_pais} mountain edge view",
        f"{nome_pais} ocean cliff height",
        f"{nome_pais} dramatic cliff look down",
        f"{nome_pais} waterfall top view",
        f"{nome_pais} viewpoint mountains cliff"
    ]

    consultas_embaralhadas = consultas[:]
    random.shuffle(consultas_embaralhadas)

    todos_videos = []

    print("======================================")
    print("🏔️ MODO: CLIFF / POV VIEWPOINT")
    print("🌎 PAÍS:", pais)
    print("======================================")

    for consulta in consultas_embaralhadas[:5]:
        print("🔎 Busca:", consulta)
        try:
            videos = buscar_videos(consulta)
            todos_videos.extend(videos)
        except Exception as erro:
            print("⚠️ Erro na busca:", erro)

        if len(todos_videos) >= 100:
            break

    if not todos_videos:
        raise Exception("Nenhum vídeo encontrado.")

    escolhido = escolher_video(todos_videos)

    if not escolhido:
        raise Exception("Não encontrei um vídeo adequado no estilo de penhasco/revelação.")

    video = escolhido["video"]
    arquivo = escolhido["arquivo"]

    video_id = video.get("id", "desconhecido")
    duracao = video.get("duration", 0)
    largura = arquivo.get("width", 0)
    altura = arquivo.get("height", 0)
    url_video = arquivo.get("link")

    if not url_video:
        raise Exception("O Pexels não forneceu o link do vídeo.")

    print("======================================")
    print("🎥 VÍDEO:", video_id)
    print("⏱️ DURAÇÃO:", duracao, "segundos")
    print("📐 RESOLUÇÃO ORIGINAL:", largura, "x", altura)
    print("======================================")

    identificador = uuid.uuid4().hex
    temp_path = os.path.join(TEMP_DIR, f"{identificador}_original.mp4")
    output_name = f"cliff_reel_{pais.lower().replace(' ', '_')}_{identificador[:8]}.mp4"
    output_path = os.path.join(VIDEO_DIR, output_name)

    try:
        baixar_video(url_video, temp_path)
        criar_reel(temp_path, output_path)
        return output_path

    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                print("🗑️ Temporário removido.")
            except Exception as erro:
                print("⚠️ Não foi possível remover temporário:", erro)


# ============================================================
# ROTA PRINCIPAL
# ============================================================

@app.route("/", methods=["GET", "POST"])
def index():

    if request.method == "POST":
        pais = request.form.get("pais")

        if not pais:
            return "Selecione um país.", 400

        try:
            caminho = gerar_video(pais)
            return send_file(
                caminho,
                as_attachment=True,
                download_name="cliff_nature_reel.mp4",
                mimetype="video/mp4"
            )

        except subprocess.TimeoutExpired:
            return """
            <html>
            <body style="background:#111; color:white; font-family:Arial; padding:30px;">
            <h2>❌ Tempo excedido</h2>
            <p>O vídeo demorou muito para ser processado. Tente novamente.</p>
            <br>
            <a href="/" style="color:white;">← Voltar</a>
            </body>
            </html>
            """, 500

        except Exception as erro:
            print("❌ ERRO:", erro)
            return f"""
            <html>
            <body style="background:#111; color:white; font-family:Arial; padding:25px;">
            <h2>❌ Erro ao criar vídeo</h2>
            <pre style="white-space:pre-wrap; background:#222; padding:15px; border-radius:10px; overflow:auto;">{str(erro)}</pre>
            <br>
            <a href="/" style="color:white;">← Voltar</a>
            </body>
            </html>
            """, 500

    return render_template_string(HTML, paises=PAISES.keys())


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health")
def health():
    return {
        "status": "ok",
        "app": "Cliff & Nature Reel",
        "type": "real portrait video",
        "theme": "cliffs, viewpoints and nature reveal",
        "duration": DURATION,
        "resolution": f"{WIDTH}x{HEIGHT}"
    }


# ============================================================
# INICIAR
# ============================================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
