from flask import Flask, request, jsonify
import os
import subprocess
from datetime import datetime, timedelta

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LICENCAS_PATH = os.path.join(BASE_DIR, "licencas.txt")

def salvar_licencas(licencas):
    with open(LICENCAS_PATH, "w") as f:
        for licenca in licencas:
            f.write("|".join(licenca) + "\n")

    repo = os.environ.get("GITHUB_REPO")
    user = os.environ.get("GITHUB_USER")
    token = os.environ.get("GITHUB_TOKEN")

    if repo and user and token:
        subprocess.run(["git", "checkout", "main"])
        subprocess.run(["git", "pull", "origin", "main"])
        subprocess.run(["git", "config", "--global", "user.email", "bot@render.com"])
        subprocess.run(["git", "config", "--global", "user.name", "RenderBot"])
        subprocess.run(["git", "add", "licencas.txt"])
        subprocess.run(["git", "commit", "-m", "Atualizando HWID/Status"])
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

    with open(LICENCAS_PATH, "r") as f:
        for linha in f:
            partes = linha.strip().split("|")
            licencas.append(partes)

    for licenca in licencas:
        if licenca[0] == chave:
            status = licenca[1]
            hwid_registrado = licenca[2]
            dias = int(licenca[3])
            data_ativacao = None
            if len(licenca) >= 5 and licenca[4] not in ["", "null"]:
                try:
                    data_ativacao = datetime.strptime(licenca[4], "%Y-%m-%d %H:%M:%S")
                except:
                    try:
                        data_ativacao = datetime.strptime(licenca[4], "%Y-%m-%d")
                    except:
                        data_ativacao = None

            # Bloqueada pelo admin
            if status == "bloqueado":
                resposta = {"valido": False, "mensagem": "❌ Licença bloqueada pelo administrador"}
                break

            # Ativação / uso
            if status in ["ativo", "usado"]:
                # Primeira ativação legítima
                if hwid_registrado == "null":
                    licenca[2] = hwid
                    licenca[1] = "usado"
                    if len(licenca) < 5:
                        licenca.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    else:
                        licenca[4] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    atualizado = True
                    resposta = {"valido": True, "mensagem": "✅ Licença ativada com sucesso", "dias": dias}

                # Validação normal
                elif hwid_registrado == hwid:
                    if data_ativacao:
                        data_final = data_ativacao + timedelta(days=dias)
                        if datetime.now() > data_final:
                            licenca[1] = "bloqueado"
                            atualizado = True
                            resposta = {"valido": False, "mensagem": "❌ Licença expirada/bloqueada pelo servidor"}
                            # 👉 Aqui o app pode apagar o licenca.txt local
                        else:
                            resposta = {"valido": True, "mensagem": "Licença válida", "dias": dias}
                    else:
                        resposta = {"valido": True, "mensagem": "Licença válida", "dias": dias}

                # HWID diferente → bloqueia
                else:
                    licenca[1] = "bloqueado"
                    atualizado = True
                    resposta = {"valido": False, "mensagem": "❌ Licença já usada em outro dispositivo"}
                    # 👉 Aqui também o app pode apagar o licenca.txt local
                break

    if atualizado:
        salvar_licencas(licencas)

    return jsonify(resposta)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
