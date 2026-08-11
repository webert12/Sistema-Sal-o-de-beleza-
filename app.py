import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os
import json
import hashlib
import hmac
from io import BytesIO
import urllib.parse
import re
import decimal
import base64
import requests
import streamlit.components.v1 as components

# --- Bibliotecas de Conexão Direta SQL ---
from sqlalchemy import create_engine, text

# --- Relatórios e Segurança ---
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# --- CONFIGURAÇÃO DE SEGURANÇA E HORÁRIO (CORRIGIDO PARA O RENDER) ---
try:
    SALT = st.secrets.get("SECURITY_SALT", "salao_fio_caixa_secure_default_2026")
except Exception:
    SALT = os.getenv("SECURITY_SALT", "salao_fio_caixa_secure_default_2026")

TZ = ZoneInfo("America/Sao_Paulo")

# URL OFICIAL NO RENDER
RENDER_BASE_URL = "https://agendassalo.onrender.com"

def gerar_hash(password: str) -> str:
    """Gera o hash da senha compatível com o padrão do projeto."""
    if not password:
        return ""
    salt_bytes = str(SALT).encode('utf-8')
    senha_bytes = str(password).encode('utf-8')
    return hmac.new(salt_bytes, senha_bytes, hashlib.sha256).hexdigest()

def hash_password(password):
    return gerar_hash(password)

def verificar_senha(senha_digitada, senha_no_banco):
    if not senha_no_banco or not senha_digitada:
        return False
    if hmac.compare_digest(str(senha_digitada), str(senha_no_banco)):
        return True
    hash_calc = gerar_hash(senha_digitada)
    return hmac.compare_digest(hash_calc, str(senha_no_banco))

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Studio & Gestão - Salão de Beleza", layout="wide", page_icon="💇‍♀️")

# --- PERSISTÊNCIA DE SESSÃO VIA URL ---
query_params = st.query_params

# ESTADOS DE SESSÃO INICIAIS
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'usuario_logado' not in st.session_state: st.session_state.usuario_logado = None
if 'eh_admin' not in st.session_state: st.session_state.eh_admin = False
if 'recuperando_senha' not in st.session_state: st.session_state.recuperando_senha = False
if 'tema_escuro' not in st.session_state: st.session_state.tema_escuro = False
if 'meta_mensal' not in st.session_state: st.session_state.meta_mensal = 5000.00

# Recupera sessão persistida pela URL se houver
if not st.session_state.autenticado and "token_sessao" in query_params:
    token_val = query_params["token_sessao"]
    if token_val == "admin_master_session":
        st.session_state.autenticado = True
        st.session_state.usuario_logado = "Administrador"
        st.session_state.eh_admin = True
    elif token_val:
        st.session_state.autenticado = True
        st.session_state.usuario_logado = str(token_val).strip().lower()
        st.session_state.eh_admin = False

