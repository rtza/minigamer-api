from flask import Flask, request, jsonify
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LICENCAS_PATH = os.path.join(BASE_DIR, "licencas.txt")

@app.route("/validar", methods=["POST"])
def validar():
    dados = request.get_json()
    chave = dados.get("chave")
    hwid = dados.get("hwid")

    licencas = []
    atualizado = False

    # Lê todas as licenças
    with open(LICENCAS_PATH, "r") as f:
        for linha in f:
            partes = linha.strip().split("|")
            licencas.append(partes)

    # Procura a chave
    for licenca in licencas:
        if licenca[0] == chave and licenca[1] == "ativo":
            if licenca[2] == "null":
                # Primeira ativação → grava HWID
                licenca[2] = hwid
                licenca[1] = "usado"
                atualizado = True
                dias = int(licenca[3])
                resposta = {"valido": True, "mensagem": "✅ Licença ativada com sucesso", "dias": dias}
            elif licenca[2] == hwid:
                # Mesmo PC → válido
                dias = int(licenca[3])
                resposta = {"valido": True, "mensagem": "Licença válida", "dias": dias}
            else:
                # HWID diferente → bloqueia
                resposta = {"valido": False, "mensagem": "❌ Licença já usada em outro dispositivo"}
            break
    else:
        resposta = {"valido": False, "mensagem": "❌ Chave inválida"}

    # Se houve atualização, salva o arquivo
    if atualizado:
        with open(LICENCAS_PATH, "w") as f:
            for licenca in licencas:
                f.write("|".join(licenca) + "\n")

    return jsonify(resposta)
