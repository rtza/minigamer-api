from flask import Flask, request, jsonify
import requests
import base64

app = Flask(__name__)

# URL da API do GitHub para o arquivo
GITHUB_API_URL = "https://api.github.com/repos/SEU_USUARIO/SEU_REPO/contents/licencas.txt"
GITHUB_TOKEN = "SEU_TOKEN_AQUI"

@app.route("/validar", methods=["POST"])
def validar():
    dados = request.get_json()
    chave = dados.get("chave")
    hwid = dados.get("hwid")

    # 1. Pega o arquivo atual do GitHub
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    resposta = requests.get(GITHUB_API_URL, headers=headers)
    conteudo = resposta.json()
    linhas = base64.b64decode(conteudo["content"]).decode().splitlines()

    novas_linhas = []
    chave_encontrada = False

    for linha in linhas:
        partes = linha.strip().split("|")
        if partes[0] == chave:
            chave_encontrada = True
            status, dias, hwid_registrado = partes[1], partes[2], partes[3] if len(partes) >= 4 else "null"

            if status == "ativo" and hwid_registrado in ["null", "", None]:
                # Atualiza HWID e marca como usado
                partes[1] = "usado"
                partes[3] = hwid
                linha = "|".join(partes)
                mensagem = f"Chave vinculada ao HWID {hwid}"
                valido = True
            elif status == "usado" and hwid_registrado == hwid:
                mensagem = "Licença renovada"
                valido = True
            else:
                mensagem = "HWID diferente ou chave inválida"
                valido = False
        novas_linhas.append(linha)

    # 2. Se atualizou, faz commit no GitHub
    if chave_encontrada:
        novo_conteudo = "\n".join(novas_linhas)
        payload = {
            "message": f"Atualizando chave {chave} com HWID {hwid}",
            "content": base64.b64encode(novo_conteudo.encode()).decode(),
            "sha": conteudo["sha"]
        }
        requests.put(GITHUB_API_URL, headers=headers, json=payload)

        return jsonify({"valido": valido, "mensagem": mensagem, "dias": int(partes[2])})
    else:
        return jsonify({"valido": False, "mensagem": "Chave não encontrada"})
