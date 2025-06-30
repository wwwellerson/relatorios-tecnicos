from fastapi import FastAPI, HTTPException, Response, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path
from pydantic import BaseModel
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from dotenv import load_dotenv
import pandas as pd
import uuid
from typing import Optional, List
import shutil
import os

# Configurações de ambiente
load_dotenv()
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
REPORTS_FOLDER = os.getenv("REPORTS_FOLDER", "reports_generated")
CSV_DATABASE = os.getenv("CSV_DATABASE", "clientes_motores.csv")

# --- Configuração do Servidor de E-mail ---
conf = ConnectionConfig(
    
    MAIL_USERNAME=os.getenv("MAIL_USERNAME", "default@email.com"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", "senha_padrao"),
    MAIL_FROM=os.getenv("MAIL_FROM", "no-reply@default.com"),
    MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.default.com"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)


# --- Mapa de Tipos e Modelo de Dados ---
DTYPE_MAP = {
    'id_cliente': 'Int64', 'nome_cliente': 'str', 'id_motor': 'str', 'descricao_motor': 'str',
    'local_instalacao': 'str', 'corrente_nominal': 'float64', 'potencia_cv': 'float64',
    'tipo_conexao': 'str', 'tensao_nominal_v': 'float64', 'grupo_tarifario': 'str',
    'telefone_contato': 'str', 'email_responsavel': 'str', 'data_da_instalacao': 'str',
    'id_esp32': 'str', 'observacoes': 'str'
}

class Motor(BaseModel):
    id_cliente: int
    nome_cliente: str
    descricao_motor: str
    local_instalacao: Optional[str] = None
    corrente_nominal: Optional[float] = None
    potencia_cv: Optional[float] = None
    tipo_conexao: Optional[str] = None
    tensao_nominal_v: Optional[float] = None
    grupo_tarifario: Optional[str] = None
    telefone_contato: Optional[str] = None
    email_responsavel: Optional[str] = None
    data_da_instalacao: Optional[str] = None
    id_esp32: Optional[str] = None
    observacoes: Optional[str] = None

# --- Inicialização do FastAPI e CORS ---
app = FastAPI()

origins = [
    "http://localhost:3000",
    "https://*.vercel.app",
    "https://seu-frontend.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"]
)

# --- Endpoints da API ---
@app.get("/")
def ler_raiz():
    return {"mensagem": "Servidor do sistema de relatórios está online!"}

@app.get("/api/clientes")
def get_clientes():
    try:
        df = pd.read_csv(CSV_DATABASE, dtype=DTYPE_MAP)
        df_clientes = df[['id_cliente', 'nome_cliente']].dropna().drop_duplicates(subset=['id_cliente'])
        return df_clientes.to_dict('records')
    except FileNotFoundError:
        return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/registros")
def get_todos_os_registros():
    try:
        df = pd.read_csv(CSV_DATABASE, dtype=DTYPE_MAP)
        return df.fillna("").to_dict('records')
    except FileNotFoundError:
        return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/clientes/{id_cliente}/motores")
def get_motores_por_cliente(id_cliente: int):
    try:
        df = pd.read_csv(CSV_DATABASE, dtype=DTYPE_MAP)
        df_motores = df[df['id_cliente'] == id_cliente][['id_motor', 'descricao_motor']]
        return df_motores.to_dict('records')
    except FileNotFoundError:
        return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/motores")
def adicionar_motor(motor: Motor):
    try:
        novo_motor_dict = motor.dict()
        novo_motor_dict['id_motor'] = str(uuid.uuid4())[:8]
        try:
            df = pd.read_csv(CSV_DATABASE, dtype=DTYPE_MAP)
        except FileNotFoundError:
            df = pd.DataFrame(columns=list(DTYPE_MAP.keys()) + ['id_motor'])
        novo_df = pd.DataFrame([novo_motor_dict])
        df_atualizado = pd.concat([df, novo_df], ignore_index=True)
        df_atualizado.to_csv(CSV_DATABASE, index=False)
        return {"mensagem": "Registro adicionado com sucesso!", "dados": novo_motor_dict}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ocorreu um erro: {str(e)}")

@app.put("/api/motores/{id_motor}")
def atualizar_motor(id_motor: str, motor_atualizado: Motor):
    try:
        df = pd.read_csv(CSV_DATABASE, dtype=DTYPE_MAP)
        df['id_motor'] = df['id_motor'].astype(str)
        if id_motor not in df['id_motor'].values:
            raise HTTPException(status_code=404, detail="Motor não encontrado")
        indice = df.index[df['id_motor'] == id_motor].tolist()[0]
        for chave, valor in motor_atualizado.dict().items():
            if (valor is None or valor == '') and pd.api.types.is_numeric_dtype(df[chave]):
                df.loc[indice, chave] = pd.NA
            else:
                df.loc[indice, chave] = valor
        df.to_csv(CSV_DATABASE, index=False)
        return {"mensagem": "Registro atualizado com sucesso!", "dados": motor_atualizado.dict()}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/motores/{id_motor}")
def remover_motor(id_motor: str):
    try:
        df = pd.read_csv(CSV_DATABASE, dtype=DTYPE_MAP)
        if id_motor not in df['id_motor'].values:
            raise HTTPException(status_code=404, detail="Motor não encontrado")
        df_atualizado = df[df['id_motor'] != id_motor]
        df_atualizado.to_csv(CSV_DATABASE, index=False)
        return Response(status_code=204)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/relatorios-salvos")
def get_relatorios_salvos():
    relatorios = []
    if not os.path.exists(REPORTS_FOLDER):
        return []
    for nome_arquivo in os.listdir(REPORTS_FOLDER):
        if nome_arquivo.endswith(".pdf"):
            try:
                partes = nome_arquivo.replace("Relatorio_", "").replace(".pdf", "").split('_')
                info = {
                    "nome_arquivo": nome_arquivo,
                    "cliente": partes[0].replace("_", " "),
                    "motor": partes[1].replace("_", " "),
                    "data": f"{partes[2]} de {partes[3]}",
                    "tamanho_mb": f"{os.path.getsize(os.path.join(REPORTS_FOLDER, nome_arquivo)) / (1024*1024):.2f} MB"
                }
                relatorios.append(info)
            except Exception:
                relatorios.append({"nome_arquivo": nome_arquivo, "cliente": "Desconhecido"})
    return sorted(relatorios, key=lambda x: x.get('data', ''), reverse=True)

@app.get("/api/relatorios-salvos/{nome_arquivo}")
def get_relatorio_especifico(nome_arquivo: str):
    caminho = Path(REPORTS_FOLDER) / nome_arquivo
    if not caminho.is_file() or not caminho.resolve().parent.samefile(Path(REPORTS_FOLDER).resolve()):
        raise HTTPException(status_code=404, detail="Acesso negado ou arquivo não encontrado.")
    return FileResponse(path=caminho, media_type='application/pdf', filename=nome_arquivo)

@app.delete("/api/relatorios-salvos/{nome_arquivo}")
def excluir_relatorio_especifico(nome_arquivo: str):
    caminho = Path(REPORTS_FOLDER) / nome_arquivo
    if not caminho.is_file() or not caminho.resolve().parent.samefile(Path(REPORTS_FOLDER).resolve()):
        raise HTTPException(status_code=404, detail="Acesso negado ou arquivo não encontrado.")
    try:
        os.remove(caminho)
        return Response(status_code=204)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Não foi possível excluir: {e}")

@app.post("/api/relatorios")
async def gerar_relatorio_endpoint(
    id_motor: str = Form(...),
    arquivo_csv: UploadFile = File(...),
    tem_vazao: bool = Form(False),
    tem_nivel: bool = Form(False)
):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    caminho_temp = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}_{arquivo_csv.filename}")
    try:
        with open(caminho_temp, "wb") as buffer:
            shutil.copyfileobj(arquivo_csv.file, buffer)
        df_brutos = pd.read_csv(caminho_temp, delimiter=';')
        df_registros = pd.read_csv(CSV_DATABASE, dtype=DTYPE_MAP)
        df_registros['id_motor'] = df_registros['id_motor'].astype(str)
        dados_motor = df_registros[df_registros['id_motor'] == id_motor].to_dict('records')
        if not dados_motor:
            raise HTTPException(status_code=404, detail=f"Motor ID {id_motor} não encontrado.")
        checkboxes = {'tem_vazao': tem_vazao, 'tem_nivel': tem_nivel}
        caminho_pdf = pdf_generator.gerar_relatorio_final(df_brutos, dados_motor[0], checkboxes)
        if os.path.exists(caminho_pdf):
            return FileResponse(
                path=caminho_pdf,
                media_type='application/pdf',
                filename=os.path.basename(caminho_pdf))
        else:
            raise HTTPException(status_code=500, detail="O PDF não foi gerado.")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Falha crítica: {str(e)}")
    finally:
        if os.path.exists(caminho_temp):
            os.remove(caminho_temp)

