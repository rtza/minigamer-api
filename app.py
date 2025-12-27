from flask import Flask, request, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)

# Banco de dados simples em memória (substitua por DB real)
chaves = {
    "K3YMNO7890": {"valido": True, "hwid": None, "expira": None}
}

def dias_restantes(expira):
    delta = expira - datetime.now()
    return max(0, delta.days)

@app.route("/validar", methods=["POST"])
def validar():
    data = request.get_json()
    chave = data.get("chave")
    hwid = data.get("hwid")

    if chave not in chaves:
        return jsonify({"valido": False, "mensagem": "Chave inválida"})

    info = chaves[chave]

    # Se já bloqueada
    if not info["valido"]:
        return jsonify({"valido": False, "mensagem": "Licença bloqueada"})

    # Primeira ativação
    if info["hwid"] is None:
        info["hwid"] = hwid
        info["expira"] = datetime.now() + timedelta(days=30)
        return jsonify({
            "valido": True,
            "mensagem": "Licença ativada com sucesso",
            "dias": 30
        })

    # Se HWID diferente → bloqueia
    if info["hwid"] != hwid:
        info["valido"] = False
        return jsonify({"valido": False, "mensagem": "Licença bloqueada"})

    # Já ativada → retorna apenas dias restantes
    dias = dias_restantes(info["expira"])
    if dias > 0:
        return jsonify({
            "valido": True,
            "mensagem": "Licença já usada",
            "dias": dias
        })
    else:
        info["valido"] = False
        return jsonify({"valido": False, "mensagem": "Licença expirada"})

@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
