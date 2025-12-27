from flask import Flask, request, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)

ARQUIVO_CHAVES = "licencas.txt"

def carregar_chaves():
    chaves = {}
    with open(ARQUIVO_CHAVES, "r") as f:
        for linha in f:
            partes = linha.strip().split("|")
            if len(partes) >= 4:
                chave = partes[0]
                status = partes[1]
                hwid = partes[2] if partes[2] != "null" else None
                dias = int(partes[3])
                expira = partes[4] if len(partes) > 4 else None
                chaves[chave] = {
                    "status": status,
                    "hwid": hwid,
                    "dias": dias,
                    "expira": expira
                }
    return chaves

def salvar_chaves(chaves):
    with open(ARQUIVO_CHAVES, "w") as f:
        for chave, info in chaves.items():
            linha = f"{chave}|{info['status']}|{info['hwid'] or 'null'}|{info['dias']}|{info['expira'] or ''}\n"
            f.write(linha)

def dias_restantes(expira_str):
    if not expira_str:
        return 0
    expira = datetime.strptime(expira_str, "%Y-%m-%d %H:%M:%S")
    delta = expira - datetime.now()
    return max(0, delta.days)

@app.route("/validar", methods=["POST"])
def validar():
    data = request.get_json()
    chave = data.get("chave")
    hwid = data.get("hwid")

    chaves = carregar_chaves()
    if chave not in chaves:
        return jsonify({"valido": False, "mensagem": "Chave inválida"})

    info = chaves[chave]

    # Bloqueada
    if info["status"] == "bloqueada":
        return jsonify({"valido": False, "mensagem": "Licença bloqueada"})

    # Primeira ativação
    if info["hwid"] is None or info["hwid"] == "null":
        info["hwid"] = hwid
        expira = datetime.now() + timedelta(days=info["dias"])
        info["expira"] = expira.strftime("%Y-%m-%d %H:%M:%S")
        info["status"] = "usado"
        salvar_chaves(chaves)
        return jsonify({"valido": True, "mensagem": "Licença ativada com sucesso", "dias": info["dias"]})

    # HWID diferente → bloqueia
    if info["hwid"] != hwid:
        info["status"] = "bloqueada"
        salvar_chaves(chaves)
        return jsonify({"valido": False, "mensagem": "Licença bloqueada"})

    # Já ativada → retorna dias restantes
    dias = dias_restantes(info["expira"])
    if dias > 0:
        return jsonify({"valido": True, "mensagem": "Licença já usada", "dias": dias})
    else:
        info["status"] = "bloqueada"
        salvar_chaves(chaves)
        return jsonify({"valido": False, "mensagem": "Licença expirada"})

@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