@app.post("/api/relatorios-salvos/{nome_arquivo}/enviar-email")
async def enviar_relatorio_por_email(nome_arquivo: str):
    pasta_relatorios = Path(REPORTS_FOLDER)
    caminho_arquivo = pasta_relatorios / nome_arquivo
    if not caminho_arquivo.is_file():
        raise HTTPException(status_code=404, detail="Arquivo de relatório não encontrado.")
    try:
        nome_cliente = nome_arquivo.replace("Relatorio_", "").split('_')[0].replace("_", " ")
        df = pd.read_csv(CSV_DATABASE, dtype=DTYPE_MAP)
        dados_cliente = df[df['nome_cliente'] == nome_cliente].to_dict('records')
        if not dados_cliente or not dados_cliente[0].get('email_responsavel'):
            raise HTTPException(status_code=404, detail=f"E-mail de contato não encontrado para o cliente {nome_cliente}.")
        email_destinatario = dados_cliente[0]['email_responsavel']
        message = MessageSchema(
            subject=f"Relatório Técnico: {nome_cliente}",
            recipients=[email_destinatario],
            body="Olá,\n\nSegue em anexo o relatório técnico de acompanhamento mensal solicitado.\n\nAtenciosamente,\nSistema de Relatórios.",
            attachments=[str(caminho_arquivo)],
            subtype="plain"
        )
        fm = FastMail(conf)
        await fm.send_message(message)
        return {"message": f"Relatório enviado com sucesso para {email_destinatario}"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Falha ao enviar e-mail: {str(e)}")
