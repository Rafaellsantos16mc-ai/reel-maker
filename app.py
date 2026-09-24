from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Reel Maker</title>
        <style>
            body {
                font-family: Arial;
                background: #111;
                color: white;
                text-align: center;
                padding: 30px;
            }

            input, select, button {
                width: 90%;
                max-width: 400px;
                padding: 15px;
                margin: 10px;
                border-radius: 10px;
                border: none;
                font-size: 16px;
            }

            button {
                background: #ff0050;
                color: white;
                font-weight: bold;
            }
        </style>
    </head>

    <body>

        <h1>🎬 Reel Maker</h1>

        <p>Crie seu vídeo para TikTok e Reels</p>

        <input id="tema" placeholder="Digite o tema do vídeo">

        <select id="duracao">
            <option value="30">30 segundos</option>
            <option value="45">45 segundos</option>
            <option value="60">60 segundos</option>
        </select>

        <select id="estilo">
            <option>Motivacional</option>
            <option>Curiosidades</option>
            <option>História</option>
            <option>Dinheiro</option>
            <option>Futebol</option>
        </select>

        <button onclick="gerar()">GERAR VÍDEO 🚀</button>

        <p id="resultado"></p>

        <script>
        async function gerar() {

            const tema = document.getElementById("tema").value;
            const duracao = document.getElementById("duracao").value;
            const estilo = document.getElementById("estilo").value;

            if (!tema) {
                alert("Digite um tema!");
                return;
            }

            document.getElementById("resultado").innerText =
                "⏳ Gerando seu vídeo...";

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

            document.getElementById("resultado").innerText =
                dados.mensagem;
        }
        </script>

    </body>
    </html>
    """


@app.route("/gerar", methods=["POST"])
def gerar():

    dados = request.json

    tema = dados.get("tema")
    duracao = dados.get("duracao")
    estilo = dados.get("estilo")

    print("Tema:", tema)
    print("Duração:", duracao)
    print("Estilo:", estilo)

    return jsonify({
        "mensagem":
        f"✅ Solicitação recebida! Tema: {tema} | "
        f"{duracao}s | {estilo}"
    })


if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 8080))

    app.run(
        host="0.0.0.0",
        port=port
    )