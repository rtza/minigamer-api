@app.route("/validar", methods=["POST"])
def validar():
    dados = request.get_json()
    chave = dados.get("chave")
    hwid = dados.get("hwid")

    if not chave or not hwid:
        return jsonify({"valido": False, "mensagem": "Chave ou HWID não fornecidos"})

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

    for linha in linhas:
        partes = linha.strip().split("|")

        if partes[0] == chave:
            chave_encontrada = True
            status = partes[1]
            hwid_registrado = partes[2] if len(partes) >= 3 else "null"

            if status == "ativo" and hwid_registrado in ["null", "", None]:
                partes[1] = "usado"
                if len(partes) < 3:
                    partes.append(hwid)
                else:
                    partes[2] = hwid
                linha = "|".join(partes)
                mensagem = "✅ Licença ativada com sucesso"
                valido = True

            elif status == "usado" and hwid_registrado == hwid:
                mensagem = "Licença válida para este dispositivo"
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

        return jsonify({"valido": valido, "mensagem": mensagem})
    else:
        return jsonify({"valido": False, "mensagem": "Licença não encontrada"})
