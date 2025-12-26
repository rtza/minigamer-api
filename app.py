from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return "API funcionando!"

@app.route("/validar", methods=["POST"])
def validar():
    dados = request.get_json()
    chave = dados.get("chave")
    hwid = dados.get("hwid")

    if chave == "CLIENTE1KEY" and hwid == "46417573975452":
        return jsonify({"valido": True, "mensagem": "Chave vinculada ao HWID"})
    else:
        return jsonify({"valido": False, "mensagem": "Chave inválida ou HWID não reconhecido"})
