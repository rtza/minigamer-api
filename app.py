from flask import Flask, request, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)

# Banco de dados simples em memória (substitua por DB real)
chaves = {
    "ABC123": {"valido": True, "hwid": None, "expira": None}
}

# Função para calcular dias restantes
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

# Rota de ping para acordar Render
@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"status": "ok"})
