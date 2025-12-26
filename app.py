from flask import Flask, request, jsonify
import requests
import base64
import os

app = Flask(__name__)

# Variáveis de ambiente do Render
GITHUB_REPO = os.getenv("GITHUB_REPO")       # exemplo: rtza/keys
GITHUB_PATH = os.getenv("GITHUB_PATH")       # exemplo: licencas.txt
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")     # seu token secreto

# URL da API do GitHub
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_PATH}"

@app.route("/validar", methods=["POST"])
def validar():
    dados = request.get_json()
    chave = dados.get("chave")
    hwid = dados.get("hwid")

    # 1. Buscar o arquivo atual no GitHub
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    resposta = requests.get(GITHUB_API_URL, headers=headers)

    if resposta.status_code != 200:
        return jsonify({"valido": False, "mensagem": "Erro interno, tente novamente mais tarde"})

    conteudo = resposta.json()
    linhas = base64.b64decode(conteudo["content"]).decode().splitlines()

    novas_linhas = []
    chave_encontrada = False
    valido = False
    mensagem = "Licença não encontrada"
    dias = 0

    for linha in linhas:
        partes = linha.strip().split("|")
        if partes[0] == chave:
            chave_encontrada = True
            status = partes[1]
            dias = int(partes[2])
            hwid_registrado = partes[3] if len(partes) >= 4 else "null"

            if status == "ativo" and hwid_registrado in ["null", "", None]:
                # Primeira ativação: atualiza HWID e marca como usado
                partes[1] = "usado"
                partes[3] = hwid
                linha = "|".join(partes)
                mensagem = "✅ Licença ativada com sucesso"
                valido = True
            elif status == "usado" and hwid_registrado == hwid:
                # Já ativada antes com esse HWID → não mostra pop-up de novo
                mensagem = "Licença válida"
                valido = True
            elif status == "usado":
                mensagem = "⚠️ Essa licença já foi utilizada em outro dispositivo"
                valido = False
            elif status == "bloqueado":
                mensagem = "🚫 Essa licença foi bloqueada"
                valido = False
            else:
                mensagem = "❌ Licença inválida"
                valido = False
        novas_linhas.append(linha)

    # 2. Se a chave foi encontrada, atualiza no GitHub
    if chave_encontrada:
        novo_conteudo = "\n".join(novas_linhas)
        payload = {
            "message": f"Atualizando chave {chave}",
            "content": base64.b64encode(novo_conteudo.encode()).decode(),
            "sha": conteudo["sha"]
        }
        put_resposta = requests.put(GITHUB_API_URL, headers=headers, json=payload)

        if put_resposta.status_code not in [200, 201]:
            return jsonify({"valido": False, "mensagem": "Erro interno ao salvar alterações"})

        return jsonify({"valido": valido, "mensagem": mensagem, "dias": dias})
    else:
        return jsonify({"valido": False, "mensagem": "Licença não encontrada"})
