from flask import Flask, request, jsonify, send_file
import os
import uuid
from moviepy import ColorClip, TextClip, CompositeVideoClip

app = Flask(name)

VIDEO_DIR = “videos”
os.makedirs(VIDEO_DIR, exist_ok=True)

@app.route(”/”)
def home():
return “””
Reel Maker

    <style>
        body {
            font-family: Arial, sans-serif;
            background: #111;
            color: white;
            text-align: center;
            padding: 30px;
        }
        h1 {
            font-size: 36px;
        }
        p {
            font-size: 18px;
        }
        input, select, button {
            width: 90%;
            max-width: 400px;
            padding: 15px;
            margin: 10px;
            border-radius: 10px;
            border: none;
            font-size: 16px;
            box-sizing: border-box;
        }
        input {
            background: white;
            color: black;
        }
        select {
            background: white;
            color: black;
        }
        button {
            background: #ff0050;
            color: white;
            font-weight: bold;
            cursor: pointer;
        }
        button:disabled {
            opacity: 0.6;
            cursor: wait;
        }
        #resultado {
            margin-top: 25px;
            line-height: 1.6;
        }
        a {
            display: inline-block;
            margin-top: 15px;
            padding: 15px 25px;
            background: #00c853;
            color: white;
            border-radius: 10px;
            font-weight: bold;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <h1>🎬 Reel Maker</h1>
    <p>Crie seu vídeo para TikTok e Reels</p>
    <input
        id="tema"
        type="text"
        placeholder="Digite o tema do vídeo"
    >
    <select id="duracao">
        <option value="30">30 segundos</option>
        <option value="45">45 segundos</option>
        <option value="60">60 segundos</option>
    </select>
    <select id="estilo">
        <option value="Motivacional">Motivacional</option>
        <option value="Curiosidades">Curiosidades</option>
        <option value="História">História</option>
        <option value="Dinheiro">Dinheiro</option>
        <option value="Futebol">Futebol</option>
    </select>
    <button id="botao" onclick="gerar()">
        GERAR VÍDEO 🚀
    </button>
    <div id="resultado"></div>
    <script>
    async function gerar() {
        const tema =
            document.getElementById("tema").value.trim();
        const duracao =
            document.getElementById("duracao").value;
        const estilo =
            document.getElementById("estilo").value;
        const botao =
            document.getElementById("botao");
        const resultado =
            document.getElementById("resultado");
        if (!tema) {
            alert("Digite um tema!");
            return;
        }
        botao.disabled = true;
        resultado.innerHTML =
            "⏳ <b>Gerando seu vídeo...</b><br>" +
            "Isso pode levar alguns segundos.";
        try {
            const resposta = await fetch("/gerar", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    tema: tema,
                    duracao: duracao,
                    estilo: estilo
                })
            });
            const dados = await resposta.json();
            if (dados.sucesso) {
                resultado.innerHTML =
                    "✅ <b>Vídeo criado com sucesso!</b><br>" +
                    '<a href="' +
                    dados.download +
                    '" target="_blank">' +
                    "⬇️ BAIXAR VÍDEO" +
                    "</a>";
            } else {
                resultado.innerHTML =
                    "❌ " +
                    (dados.mensagem ||
                    "Erro ao criar o vídeo.");
            }
        } catch (erro) {
            console.error(erro);
            resultado.innerHTML =
                "❌ Erro de conexão com o servidor.";
        }
        botao.disabled = false;
    }
    </script>
</body>
</html>
"""

@app.route(”/gerar”, methods=[“POST”])
def gerar():

try:
    dados = request.get_json()
    if not dados:
        return jsonify({
            "sucesso": False,
            "mensagem": "Nenhum dado recebido."
        }), 400
    tema = dados.get("tema", "").strip()
    duracao = int(
        dados.get("duracao", 30)
    )
    estilo = dados.get(
        "estilo",
        "Motivacional"
    )
    if not tema:
        return jsonify({
            "sucesso": False,
            "mensagem": "Digite um tema."
        }), 400
    if duracao not in [30, 45, 60]:
        duracao = 30
    print("================================")
    print("REEL MAKER")
    print("Tema:", tema)
    print("Duração:", duracao)
    print("Estilo:", estilo)
    print("================================")
    nome = (
        "reel_" +
        uuid.uuid4().hex +
        ".mp4"
    )
    caminho = os.path.join(
        VIDEO_DIR,
        nome
    )
    # =========================
    # CONFIGURAÇÃO DO VÍDEO
    # =========================
    largura = 1080
    altura = 1920
    # =========================
    # FUNDO
    # =========================
    fundo = ColorClip(
        size=(largura, altura),
        color=(17, 17, 17)
    )
    fundo = fundo.with_duration(
        duracao
    )
    # =========================
    # ESTILO
    # =========================
    estilo_texto = TextClip(
        text=estilo.upper(),
        font_size=50,
        color="white",
        size=(900, 150),
        method="caption",
        text_align="center"
    )
    estilo_texto = estilo_texto.with_duration(
        duracao
    )
    estilo_texto = estilo_texto.with_position(
        ("center", 300)
    )
    # =========================
    # TEMA
    # =========================
    texto = TextClip(
        text=tema,
        font_size=90,
        color="white",
        size=(900, 700),
        method="caption",
        text_align="center"
    )
    texto = texto.with_duration(
        duracao
    )
    texto = texto.with_position(
        "center"
    )
    # =========================
    # MONTAR VÍDEO
    # =========================
    video = CompositeVideoClip(
        [
            fundo,
            estilo_texto,
            texto
        ],
        size=(largura, altura)
    )
    # =========================
    # EXPORTAR
    # =========================
    video.write_videofile(
        caminho,
        fps=30,
        codec="libx264",
        audio=False,
        preset="ultrafast",
        threads=2
    )
    video.close()
    fundo.close()
    estilo_texto.close()
    texto.close()
    print(
        "Vídeo criado:",
        caminho
    )
    return jsonify({
        "sucesso": True,
        "mensagem":
            "Vídeo criado com sucesso!",
        "download":
            "/download/" + nome
    })
except Exception as erro:
    print(
        "ERRO AO GERAR VÍDEO:",
        erro
    )
    return jsonify({
        "sucesso": False,
        "mensagem":
            "Erro ao criar vídeo: " +
            str(erro)
    }), 500

@app.route(”/download/”)
def download(nome):

caminho = os.path.join(
    VIDEO_DIR,
    nome
)
if not os.path.exists(caminho):
    return (
        "Vídeo não encontrado.",
        404
    )
return send_file(
    caminho,
    as_attachment=True,
    download_name=nome,
    mimetype="video/mp4"
)

if name == “main”:

port = int(
    os.environ.get(
        "PORT",
        8080
    )
)
app.run(
    host="0.0.0.0",
    port=port
)