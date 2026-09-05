import os
import datetime
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import gspread

app = FastAPI()

# Permite conexões do frontend web ou mobile
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuração de Conexão com o Google Sheets usando Variáveis de Ambiente do Render
def conectar_google_sheets():
    try:
        credentials_dict = {
            "type": "service_account",
            "project_id": os.getenv("GOOGLE_PROJECT_ID"),
            "private_key_id": os.getenv("GOOGLE_PRIVATE_KEY_ID"),
            "private_key": os.getenv("GOOGLE_PRIVATE_KEY").replace("\\n", "\n"),
            "client_email": os.getenv("GOOGLE_CLIENT_EMAIL"),
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "auth_uri": "https://accounts.google.com/oauth2/v3/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": os.getenv("GOOGLE_CERT_URL")
        }
        
        gc = gspread.service_account_from_dict(credentials_dict)
        planilha = gc.open(os.getenv("GOOGLE_SHEET_NAME", "Logs Calculadora Cavaco"))
        
        try:
            aba_logs = planilha.worksheet("Logs")
        except gspread.WorksheetNotFound:
            aba_logs = planilha.add_worksheet(title="Logs", rows="500", cols="20")
            aba_logs.append_row(["Data/Hora", "Operador", "Valor p/ Tonelada", "Umidade Base", "Umidade Entregue", "Preço Final p/ Tonelada"])

        return aba_logs
    except Exception as e:
        print(f"Erro ao conectar com o Google Sheets: {e}")
        return None

class DadosCalculo(BaseModel):
    operador: str
    valorTon: float
    umidBase: float
    umidEntregue: float

@app.get("/")
def home():
    return {"status": "API da Calculadora de Cavaco integrada com sucesso!"}

@app.post("/calcular")
def calcular(dados: DadosCalculo):
    porcentagem_agua_base = dados.umidBase / 100.0
    porcentagem_agua_entregue = dados.umidEntregue / 100.0
    
    massa_seca_base = 1.0 - porcentagem_agua_base
    massa_seca_entregue = 1.0 - porcentagem_agua_entregue
    
    if massa_seca_base == 0:
        preco_final = 0.0
    else:
        preco_final = dados.valorTon * (massa_seca_entregue / massa_seca_base)

    # Salvando no Google Sheets automaticamente
    aba_logs = conectar_google_sheets()
    if aba_logs:
        data_hora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        nova_linha = [
            data_hora,
            dados.operador or "Web User",
            f"R$ {dados.valorTon:.2f}",
            f"{dados.umidBase:.2f}%",
            f"{dados.umidEntregue:.2f}%",
            f"R$ {preco_final:.2f}"
        ]
        aba_logs.append_row(nova_linha)

    return {
        "operador": dados.operador or "Web User",
        "precoFinal": round(preco_final, 2)
    }
