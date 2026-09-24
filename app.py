from flask import Flask, request, jsonify, send_file
import os
import uuid

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
        button {
            background: #ff0050;
            color: white;
            font-weight: bold;
            cursor: pointer;
        }
        button:disabled {
            opacity: 0.6;
        }
        #resultado {
            margin-top: 25px;
        }
        a {
            color: #00ff99;
            font-weight: bold;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <h1>Reel Maker</h1>
    <p>Crie seu video para TikTok e Reels</p>
    <input id="tema" placeholder="Digite o tema do video">
    <select id="duracao">
        <option value="30">30 segundos</option>
        <option value="45">45 segundos</option>
        <option value="60">60 segundos</option>
    </select>
    <select id="estilo">
        <option value="Motivacional">Motivacional</option>
        <option value="Curiosidades">Curiosidades</option>
        <option value="Historia">Historia</option>
        <option value="Dinheiro">Dinheiro</option>
        <option value="Futebol">Futebol</option>
    </select>
    <button id="botao" onclick="gerar()">
        GERAR VIDEO
    </button>
    <p id="resultado"></p>
    <script>
    async function gerar() {
        const tema = document.getElementById("tema").value.trim();
        const duracao = document.getElementById("duracao").value;
        const estilo = document.getElementById("estilo").value;
        const botao = document.getElementById("botao");
        const resultado = document.getElementById("resultado");
        if (!tema) {
            alert("Digite um tema!");
            return;
        }
        botao.disabled = true;
        resultado.innerText = "Gerando seu video... aguarde.";
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
                    "Video criado com sucesso!<br><br>" +
                    '<a href="' + dados.download + '" target="_blank">' +
                    "BAIXAR VIDEO" +
                    "</a>";
            } else {
                resultado.innerText =
                    dados.mensagem || "Erro ao criar video.";
            }
        } catch (erro) {
            console.error(erro);
            resultado.innerText =
                "Erro de conexao com o servidor.";
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
    print("Tema:", tema)
    print("Duracao:", duracao)
    print("Estilo:", estilo)
    nome = "reel_" + uuid.uuid4().hex + ".mp4"
    caminho = os.path.join(
        VIDEO_DIR,
        nome
    )
    # Verifica se o MoviePy esta instalado
    try:
        from moviepy import ColorClip, TextClip, CompositeVideoClip
    except Exception as erro:
        return jsonify({
            "sucesso": False,
            "mensagem": "MoviePy nao esta instalado: " + str(erro)
        }), 500
    largura = 1080
    altura = 1920
    fundo = ColorClip(
        size=(largura, altura),
        color=(17, 17, 17)
    ).with_duration(duracao)
    texto = TextClip(
        text=tema,
        font_size=80,
        color="white",
        size=(900, 700),
        method="caption",
        text_align="center"
    ).with_duration(duracao)
    texto = texto.with_position("center")
    titulo = TextClip(
        text=estilo.upper(),
        font_size=45,
        color="white",
        size=(900, 150),
        method="caption",
        text_align="center"
    ).with_duration(duracao)
    titulo = titulo.with_position(
        ("center", 300)
    )
    video = CompositeVideoClip(
        [
            fundo,
            titulo,
            texto
        ],
        size=(largura, altura)
    )
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
    texto.close()
    titulo.close()
    return jsonify({
        "sucesso": True,
        "mensagem": "Video criado com sucesso!",
        "download": "/download/" + nome
    })
except Exception as erro:
    print("ERRO:", erro)
    return jsonify({
        "sucesso": False,
        "mensagem": "Erro ao criar video: " + str(erro)
    }), 500

@app.route(”/download/”)
def download(nome):

caminho = os.path.join(
    VIDEO_DIR,
    nome
)
if not os.path.exists(caminho):
    return "Video nao encontrado.", 404
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