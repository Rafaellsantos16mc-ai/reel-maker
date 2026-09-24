from flask import Flask, request, jsonify
import os

app = Flask(name)

@app.route(”/”)
def home():
return “””

<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Reel Maker</title>
</head>
<body style="background:#111;color:white;text-align:center;font-family:Arial;padding:30px">
<h1>Reel Maker</h1>
<p>Crie seu video para TikTok e Reels</p>
<input id="tema" placeholder="Digite o tema">
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
<button onclick="gerar()" style="padding:15px;background:#ff0050;color:white;border:0;border-radius:10px">
GERAR VIDEO
</button>
<p id="resultado"></p>
<script>
async function gerar() {
    const tema = document.getElementById("tema").value;
    const duracao = document.getElementById("duracao").value;
    const estilo = document.getElementById("estilo").value;
    if (!tema.trim()) {
        alert("Digite um tema!");
        return;
    }
    document.getElementById("resultado").innerText =
        "Solicitando video...";
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

@app.route(”/gerar”, methods=[“POST”])
def gerar():

dados = request.get_json()
tema = dados.get("tema", "")
duracao = dados.get("duracao", "30")
estilo = dados.get("estilo", "Motivacional")
print("Tema:", tema)
print("Duracao:", duracao)
print("Estilo:", estilo)
return jsonify({
    "sucesso": True,
    "mensagem": (
        "Solicitacao recebida! "
        "Tema: " + tema +
        " | " + duracao +
        " segundos | " + estilo
    )
})

if name == “main”:

port = int(os.environ.get("PORT", "8080"))
app.run(
    host="0.0.0.0",
    port=port
)