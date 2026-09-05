import os
import json
import datetime
import gspread
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Permite que o site HTML converse com a API sem bloqueios de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELO DE DADOS RECEBIDOS DO SITE ---
class CalculoRequest(BaseModel):
    operador: str
    valorTon: float
    umidBase: float
    umidEntregue: float

# --- CONEXÃO COM O GOOGLE SHEETS VIA VARIÁVEIS DE AMBIENTE ---
def conectar_google_sheets():
    try:
        # Se estiver na nuvem (Render), pega das variáveis de ambiente.
        # Se estiver testando no PC, você pode criar um dicionário fixo temporariamente se preferir.
        private_key_env = os.environ.get("GOOGLE_PRIVATE_KEY")
        client_email_env = os.environ.get("GOOGLE_CLIENT_EMAIL")

        if private_key_env and client_email_env:
            google_creds = {
                "type": "service_account",
                "private_key": private_key_env.replace("\\n", "\n"),
                "client_email": client_email_env,
                "token_uri": "https://oauth2.googleapis.com/token",
            }
            gc = gspread.service_account_from_dict(google_creds)
        else:
            # Fallback para o arquivo local se estiver testando no seu computador
            caminho_credenciais = os.path.join(os.path.dirname(__file__), "credentials.json")
            gc = gspread.service_account(filename=caminho_credenciais)
        
        planilha = gc.open("Logs Calculadora Cavaco")
        
        # Aba de Logs
        try:
            aba_logs = planilha.worksheet("Logs")
        except gspread.WorksheetNotFound:
            aba_logs = planilha.add_worksheet(title="Logs", rows="500", cols="20")
            aba_logs.append_row(["Data/Hora", "Operador", "Valor p/ Tonelada", "Umidade Base", "Umidade Entregue", "Preço Final p/ Tonelada"])

        return aba_logs
    except Exception as e:
        print(f"\nErro ao conectar com o Google Sheets: {e}")
        return None

# --- LÓGICA DE CÁLCULO ---
def calcular_preco_ajustado(valor_ton, umidade_base, umidade_entregue):
    porcentagem_agua_base = umidade_base / 100.0
    porcentagem_agua_entregue = umidade_entregue / 100.0
    
    massa_seca_base = 1.0 - porcentagem_agua_base
    massa_seca_entregue = 1.0 - porcentagem_agua_entregue
    
    if massa_seca_base == 0:
        return 0.0
        
    return valor_ton * (massa_seca_entregue / massa_seca_base)

# --- REGISTRO DO LOG ---
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

# --- ROTA DA API PARA O SITE ---
@app.post("/calcular")
def calcular(dados: CalculoRequest):
    aba_logs = conectar_google_sheets()
    if not aba_logs:
        raise HTTPException(status_code=500, detail="Erro ao conectar com o Google Sheets.")

    # Executa o cálculo
    preco_final = calcular_preco_ajustado(dados.valorTon, dados.umidBase, dados.umidEntregue)

    # Salva na planilha do Google
    registrar_log(aba_logs, dados.operador, dados.valorTon, dados.umidBase, dados.umidEntregue, preco_final)

    # Retorna o resultado para o JavaScript do site
    return {
        "operador": dados.operador,
        "precoFinal": preco_final
    }

# --- INICIALIZAÇÃO PARA SUPORTE À NUVEM E LOCAL ---
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
