from flask import Flask, request, jsonify
import os
import subprocess

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LICENCAS_PATH = os.path.join(BASE_DIR, "licencas.txt")

def salvar_licencas(licencas):
    # Salva localmente no servidor Render
    with open(LICENCAS_PATH, "w") as f:
        for licenca in licencas:
            f.write("|".join(licenca) + "\n")

    # Faz commit e push para o GitHub
    repo = os.environ.get("GITHUB_REPO")
    user = os.environ.get("GITHUB_USER")
    token = os.environ.get("GITHUB_TOKEN")

    if repo and user and token:
        subprocess.run(["git", "config", "--global", "user.email", "bot@render.com"])
        subprocess.run(["git", "config", "--global", "user.name", "RenderBot"])
        subprocess.run(["git", "add", "licencas.txt"])
        subprocess.run(["git", "commit", "-m", "Atualizando HWID"])
        subprocess.run([
            "git", "push",
            f"https://{user}:{token}@github.com/{repo}.git",
            "main"
        ])

@app.route("/validar", methods=["POST"])
def validar():
    dados = request.get_json()
    chave = dados.get("chave")
    hwid = dados.get("hwid")

    licencas = []
    resposta = {"valido": False, "mensagem": "❌ Chave inválida"}
    atualizado = False

    # Lê todas as licenças
    with open(LICENCAS_PATH, "r") as f:
        for linha in f:
            partes = linha.strip().split("|")
            licencas.append(partes)

    # Procura a chave
    for licenca in licencas:
        if licenca[0] == chave and licenca[1] in ["ativo", "usado"]:
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

    # Se houve atualização, salva localmente e envia para GitHub
    if atualizado:
        salvar_licencas(licencas)

    return jsonify(resposta)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
