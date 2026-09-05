import datetime
import os
import gspread

# --- CONFIGURAÇÕES DO SISTEMA ---
SENHA_ADMIN = "777"

# 1. CONEXÃO COM AS ABAS DO GOOGLE SHEETS
def conectar_google_sheets():
    try:
        caminho_credenciais = os.path.join(os.path.dirname(__file__), "credentials.json")
        gc = gspread.service_account(filename=caminho_credenciais)
        
        planilha = gc.open("Logs Calculadora Cavaco")
        
        # Aba de Logs
        try:
            aba_logs = planilha.worksheet("Logs")
        except gspread.WorksheetNotFound:
            aba_logs = planilha.add_worksheet(title="Logs", rows="500", cols="20")
            aba_logs.append_row(["Data/Hora", "Operador", "Valor p/ Tonelada", "Umidade Base", "Umidade Entregue", "Preço Final p/ Tonelada"])

        # Aba de Usuários
        try:
            aba_usuarios = planilha.worksheet("Usuarios")
        except gspread.WorksheetNotFound:
            aba_usuarios = planilha.add_worksheet(title="Usuarios", rows="100", cols="20")
            aba_usuarios.append_row(["PIN", "Nome"])
            # Usuário padrão
            #aba_usuarios.append_row(["101", "Operador Padrao"])

        return aba_logs, aba_usuarios
    except Exception as e:
        print(f"\nErro ao conectar com o Google Sheets: {e}")
        return None, None

# 2. CADASTRAR NOVO USUÁRIO (PROTEGIDO POR SENHA ADMIN)
def cadastrar_novo_usuario(aba_usuarios):
    print("\n" + "="*40)
    print("       PAINEL DE ADMINISTRAÇÃO")
    print("="*40)
    
    # Validação da Senha Admin
    senha_digitada = input("Digite a Senha do Administrador: ").strip()
    if senha_digitada != SENHA_ADMIN:
        print("Senha de Administrador incorreta! Acesso negado.\n")
        return

    print("\n--- CADASTRO DE NOVO OPERADOR ---")
    
    # Valida PIN (não aceita vazio)
    while True:
        novo_pin = input("Digite o novo PIN (ex: 102): ").strip()
        if not novo_pin:
            print("O PIN não pode ficar em branco!")
            continue
            
        # Verifica se PIN já existe
        registros = aba_usuarios.get_all_records()
        pin_existente = any(str(r.get("PIN")) == novo_pin for r in registros)
        
        if pin_existente:
            print("Este PIN já está cadastrado para outro usuário! Escolha outro.")
        else:
            break

    # Valida Nome (não aceita vazio)
    while True:
        novo_nome = input("Digite o nome do operador: ").strip()
        if not novo_nome:
            print("O nome não pode ficar em branco!")
        else:
            break

    # Salva no Google Sheets
    aba_usuarios.append_row([novo_pin, novo_nome])
    print(f"\nOperador '{novo_nome}' com PIN '{novo_pin}' cadastrado com sucesso na nuvem!\n")

# 3. TELA DE LOGIN
def fazer_login(aba_usuarios):
    while True:
        print("=" * 45)
        print("      CALCULADORA DE CAVACO - LOGIN")
        print("=" * 45)
        print(" [ Digite seu PIN para entrar ]")
        print(" [ Digite 'admin' para cadastrar novo usuário ]")
        print("-" * 45)

        entrada = input("PIN ou Comando: ").strip()

        # Validação de campo vazio no Login
        if not entrada:
            print("Por favor, digite um PIN válido.\n")
            continue

        # Atalho para o painel de admin
        if entrada.lower() == "admin":
            cadastrar_novo_usuario(aba_usuarios)
            continue

        # Consulta os usuários no Google Sheets
        registros = aba_usuarios.get_all_records()
        usuarios = {str(r["PIN"]): str(r["Nome"]) for r in registros}

        if entrada in usuarios:
            nome_operador = usuarios[entrada]
            print(f"\nBem-vindo(a), {nome_operador}!\n")
            return nome_operador
        else:
            print("PIN não encontrado ou incorreto. Tente novamente.\n")

# 4. LÓGICA DE CÁLCULO
def calcular_preco_ajustado(valor_ton, umidade_base, umidade_entregue):
    porcentagem_agua_base = umidade_base / 100.0
    porcentagem_agua_entregue = umidade_entregue / 100.0
    
    massa_seca_base = 1.0 - porcentagem_agua_base
    massa_seca_entregue = 1.0 - porcentagem_agua_entregue
    
    if massa_seca_base == 0:
        return 0.0
        
    return valor_ton * (massa_seca_entregue / massa_seca_base)

# 5. REGISTRO DO LOG
def registrar_log(aba_logs, usuario, valor_ton, umid_base, umid_entregue, preco_pago):
    data_hora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    nova_linha = [
        data_hora,
        usuario,
        f"R$ {valor_ton:.2f}",
        f"{umid_base:.2f}%",
        f"{umid_entregue:.2f}%",
        f"R$ {preco_pago:.2f}"
    ]
    aba_logs.append_row(nova_linha)
    print("\nCálculo salvo com sucesso no Google Sheets!")

# --- EXECUÇÃO PRINCIPAL ---
if __name__ == "__main__":
    aba_logs, aba_usuarios = conectar_google_sheets()

    if aba_logs and aba_usuarios:
        operador = fazer_login(aba_usuarios)

        while True:
            print("-" * 45)
            print("          NOVO CÁLCULO DE CAVACO")
            print("-" * 45)

            try:
                valor_ton = float(input("Valor por Tonelada (R$): "))
                umidade_base = float(input("Umidade Base (%): "))
                umidade_entregue = float(input("Umidade Entregue (%): "))

                preco_final = calcular_preco_ajustado(valor_ton, umidade_base, umidade_entregue)

                print("\n" + "=" * 45)
                print(f" OPERADOR: {operador}")
                print(f" PREÇO A SER PAGO: R$ {preco_final:.2f} / Ton")
                print("=" * 45)

                registrar_log(aba_logs, operador, valor_ton, umidade_base, umidade_entregue, preco_final)

            except ValueError:
                print("\nDigite apenas números válidos.")

            continuar = input("\nDeseja fazer outro cálculo? (s/n): ").strip().lower()
            if continuar != 's':
                print(f"\nAté mais, {operador}!")
                break