# --- OTIMIZAÇÃO DE VELOCIDADE: CACHE DA IMAGEM DE FUNDO ---
@st.cache_data
def get_image_base64(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    return ""

# --- DESIGN & CSS FEMININO ULTRA ELEGANTE ---
def set_background_com_logo(image_path):
    encoded_string = get_image_base64(image_path)

    if st.session_state.tema_escuro:
        bg_style = 'background: linear-gradient(135deg, #1f111a 0%, #2a1523 50%, #150a12 100%) !important;'
        app_bg = "#1f111a"
        input_bg = "rgba(42, 21, 35, 0.85)"
        text_color = "#fce7f3"
        card_bg = "linear-gradient(145deg, rgba(42, 21, 35, 0.85) 0%, rgba(26, 12, 21, 0.95) 100%)"
        border_color = "rgba(244, 114, 182, 0.2)"
    else:
        bg_style = 'background: linear-gradient(135deg, #fdf2f8 0%, #fce7f3 40%, #fbcfe8 100%) !important;'
        app_bg = "#fdf2f8"
        input_bg = "rgba(255, 255, 255, 0.9)"
        text_color = "#831843"
        card_bg = "linear-gradient(145deg, rgba(255, 255, 255, 0.92) 0%, rgba(253, 242, 248, 0.98) 100%)"
        border_color = "rgba(244, 114, 182, 0.3)"

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Playfair+Display:ital,wght@0,600;0,700;1,600&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');

        .stApp {{
            {bg_style}
            background-color: {app_bg} !important;
            background-attachment: fixed !important;
            color: {text_color} !important;
            font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif !important;
        }}

        html, body, p, label, div {{
            color: {text_color};
            font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
        }}

        h1, h2, h3, h4, h5, h6 {{
            color: #831843 !important;
            font-family: 'Playfair Display', Georgia, serif !important;
            font-weight: 700 !important;
            letter-spacing: -0.3px !important;
        }}

        ::-webkit-scrollbar {{ width: 8px; height: 8px; }}
        ::-webkit-scrollbar-track {{ background: rgba(251, 207, 232, 0.3); }}
        ::-webkit-scrollbar-thumb {{ background: #f472b6; border-radius: 999px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: #db2777; }}

        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div,
        input, select, textarea,
        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input,
        [data-testid="stDateInput"] input {{
            background-color: {input_bg} !important;
            color: #831843 !important;
            -webkit-text-fill-color: #831843 !important;
            border: 1px solid {border_color} !important;
            border-radius: 14px !important;
            padding: 10px 14px !important;
            font-size: 0.95rem !important;
            transition: all 0.25s ease !important;
            box-shadow: 0 2px 8px rgba(244, 114, 182, 0.08) !important;
        }}

        input:focus, div[data-baseweb="input"] > div:focus-within, div[data-baseweb="select"] > div:focus-within {{
            border-color: #ec4899 !important;
            box-shadow: 0 0 14px rgba(236, 72, 153, 0.25) !important;
        }}

        div[data-testid="stForm"] {{
            border: 1px solid rgba(244, 114, 182, 0.3) !important;
            border-radius: 22px !important;
            padding: 24px !important;
            background: {card_bg} !important;
            backdrop-filter: blur(12px) !important;
            box-shadow: 0 12px 35px rgba(219, 39, 119, 0.08) !important;
        }}

        div[data-testid="stPopoverBody"] {{
            background-color: #fff0f6 !important;
            border: 1px solid rgba(236, 72, 153, 0.4) !important;
            border-radius: 20px !important;
            box-shadow: 0 20px 50px rgba(131, 24, 67, 0.18) !important;
            z-index: 999999 !important;
            padding: 18px !important;
        }}
        div[data-testid="stPopoverBody"] * {{ color: #831843 !important; }}

        .kpi-card-v2 {{ 
            background: {card_bg}; 
            border: 1px solid rgba(244, 114, 182, 0.25); 
            border-radius: 20px; 
            padding: 22px; 
            box-shadow: 0 10px 25px -5px rgba(219, 39, 119, 0.08); 
            backdrop-filter: blur(12px);
            height: 100%; 
            display: flex; 
            flex-direction: column; 
            justify-content: space-between; 
            transition: all 0.3s ease;
        }}
        .kpi-title-v2 {{ font-size: 0.88rem; color: #9d174d !important; font-weight: 600; margin-bottom: 8px; display: flex; align-items: center; gap: 8px; }}
        .kpi-value-v2 {{ font-size: 1.85rem; font-weight: 800; margin-bottom: 8px; letter-spacing: -0.8px; color: #831843 !important; }}
        .kpi-val-green {{ color: #059669 !important; }}
        .kpi-val-red {{ color: #e11d48 !important; }}
        .kpi-val-pink {{ color: #db2777 !important; }}
        .kpi-val-purple {{ color: #9333ea !important; }}
        .kpi-val-gold {{ color: #d97706 !important; }}
        .kpi-perc {{ font-size: 0.82rem; font-weight: 700; display: flex; align-items: center; gap: 4px; }}
        .perc-up {{ color: #059669 !important; }}
        .perc-down {{ color: #e11d48 !important; }}
        .perc-neutral {{ color: #9d174d !important; }}

        .ui-card {{ 
            background: {card_bg}; 
            border: 1px solid rgba(244, 114, 182, 0.25); 
            border-radius: 22px; 
            padding: 26px; 
            margin-bottom: 20px; 
            box-shadow: 0 12px 30px -5px rgba(219, 39, 119, 0.08); 
            backdrop-filter: blur(12px);
        }}

        .login-card {{ 
            background: linear-gradient(180deg, #ffffff 0%, #fdf2f8 100%); 
            border: 1px solid rgba(236, 72, 153, 0.3); 
            border-radius: 28px; 
            padding: 42px 36px; 
            box-shadow: 0 25px 60px -10px rgba(219, 39, 119, 0.2); 
            max-width: 480px; 
            margin: 0 auto; 
        }}
        .login-brand-wrapper {{ text-align: center; margin-bottom: 24px; }}
        .login-badge-icon {{
            display: inline-flex; align-items: center; justify-content: center;
            width: 75px; height: 75px;
            background: linear-gradient(135deg, #f472b6 0%, #db2777 100%);
            border-radius: 24px; font-size: 36px; margin-bottom: 16px;
            box-shadow: 0 12px 28px rgba(219, 39, 119, 0.35);
        }}
        .login-title {{ 
            color: #831843 !important; font-size: 2.3rem !important; font-weight: 800 !important; 
            letter-spacing: -1px !important; margin-bottom: 6px !important; text-align: center; 
        }}
        .login-subtitle {{ color: #9d174d !important; font-size: 0.95rem !important; text-align: center; margin-bottom: 26px; font-weight: 500; }}

        .stButton > button, [data-testid="stDownloadButton"] > button {{
            background: linear-gradient(135deg, #fbcfe8 0%, #f472b6 100%) !important;
            color: #831843 !important;
            border: none !important;
            border-radius: 14px !important;
            font-weight: 700 !important;
            padding: 10px 16px !important;
            transition: all 0.25s ease !important;
            width: 100% !important;
            min-height: 46px !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 8px !important;
            font-size: 0.92rem !important;
            box-shadow: 0 4px 14px rgba(244, 114, 182, 0.3) !important;
        }}

        .stButton > button[kind="primary"] {{ 
            background: linear-gradient(135deg, #ec4899 0%, #db2777 100%) !important; 
            color: #ffffff !important; border: none !important; 
            box-shadow: 0 6px 20px rgba(219, 39, 119, 0.4) !important; 
        }}

        .stTabs [data-baseweb="tab-list"] {{ 
            gap: 10px; background: rgba(253, 242, 248, 0.8); padding: 8px; border-radius: 20px;
            border: 1px solid rgba(244, 114, 182, 0.3); backdrop-filter: blur(12px);
            display: flex; justify-content: center; margin-bottom: 24px;
        }}
        .stTabs [data-baseweb="tab"] {{ 
            background-color: transparent !important; border-radius: 14px !important; border: none !important; 
            padding: 10px 20px !important; color: #9d174d !important; font-size: 0.95rem; font-weight: 600;
        }}
        .stTabs [aria-selected="true"] {{ 
            background: linear-gradient(135deg, #f472b6 0%, #ec4899 100%) !important; 
            color: #ffffff !important; font-weight: 700; 
            box-shadow: 0 4px 15px rgba(236, 72, 153, 0.3) !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

set_background_com_logo("logo.png")

st.markdown("""
    <style>
        footer, [data-testid="stFooter"], .stFooter, #MainMenu, [data-testid="stToolbar"], [data-testid="stDecoration"], .stDeployButton { display: none !important; }
        [data-testid="collapsedControl"] { display: none !important; }
        .main .block-container { padding-top: 1.5rem !important; padding-bottom: 2rem !important; }
    </style>
""", unsafe_allow_html=True)

# --- CONEXÃO BANCO DE DADOS (CORRIGIDO PARA O RENDER) ---
DB_URL = os.getenv("DB_URL")

if not DB_URL:
    try:
        if "DB_URL" in st.secrets:
            DB_URL = st.secrets["DB_URL"]
    except Exception:
        pass

if not DB_URL:
    st.error("❌ ERRO CRÍTICO: Variável 'DB_URL' não encontrada nas Variáveis de Ambiente do Render nem nos Secrets.")
    st.stop()

@st.cache_resource
def init_connection(url):
    return create_engine(url, pool_pre_ping=True, pool_size=10, max_overflow=20, pool_recycle=1800)

try:
    engine = init_connection(DB_URL)
except Exception as e:
    st.error(f"Erro de conexão com o banco de dados: {e}")
    st.stop()

# --- INICIALIZAÇÃO DO BANCO ---
@st.cache_resource
def inicializar_banco():
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.execute(text("SET SESSION CHARACTERISTICS AS TRANSACTION READ WRITE;"))
        conn.execute(text("CREATE TABLE IF NOT EXISTS admin_config (id INT PRIMARY KEY, hash1 TEXT NOT NULL, hash2 TEXT NOT NULL, url_sistema TEXT);"))
        conn.execute(text("ALTER TABLE admin_config ADD COLUMN IF NOT EXISTS url_sistema TEXT;"))
        conn.execute(text("CREATE TABLE IF NOT EXISTS usuarios (id TEXT PRIMARY KEY, senha TEXT NOT NULL, email TEXT, tipo TEXT, vencimento TEXT, status TEXT, whatsapp TEXT);"))
        conn.execute(text("ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS whatsapp TEXT;"))
        conn.execute(text("CREATE TABLE IF NOT EXISTS servicos (id SERIAL PRIMARY KEY, usuario_id TEXT NOT NULL, nome TEXT NOT NULL, preco NUMERIC NOT NULL);"))
        conn.execute(text("CREATE TABLE IF NOT EXISTS fluxo_caixa (id SERIAL PRIMARY KEY, usuario_id TEXT NOT NULL, data TEXT NOT NULL, tipo TEXT NOT NULL, descricao TEXT NOT NULL, valor NUMERIC NOT NULL);"))
        conn.execute(text("CREATE TABLE IF NOT EXISTS agendamentos (id SERIAL PRIMARY KEY, usuario_id TEXT NOT NULL, cliente_nome TEXT NOT NULL, cliente_contato TEXT, servico_nome TEXT NOT NULL, data TEXT NOT NULL, hora TEXT NOT NULL);"))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS clientes_mensais (
                id SERIAL PRIMARY KEY,
                usuario_id TEXT NOT NULL,
                nome_cliente TEXT NOT NULL,
                telefone TEXT,
                servicos_feitos INT DEFAULT 0,
                valor_devido NUMERIC DEFAULT 0.0,
                status_divida TEXT DEFAULT 'Pendente'
            );
        """))
    return True

try:
    inicializar_banco()
except Exception as e:
    st.error(f"Erro na criação de tabelas: {e}")
    st.stop()

# --- FUNÇÕES DE PERSISTÊNCIA & CACHE ---
def limpar_cache_sessao():
    if "dados_carregados_sessao" in st.session_state:
        del st.session_state["dados_carregados_sessao"]

@st.cache_data(ttl=600)
def carregar_admin_hashes():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT hash1, hash2, url_sistema FROM admin_config WHERE id = 1")).fetchone()
            if result: return result[0], result[1], result[2]
    except Exception: pass
    return None, None, None

def salvar_admin_hashes(password1, password2, url=""):
    try:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.execute(text("SET SESSION CHARACTERISTICS AS TRANSACTION READ WRITE;"))
            conn.execute(text("""
                INSERT INTO admin_config (id, hash1, hash2, url_sistema) VALUES (1, :h1, :h2, :url)
                ON CONFLICT (id) DO UPDATE SET hash1 = EXCLUDED.hash1, hash2 = EXCLUDED.hash2, url_sistema = EXCLUDED.url_sistema
            """), {"h1": password1, "h2": password2, "url": url})
        carregar_admin_hashes.clear()
    except Exception as e: st.error(f"Erro: {e}")

def atualizar_url_sistema(url):
    try:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.execute(text("SET SESSION CHARACTERISTICS AS TRANSACTION READ WRITE;"))
            conn.execute(text("UPDATE admin_config SET url_sistema = :url WHERE id = 1"), {"url": url})
        carregar_admin_hashes.clear()
    except Exception: pass

@st.cache_data(ttl=300)
def carregar_usuarios():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT id, senha, email, tipo, vencimento, status, whatsapp FROM usuarios"))
            rows = result.fetchall()
            if rows: 
                return {
                    str(row[0]).strip().lower(): {
                        "id": str(row[0]).strip().lower(), 
                        "senha": row[1], 
                        "email": row[2], 
                        "tipo": row[3], 
                        "vencimento": row[4], 
                        "status": row[5],
                        "whatsapp": row[6] if len(row) > 6 and row[6] is not None else ""
                    } for row in rows
                }
    except Exception: pass
    return {}

def salvar_usuarios(usuarios_dict):
    if not usuarios_dict: return
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.execute(text("SET SESSION CHARACTERISTICS AS TRANSACTION READ WRITE;"))
        for k, v in usuarios_dict.items():
            user_clean = str(k).strip().lower()
            venc_val = v["vencimento"]
            if hasattr(venc_val, 'strftime'):
                venc_str = venc_val.strftime('%Y-%m-%d')
            else:
                venc_str = str(venc_val) if venc_val else datetime.now(TZ).strftime('%Y-%m-%d')

            senha_val = str(v["senha"])
            if not senha_val.startswith("pbkdf2_sha256$") and len(senha_val) < 60:
                senha_val = gerar_hash(senha_val)

            conn.execute(text("""
                INSERT INTO usuarios (id, senha, email, tipo, vencimento, status, whatsapp) 
                VALUES (:id, :senha, :email, :tipo, :vencimento, :status, :whatsapp)
                ON CONFLICT (id) DO UPDATE SET 
                    senha = EXCLUDED.senha, 
                    email = EXCLUDED.email, 
                    tipo = EXCLUDED.tipo, 
                    vencimento = EXCLUDED.vencimento, 
                    status = EXCLUDED.status,
                    whatsapp = EXCLUDED.whatsapp
            """), {
                "id": user_clean, 
                "senha": senha_val, 
                "email": v.get("email", ""), 
                "tipo": v["tipo"], 
                "vencimento": venc_str, 
                "status": v["status"],
                "whatsapp": v.get("whatsapp", "")
            })
    carregar_usuarios.clear()

@st.cache_data(ttl=300)
def carregar_servicos_por_salao(salao_id):
    salao_id_clean = urllib.parse.unquote(str(salao_id)).strip().lower() if salao_id else "padrao"
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT nome, preco FROM servicos WHERE usuario_id = :user ORDER BY nome ASC"), {"user": salao_id_clean})
            rows = result.fetchall()
            if rows: return {row[0]: float(row[1]) for row in rows}
    except Exception: pass
    return {"Escova & Penteado": 60.00, "Manicure & Pedicure": 50.00, "Corte Feminino": 80.00, "Hidratação Profunda": 120.00, "Design de Sobrancelhas": 45.00}

def carregar_servicos(usuario_logado=None):
    usuario = usuario_logado or st.session_state.get("usuario_logado", "padrao")
    return carregar_servicos_por_salao(usuario)

def salvar_ou_atualizar_servico(nome_antigo, nome_novo, preco):
    usuario = str(st.session_state.get("usuario_logado", "padrao")).strip().lower()
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.execute(text("SET SESSION CHARACTERISTICS AS TRANSACTION READ WRITE;"))
        if nome_antigo and nome_antigo != "➕ Cadastrar Novo Serviço":
            conn.execute(text("UPDATE servicos SET nome = :novo, preco = :preco WHERE usuario_id = :user AND nome = :antigo"), {"novo": nome_novo, "preco": float(preco), "user": usuario, "antigo": nome_antigo})
        else:
            conn.execute(text("INSERT INTO servicos (usuario_id, nome, preco) VALUES (:user, :nome, :preco)"), {"user": usuario, "nome": nome_novo, "preco": float(preco)})
    carregar_servicos_por_salao.clear()
    limpar_cache_sessao()

def deletar_servico_banco(nome):
    usuario = str(st.session_state.get("usuario_logado", "padrao")).strip().lower()
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.execute(text("SET SESSION CHARACTERISTICS AS TRANSACTION READ WRITE;"))
        conn.execute(text("DELETE FROM servicos WHERE usuario_id = :user AND nome = :nome"), {"user": usuario, "nome": nome})
    carregar_servicos_por_salao.clear()
    limpar_cache_sessao()

@st.cache_data(ttl=180)
def carregar_fluxo_por_usuario(usuario):
    usuario_clean = str(usuario).strip().lower()
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT id, data, tipo, descricao, valor FROM fluxo_caixa WHERE usuario_id = :user ORDER BY id DESC"), {"user": usuario_clean})
            rows = result.fetchall()
            if rows:
                df = pd.DataFrame(rows, columns=['id', 'Data', 'Tipo', 'Descrição', 'Valor'])
                df['Data'] = pd.to_datetime(df['Data'])
                return df
    except Exception: pass
    return pd.DataFrame(columns=["id", "Data", "Tipo", "Descrição", "Valor"])

def carregar_fluxo(usuario_logado=None):
    usuario = usuario_logado or st.session_state.get("usuario_logado", "padrao")
    return carregar_fluxo_por_usuario(usuario)

def inserir_movimentacao_direta(tipo, descricao, valor, data_input):
    usuario = str(st.session_state.get("usuario_logado", "padrao")).strip().lower()
    data_str = data_input.strftime('%Y-%m-%d') if hasattr(data_input, 'strftime') else str(data_input)
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.execute(text("SET SESSION CHARACTERISTICS AS TRANSACTION READ WRITE;"))
        conn.execute(text("INSERT INTO fluxo_caixa (usuario_id, data, tipo, descricao, valor) VALUES (:user, :data, :tipo, :descricao, :valor)"), {"user": usuario, "data": data_str, "tipo": tipo, "descricao": descricao, "valor": float(valor)})
    carregar_fluxo_por_usuario.clear()
    limpar_cache_sessao()

def dar_baixa_fiado_direta(id_registro, nova_descricao):
    usuario = str(st.session_state.get("usuario_logado", "padrao")).strip().lower()
    data_hoje = datetime.now(TZ).strftime('%Y-%m-%d')
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.execute(text("SET SESSION CHARACTERISTICS AS TRANSACTION READ WRITE;"))
        conn.execute(text("UPDATE fluxo_caixa SET tipo = 'Entrada', data = :data, descricao = :desc WHERE id = :id AND usuario_id = :user"), {"data": data_hoje, "desc": nova_descricao, "id": int(id_registro), "user": usuario})
    carregar_fluxo_por_usuario.clear()
    limpar_cache_sessao()

def deletar_movimentacao_fluxo(id_registro):
    usuario = str(st.session_state.get("usuario_logado", "padrao")).strip().lower()
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.execute(text("SET SESSION CHARACTERISTICS AS TRANSACTION READ WRITE;"))
        conn.execute(text("DELETE FROM fluxo_caixa WHERE id = :id AND usuario_id = :user"), {"id": int(id_registro), "user": usuario})
    carregar_fluxo_por_usuario.clear()
    limpar_cache_sessao()

@st.cache_data(ttl=120)
def carregar_agendamentos_por_usuario_direto(usuario):
    usuario_clean = str(usuario).strip().lower()
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT id, cliente_nome, cliente_contato, servico_nome, data, hora FROM agendamentos WHERE usuario_id = :user ORDER BY data ASC, hora ASC"), {"user": usuario_clean})
            rows = result.fetchall()
            if rows: return pd.DataFrame(rows, columns=["id", "Cliente", "Contato/WhatsApp", "Serviço", "Data", "Horário"])
    except Exception: pass
    return pd.DataFrame(columns=["id", "Cliente", "Contato/WhatsApp", "Serviço", "Data", "Horário"])

def carregar_agendamentos(usuario_logado=None):
    usuario = usuario_logado or st.session_state.get("usuario_logado", "padrao")
    return carregar_agendamentos_por_usuario_direto(usuario)

def deletar_agendamento(id_agendamento):
    usuario = str(st.session_state.get("usuario_logado", "padrao")).strip().lower()
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.execute(text("SET SESSION CHARACTERISTICS AS TRANSACTION READ WRITE;"))
        conn.execute(text("DELETE FROM agendamentos WHERE id = :id AND usuario_id = :user"), {"id": int(id_agendamento), "user": usuario})
    carregar_agendamentos_por_usuario_direto.clear()
    limpar_cache_sessao()

def enviar_alerta_servidor_whatsapp(numero_salao, texto_mensagem):
    try:
        wa_api_url = st.secrets.get("WA_API_URL", "")
        wa_api_token = st.secrets.get("WA_API_TOKEN", "")
    except Exception:
        wa_api_url = os.getenv("WA_API_URL", "")
        wa_api_token = os.getenv("WA_API_TOKEN", "")
    
    if wa_api_url and wa_api_token and numero_salao:
        try:
            num_limpo = re.sub(r'\D', '', str(numero_salao))
            if not num_limpo.startswith('55') and len(num_limpo) <= 11:
                num_limpo = '55' + num_limpo
                
            payload = { "number": num_limpo, "message": texto_mensagem }
            headers = { "Content-Type": "application/json", "apikey": wa_api_token }
            requests.post(wa_api_url, json=payload, headers=headers, timeout=5)
        except Exception:
            pass

@st.cache_data(ttl=180)
def carregar_clientes_mensais_banco(usuario_logado=None):
    usuario = usuario_logado or st.session_state.get("usuario_logado", "padrao")
    usuario_clean = str(usuario).strip().lower()
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT id, nome_cliente, telefone, servicos_feitos, valor_devido, status_divida FROM clientes_mensais WHERE usuario_id = :user ORDER BY id DESC"), {"user": usuario_clean})
            rows = result.fetchall()
            if rows:
                return pd.DataFrame(rows, columns=["id", "Cliente", "Telefone", "Serviços Feitos", "Valor Devido", "Status"])
    except Exception: pass
    return pd.DataFrame(columns=["id", "Cliente", "Telefone", "Serviços Feitos", "Valor Devido", "Status"])

def cadastrar_cliente_mensal_banco(nome, telefone):
    usuario = str(st.session_state.get("usuario_logado", "padrao")).strip().lower()
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.execute(text("SET SESSION CHARACTERISTICS AS TRANSACTION READ WRITE;"))
        conn.execute(text("""
            INSERT INTO clientes_mensais (usuario_id, nome_cliente, telefone, servicos_feitos, valor_devido, status_divida)
            VALUES (:user, :nome, :tel, 0, 0.0, 'Pendente')
        """), {"user": usuario, "nome": nome.strip(), "tel": telefone.strip()})
    carregar_clientes_mensais_banco.clear()
    limpar_cache_sessao()

def atualizar_cortes_cliente_mensal(id_cliente, qtd_adicionar, valor_por_servico):
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.execute(text("SET SESSION CHARACTERISTICS AS TRANSACTION READ WRITE;"))
        res = conn.execute(text("SELECT servicos_feitos, valor_devido FROM clientes_mensais WHERE id = :id"), {"id": int(id_cliente)}).fetchone()
        if res:
            novos_servicos = int(res[0]) + int(qtd_adicionar)
            novo_valor = float(res[1]) + (float(qtd_adicionar) * float(valor_por_servico))
            conn.execute(text("""
                UPDATE clientes_mensais 
                SET servicos_feitos = :s, valor_devido = :v, status_divida = 'Pendente'
                WHERE id = :id
            """), {"s": novos_servicos, "v": novo_valor, "id": int(id_cliente)})
    carregar_clientes_mensais_banco.clear()
    limpar_cache_sessao()

def dar_baixa_divida_mensalista(id_cliente, valor_baixa):
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.execute(text("SET SESSION CHARACTERISTICS AS TRANSACTION READ WRITE;"))
        res = conn.execute(text("SELECT valor_devido FROM clientes_mensais WHERE id = :id"), {"id": int(id_cliente)}).fetchone()
        if res:
            devido_atual = float(res[0])
            novo_valor_devido = max(0.0, devido_atual - float(valor_baixa))
            novo_status = 'Quitado' if novo_valor_devido == 0 else 'Pendente'
            conn.execute(text("""
                UPDATE clientes_mensais 
                SET valor_devido = :v, status_divida = :st
                WHERE id = :id
            """), {"v": novo_valor_devido, "st": novo_status, "id": int(id_cliente)})
    carregar_clientes_mensais_banco.clear()
    limpar_cache_sessao()

def gerar_backup_json_completo(usuario_logado=None):
    usuario = usuario_logado or st.session_state.get("usuario_logado", "padrao")
    df_f = carregar_fluxo(usuario)
    fluxo_dict = []
    if not df_f.empty:
        df_copy = df_f.copy()
        if 'Data' in df_copy.columns: df_copy['Data'] = df_copy['Data'].dt.strftime('%Y-%m-%d')
        fluxo_dict = df_copy.to_dict(orient="records")
    def custom_serializer(obj):
        if isinstance(obj, (decimal.Decimal, float)): return float(obj)
        if isinstance(obj, (datetime, pd.Timestamp)): return obj.strftime('%Y-%m-%d')
        return str(obj)
    dados_backup = {"sistema": "StudioBeleza_Gestao", "usuario_dono": usuario, "data_geracao": datetime.now(TZ).strftime('%d/%m/%Y %H:%M:%S'), "catalogo_servicos": carregar_servicos(usuario), "historico_financeiro": fluxo_dict}
    return json.dumps(dados_backup, indent=4, ensure_ascii=False, default=custom_serializer)

def gerar_pdf_contabilidade(df, mes_ref):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor("#ec4899"), spaceAfter=15)
    story.append(Paragraph(f"Studio & Beleza - Relatório Contábil ({mes_ref})", title_style))
    table_data = [["Data", "Tipo", "Descrição", "Valor"]]
    for _, row in df.iterrows():
        dt_str = row['Data'].strftime('%d/%m/%Y') if hasattr(row['Data'], 'strftime') else str(row['Data'])
        table_data.append([dt_str, str(row['Tipo']), str(row['Descrição']), f"R$ {row['Valor']:.2f}"])
    t = Table(table_data, colWidths=[75, 60, 265, 80])
    t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#fce7f3")), ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor("#831843")), ('GRID', (0,0), (-1,-1), 0.5, colors.pink), ('FONTSIZE', (0,0), (-1,-1), 9)]))
    story.append(t)
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def renderizar_botao_download_apk(dados_bytes, nome_arquivo, mime_type, label_botao):
    st.download_button(
        label=label_botao,
        data=dados_bytes,
        file_name=nome_arquivo,
        mime=mime_type,
        use_container_width=True
    )

def renderizar_whatsapp_flutuante():
    wa_msg = urllib.parse.quote("Olá! Preciso de suporte ou tenho dúvidas sobre o sistema de gestão do Salão.")
    try:
        support_phone = st.secrets.get("SUPPORT_PHONE", "5537991598179")
    except Exception:
        support_phone = os.getenv("SUPPORT_PHONE", "5537991598179")
        
    st.markdown(f"""
        <style>
        .floating-wa {{ position: fixed; width: 55px; height: 55px; bottom: 30px; right: 30px; background: linear-gradient(135deg, #25d366 0%, #128c7e 100%); border-radius: 50px; text-align: center; box-shadow: 0px 8px 25px rgba(37,211,102,0.4); z-index: 9999999; display: flex; align-items: center; justify-content: center; text-decoration: none; transition: all 0.3s ease; }}
        .floating-wa:hover {{ transform: scale(1.1) translateY(-3px); box-shadow: 0px 12px 30px rgba(37,211,102,0.6); }}
        .floating-wa svg {{ width: 30px; height: 30px; fill: white; }}
        </style>
        <a href="https://api.whatsapp.com/send?phone={support_phone}&text={wa_msg}" class="floating-wa" target="_blank" title="Falar com Suporte">
            <svg viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg"><path d="M16 2a13 13 0 0 0-10.85 20.24L3.6 28.5l6.43-1.5A13 13 0 1 0 16 2zm0 24a10.9 10.9 0 0 1-5.54-1.5l-.4-.24-4.14 1 .97-4.04-.26-.4A11 11 0 1 1 16 26zm6-8.2c-.33-.16-1.95-.96-2.25-1.07-.3-.1-.52-.16-.74.17-.22.33-.85 1.07-1.04 1.28-.2.22-.39.25-.72.09-.33-.16-1.4-.52-2.65-1.64-1-1-1.68-2.22-1.88-2.55-.2-.33-.02-.51.15-.67.15-.15.33-.39.5-.59.16-.2.22-.33.32-.55.1-.22.05-.42-.03-.58-.08-.16-.74-1.78-1-2.43-.27-.64-.53-.55-.74-.56h-.63c-.22 0-.58.08-.88.42-.3.33-1.15 1.12-1.15 2.73s1.18 3.16 1.34 3.37c.16.22 2.3 3.51 5.56 4.92 2.22.95 3.02 1.02 4.1 1.02s1.95-.8 2.25-1.57c.3-.77.3-1.43.22-1.57-.1-.13-.33-.2-.66-.36z"/></svg>
        </a>
    """, unsafe_allow_html=True)

# ==============================================================================
# ROTA PÚBLICA DE AGENDAMENTO CLIENTE FEMININO (?salao=nome)
# ==============================================================================
salao_url = query_params.get("salao", None)

if salao_url:
    st.markdown('<style>[data-testid="stSidebar"] {display: none !important;} [data-testid="collapsedControl"] {display: none !important;}</style>', unsafe_allow_html=True)
    salao_id_clean = urllib.parse.unquote(str(salao_url)).strip().lower()
    nome_salao_formatado = salao_id_clean.replace('_', ' ').replace('-', ' ').title()
    HORARIOS_DISPONIVEIS = ["08:00", "09:00", "10:00", "11:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00"]
    servicos_salao = carregar_servicos_por_salao(salao_id_clean)

    todos_usuarios = carregar_usuarios()
    dados_dono = todos_usuarios.get(salao_id_clean, {})
    wa_dono = dados_dono.get("whatsapp", "")

    st.markdown(f'''
        <div style="text-align: center; margin-bottom: 30px; background: linear-gradient(135deg, #ffffff 0%, #fdf2f8 100%); padding: 30px 20px; border-radius: 24px; border: 1px solid rgba(244,114,182,0.3); box-shadow: 0 10px 30px rgba(219,39,119,0.08);">
            <div style="font-size: 40px; margin-bottom: 8px;">✨💇‍♀️✨</div>
            <h1 style="margin: 0; color: #831843; font-size: 2.2rem; font-family: 'Playfair Display', Georgia, serif;">{nome_salao_formatado}</h1>
            <p style="color: #db2777 !important; font-weight: 600; margin-top: 6px; font-size: 1rem;">Agendamento Online de Beleza & Estética</p>
        </div>
    ''', unsafe_allow_html=True)

    if st.session_state.get("agendamento_sucesso"):
        dados_ag = st.session_state.agendamento_sucesso
        st.success(f"🎉 Agendamento realizado com sucesso para {dados_ag['nome']} às {dados_ag['hora']} no dia {dados_ag['data_formatada']}!")
        st.balloons()

        wa_dono_clean = re.sub(r'\D', '', str(dados_ag.get("wa_dono", "")))
        if wa_dono_clean:
            if not wa_dono_clean.startswith('55') and len(wa_dono_clean) <= 11:
                wa_dono_clean = '55' + wa_dono_clean
            
            msg_wa = urllib.parse.quote(
                f"✨ *NOVO AGENDAMENTO RECEBIDO!* ✨\n\n"
                f"👤 *Cliente:* {dados_ag['nome']}\n"
                f"📱 *Contato:* {dados_ag['contato']}\n"
                f"💅 *Serviço(s):* {dados_ag['servico']}\n"
                f"📅 *Data:* {dados_ag['data_formatada']}\n"
                f"⏰ *Horário:* {dados_ag['hora']}\n"
                f"💵 *Valor Estimado:* R$ {dados_ag.get('valor_total', 0.0):.2f}"
            )
            link_wa_dono = f"https://api.whatsapp.com/send?phone={wa_dono_clean}&text={msg_wa}"
            
            components.html(f'''
                <script>
                    setTimeout(function() {{
                        window.top.location.href = "{link_wa_dono}";
                    }}, 800);
                </script>
            ''', height=0, width=0)

            st.markdown(f'''
                <a href="{link_wa_dono}" target="_top" style="display:flex; align-items:center; justify-content:center; gap:10px; width:100%; text-align:center; background: linear-gradient(135deg, #25d366 0%, #128c7e 100%); color:#ffffff; padding:1.1rem; border-radius:18px; text-decoration:none; font-weight:800; font-size:1.05rem; margin-top:18px; margin-bottom:18px; box-shadow: 0 8px 25px rgba(37,211,102,0.35); transition: all 0.3s ease;">
                    <svg viewBox="0 0 32 32" width="24" height="24" fill="white" xmlns="http://www.w3.org/2000/svg"><path d="M16 2a13 13 0 0 0-10.85 20.24L3.6 28.5l6.43-1.5A13 13 0 1 0 16 2zm0 24a10.9 10.9 0 0 1-5.54-1.5l-.4-.24-4.14 1 .97-4.04-.26-.4A11 11 0 1 1 16 26zm6-8.2c-.33-.16-1.95-.96-2.25-1.07-.3-.1-.52-.16-.74.17-.22.33-.85 1.07-1.04 1.28-.2.22-.39.25-.72.09-.33-.16-1.4-.52-2.65-1.64-1-1-1.68-2.22-1.88-2.55-.2-.33-.02-.51.15-.67.15-.15.33-.39.5-.59.16-.2.22-.33.32-.55.1-.22.05-.42-.03-.58-.08-.16-.74-1.78-1-2.43-.27-.64-.53-.55-.74-.56h-.63c-.22 0-.58.08-.88.42-.3.33-1.15 1.12-1.15 2.73s1.18 3.16 1.34 3.37c.16.22 2.3 3.51 5.56 4.92 2.22.95 3.02 1.02 4.1 1.02s1.95-.8 2.25-1.57c.3-.77.3-1.43.22-1.57-.1-.13-.33-.2-.66-.36z"/></svg>
                    Clique aqui se não abrir o WhatsApp automaticamente
                </a>
            ''', unsafe_allow_html=True)

        if st.button("Fazer Outro Agendamento ✨", use_container_width=True):
            del st.session_state.agendamento_sucesso
            st.rerun()
        st.stop()

    with st.form("form_agendamento_cliente", clear_on_submit=True):
        nome_cliente = st.text_input("Seu Nome Completo:", placeholder="Ex: Maria Oliveira")
        telefone_cliente = st.text_input("Seu WhatsApp (com DDD):", placeholder="Ex: 31999998888")
        
        if servicos_salao:
            servicos_escolhidos = st.multiselect(
                "Escolha os Serviços Desejados (Pode escolher mais de um):", 
                options=list(servicos_salao.keys()),
                format_func=lambda x: f"✨ {x} — R$ {servicos_salao[x]:.2f}"
            )
        else:
            servicos_escolhidos = []
            st.warning("Nenhum serviço cadastrado no momento.")

        data_escolhida = st.date_input("Escolha a Data:", min_value=datetime.now(TZ).date())
        data_str = data_escolhida.strftime("%Y-%m-%d")
        data_formatada = data_escolhida.strftime("%d/%m/%Y")
        
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT hora FROM agendamentos WHERE usuario_id = :user AND data = :dt"), {"user": salao_id_clean, "dt": data_str})
                ocupados = [r[0] for r in result.fetchall()]
        except Exception: ocupados = []
        
        horarios_livres = [h for h in HORARIOS_DISPONIVEIS if h not in ocupados]
        horario_escolhido = st.selectbox("Horário Disponível:", horarios_livres) if horarios_livres else None
        if not horarios_livres: st.warning("⚠️ Todos os horários estão preenchidos nesta data.")
        
        if servicos_escolhidos and servicos_salao:
            val_tot = sum([servicos_salao[s] for s in servicos_escolhidos])
            st.info(f"💵 **Valor Total Estimado:** R$ {val_tot:.2f} ({len(servicos_escolhidos)} serviço(s) selecionado(s))")

        enviar_agendamento = st.form_submit_button("Confirmar Agendamento ✨", type="primary", use_container_width=True)

    if enviar_agendamento:
        try:
            if not nome_cliente or not telefone_cliente:
                st.warning("⚠️ Por favor, informe seu nome e WhatsApp.")
            elif not servicos_escolhidos:
                st.error("⚠️ Por favor, selecione ao menos um serviço da lista.")
            elif not horario_escolhido:
                st.error("⚠️ Selecione um horário válido.")
            else:
                servico_final_str = ", ".join(servicos_escolhidos)
                val_tot_final = sum([servicos_salao[s] for s in servicos_escolhidos])

                with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
                    conn.execute(text("SET SESSION CHARACTERISTICS AS TRANSACTION READ WRITE;"))
                    conn.execute(text("INSERT INTO agendamentos (usuario_id, cliente_nome, cliente_contato, servico_nome, data, hora) VALUES (:user, :nome, :contato, :servico, :data, :hora)"), {"user": salao_id_clean, "nome": nome_cliente.strip(), "contato": telefone_cliente.strip(), "servico": servico_final_str, "data": data_str, "hora": horario_escolhido})
                
                if wa_dono:
                    texto_alerta_api = f"✨ NOVO AGENDAMENTO RECEBIDO!\n\nCliente: {nome_cliente.strip()}\nContato: {telefone_cliente.strip()}\nServiços: {servico_final_str}\nData: {data_formatada}\nHorário: {horario_escolhido}\nTotal: R$ {val_tot_final:.2f}"
                    enviar_alerta_servidor_whatsapp(wa_dono, texto_alerta_api)

                st.session_state.agendamento_sucesso = {
                    "nome": nome_cliente.strip(),
                    "contato": telefone_cliente.strip(),
                    "servico": servico_final_str,
                    "hora": horario_escolhido,
                    "data_formatada": data_formatada,
                    "valor_total": val_tot_final,
                    "wa_dono": wa_dono
                }
                limpar_cache_sessao()
                st.rerun()
        except Exception as e: st.error(f"Erro ao registrar agendamento: {e}")
    st.stop()

# ==============================================================================
# TELA DE AUTENTICAÇÃO E LOGIN
# ==============================================================================
if not st.session_state.autenticado:
    admin_hash1, admin_hash2, url_sistema_salva = carregar_admin_hashes()
    usuarios_cadastrados = carregar_usuarios()

    if not admin_hash1 or not admin_hash2:
        st.title("⚠️ Configuração Inicial de Segurança")
        with st.form("primeiro_acesso"):
            nova_adm_pass1 = st.text_input("Senha Principal Admin:", type="password")
            nova_adm_pass2 = st.text_input("Senha Secundária Admin:", type="password")
            url_padrao_app = st.text_input("URL Base do App:", value=RENDER_BASE_URL)
            if st.form_submit_button("Salvar Inicialização"):
                if nova_adm_pass1 and nova_adm_pass2:
                    salvar_admin_hashes(nova_adm_pass1, nova_adm_pass2, url_padrao_app.strip())
                    st.success("Administração inicializada!")
                    st.rerun()
        st.stop()

    if st.session_state.recuperando_senha:
        st.markdown('<br><br>', unsafe_allow_html=True)
        _, col_rec_centro, _ = st.columns([1, 2, 1])
        with col_rec_centro:
            st.markdown('<div class="login-card"><div class="login-brand-wrapper"><div class="login-badge-icon">🔐</div><h1 class="login-title">Recuperação</h1><p class="login-subtitle">Redefina a senha da sua conta</p></div>', unsafe_allow_html=True)
            with st.form("form_recuperacao"):
                user_recup = st.text_input("Usuário:").strip().lower()
                email_recup = st.text_input("E-mail Cadastrado:").strip().lower()
                nova_senha_recup = st.text_input("Nova Senha:", type="password")
                conf_senha_recup = st.text_input("Confirme a Nova Senha:", type="password")
                if st.form_submit_button("Atualizar Senha", type="primary", use_container_width=True):
                    if user_recup in usuarios_cadastrados and usuarios_cadastrados[user_recup].get("email") == email_recup:
                        if nova_senha_recup == conf_senha_recup and nova_senha_recup:
                            usuarios_cadastrados[user_recup]["senha"] = hash_password(nova_senha_recup)
                            salvar_usuarios(usuarios_cadastrados)
                            st.success("✅ Senha alterada com sucesso!")
                            st.session_state.recuperando_senha = False
                            st.rerun()
                        else: st.error("As senhas não conferem.")
                    else: st.error("Usuário ou e-mail incorretos.")
            if st.button("Voltar ao Login", use_container_width=True):
                st.session_state.recuperando_senha = False
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

    col_vazia, col_btn_tema = st.columns([8, 1])
    with col_btn_tema:
        if st.button("🌸 Rose" if st.session_state.tema_escuro else "🌙 Noturno", use_container_width=True):
            st.session_state.tema_escuro = not st.session_state.tema_escuro
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    _, col_login_centro, _ = st.columns([1, 2, 1])

    with col_login_centro:
        st.markdown('''
            <div class="login-card">
                <div class="login-brand-wrapper">
                    <div class="login-badge-icon">💇‍♀️</div>
                    <h1 class="login-title">Studio & Gestão</h1>
                    <p class="login-subtitle">Plataforma Exclusiva de Gestão para Salões de Beleza</p>
                </div>
        ''', unsafe_allow_html=True)
        
        tipo_acesso = st.radio("Acesso como:", ["Salão de Beleza", "Admin Mestre"], horizontal=True, label_visibility="collapsed")

        with st.form("form_login_moderno"):
            usuario_input = st.text_input("Usuário / Login").strip().lower()
            senha_input = st.text_input("Senha", type="password")
            senha2_input = st.text_input("Senha Secundária Admin", type="password") if tipo_acesso == "Admin Mestre" else ""
            st.markdown("<br>", unsafe_allow_html=True)
            submit_login = st.form_submit_button("Entrar no Studio ✨", type="primary", use_container_width=True)
            if submit_login:
                if tipo_acesso == "Admin Mestre":
                    if usuario_input == "admin" and verificar_senha(senha_input, admin_hash1) and verificar_senha(senha2_input, admin_hash2):
                        st.session_state.autenticado = True
                        st.session_state.usuario_logado = "Administrador"
                        st.session_state.eh_admin = True
                        st.query_params["token_sessao"] = "admin_master_session"
                        st.rerun()
                    else: st.error("Credenciais inválidas.")
                else:
                    if usuario_input in usuarios_cadastrados and verificar_senha(senha_input, usuarios_cadastrados[usuario_input]["senha"]):
                        dados_user = usuarios_cadastrados[usuario_input]
                        try:
                            data_venc = datetime.strptime(str(dados_user["vencimento"]), "%Y-%m-%d").date()
                        except Exception:
                            data_venc = datetime.now(TZ).date() + timedelta(days=30)

                        if datetime.now(TZ).date() > data_venc or dados_user.get("status") == "Suspenso":
                            st.error("❌ Acesso bloqueado. Licença expirada.")
                            st.stop()
                        st.session_state.autenticado = True
                        st.session_state.usuario_logado = usuario_input
                        st.session_state.eh_admin = False
                        st.query_params["token_sessao"] = usuario_input
                        st.rerun()
                    else: st.error("Usuário ou senha incorretos.")

        st.markdown("<hr style='border-color: rgba(244,114,182,0.2); margin: 20px 0;'>", unsafe_allow_html=True)

        try:
            support_phone = st.secrets.get("SUPPORT_PHONE", "5537991598179")
        except Exception:
            support_phone = os.getenv("SUPPORT_PHONE", "5537991598179")

        col_esqueci, col_whats = st.columns(2)
        with col_esqueci:
            if st.button("Esqueci minha senha", use_container_width=True):
                st.session_state.recuperando_senha = True
                st.rerun()
        with col_whats:
            wa_login_msg = urllib.parse.quote("Olá! Gostaria de falar sobre o sistema de Salão de Beleza.")
            st.markdown(f'<a href="https://api.whatsapp.com/send?phone={support_phone}&text={wa_login_msg}" target="_blank" style="display: flex; align-items: center; justify-content: center; gap: 8px; background: linear-gradient(135deg, #25d366 0%, #128c7e 100%); color: white; padding: 10px; border-radius: 12px; text-decoration: none; font-weight: bold; height: 46px; box-shadow: 0 4px 15px rgba(37, 211, 102, 0.3);"><svg viewBox="0 0 32 32" width="20" height="20" fill="white" xmlns="http://www.w3.org/2000/svg"><path d="M16 2a13 13 0 0 0-10.85 20.24L3.6 28.5l6.43-1.5A13 13 0 1 0 16 2zm0 24a10.9 10.9 0 0 1-5.54-1.5l-.4-.24-4.14 1 .97-4.04-.26-.4A11 11 0 1 1 16 26zm6-8.2c-.33-.16-1.95-.96-2.25-1.07-.3-.1-.52-.16-.74.17-.22.33-.85 1.07-1.04 1.28-.2.22-.39.25-.72.09-.33-.16-1.4-.52-2.65-1.64-1-1-1.68-2.22-1.88-2.55-.2-.33-.02-.51.15-.67.15-.15.33-.39.5-.59.16-.2.22-.33.32-.55.1-.22.05-.42-.03-.58-.08-.16-.74-1.78-1-2.43-.27-.64-.53-.55-.74-.56h-.63c-.22 0-.58.08-.88.42-.3.33-1.15 1.12-1.15 2.73s1.18 3.16 1.34 3.37c.16.22 2.3 3.51 5.56 4.92 2.22.95 3.02 1.02 4.1 1.02s1.95-.8 2.25-1.57c.3-.77.3-1.43.22-1.57-.1-.13-.33-.2-.66-.36z"/></svg>Suporte</a>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

renderizar_whatsapp_flutuante()

# ==============================================================================
# MODO ADMINISTRADOR MESTRE
# ==============================================================================
if st.session_state.eh_admin:
    col_adm_title, col_adm_logout = st.columns([3, 1])
    with col_adm_title:
        st.title("👑 Gestão Geral de Salões (Admin Mestre)")
    with col_adm_logout:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚪 Sair do Sistema", type="secondary", use_container_width=True, key="admin_top_logout_btn"):
            st.session_state.clear()
            if "token_sessao" in st.query_params:
                del st.query_params["token_sessao"]
            st.rerun()

    tab_cad, tab_ger, tab_assinantes, tab_config = st.tabs(["➕ Cadastrar / Renovar", "⚙️ Salões Cadastrados", "📊 Painel de Assinantes", "🔧 Configurações Mestre"])
    admin_hash1, admin_hash2, url_sistema_salva = carregar_admin_hashes()
    usuarios_cadastrados = carregar_usuarios()

    with tab_cad:
        with st.form("form_cadastro_cliente"):
            novo_usuario = st.text_input("Usuário do Salão (sem espaços):").strip().lower()
            novo_email = st.text_input("E-mail de Contato:").strip().lower()
            novo_whatsapp = st.text_input("WhatsApp do Salão (com DDD, ex: 5537999999999):").strip()
            nova_senha = st.text_input("Senha de Acesso:", type="password").strip()
            tipo_conta = st.selectbox("Perfil:", ["Teste", "Cliente"])
            dias_validade = st.number_input("Dias de Acesso:", min_value=1, value=30)
            if st.form_submit_button("Cadastrar Salão", type="primary"):
                if novo_usuario and nova_senha and novo_email:
                    venc = (datetime.now(TZ) + timedelta(days=dias_validade)).strftime("%Y-%m-%d")
                    usuarios_cadastrados[novo_usuario] = {
                        "senha": hash_password(nova_senha), 
                        "email": novo_email, 
                        "whatsapp": novo_whatsapp,
                        "tipo": tipo_conta, 
                        "vencimento": venc, 
                        "status": "Ativo"
                    }
                    salvar_usuarios(usuarios_cadastrados)
                    st.success("Salão cadastrado com sucesso!")
                    st.rerun()
    with tab_ger:
        if usuarios_cadastrados:
            salao_sel = st.selectbox("Selecione um Salão:", list(usuarios_cadastrados.keys()))
            dados = usuarios_cadastrados[salao_sel]
            with st.expander("📝 Editar Conta", expanded=True):
                e_email = st.text_input("E-mail:", value=dados.get("email", ""))
                e_whatsapp = st.text_input("WhatsApp (com DDD):", value=dados.get("whatsapp", ""))
                e_senha_nova = st.text_input("Alterar Senha (opcional):", type="password")
                e_tipo = st.selectbox("Tipo:", ["Teste", "Cliente"], index=0 if dados['tipo'] == "Teste" else 1)

                try:
                    data_venc_atual = datetime.strptime(str(dados['vencimento']), "%Y-%m-%d").date()
                except Exception:
                    data_venc_atual = datetime.now(TZ).date()

                e_venc = st.date_input("Vencimento:", data_venc_atual)
                e_status = st.selectbox("Status:", ["Ativo", "Suspenso"], index=0 if dados['status'] == "Ativo" else 1)
                if st.button("Salvar Modificações"):
                    senha_f = hash_password(e_senha_nova) if e_senha_nova else dados['senha']
                    venc_str_save = e_venc.strftime("%Y-%m-%d") if hasattr(e_venc, 'strftime') else str(e_venc)
                    usuarios_cadastrados[salao_sel] = {
                        "senha": senha_f, 
                        "email": e_email.strip().lower(), 
                        "whatsapp": e_whatsapp.strip(),
                        "tipo": e_tipo, 
                        "vencimento": venc_str_save, 
                        "status": e_status
                    }
                    salvar_usuarios(usuarios_cadastrados)
                    st.success("Conta atualizada!")
                    st.rerun()
            if st.checkbox(f"Confirmar exclusão de {salao_sel}"):
                if st.button("EXCLUIR PERMANENTEMENTE", type="primary"):
                    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
                        conn.execute(text("SET SESSION CHARACTERISTICS AS TRANSACTION READ WRITE;"))
                        conn.execute(text("DELETE FROM usuarios WHERE id = :id"), {"id": salao_sel})
                    carregar_usuarios.clear()
                    st.rerun()

    with tab_assinantes:
        st.markdown("### 📊 Painel de Monitoramento de Assinantes")
        st.markdown("<p style='color: #9d174d;'>Acompanhe o status das assinaturas dos salões, verifique vencimentos e gerencie acessos.</p>", unsafe_allow_html=True)

        if usuarios_cadastrados:
            data_hoje = datetime.now(TZ).date()
            
            houve_alteracao_auto = False
            for u_id, u_info in usuarios_cadastrados.items():
                try:
                    dt_venc = datetime.strptime(str(u_info.get("vencimento")), "%Y-%m-%d").date()
                except Exception:
                    dt_venc = data_hoje
                
                if dt_venc < data_hoje and u_info.get("status") == "Ativo":
                    usuarios_cadastrados[u_id]["status"] = "Suspenso"
                    houve_alteracao_auto = True

            if houve_alteracao_auto:
                salvar_usuarios(usuarios_cadastrados)
                usuarios_cadastrados = carregar_usuarios()

            total_clientes = len(usuarios_cadastrados)
            ativos_count = sum(1 for u in usuarios_cadastrados.values() if u.get("status") == "Ativo" and datetime.strptime(str(u.get("vencimento")), "%Y-%m-%d").date() >= data_hoje)
            vencidos_count = sum(1 for u in usuarios_cadastrados.values() if datetime.strptime(str(u.get("vencimento")), "%Y-%m-%d").date() < data_hoje or u.get("status") == "Suspenso")
            
            kpi1, kpi2, kpi3 = st.columns(3)
            with kpi1:
                st.markdown(f'<div class="kpi-card-v2"><div class="kpi-title-v2">Total de Salões</div><div class="kpi-value-v2 kpi-val-pink">{total_clientes}</div></div>', unsafe_allow_html=True)
            with kpi2:
                st.markdown(f'<div class="kpi-card-v2"><div class="kpi-title-v2">Salões Em Dia (Ativos)</div><div class="kpi-value-v2 kpi-val-green">{ativos_count}</div></div>', unsafe_allow_html=True)
            with kpi3:
                st.markdown(f'<div class="kpi-card-v2"><div class="kpi-title-v2">Salões Vencidos / Bloqueados</div><div class="kpi-value-v2 kpi-val-red">{vencidos_count}</div></div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### Gerenciamento de Acessos")

            for u_id, u_info in usuarios_cadastrados.items():
                try:
                    dt_venc = datetime.strptime(str(u_info.get("vencimento")), "%Y-%m-%d").date()
                except Exception:
                    dt_venc = data_hoje

                status_atual = u_info.get("status", "Ativo")
                esta_vencido = dt_venc < data_hoje

                cor_status = "#059669" if (status_atual == "Ativo" and not esta_vencido) else "#e11d48"
                texto_status = "Em Dia (Ativo)" if (status_atual == "Ativo" and not esta_vencido) else "Vencido / Bloqueado"

                with st.container():
                    st.markdown('<div class="ui-card" style="padding: 16px 20px; margin-bottom: 12px;">', unsafe_allow_html=True)
                    c_info, c_venc, c_status_lbl, c_btn = st.columns([2.5, 1.5, 2, 2])
                    with c_info:
                        st.markdown(f"**🌸 Salão:** `{u_id}`<br><span style='color: #9d174d; font-size: 0.85rem;'>{u_info.get('email', 'Sem e-mail')}</span>", unsafe_allow_html=True)
                    with c_venc:
                        st.markdown(f"**Vencimento:**<br>{dt_venc.strftime('%d/%m/%Y')}", unsafe_allow_html=True)
                    with c_status_lbl:
                        st.markdown(f"**Status:**<br><span style='color: {cor_status}; font-weight: 700;'>● {texto_status}</span>", unsafe_allow_html=True)
                    with c_btn:
                        if status_atual == "Ativo" and not esta_vencido:
                            if st.button("🔒 Bloquear", key=f"bloquear_{u_id}", use_container_width=True):
                                usuarios_cadastrados[u_id]["status"] = "Suspenso"
                                salvar_usuarios(usuarios_cadastrados)
                                st.success(f"Acesso de {u_id} bloqueado!")
                                st.rerun()
                        else:
                            if st.button("🔓 Desbloquear", key=f"desbloquear_{u_id}", type="primary", use_container_width=True):
                                novo_venc_renovado = (data_hoje + timedelta(days=30)).strftime("%Y-%m-%d")
                                usuarios_cadastrados[u_id]["status"] = "Ativo"
                                usuarios_cadastrados[u_id]["vencimento"] = novo_venc_renovado
                                salvar_usuarios(usuarios_cadastrados)
                                st.success(f"Acesso de {u_id} desbloqueado e renovado!")
                                st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Nenhum salão cadastrado no momento.")

    with tab_config:
        nova_url_input = st.text_input("URL Principal do Sistema:", value=url_sistema_salva if url_sistema_salva else RENDER_BASE_URL)
        if st.button("Salvar URL Global"):
            atualizar_url_sistema(nova_url_input.strip())
            st.success("URL Salva!")
            st.rerun()
    with st.sidebar:
        st.markdown("---")
        if st.button("🚪 Sair do Mestre", use_container_width=True):
            st.session_state.clear()
            if "token_sessao" in st.query_params:
                del st.query_params["token_sessao"]
            st.rerun()
    st.stop()

# ==============================================================================
# PAINEL PRINCIPAL DO SALÃO (USUÁRIO LOGADO)
# ==============================================================================
usuario_logado_atual = st.session_state.usuario_logado

if "dados_carregados_sessao" not in st.session_state:
    st.session_state["df_fluxo_caixa"] = carregar_fluxo(usuario_logado_atual)
    st.session_state["servicos"] = carregar_servicos(usuario_logado_atual)
    st.session_state["df_agendamentos_all"] = carregar_agendamentos(usuario_logado_atual)
    st.session_state["df_clientes_m"] = carregar_clientes_mensais_banco(usuario_logado_atual)
    st.session_state["dados_carregados_sessao"] = True

df_fluxo_caixa = st.session_state["df_fluxo_caixa"]
servicos = st.session_state["servicos"]
df_agendamentos_all = st.session_state["df_agendamentos_all"]
df_clientes_m = st.session_state["df_clientes_m"]

_, _, url_sistema_salva = carregar_admin_hashes()

hoje = pd.Timestamp(datetime.now(TZ).date())
mes_atual = hoje.month
ano_atual = hoje.year
mes_passado = mes_atual - 1 if mes_atual > 1 else 12
ano_passado = ano_atual if mes_atual > 1 else ano_atual - 1

if not df_fluxo_caixa.empty:
    df_limpo = df_fluxo_caixa.dropna(subset=['Data']).copy()
    df_mes_atual = df_limpo[(df_limpo['Data'].dt.month == mes_atual) & (df_limpo['Data'].dt.year == ano_atual)]
    df_mes_passado = df_limpo[(df_limpo['Data'].dt.month == mes_passado) & (df_limpo['Data'].dt.year == ano_passado)]
    df_ano_atual = df_limpo[df_limpo['Data'].dt.year == ano_atual]
else:
    df_limpo = pd.DataFrame(columns=['id', 'Data', 'Tipo', 'Descrição', 'Valor'])
    df_mes_atual = pd.DataFrame(columns=['id', 'Data', 'Tipo', 'Descrição', 'Valor'])
    df_mes_passado = pd.DataFrame(columns=['id', 'Data', 'Tipo', 'Descrição', 'Valor'])
    df_ano_atual = pd.DataFrame(columns=['id', 'Data', 'Tipo', 'Descrição', 'Valor'])

base_url = RENDER_BASE_URL.rstrip('/')
link_clientes = f"{base_url}/?salao={st.session_state.usuario_logado}"
nome_salao_titulo = str(st.session_state.usuario_logado).replace('_', ' ').replace('-', ' ').title()
wa_url_geral = f"https://api.whatsapp.com/send?text={urllib.parse.quote(f'Olá! 👋 Agende seu momento de beleza no *{nome_salao_titulo}* de forma prática: {link_clientes}')}"

col_top_left, _ = st.columns([1, 4])
with col_top_left:
    with st.popover("⚙️ Configurar Serviços", use_container_width=False):
        st.subheader("⚙️ Tabela de Serviços & Valores")
        st.markdown("---")
        opcoes_gerenciamento_pop = ["➕ Cadastrar Novo Serviço"] + list(servicos.keys())
        servico_sel_pop = st.selectbox("Ação / Serviço:", opcoes_gerenciamento_pop, key="top_select_servico")
        nome_p_pop = "" if servico_sel_pop == "➕ Cadastrar Novo Serviço" else servico_sel_pop
        preco_p_pop = 0.0 if servico_sel_pop == "➕ Cadastrar Novo Serviço" else float(servicos[servico_sel_pop])
        novo_servico_pop = st.text_input("Nome do Serviço:", value=nome_p_pop, key=f"top_nome_{servico_sel_pop}")
        novo_preco_pop = st.number_input("Valor do Serviço (R$):", min_value=0.0, value=preco_p_pop, step=5.0, key=f"top_prc_{servico_sel_pop}")

        col_tp1, col_tp2 = st.columns(2)
        with col_tp1:
            if st.button("💾 Salvar", type="primary", use_container_width=True, key="top_save_btn"):
                if novo_servico_pop.strip():
                    salvar_ou_atualizar_servico(servico_sel_pop, novo_servico_pop.strip(), novo_preco_pop)
                    st.success("Serviço atualizado com sucesso!")
                    st.rerun()
                else: st.error("Informe o nome do serviço.")
        with col_tp2:
            if servico_sel_pop != "➕ Cadastrar Novo Serviço":
                if st.button("🗑️ Excluir", use_container_width=True, key="top_del_btn"):
                    deletar_servico_banco(servico_sel_pop)
                    st.warning("Serviço excluído com sucesso!")
                    st.rerun()

        st.markdown("---")
        renderizar_botao_download_apk(gerar_backup_json_completo(usuario_logado_atual).encode('utf-8'), f"backup_{st.session_state.usuario_logado}_{datetime.now(TZ).strftime('%d_%m_%Y')}.json", "application/json", "📥 Baixar Backup JSON")
        st.markdown("---")
        if st.button("🚪 Sair do Sistema", use_container_width=True, type="secondary", key="top_logout_btn"):
            st.session_state.clear()
            if "token_sessao" in st.query_params:
                del st.query_params["token_sessao"]
            st.rerun()

st.markdown(f'''
    <div style="display: flex; justify-content: space-between; align-items: center; padding: 22px 30px; background: linear-gradient(135deg, #ffffff 0%, #fdf2f8 100%); border: 1px solid rgba(244,114,182,0.3); border-radius: 24px; margin-bottom: 24px; box-shadow: 0 10px 30px rgba(219,39,119,0.06);">
        <div>
            <h2 style="margin: 0; color: #831843; font-size: 2rem; font-weight: 800; font-family: 'Playfair Display', Georgia, serif;">✨ {nome_salao_titulo}</h2>
            <p style="margin: 4px 0 0 0; color: #db2777 !important; font-size: 0.95rem; font-weight: 500;">Painel de Gestão do Salão de Beleza & Estética</p>
        </div>
    </div>
''', unsafe_allow_html=True)

# ==============================================================================
# FUNÇÕES DE DIÁLOGO (MODAIS PARA AÇÕES RÁPIDAS)
# ==============================================================================

@st.dialog("💇‍♀️ Registrar Atendimento Realizado")
def dialog_novo_atendimento(servicos_dict):
    if list(servicos_dict.keys()):
        servico_selecionado = st.selectbox("Serviço Realizado:", list(servicos_dict.keys()), key="f_atend_serv_modal")
        preco_final = st.number_input("Valor Recebido (R$):", value=float(servicos_dict[servico_selecionado]), step=1.0, key=f"prc_atend_din_{servico_selecionado}_modal")
        data_entrada = st.date_input("Data do Atendimento:", datetime.now(TZ).date(), key="f_atend_dt_modal")
        if st.button("✅ Confirmar Entrada no Caixa", type="primary", use_container_width=True):
            inserir_movimentacao_direta("Entrada", f"Atendimento: {servico_selecionado}", preco_final, data_entrada)
            st.success("Atendimento registrado no caixa com sucesso!")
            st.rerun()

@st.dialog("🛍️ Registrar Nova Despesa do Salão")
def dialog_nova_despesa():
    descricao_saida = st.text_input("Descrição da Despesa:", key="f_venda_desc_modal", placeholder="Ex: Esmaltes, produtos de cabelo, conta de luz...")
    valor_saida = st.number_input("Valor Pago (R$):", min_value=0.0, step=5.0, key="f_venda_val_modal")
    data_saida = st.date_input("Data do Pagamento:", datetime.now(TZ).date(), key="f_venda_dt_modal")
    if st.button("🔴 Lançar Saída", type="primary", use_container_width=True):
        if descricao_saida and valor_saida > 0:
            inserir_movimentacao_direta("Saída", descricao_saida, -valor_saida, data_saida)
            st.success("Despesa lançada!")
            st.rerun()
        else:
            st.warning("Preencha a descrição e um valor válido.")

@st.dialog("💰 Registrar Atendimento Fiado / Conta Cliente")
def dialog_anotar_fiado(servicos_dict):
    if list(servicos_dict.keys()):
        nome_devedor = st.text_input("Nome da Cliente:", key="f_fiado_nome_modal")
        servico_pendente = st.selectbox("Serviço Realizado:", list(servicos_dict.keys()), key="f_fiado_serv_modal")
        preco_final_p = st.number_input("Valor a Pagar (R$):", value=float(servicos_dict[servico_pendente]), key=f"prc_fiado_din_{servico_pendente}_modal")
        data_pendencia = st.date_input("Data do Serviço:", datetime.now(TZ).date(), key="f_fiado_dt_modal")
        if st.button("⚠️ Anotar Pendência", type="primary", use_container_width=True):
            if nome_devedor:
                inserir_movimentacao_direta("Pendência", f"Fiado de: {nome_devedor} ({servico_pendente})", preco_final_p, data_pendencia)
                st.success("Conta anotada com sucesso!")
                st.rerun()
            else:
                st.warning("Informe o nome da cliente.")

@st.dialog("💸 Receber Pagamento de Conta / Fiado")
def dialog_baixar_fiado(df_fluxo):
    df_pendencias = df_fluxo[df_fluxo['Tipo'] == 'Pendência']
    if not df_pendencias.empty:
        opcoes_pendentes = {f"{row['Descrição']} - R$ {abs(row['Valor']):.2f}": row['id'] for _, row in df_pendencias.iterrows()}
        pendencia_selecionada = st.selectbox("Selecione a Conta a Receber:", list(opcoes_pendentes.keys()), key="f_pago_sel_modal")
        if st.button("💰 Confirmar Recebimento", type="primary", use_container_width=True):
            id_alterar = opcoes_pendentes[pendencia_selecionada]
            row_atual = df_pendencias[df_pendencias['id'] == id_alterar].iloc[0]
            nova_desc = row_atual['Descrição'].replace("Fiado de:", "Recebido Fiado:") + " [PAGO]"
            dar_baixa_fiado_direta(id_alterar, nova_desc)
            st.success("Pagamento registrado no caixa!")
            st.rerun()
    else:
        st.info("Nenhuma pendência no momento.")

# ==============================================================================
# ABAS DO PAINEL PRINCIPAL
# ==============================================================================
tab_dashboard, tab_servicos, tab_mensais, tab_agend, tab_historico = st.tabs(["📊 Dashboard Studio", "⚡ Serviços", "👥 Clientes VIP / Planos", "📅 Agendamentos", "💸 Fluxo de Caixa"])

# ==============================================================================
# TAB 1: DASHBOARD
# ==============================================================================
with tab_dashboard:
    def calc_perc(atual, anterior):
        if anterior == 0: return 0 if atual == 0 else 100
        return ((atual - anterior) / anterior) * 100

    def render_perc(val, reverse_colors=False):
        if val == 0: return f'<span class="kpi-perc perc-neutral">0% vs mês anterior</span>'
        seta = "▲" if val > 0 else "▼"
        cor = "perc-up" if (val > 0 and not reverse_colors) or (val < 0 and reverse_colors) else "perc-down"
        return f'<span class="kpi-perc {cor}">{seta} {abs(val):.1f}% vs mês ant.</span>'

    dt_hoje = hoje.date()
    dt_hoje_str = dt_hoje.strftime('%Y-%m-%d')

    rec_dia = df_limpo[(df_limpo['Data'].dt.date == dt_hoje) & (df_limpo['Tipo'].isin(['Entrada', 'Pendência']))]['Valor'].sum() if not df_limpo.empty else 0.0
    rec_mes = df_mes_atual[df_mes_atual['Tipo'].isin(['Entrada', 'Pendência'])]['Valor'].sum() if not df_mes_atual.empty else 0.0
    rec_ano = df_ano_atual[df_ano_atual['Tipo'].isin(['Entrada', 'Pendência'])]['Valor'].sum() if not df_ano_atual.empty else 0.0
    
    ent_mes = df_mes_atual[df_mes_atual['Tipo'] == 'Entrada']['Valor'].sum() if not df_mes_atual.empty else 0.0
    sai_mes = abs(df_mes_atual[df_mes_atual['Tipo'] == 'Saída']['Valor'].sum()) if not df_mes_atual.empty else 0.0
    lucro_mes = ent_mes - sai_mes

    rec_mes_passado = df_mes_passado[df_mes_passado['Tipo'].isin(['Entrada', 'Pendência'])]['Valor'].sum() if not df_mes_passado.empty else 0.0
    ent_mes_passado = df_mes_passado[df_mes_passado['Tipo'] == 'Entrada']['Valor'].sum() if not df_mes_passado.empty else 0.0
    sai_mes_passado = abs(df_mes_passado[df_mes_passado['Tipo'] == 'Saída']['Valor'].sum()) if not df_mes_passado.empty else 0.0
    lucro_mes_passado = ent_mes_passado - sai_mes_passado

    perc_rec_mes = calc_perc(rec_mes, rec_mes_passado)
    perc_lucro_mes = calc_perc(lucro_mes, lucro_mes_passado)

    qtd_atendimentos_mes = len(df_mes_atual[df_mes_atual['Tipo'] == 'Entrada']) if not df_mes_atual.empty else 0
    ticket_medio = (ent_mes / qtd_atendimentos_mes) if qtd_atendimentos_mes > 0 else 0.0

    agendamentos_hoje = df_agendamentos_all[df_agendamentos_all['Data'] == dt_hoje_str] if not df_agendamentos_all.empty else pd.DataFrame()
    qtd_agend_hoje = len(agendamentos_hoje)

    if not df_agendamentos_all.empty:
        df_proximos = df_agendamentos_all[df_agendamentos_all['Data'] >= dt_hoje_str].sort_values(by=['Data', 'Horário']).head(5)
    else:
        df_proximos = pd.DataFrame()

    set_clientes = set(df_clientes_m['Cliente'].unique()) if not df_clientes_m.empty else set()
    if not df_agendamentos_all.empty:
        set_clientes.update(df_agendamentos_all['Cliente'].unique())
    total_clientes_cadastrados = len(set_clientes)
    if total_clientes_cadastrados == 0 and not df_limpo.empty:
        total_clientes_cadastrados = len(df_limpo['Descrição'].unique())

    # BARRA DE META MENSAL
    st.markdown('<div class="ui-card">', unsafe_allow_html=True)
    c_meta_input, c_meta_bar = st.columns([1, 2.5])
    with c_meta_input:
        meta_val = st.number_input("🎯 Sua Meta Mensal do Salão (R$):", min_value=100.0, value=float(st.session_state.meta_mensal), step=500.0, key="input_meta_dinamica")
        st.session_state.meta_mensal = meta_val
    with c_meta_bar:
        pct_meta = min(100.0, (float(rec_mes) / meta_val) * 100) if meta_val > 0 else 0.0
        restante_meta = max(0.0, meta_val - float(rec_mes))
        cor_barra = "#059669" if pct_meta >= 100 else "#ec4899"
        
        st.markdown(f"""
            <div style="margin-top: 5px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="font-weight: 700; color: #831843; font-size: 1rem;">Progresso da Meta Faturamento</span>
                    <span style="font-weight: 800; color: {cor_barra}; font-size: 1.1rem;">{pct_meta:.1f}% ({'Meta Batida! 🎉✨' if pct_meta >= 100 else f'Faltam R$ {restante_meta:,.2f}'})</span>
                </div>
                <div style="width: 100%; background: rgba(244,114,182,0.15); border-radius: 999px; height: 16px; overflow: hidden; border: 1px solid rgba(244,114,182,0.3);">
                    <div style="width: {pct_meta}%; background: linear-gradient(90deg, #f472b6 0%, {cor_barra} 100%); height: 100%; border-radius: 999px; transition: width 0.8s ease;"></div>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 0.82rem; color: #9d174d; margin-top: 6px;">
                    <span>Faturado: <strong>R$ {rec_mes:,.2f}</strong></span>
                    <span>Meta: <strong>R$ {meta_val:,.2f}</strong></span>
                </div>
            </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # GRID DE KPIS
    col_k1, col_k2, col_k3, col_k4 = st.columns(4)
    with col_k1:
        st.markdown(f'''
            <div class="kpi-card-v2">
                <div class="kpi-title-v2">💖 Receita do Dia</div>
                <div class="kpi-value-v2 kpi-val-green">R$ {rec_dia:,.2f}</div>
                <span class="kpi-perc perc-neutral">Hoje ({dt_hoje.strftime('%d/%m')})</span>
            </div>
        ''', unsafe_allow_html=True)
    with col_k2:
        st.markdown(f'''
            <div class="kpi-card-v2">
                <div class="kpi-title-v2">💰 Receita do Mês</div>
                <div class="kpi-value-v2 kpi-val-pink">R$ {rec_mes:,.2f}</div>
                {render_perc(perc_rec_mes)}
            </div>
        ''', unsafe_allow_html=True)
    with col_k3:
        st.markdown(f'''
            <div class="kpi-card-v2">
                <div class="kpi-title-v2">📅 Receita Anual</div>
                <div class="kpi-value-v2 kpi-val-purple">R$ {rec_ano:,.2f}</div>
                <span class="kpi-perc perc-neutral">Acumulado {ano_atual}</span>
            </div>
        ''', unsafe_allow_html=True)
    with col_k4:
        st.markdown(f'''
            <div class="kpi-card-v2">
                <div class="kpi-title-v2">📈 Lucro Líquido (Mês)</div>
                <div class="kpi-value-v2 kpi-val-gold">R$ {lucro_mes:,.2f}</div>
                {render_perc(perc_lucro_mes)}
            </div>
        ''', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_k5, col_k6, col_k7, col_k8 = st.columns(4)
    with col_k5:
        st.markdown(f'''
            <div class="kpi-card-v2">
                <div class="kpi-title-v2">✨ Ticket Médio</div>
                <div class="kpi-value-v2 kpi-val-pink">R$ {ticket_medio:,.2f}</div>
                <span class="kpi-perc perc-neutral">Por cliente no mês</span>
            </div>
        ''', unsafe_allow_html=True)
    with col_k6:
        st.markdown(f'''
            <div class="kpi-card-v2">
                <div class="kpi-title-v2">👥 Total de Clientes</div>
                <div class="kpi-value-v2 kpi-val-purple">{total_clientes_cadastrados}</div>
                <span class="kpi-perc perc-neutral">Base cadastrada</span>
            </div>
        ''', unsafe_allow_html=True)
    with col_k7:
        st.markdown(f'''
            <div class="kpi-card-v2">
                <div class="kpi-title-v2">📅 Agendamentos Hoje</div>
                <div class="kpi-value-v2 kpi-val-gold">{qtd_agend_hoje}</div>
                <span class="kpi-perc perc-neutral">Marcados para hoje</span>
            </div>
        ''', unsafe_allow_html=True)
    with col_k8:
        st.markdown(f'''
            <div class="kpi-card-v2">
                <div class="kpi-title-v2">📊 Crescimento vs Mês Ant.</div>
                <div class="kpi-value-v2 {'kpi-val-green' if perc_rec_mes >= 0 else 'kpi-val-red'}">{'+' if perc_rec_mes > 0 else ''}{perc_rec_mes:.1f}%</div>
                <span class="kpi-perc perc-neutral">Comparativo de faturamento</span>
            </div>
        ''', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # AGENDA DO DIA E PRÓXIMOS HORÁRIOS
    c_ag_hoje, c_ag_prox = st.columns(2)
    with c_ag_hoje:
        st.markdown('<div class="ui-card" style="height: 100%;">', unsafe_allow_html=True)
        st.markdown('<h4 style="margin-bottom: 16px; color: #831843;">📌 Agendamentos de Hoje</h4>', unsafe_allow_html=True)
        if not agendamentos_hoje.empty:
            for _, r in agendamentos_hoje.iterrows():
                st.markdown(f"""
                    <div style="background: rgba(244,114,182,0.1); border-left: 4px solid #ec4899; border-radius: 12px; padding: 12px 16px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong style="color: #831843; font-size: 0.98rem;">{r['Cliente']}</strong><br>
                            <span style="color: #9d174d; font-size: 0.85rem;">✨ {r['Serviço']}</span>
                        </div>
                        <span style="background: #fbcfe8; color: #831843; padding: 4px 12px; border-radius: 10px; font-weight: 700; font-size: 0.9rem;">⏰ {r['Horário']}</span>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Nenhum agendamento marcado para hoje.")
        st.markdown('</div>', unsafe_allow_html=True)

    with c_ag_prox:
        st.markdown('<div class="ui-card" style="height: 100%;">', unsafe_allow_html=True)
        st.markdown('<h4 style="margin-bottom: 16px; color: #831843;">⏱️ Próximas Clientes Marcadas</h4>', unsafe_allow_html=True)
        if not df_proximos.empty:
            for _, r in df_proximos.iterrows():
                dt_p = pd.to_datetime(r['Data']).strftime('%d/%m') if r['Data'] else ""
                st.markdown(f"""
                    <div style="background: rgba(244,114,182,0.1); border-left: 4px solid #db2777; border-radius: 12px; padding: 12px 16px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong style="color: #831843; font-size: 0.98rem;">{r['Cliente']}</strong><br>
                            <span style="color: #9d174d; font-size: 0.85rem;">✨ {r['Serviço']}</span>
                        </div>
                        <span style="background: #fbcfe8; color: #831843; padding: 4px 12px; border-radius: 10px; font-weight: 700; font-size: 0.85rem;">📅 {dt_p} às {r['Horário']}</span>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Nenhum agendamento futuro encontrado.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # GRÁFICOS PLOTLY
    col_g1, col_g2 = st.columns([1.6, 1])
    with col_g1:
        st.markdown('<div class="ui-card">', unsafe_allow_html=True)
        st.markdown('<h4 style="margin-bottom: 18px; color: #831843;">📈 Evolução Financeira Diária (Mês)</h4>', unsafe_allow_html=True)
        if not df_mes_atual.empty:
            df_m_chart = df_mes_atual.copy()
            df_m_chart['DataStr'] = df_m_chart['Data'].dt.strftime('%d/%m')
            df_grp = df_m_chart.groupby(['DataStr', 'Tipo'])['Valor'].sum().unstack(fill_value=0).reset_index()
            for c in ['Entrada', 'Saída', 'Pendência']:
                if c not in df_grp: df_grp[c] = 0
            df_grp['Saída_Abs'] = df_grp['Saída'].abs()
            df_grp['Lucro'] = df_grp['Entrada'] - df_grp['Saída_Abs']

            fig_evo = go.Figure()
            fig_evo.add_trace(go.Scatter(x=df_grp['DataStr'], y=df_grp['Lucro'], mode='lines+markers', name='Lucro Líquido', line=dict(color='#059669', width=3, shape='spline'), fill='tozeroy', fillcolor='rgba(5, 150, 105, 0.1)'))
            fig_evo.add_trace(go.Scatter(x=df_grp['DataStr'], y=df_grp['Entrada'], mode='lines+markers', name='Entradas', line=dict(color='#ec4899', width=2, shape='spline')))
            fig_evo.add_trace(go.Scatter(x=df_grp['DataStr'], y=df_grp['Saída_Abs'], mode='lines+markers', name='Despesas', line=dict(color='#e11d48', width=2, shape='spline')))
            
            fig_evo.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#831843', family='Plus Jakarta Sans'),
                xaxis=dict(showgrid=False, tickfont=dict(color='#831843')),
                yaxis=dict(showgrid=True, gridcolor='rgba(244,114,182,0.2)', tickfont=dict(color='#831843')),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(color='#831843')),
                margin=dict(l=10, r=10, t=10, b=10), height=340, hovermode="x unified"
            )
            st.plotly_chart(fig_evo, use_container_width=True)
        else:
            st.info("Insira lançamentos para visualizar o gráfico diário.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_g2:
        st.markdown('<div class="ui-card">', unsafe_allow_html=True)
        st.markdown('<h4 style="margin-bottom: 18px; color: #831843;">📊 Faturamento Anual do Salão</h4>', unsafe_allow_html=True)
        if not df_ano_atual.empty:
            df_ano_chart = df_ano_atual[df_ano_atual['Tipo'].isin(['Entrada', 'Pendência'])].copy()
            df_ano_chart['MesNum'] = df_ano_chart['Data'].dt.month
            df_ano_chart['Mês'] = df_ano_chart['Data'].dt.strftime('%b')
            df_ano_grp = df_ano_chart.groupby(['MesNum', 'Mês'])['Valor'].sum().reset_index().sort_values('MesNum')
            
            fig_bar_ano = px.bar(df_ano_grp, x='Mês', y='Valor', text_auto='.2s', color_discrete_sequence=['#ec4899'])
            fig_bar_ano.update_traces(marker_line_color='#db2777', marker_line_width=1.5, opacity=0.85)
            fig_bar_ano.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#831843', family='Plus Jakarta Sans'),
                xaxis=dict(showgrid=False, tickfont=dict(color='#831843')),
                yaxis=dict(showgrid=True, gridcolor='rgba(244,114,182,0.2)', tickfont=dict(color='#831843')),
                margin=dict(l=10, r=10, t=10, b=10), height=340
            )
            st.plotly_chart(fig_bar_ano, use_container_width=True)
        else:
            st.info("Sem dados anuais registrados.")
        st.markdown('</div>', unsafe_allow_html=True)

    # RANKINGS
    col_rank1, col_rank2 = st.columns(2)
    
    with col_rank1:
        st.markdown('<div class="ui-card">', unsafe_allow_html=True)
        st.markdown('<h4 style="margin-bottom: 18px; color: #831843;">💅 Serviços Mais Procurados</h4>', unsafe_allow_html=True)
        
        dict_servicos_count = {s: 0 for s in servicos.keys()}
        if not df_limpo.empty:
            for desc in df_limpo['Descrição']:
                for s_nome in servicos.keys():
                    if s_nome.lower() in desc.lower():
                        dict_servicos_count[s_nome] += 1
        if not df_agendamentos_all.empty:
            for s_nome in df_agendamentos_all['Serviço']:
                if s_nome in dict_servicos_count:
                    dict_servicos_count[s_nome] += 1
                else:
                    dict_servicos_count[s_nome] = 1

        df_srv_top = pd.DataFrame(list(dict_servicos_count.items()), columns=['Serviço', 'Vendas']).sort_values(by='Vendas', ascending=False)
        df_srv_top = df_srv_top[df_srv_top['Vendas'] > 0]

        if not df_srv_top.empty:
            fig_pie_srv = px.pie(df_srv_top, names='Serviço', values='Vendas', hole=0.55, color_discrete_sequence=['#f472b6', '#ec4899', '#db2777', '#c084fc', '#fb7185'])
            fig_pie_srv.update_traces(textposition='inside', textinfo='percent+label')
            fig_pie_srv.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#831843', family='Plus Jakarta Sans'),
                showlegend=False, margin=dict(l=10, r=10, t=10, b=10), height=280
            )
            st.plotly_chart(fig_pie_srv, use_container_width=True)
        else:
            st.info("Nenhum serviço contabilizado até o momento.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_rank2:
        st.markdown('<div class="ui-card">', unsafe_allow_html=True)
        st.markdown('<h4 style="margin-bottom: 18px; color: #831843;">🏆 Top Clientes do Salão</h4>', unsafe_allow_html=True)
        
        mapa_fat_clientes = {}
        if not df_clientes_m.empty:
            for _, r in df_clientes_m.iterrows():
                cli = r['Cliente']
                val = float(r['Valor Devido']) + (float(r['Serviços Feitos']) * 50.0)
                mapa_fat_clientes[cli] = mapa_fat_clientes.get(cli, 0.0) + val

        if not df_limpo.empty:
            for _, r in df_limpo.iterrows():
                desc = r['Descrição']
                val = abs(float(r['Valor']))
                if "Fiado de:" in desc or "Atendimento:" in desc or "Mensalidade recebida" in desc:
                    parts = desc.split(":")
                    if len(parts) > 1:
                        cli_nome = parts[1].split("(")[0].strip()
                        if cli_nome:
                            mapa_fat_clientes[cli_nome] = mapa_fat_clientes.get(cli_nome, 0.0) + val

        df_rank_cli = pd.DataFrame(list(mapa_fat_clientes.items()), columns=['Cliente', 'Faturamento']).sort_values(by='Faturamento', ascending=False).head(5)

        if not df_rank_cli.empty:
            medals = ["🥇", "🥈", "🥉", "4º", "5º"]
            for idx, (_, r) in enumerate(df_rank_cli.iterrows()):
                icone = medals[idx] if idx < len(medals) else f"{idx+1}º"
                st.markdown(f"""
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 14px; background: rgba(244,114,182,0.1); border-radius: 12px; margin-bottom: 8px;">
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <span style="font-size: 1.1rem;">{icone}</span>
                            <strong style="color: #831843; font-size: 0.95rem;">{r['Cliente']}</strong>
                        </div>
                        <span style="color: #059669; font-weight: 800; font-size: 0.95rem;">R$ {r['Faturamento']:,.2f}</span>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Sem dados para exibir o ranking.")
        st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# TAB 2: SERVIÇOS E AÇÕES
# ==============================================================================
with tab_servicos:
    st.markdown('<div class="ui-card">', unsafe_allow_html=True)
    st.markdown('<h3 style="margin-bottom: 8px; color: #831843;">⚡ Ações Rápidas de Caixa</h3>', unsafe_allow_html=True)
    st.markdown("<p style='color: #9d174d !important; margin-bottom: 20px;'>Utilize os botões abaixo para gerenciar atendimentos e despesas rapidamente.</p>", unsafe_allow_html=True)
    
    col_srv1, col_srv2, col_srv3, col_srv4 = st.columns(4)
    
    with col_srv1:
        if st.button("💇‍♀️ Novo Atendimento", use_container_width=True, type="primary"):
            dialog_novo_atendimento(servicos)
            
    with col_srv2:
        if st.button("🛍️ Nova Despesa", use_container_width=True):
            dialog_nova_despesa()
            
    with col_srv3:
        if st.button("💳 Anotar Fiado", use_container_width=True):
            dialog_anotar_fiado(servicos)
            
    with col_srv4:
        if st.button("💸 Receber Conta", use_container_width=True):
            dialog_baixar_fiado(df_fluxo_caixa)
    st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# TAB 3: CLIENTES VIP / PLANOS MENSAIS
# ==============================================================================
with tab_mensais:
    st.markdown('### 👥 Gestão de Clientes VIP & Planos Mensais')
    st.markdown("<p style='color: #9d174d !important;'>Cadastre suas clientes participantes de pacotes ou planos de beleza mensais, registre os procedimentos e controle os acertos.</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    tab_m_cad, tab_m_lanc, tab_m_lista = st.tabs(["➕ Cadastrar Cliente VIP", "💆‍♀️ Registrar Procedimento", "📋 Acompanhar Planos e Baixas"])

    with tab_m_cad:
        with st.form("form_cad_cliente_mensal", clear_on_submit=True):
            st.markdown("#### Informações da Cliente VIP")
            nome_cli_m = st.text_input("Nome Completo da Cliente:")
            tel_cli_m = st.text_input("Telefone / WhatsApp:")
            
            btn_salvar_cli_m = st.form_submit_button("Cadastrar Cliente VIP", type="primary", use_container_width=True)
            if btn_salvar_cli_m:
                if nome_cli_m.strip():
                    cadastrar_cliente_mensal_banco(nome_cli_m, tel_cli_m)
                    st.success(f"Cliente VIP `{nome_cli_m}` cadastrada com sucesso!")
                    st.rerun()
                else:
                    st.warning("⚠️ Informe o nome da cliente.")

    with tab_m_lanc:
        st.markdown('<div class="ui-card">', unsafe_allow_html=True)
        st.markdown("<h4 style='margin-bottom: 15px; color: #831843;'>Registrar Procedimento / Serviço VIP</h4>", unsafe_allow_html=True)
        df_mensalistas = carregar_clientes_mensais_banco(usuario_logado_atual)
        if not df_mensalistas.empty:
            mapa_clientes = {row['Cliente']: row['id'] for _, row in df_mensalistas.iterrows()}
            cliente_escolhido_l = st.selectbox("Selecione a Cliente VIP:", list(mapa_clientes.keys()))
            id_cli_sel = mapa_clientes[cliente_escolhido_l]
            
            qtd_cortes = st.number_input("Quantidade de serviços realizados:", min_value=1, value=1, step=1)
            preco_serv_mensal = st.number_input("Valor unitário cobrado por este procedimento (R$):", min_value=0.0, value=50.0, step=5.0)

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Adicionar Procedimento à Conta da Cliente", type="primary", use_container_width=True):
                atualizar_cortes_cliente_mensal(id_cli_sel, qtd_cortes, preco_serv_mensal)
                st.success(f"Adicionado {qtd_cortes} procedimento(s) para `{cliente_escolhido_l}`.")
                st.rerun()
        else:
            st.info("Nenhuma cliente VIP cadastrada. Cadastre na aba anterior.")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab_m_lista:
        st.markdown("#### Status de Contas e Acertos")
        df_mensalistas = carregar_clientes_mensais_banco(usuario_logado_atual)
        if not df_mensalistas.empty:
            for _, row in df_mensalistas.iterrows():
                c_id = row['id']
                c_nome = row['Cliente']
                c_tel = row['Telefone']
                c_serv = row['Serviços Feitos']
                c_val = float(row['Valor Devido'])
                c_status = row['Status']

                cor_st = "#059669" if c_status == "Quitado" or c_val == 0 else "#e11d48"
                
                with st.container():
                    st.markdown('<div class="ui-card" style="padding: 18px 24px; margin-bottom: 14px;">', unsafe_allow_html=True)
                    col_info_m, col_val_m, col_action_m = st.columns([3, 2, 2])
                    with col_info_m:
                        st.markdown(f"**👤 {c_nome}** (`{c_tel if c_tel else 'Sem Tel'}`)<br><span style='color: #9d174d; font-size: 0.85rem;'>Procedimentos realizados: {c_serv}</span>", unsafe_allow_html=True)
                    with col_val_m:
                        st.markdown(f"**Valor Aberto:**<br><span style='color: {cor_st}; font-weight: 800; font-size: 1.15rem;'>R$ {c_val:,.2f}</span>", unsafe_allow_html=True)
                    with col_action_m:
                        if c_val > 0:
                            with st.popover(f"💸 Dar Baixa ({c_nome})", use_container_width=True):
                                st.markdown(f"**Valor pendente:** R$ {c_val:,.2f}")
                                tipo_baixa = st.radio("Escolha o tipo de baixa:", ["Quitar valor total", "Baixa parcial (escolher valor)"], key=f"tipo_baixa_{c_id}")
                                
                                valor_a_baixar = c_val
                                if tipo_baixa == "Baixa parcial (escolher valor)":
                                    valor_a_baixar = st.number_input("Valor que a cliente pagou (R$):", min_value=0.01, max_value=c_val, value=c_val, step=5.0, key=f"val_parcial_{c_id}")
                                
                                if st.button("Confirmar Recebimento", key=f"btn_conf_baixa_{c_id}", type="primary", use_container_width=True):
                                    inserir_movimentacao_direta("Entrada", f"Mensalidade/Plano recebido ({'parcial' if tipo_baixa != 'Quitar valor total' else 'total'}): {c_nome}", valor_a_baixar, datetime.now(TZ).date())
                                    dar_baixa_divida_mensalista(c_id, valor_a_baixar)
                                    st.success(f"Recebimento de R$ {valor_a_baixar:,.2f} registrado com sucesso!")
                                    st.rerun()
                        else:
                            st.markdown("<span style='color: #059669; font-weight: 700;'>✔ Quitado / Em Dia</span>", unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Nenhuma cliente VIP cadastrada no momento.")

# ==============================================================================
# TAB 4: AGENDAMENTOS
# ==============================================================================
with tab_agend:
    col_ag_title, col_ag_btn = st.columns([3, 1])
    with col_ag_title:
        st.markdown("### 📅 Central de Agendamentos")
        st.markdown("<p style='color: #9d174d !important; margin: 0;'>Gerencie as clientes agendadas em tempo real.</p>", unsafe_allow_html=True)
    with col_ag_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Atualizar Lista", type="primary", use_container_width=True): 
            limpar_cache_sessao()
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f'<a href="{wa_url_geral}" target="_blank" style="display:flex; align-items:center; justify-content:center; gap:8px; width:100%; text-align:center; background: linear-gradient(135deg, #25d366 0%, #128c7e 100%); color:#ffffff; padding:0.95rem; border-radius:16px; text-decoration:none; font-weight:700; margin-bottom:24px; box-shadow: 0 6px 20px rgba(37, 211, 102, 0.3); transition: all 0.3s ease;">📲 Compartilhar Link de Agendamento com Clientes</a>', unsafe_allow_html=True)
    
    df_agendamentos = carregar_agendamentos(usuario_logado_atual)

    if not df_agendamentos.empty:
        total_agendamentos = len(df_agendamentos)
        data_hoje_str = datetime.now(TZ).strftime('%Y-%m-%d')
        df_hoje = df_agendamentos[df_agendamentos['Data'] == data_hoje_str]
        qtd_hoje = len(df_hoje)

        texto_alerta = f"Você possui <strong>{total_agendamentos}</strong> agendamento(s) marcado(s) na sua lista!"
        if qtd_hoje > 0:
            texto_alerta += f" (Sendo <strong>{qtd_hoje}</strong> para o dia de hoje)."

        st.markdown(f'''
            <div style="background: linear-gradient(135deg, #fbcfe8 0%, #f472b6 100%); border: 1px solid #ec4899; border-radius: 18px; padding: 18px 24px; margin-bottom: 22px; color: #831843;">
                <span style="font-size: 1.1rem; font-weight: 800;">🔔 ALERTA DE AGENDAMENTOS</span>
                <p style="margin: 4px 0 0 0; font-size: 0.95rem;">{texto_alerta}</p>
            </div>
        ''', unsafe_allow_html=True)

        st.markdown('<h4 style="margin-bottom: 16px; color: #831843;">📋 Agendamentos Confirmados</h4>', unsafe_allow_html=True)
        
        servicos_salao = carregar_servicos(usuario_logado_atual)

        for index, row in df_agendamentos.iterrows():
            id_ag = row['id']
            cliente = row['Cliente']
            contato = row['Contato/WhatsApp']
            servico = row['Serviço']
            data_bd = row['Data']
            hora = row['Horário']
            
            try:
                data_formatada = pd.to_datetime(data_bd).strftime('%d/%m/%Y')
            except:
                data_formatada = data_bd

            with st.container():
                st.markdown('<div class="ui-card" style="padding: 18px 24px; margin-bottom: 14px;">', unsafe_allow_html=True)
                col_info, col_zap, col_conf, col_canc = st.columns([3, 1, 2.5, 1.5])
                
                with col_info:
                    st.markdown(f"<div><strong style='font-size: 1.05rem; color: #831843;'>{cliente}</strong><br><span style='color:#9d174d; font-size:0.85rem;'>📅 {data_formatada} às {hora} | ✨ {servico}</span></div>", unsafe_allow_html=True)
                
                with col_zap:
                    num_clean = re.sub(r'\D', '', str(contato))
                    if num_clean:
                        if not num_clean.startswith('55') and len(num_clean) <= 11: num_clean = '55' + num_clean
                        msg_cli = urllib.parse.quote(f"Olá {cliente}! Confirmando seu agendamento no {nome_salao_titulo} para {data_formatada} às {hora}.")
                        wa_direct = f"https://api.whatsapp.com/send?phone={num_clean}&text={msg_cli}"
                        st.markdown(f'<a href="{wa_direct}" target="_blank" style="display:inline-block;width:100%;text-align:center;background-color:#25d366;color:white;padding:10px;border-radius:12px;text-decoration:none;font-weight:700; font-size: 14px; box-shadow: 0 4px 12px rgba(37,211,102,0.25);" title="Chamar no WhatsApp">💬 Zap</a>', unsafe_allow_html=True)
                    else:
                        st.markdown("<p style='text-align:center; color:#9d174d; font-size:12px; margin-top:10px;'>Sem Nº</p>", unsafe_allow_html=True)

                with col_conf:
                    if st.button("✅ Confirmar & Faturar", key=f"conf_{id_ag}", type="primary", use_container_width=True):
                        preco_servico = float(servicos_salao.get(servico, 0.0))
                        inserir_movimentacao_direta("Entrada", f"Agendamento: {cliente} ({servico})", preco_servico, datetime.now(TZ).date())
                        deletar_agendamento(id_ag)
                        st.success(f"Atendimento de {cliente} faturado com sucesso no valor de R$ {preco_servico:.2f}!")
                        st.rerun()
                
                with col_canc:
                    if st.button("❌ Cancelar", key=f"canc_{id_ag}", use_container_width=True):
                        deletar_agendamento(id_ag)
                        st.warning(f"Agendamento de {cliente} removido.")
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="ui-card" style="text-align: center; padding: 40px;"><h4 style="color: #9d174d; margin: 0;">Nenhum agendamento pendente no momento.</h4><p style="color: #be185d; font-size: 0.9rem; margin-top: 6px;">Envie o link do seu agendamento para suas clientes para receber novas marcações.</p></div>', unsafe_allow_html=True)

# ==============================================================================
# TAB 5: MOVIMENTAÇÃO (FLUXO DE CAIXA / HISTÓRICO)
# ==============================================================================
with tab_historico:
    st.subheader("💸 Fluxo de Caixa / Histórico Financeiro")
    
    if "mostrar_movimentacao" not in st.session_state:
        st.session_state.mostrar_movimentacao = False

    btn_label = "📂 Ocultar Historico" if st.session_state.mostrar_movimentacao else "📁 Abrir Histórico Financeiro"
    if st.button(btn_label, use_container_width=True, type="primary"):
        st.session_state.mostrar_movimentacao = not st.session_state.mostrar_movimentacao
        st.rerun()

    if st.session_state.mostrar_movimentacao:
        st.markdown("<br>", unsafe_allow_html=True)
        if not df_fluxo_caixa.empty:
            df_filtro = df_fluxo_caixa.dropna(subset=['Data']).copy()
            df_filtro['Mês/Ano'] = df_filtro['Data'].dt.strftime('%m/%Y')

            modo_filtro = st.radio("Filtro de Exibição:", ["Por Mês Fechado", "Por Período Customizado"], horizontal=True)
            if modo_filtro == "Por Mês Fechado":
                meses = sorted(df_filtro['Mês/Ano'].unique(), reverse=True)
                mes_escolhido = st.selectbox("📅 Selecione o Mês:", ["Ver Tudo"] + meses)
                df_exibicao = df_filtro[df_filtro['Mês/Ano'] == mes_escolhido] if mes_escolhido != "Ver Tudo" else df_filtro
                texto_pdf = mes_escolhido
                nome_arq = f"contabilidade_{mes_escolhido.replace('/', '_')}" if mes_escolhido != "Ver Tudo" else "contabilidade_geral"
            else:
                col_dt1, col_dt2 = st.columns(2)
                with col_dt1: dt_inicio = st.date_input("Data Inicial:", datetime.now(TZ).date() - timedelta(days=30))
                with col_dt2: dt_fim = st.date_input("Data Final:", datetime.now(TZ).date())
                df_exibicao = df_filtro[(df_filtro['Data'].dt.date >= dt_inicio) & (df_filtro['Data'].dt.date <= dt_fim)]
                texto_pdf = f"{dt_inicio.strftime('%d/%m/%Y')} a {dt_fim.strftime('%d/%m/%Y')}"
                nome_arq = "contabilidade_periodo"

            if not df_exibicao.empty:
                st.markdown("<br>", unsafe_allow_html=True)
                pdf_bytes = gerar_pdf_contabilidade(df_exibicao, texto_pdf)
                st.download_button(label="📥 Baixar Relatório Contábil em PDF", data=pdf_bytes, file_name=f"{nome_arq}.pdf", mime="application/pdf", use_container_width=True)
                st.markdown("<br>", unsafe_allow_html=True)

                df_exibicao['DataApenas'] = df_exibicao['Data'].dt.date
                datas_unicas = sorted(df_exibicao['DataApenas'].unique(), reverse=True)

                for dt_val in datas_unicas:
                    df_dia_atual = df_exibicao[df_exibicao['DataApenas'] == dt_val]
                    data_formatada_titulo = dt_val.strftime('%d/%m/%Y')
                    
                    st.markdown(f"#### 📅 Data: {data_formatada_titulo}")
                    
                    for index, row in df_dia_atual.iterrows():
                        id_reg = row['id']
                        tipo = row['Tipo']
                        desc = row['Descrição']
                        val = row['Valor']

                        if tipo == 'Entrada':
                            cor_val = "#059669"
                            sinal = "+"
                        elif tipo == 'Saída':
                            cor_val = "#e11d48"
                            sinal = "-"
                        else:
                            cor_val = "#d97706"
                            sinal = "⏳"

                        val_formatado = f"{sinal} R$ {abs(val):,.2f}"

                        with st.container():
                            st.markdown('<div class="ui-card" style="padding: 14px 20px; margin-bottom: 10px;">', unsafe_allow_html=True)
                            col_reg_info, col_reg_btn = st.columns([5, 1])
                            with col_reg_info:
                                st.markdown(f"*{tipo}* — {desc} <br><span style='color: {cor_val}; font-weight: 700; font-size: 1.05rem;'>{val_formatado}</span>", unsafe_allow_html=True)
                            with col_reg_btn:
                                if st.button("🗑️ Excluir", key=f"del_mov_{id_reg}", use_container_width=True):
                                    deletar_movimentacao_fluxo(id_reg)
                                    st.warning("Registro excluído!")
                                    st.rerun()
                            st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
            else:
                st.info("Nenhum registro encontrado para este período.")
        else:
            st.info("O histórico financeiro está vazio.")
