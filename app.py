from flask import Flask

app = Flask(name)

@app.route(”/”)
def home():
return chr(79) + chr(75)