from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/validar", methods=["POST"])
def validar():
    dados = request.get_json()
    chave = dados.get("chave")
    hwid = dados.get("hwid")

    with open("licencas.txt", "r") as f:
        linhas = f.readlines()

    nova_lista = []
    valido = False
    mensagem = "❌ Chave inválida"
    dias = 30  # padrão

    for linha in linhas:
        partes = linha.strip().split("|")
        if len(partes) < 4:
            continue

        chave_arquivo, status, hwid_arquivo, dias_arquivo = partes

        if chave == chave_arquivo:
            if status == "ativo":
                # primeira ativação
                valido = True
                mensagem = "✅ Licença ativada com sucesso"
                dias = int(dias_arquivo)
                nova_lista.append(f"{chave}|usado|{hwid}|{dias_arquivo}\n")
            elif status == "usado" and hwid == hwid_arquivo:
                # já usada neste PC
                valido = True
                mensagem = "✅ Licença validada neste dispositivo"
                dias = int(dias_arquivo)
                nova_lista.append(linha)
            elif status == "bloqueado":
                mensagem = "🚫 Essa licença foi bloqueada"
                nova_lista.append(linha)
            else:
                mensagem = "⚠️ Essa licença já foi utilizada em outro dispositivo"
                nova_lista.append(linha)
        else:
            nova_lista.append(linha)

    with open("licencas.txt", "w") as f:
        f.writelines(nova_lista)

    return jsonify({"valido": valido, "mensagem": mensagem, "dias": dias})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
