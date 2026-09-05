def conectar_google_sheets():
    try:
        private_key = os.getenv("GOOGLE_PRIVATE_KEY", "")
        # Remove eventuais aspas e converte caracteres \n em quebras de linha reais
        private_key = private_key.strip('"\'').replace("\\n", "\n")

        credentials_dict = {
            "type": "service_account",
            "client_email": os.getenv("GOOGLE_CLIENT_EMAIL"),
            "private_key": private_key,
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        
        gc = gspread.service_account_from_dict(credentials_dict)
        sheet_name = os.getenv("GOOGLE_SHEET_NAME", "Logs Calculadora Cavaco")
        planilha = gc.open(sheet_name)
        
        try:
            aba_logs = planilha.worksheet("Logs")
        except gspread.WorksheetNotFound:
            aba_logs = planilha.add_worksheet(title="Logs", rows="500", cols="20")
            aba_logs.append_row(["Data/Hora", "Operador", "Valor p/ Tonelada", "Umidade Base", "Umidade Entregue", "Preço Final p/ Tonelada"])

        return aba_logs
    except Exception as e:
        print(f"Erro ao conectar com o Google Sheets: {e}")
        return None
