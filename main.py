import os
import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbz717pcAGv8W1VAvHg--Xkh7_sUPrViivf2yUrT3GdTVuOVJQiZWiCTYwV6S0-Tu9H-/exec"

class DadosCalculo(BaseModel):
    operador: str
    valorTon: float
    umidBase: float
    umidEntregue: float

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

    preco_final_arredondado = round(preco_final, 2)

    payload = {
        "operador": dados.operador or "Web User",
        "valorTon": f"R$ {dados.valorTon:.2f}",
        "umidBase": f"{dados.umidBase:.2f}%",
        "umidEntregue": f"{dados.umidEntregue:.2f}%",
        "precoFinal": f"R$ {preco_final_arredondado:.2f}"
    }

    try:
        response = requests.post(GOOGLE_SCRIPT_URL, json=payload)
        print("Resposta do Google Apps Script:", response.text)
    except Exception as e:
        print(f"Erro ao enviar para o Apps Script: {e}")

    return {
        "operador": dados.operador or "Web User",
        "precoFinal": preco_final_arredondado
    }