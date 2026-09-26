import os

from flask import Flask

app = Flask(name)

PORT = int(os.environ.get(“PORT”, “8080”))

@app.route(”/”)
def home():
return “REEL MAKER ONLINE”

if name == “main”:
app.run(host=“0.0.0.0”, port=PORT)