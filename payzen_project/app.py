import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash
from flask import send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from io import BytesIO
import os
import io

# Inicializar o Flask
app = Flask(__name__)

# Definir uma chave secreta para usar flash messages
app.secret_key = 'sua_chave_secreta_aqui'

# Função para criar ou atualizar o banco de dados
def init_db():
    conn = sqlite3.connect('payzen.db')
    cursor = conn.cursor()
    
    # Criar a tabela se não existir
    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS funcionarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_completo TEXT NOT NULL,
            data_nascimento TEXT NOT NULL,
            salario REAL NOT NULL,
            cpf TEXT UNIQUE NOT NULL,
            cargo TEXT NOT NULL,
            numero_conta TEXT NOT NULL,
            horas_trabalhadas REAL DEFAULT 0,
            vale_transporte REAL DEFAULT 0,
            irrf REAL DEFAULT 0,
            inss REAL DEFAULT 0,
            vale_alimentacao REAL DEFAULT 0,
            horas_extras REAL DEFAULT 0
        )
    ''')

    # Verificar e adicionar colunas que estão faltando na tabela existente
    existing_columns = set(row[1] for row in cursor.execute("PRAGMA table_info(funcionarios)").fetchall())
    new_columns = {
        "horas_trabalhadas": "REAL DEFAULT 0",
        "vale_transporte": "REAL DEFAULT 0",
        "irrf": "REAL DEFAULT 0",
        "inss": "REAL DEFAULT 0",
        "vale_alimentacao": "REAL DEFAULT 0",
        "horas_extras": "REAL DEFAULT 0",
    }
    
    for column, definition in new_columns.items():
        if column not in existing_columns:
            cursor.execute(f"ALTER TABLE funcionarios ADD COLUMN {column} {definition}")

    conn.commit()
    conn.close()

# Inicializar o banco ao iniciar o aplicativo
init_db()

# Rota inicial: redireciona para a página de login
@app.route('/')
def home():
    return redirect(url_for('login'))

# Nova rota para exibir a página de cadastro
@app.route('/cadastro')
def cadastro():
    return render_template('cadastro_funcionario.html')

# Rota para cadastrar os funcionários
@app.route('/cadastrar', methods=['POST'])
def cadastrar():
    if request.method == 'POST':
        # Obter dados do formulário
        nome = request.form['nome_completo']
        data_nascimento = request.form['data_nascimento']
        salario = request.form['salario']
        cpf = request.form['cpf']
        cargo = request.form['cargo']
        numero_conta = request.form['numero_conta']
        horas_trabalhadas = request.form.get('horas_trabalhadas', 0)
        vale_transporte = request.form.get('vale_transporte', 0)
        irrf = request.form.get('irrf', 0)
        inss = request.form.get('inss', 0)
        vale_alimentacao = request.form.get('vale_alimentacao', 0)
        horas_extras = request.form.get('horas_extras', 0)

        # Inserir os dados no banco
        conn = sqlite3.connect('payzen.db')
        cursor = conn.cursor()
        try:
            cursor.execute(''' 
                INSERT INTO funcionarios (
                    nome_completo, data_nascimento, salario, cpf, cargo, numero_conta,
                    horas_trabalhadas, vale_transporte, irrf, inss, vale_alimentacao, horas_extras
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (nome, data_nascimento, salario, cpf, cargo, numero_conta,
                  horas_trabalhadas, vale_transporte, irrf, inss, vale_alimentacao, horas_extras))
            conn.commit()
            flash('Cadastro realizado com sucesso!', 'success')
        except sqlite3.IntegrityError:
            flash('Erro: CPF já cadastrado.', 'error')
        finally:
            conn.close()

        return redirect(url_for('cadastro'))
