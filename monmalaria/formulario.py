# app.py

from flask import Flask, render_template, request, redirect, url_for
from firebase_admin import credentials, firestore, initialize_app, get_app
from datetime import datetime
import uuid
import os

# --- CONFIGURAÇÃO DO FIREBASE ---

# Substitua 'serviceAccountKey.json' pelo nome do seu arquivo de credenciais
try:
    # 1. Tenta verificar se o app já está inicializado.
    get_app() 
    
except ValueError:
    # 2. Se o app não estiver inicializado (ValueError), procedemos à inicialização.
    try:
        cred = credentials.Certificate("meuaplicativosaude-firebase-adminsdk-fbsvc-9d8a3954f8.json")
        initialize_app(cred)
        print("Firebase Admin SDK inicializado com sucesso.")
    except FileNotFoundError:
        print("\nERRO CRÍTICO: O arquivo 'serviceAccountKey.json' não foi encontrado.")
        print("Por favor, baixe o arquivo de credenciais da sua conta de serviço do Firebase e coloque-o na mesma pasta.\n")
        # Levanta o erro para parar a execução, pois não podemos conectar sem credenciais.
        raise

# A partir deste ponto, o cliente Firestore é criado, 
# pois garantimos que o initialize_app foi chamado ou já existia.
db = firestore.client()

# Substitua 'YOUR_APP_ID' pelo ID real do seu aplicativo/projeto Firebase.
APP_ID = "meuappsaude" # Mantendo o valor que apareceu no seu erro
COLLECTION_PATH = f"artifacts/{APP_ID}/users"

# --- APLICAÇÃO FLASK ---

app = Flask(__name__)

def generate_unique_id():
    """Gera um UID único para o registro, imitando a criação de um novo documento de usuário."""
    # Gera um UUID simples (o Firebase Auth usa IDs de 28 caracteres; este é um placeholder para cadastros diretos)
    return uuid.uuid4().hex

@app.route('/', methods=['GET'])
def home():
    """Renderiza o formulário de cadastro. O email está preenchido com um placeholder pois o formulário real
    teria o email do Google preenchido pelo JS."""
    # Simulando um email para o campo não editável no formulário web
    return render_template('form.html', email_value="") # Passe string vazia ou remova o argumento

@app.route('/submit_form', methods=['POST'])
def submit_form():
    """Processa a submissão do formulário e salva os dados no Firestore."""
    
    # 1. Coleta e Organização dos Dados do Formulário
    
    # Checkboxes de Múltipla Escolha
    medicacao = request.form.getlist('medicacao')
    comorbidades = request.form.getlist('comorbidade')

    # Trata campos de radio button (retorna 'sim' ou 'nao')
    recebeuOrientacoes_val = request.form.get('recebeuOrientacoes')
    viajouAreaRisco_val = request.form.get('viajouAreaRisco')
    
    # Converte 'sim'/'nao' para booleano (ou deixa como string se o valor for diferente)
    def to_bool_sim_nao(val):
        if val == 'sim':
            return True
        elif val == 'nao':
            return False
        return None 

    # Se o checkbox de "Outra Medicação" estiver marcado, adiciona o valor de texto à lista
    medicacao_outra_desc = request.form.get('medicacaoOutraDescricao')
    if request.form.get('medicacao_outra_flag') == 'Outra_Selecionada' and medicacao_outra_desc:
        medicacao.append(f"Outra: {medicacao_outra_desc}")

    # Cria o objeto de dados a ser salvo
    formData = {
        # --- 1. Identificação e Contato ---
        "nomeCompleto": request.form.get('nomeCompleto'),
        "email": request.form.get('email'), # Valor do campo 'disabled'
        "dataNascimento": request.form.get('dataNascimento'),
        "sexo": request.form.get('sexo'),
        "corRaca": request.form.get('corRaca'),
        "escolaridade": request.form.get('escolaridade'),
        "contato": request.form.get('contato'),
        "cpf": request.form.get('cpf'),
        
        # --- Endereço ---
        "cep": request.form.get('cep'),
        "cidade": request.form.get('cidade'),
        "estado": request.form.get('estado'),
        "endereco": request.form.get('endereco'),
        "numero": request.form.get('numero'),
        "complemento": request.form.get('complemento'),
        
        # --- 2. Dados do Diagnóstico e Tratamento ---
        "tipoMalaria": request.form.get('tipoMalaria'),
        "dataDiagnostico": request.form.get('dataDiagnostico'),
        "unidadeAtendimento": request.form.get('unidadeAtendimento'),
        
        "medicacao": medicacao,
        "recebeuOrientacoes": to_bool_sim_nao(recebeuOrientacoes_val),
        "viajouAreaRisco": to_bool_sim_nao(viajouAreaRisco_val),
        
        # --- 3. Comorbidades ---
        "comorbidades": comorbidades, # Lista de comorbidades marcadas
        
        # --- Metadados do Sistema ---
        "consentido": False,
        "createdAt": firestore.SERVER_TIMESTAMP, # Usa o timestamp do servidor
        "uid": generate_unique_id(),
        "providerId": "cadastro.direto" # Marca o cadastro como direto e não via Google
    }

    # 2. Salvar no Firestore
    try:
        # Usa o 'uid' gerado como ID do documento
        user_doc_ref = db.collection(COLLECTION_PATH).document(formData['uid'])
        user_doc_ref.set(formData)
        
        return redirect(url_for('success', name=formData['nomeCompleto']))
    
    except Exception as e:
        print(f"Erro ao salvar no Firestore: {e}")
        return f"Erro interno ao salvar os dados. Detalhes: {e}", 500

@app.route('/success')
def success():
    """Página de sucesso após o cadastro."""
    name = request.args.get('name', 'Participante')
    return f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head><meta charset="UTF-8"><title>Sucesso</title>
    <style>body {{ font-family: Arial, sans-serif; padding: 50px; text-align: center; }} h1 {{ color: #4CAF50; }}</style>
    </head>
    <body>
        <h1>✅ Cadastro de {name} concluído com sucesso!</h1>
        <p>Os dados foram salvos na coleção: <b>{COLLECTION_PATH}</b> no Firestore.</p>
        <p><a href="/">Realizar novo cadastro</a></p>
    </body>
    </html>
    """

if __name__ == '__main__':
    # Use '0.0.0.0' para acessar o servidor de outras máquinas 
    print(f"\nServidor Flask rodando em: http://127.0.0.1:5000/")
    print(f"Coleção de destino do Firestore: {COLLECTION_PATH}\n")
    app.run(debug=True, host='127.0.0.1', port=5000)