# Rota para exibir os funcionários cadastrados
@app.route('/busca')
def busca_funcionario():
    # Conectar ao banco de dados
    conn = sqlite3.connect('payzen.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Buscar todos os funcionários cadastrados
    cursor.execute('SELECT id, nome_completo, cpf, cargo FROM funcionarios')
    funcionarios = cursor.fetchall()

    conn.close()

    # Passar os funcionários para o template
    return render_template('busca_funcionario.html', funcionarios=funcionarios)

# Rota para visualizar e editar os detalhes de um funcionário
@app.route('/funcionario/<int:id>', methods=['GET', 'POST'])
def visualizar_funcionario(id):
    conn = sqlite3.connect('payzen.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Buscar os dados do funcionário
    cursor.execute('SELECT * FROM funcionarios WHERE id = ?', (id,))
    funcionario = cursor.fetchone()

    if not funcionario:
        conn.close()
        return "Funcionário não encontrado", 404

    if request.method == 'POST':
        # Atualizar os dados do funcionário
        nome = request.form['nome_completo']
        data_nascimento = request.form['data_nascimento']
        salario = request.form['salario']
        cargo = request.form['cargo']
        numero_conta = request.form['numero_conta']
        horas_trabalhadas = request.form.get('horas_trabalhadas', 0)
        vale_transporte = request.form.get('vale_transporte', 0)
        irrf = request.form.get('irrf', 0)
        inss = request.form.get('inss', 0)
        vale_alimentacao = request.form.get('vale_alimentacao', 0)
        horas_extras = request.form.get('horas_extras', 0)

        cursor.execute(''' 
            UPDATE funcionarios
            SET nome_completo = ?, data_nascimento = ?, salario = ?, cargo = ?, numero_conta = ?,
                horas_trabalhadas = ?, vale_transporte = ?, irrf = ?, inss = ?, vale_alimentacao = ?, horas_extras = ?
            WHERE id = ?
        ''', (nome, data_nascimento, salario, cargo, numero_conta, horas_trabalhadas, vale_transporte, irrf, inss, vale_alimentacao, horas_extras, id))
        conn.commit()
        conn.close()
        return redirect(url_for('busca_funcionario'))

    conn.close()
    return render_template('visualizar_funcionario.html', funcionario=funcionario)

# Rota para excluir um funcionário
@app.route('/excluir/<int:id>', methods=['POST'])
def excluir_funcionario(id):
    conn = sqlite3.connect('payzen.db')
    cursor = conn.cursor()
    
    # Deletar o funcionário pelo ID
    cursor.execute('DELETE FROM funcionarios WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('busca_funcionario'))

# Rota para exibir mais informações sobre um funcionário
@app.route('/mais_informacoes/<int:id>', methods=['GET', 'POST'])
def mais_informacoes(id):
    conn = sqlite3.connect('payzen.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Buscar os dados do funcionário pelo ID
    cursor.execute('SELECT * FROM funcionarios WHERE id = ?', (id,))
    funcionario = cursor.fetchone()
    
    if not funcionario:
        conn.close()
        return "Funcionário não encontrado", 404

    if request.method == 'POST':
        # Atualizar informações adicionais (não afetando dados já existentes)
        horas_trabalhadas = request.form.get('horas_trabalhadas', 0)
        vale_transporte = request.form.get('vale_transporte', 0)
        irrf = request.form.get('irrf', 0)
        inss = request.form.get('inss', 0)
        vale_alimentacao = request.form.get('vale_alimentacao', 0)
        horas_extras = request.form.get('horas_extras', 0)

        cursor.execute(''' 
            UPDATE funcionarios
            SET horas_trabalhadas = ?, vale_transporte = ?, irrf = ?, inss = ?, vale_alimentacao = ?, horas_extras = ?
            WHERE id = ?
        ''', (horas_trabalhadas, vale_transporte, irrf, inss, vale_alimentacao, horas_extras, id))
        conn.commit()

        # Fechar a conexão apenas depois de concluir todas as operações
        conn.close()
        return redirect(url_for('busca_funcionario'))

    conn.close()
    return render_template('mais_informacoes.html', funcionario=funcionario)

# Rota para exibir a página de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        # Definir os dados corretos de login
        usuario_correto = 'rh@admin.com'
        senha_correta = 'admin321'

        # Verificar se o email e senha são corretos
        if email == usuario_correto and senha == senha_correta:
            # Redireciona para a página de cadastro após login
            return redirect(url_for('cadastro'))
        else:
            flash('Email ou senha incorretos. Tente novamente.', 'error')
            print('senha incorreta!')  # terminal
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/folha_pagamento_funcionario/<int:id>', methods=['GET'])
def visualizar_folha_pagamento_funcionario(id):
    # Conecta ao banco de dados
    conn = sqlite3.connect('payzen.db')  # Corrigido para o banco correto
    cursor = conn.cursor()

    # Consulta as informações do funcionário
    cursor.execute("SELECT * FROM funcionarios WHERE id = ?", (id,))
    funcionario = cursor.fetchone()

    # Caso o funcionário não exista, redireciona para a busca
    if not funcionario:
        return redirect(url_for('busca_funcionario'))

    # Imprima os dados para verificar a estrutura
    print(funcionario)  # Depuração: veja os dados que estão sendo retornados

    # Verifique se o salário é realmente um número e se está no índice correto
    try:
        salario = float(funcionario[2]) if funcionario[2] else 0.0
    except ValueError:
        salario = 0.0  # Se ocorrer um erro, definimos o salário como 0.0

    horas_trabalhadas = int(funcionario[7]) if funcionario[7] else 0
    vale_transporte = float(funcionario[8]) if funcionario[8] else 0.0
    vale_alimentacao = float(funcionario[10]) if funcionario[10] else 0.0
    irrf = float(funcionario[9]) if funcionario[9] else 0.0
    inss = float(funcionario[11]) if funcionario[11] else 0.0
    horas_extras = int(funcionario[12]) if funcionario[12] else 0

    # Calcular o salário por hora
    salario_por_hora = salario / horas_trabalhadas if horas_trabalhadas else 0

    # Calcular o total a receber
    total_a_receber = salario + vale_transporte + vale_alimentacao - irrf - inss + (horas_extras * salario_por_hora)

    # Converte o resultado em um dicionário
    funcionario_dict = {
        'id': funcionario[0],
        'nome': funcionario[1],
        'salario': salario,
        'salario_por_hora': salario_por_hora,
        'total_a_receber': total_a_receber,
        'horas_trabalhadas': horas_trabalhadas,
        'vale_transporte': vale_transporte,
        'vale_alimentacao': vale_alimentacao,
        'irrf': irrf,
        'inss': inss,
        'horas_extras': horas_extras
    }

    # Gerar o holerite (aqui você pode implementar o formato desejado)
    return render_template('folha_pagamento_funcionario.html', funcionario=funcionario_dict)

@app.route('/gerar_holerite/<int:id>')
def gerar_holerite(id):
    conn = sqlite3.connect('payzen.db')
    cursor = conn.cursor()
    cursor.execute("SELECT nome_completo, salario, horas_trabalhadas, vale_transporte, vale_alimentacao, irrf, inss, horas_extras FROM funcionarios WHERE id = ?", (id,))
    funcionario = cursor.fetchone()
    conn.close()

    if not funcionario:
        return "Funcionário não encontrado", 404

    nome, salario, horas_trabalhadas, vale_transporte, vale_alimentacao, irrf, inss, horas_extras = funcionario
    salario_por_hora = salario / horas_trabalhadas if horas_trabalhadas else 0
    total_vencimentos = salario + vale_transporte + vale_alimentacao + (salario_por_hora * horas_extras)
    total_descontos = irrf + inss
    total_liquido = total_vencimentos - total_descontos

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Cabeçalho
    elements.append(Paragraph("<b>Recibo de Pagamento de Salário</b>", styles['Title']))
    elements.append(Paragraph("Referente ao Mês/Ano: Janeiro-2024", styles['Normal']))
    elements.append(Spacer(1, 12))

    # Dados do Funcionário
    dados_funcionario = [
        ["Nome:", nome],
        ["Salário Base:", f"R$ {salario:.2f}"],
        ["Horas Trabalhadas:", horas_trabalhadas],
        ["Horas Extras:", horas_extras],
    ]
    tabela_dados = Table(dados_funcionario, colWidths=[150, 250])
    tabela_dados.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
    ]))
    elements.append(tabela_dados)
    elements.append(Spacer(1, 12))

    # Tabela de Proventos e Descontos
    tabela_salario = [
        ["Cód.", "Descrição", "Referência", "Proventos", "Descontos"],
        ["001", "Salário Base", f"{horas_trabalhadas}", f"R$ {salario:.2f}", "-"],
        ["002", "Horas Extras", f"{horas_extras}", f"R$ {salario_por_hora * horas_extras:.2f}", "-"],
        ["003", "Vale Transporte", "-", f"R$ {vale_transporte:.2f}", "-"],
        ["004", "Vale Alimentação", "-", f"R$ {vale_alimentacao:.2f}", "-"],
        ["051", "INSS", "-", "-", f"R$ {inss:.2f}"],
        ["054", "IRRF", "-", "-", f"R$ {irrf:.2f}"],
        ["", "", "", "", ""]
    ]
    tabela = Table(tabela_salario, colWidths=[50, 150, 80, 100, 100])
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    elements.append(tabela)
    elements.append(Spacer(1, 12))

    # Resumo Financeiro
    resumo = [
        ["Total Vencimentos:", f"R$ {total_vencimentos:.2f}"],
        ["Total Descontos:", f"R$ {total_descontos:.2f}"],
        ["Líquido a Receber:", f"R$ {total_liquido:.2f}"]
    ]
    tabela_resumo = Table(resumo, colWidths=[200, 200])
    tabela_resumo.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    elements.append(tabela_resumo)
    elements.append(Spacer(1, 30))

    # Assinatura
    elements.append(Paragraph("Declaro ter recebido a importância líquida discriminada neste recibo.", styles['Normal']))
    elements.append(Spacer(1, 40))
    elements.append(Paragraph("___________________________", styles['Normal']))
    elements.append(Paragraph("Assinatura do Funcionário", styles['Normal']))

    doc.build(elements)
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name=f"holerite_{nome}.pdf", mimetype='application/pdf')

if __name__ == '__main__':
    app.run(debug=True)
