import calendar
from datetime import datetime
import os
import pandas as pd
import streamlit as st

# Configuração da página do aplicativo
st.set_page_config(
    page_title="Calendário Dinâmico de Aulas", layout="centered"
)

# Inicializar os estados da sessão do Streamlit
if "dia_selecionado" not in st.session_state:
    st.session_state.dia_selecionado = None
if "mes_anterior" not in st.session_state:
    st.session_state.mes_anterior = 10
if "ano_anterior" not in st.session_state:
    st.session_state.ano_anterior = 2026

# Configurando o calendário do Python explicitamente para Português do Brasil
try:
    calendar.setlocale(calendar.LC_ALL, 'pt_BR.UTF-8')
except:
    try:
        calendar.setlocale(calendar.LC_ALL, 'ptb') # Alternativa para Windows
    except:
        pass

# Dicionário de tradução manual de contingência para os meses
MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
    7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

# -------------------------------------------------------------
# INJEÇÃO DE CSS DE ALTO CONTRASTE (DESTAQUE MÁXIMO PARA OS DIAS COM AULA)
# -------------------------------------------------------------
st.markdown("""
    <style>
    /* Configuração de fundo escuro profundo */
    .stApp {
        background-color: #040805 !important;
    }
    
    /* Textos principais e títulos do sistema */
    h1, h2, h3, p, span, label {
        color: #f0fdf4 !important;
    }
    
    /* Grid de alinhamento perfeito para as colunas de dias da semana */
    [data-testid="stHorizontalBlock"] {
        gap: 8px !important;
        padding-left: 0px !important;
        padding-right: 0px !important;
    }
    
    div.btn-cal-header, div.btn-cal-neon, div.btn-cal-vazio {
        width: 100% !important;
    }

    /* ESTILO DO CABEÇALHO DA SEMANA (VERDE BRILHANTE) */
    div.btn-cal-header button {
        background-color: transparent !important;
        color: #39ff14 !important;
        border: none !important;
        font-weight: bold !important;
        font-size: 16px !important;
        height: 45px !important;
        width: 100% !important;
        text-align: center !important;
        cursor: default !important;
        box-shadow: none !important;
        transform: none !important;
    }
    
    /* 🟢 DIAS COM AULA: Super Destaque Vidro Verde Neon */
    div.btn-cal-neon button, div.btn-cal-neon button[data-testid="baseButton-secondary"] {
        background-color: rgba(57, 255, 20, 0.18) !important; /* Fundo mais denso e visível */
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
        color: #ffffff !important;
        border: 2px solid #39ff14 !important; /* Borda mais grossa e totalmente acesa */
        border-radius: 10px !important;
        width: 100% !important;
        height: 78px !important;
        padding: 4px 0px !important;
        font-size: 21px !important;
        line-height: 1.2 !important;
        font-weight: 900 !important; /* Texto mais espesso */
        white-space: pre-wrap !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        align-items: center !important;
        /* Brilho externo expandido estilo Cyberpunk */
        box-shadow: 0 0 20px rgba(57, 255, 20, 0.4), inset 0 0 10px rgba(57, 255, 20, 0.2) !important;
        transition: all 0.3s ease-in-out !important;
    }
    div.btn-cal-neon button:hover, div.btn-cal-neon button[data-testid="baseButton-secondary"]:hover {
        background-color: rgba(57, 255, 20, 0.35) !important;
        border-color: #39ff14 !important;
        box-shadow: 0 0 32px rgba(57, 255, 20, 0.8), 0 0 45px rgba(57, 255, 20, 0.4) !important;
        transform: scale(1.05) !important;
    }

    /* 🔵 DIAS VAZIOS: Efeito Apagado/Segundo Plano (Contraste) */
    div.btn-cal-vazio button, div.btn-cal-vazio button[data-testid="baseButton-secondary"] {
        background-color: rgba(0, 150, 255, 0.03) !important; /* Quase transparente */
        backdrop-filter: blur(4px) !important;
        -webkit-backdrop-filter: blur(4px) !important;
        color: rgba(209, 230, 255, 0.4) !important; /* Texto fosco/acinzentado */
        border: 1px solid rgba(0, 150, 255, 0.15) !important; /* Borda bem suave */
        border-radius: 8px !important;
        width: 100% !important;
        height: 75px !important;
        font-size: 19px !important;
        font-weight: normal !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        box-shadow: none !important; /* Sem brilho nenhum */
        transition: all 0.3s ease-in-out !important;
    }
    div.btn-cal-vazio button:hover, div.btn-cal-vazio button[data-testid="baseButton-secondary"]:hover {
        background-color: rgba(0, 150, 255, 0.15) !important;
        color: #ffffff !important;
        border-color: rgba(0, 204, 255, 0.6) !important;
        box-shadow: 0 0 15px rgba(0, 204, 255, 0.3) !important;
        transform: translateY(-1px) !important;
    }
    
    /* 🟠 PAINEL DE DIA SELECIONADO (Cyberpunk Laranja) */
    .caixa-dia-foco {
        background: linear-gradient(90deg, rgba(255, 94, 0, 0.15), rgba(255, 153, 0, 0.05)) !important;
        border: 1px solid #ff5e00 !important;
        padding: 12px 18px !important;
        border-radius: 8px !important;
        color: #ff9900 !important;
        font-weight: bold !important;
        font-size: 16px !important;
        box-shadow: 0 0 15px rgba(255, 94, 0, 0.2) !important;
        margin-bottom: 20px !important;
    }
    
    /* CARDS DE MÉTRICAS DO TOPO */
    .card-metrica-topo {
        background-color: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(57, 255, 20, 0.2) !important;
        border-radius: 8px;
        padding: 14px;
        text-align: center;
    }
    
    /* Botões Padrão do Painel Inferior */
    div.stButton > button {
        background-color: rgba(57, 255, 20, 0.05) !important;
        color: #39ff14 !important;
        border: 1px solid rgba(57, 255, 20, 0.4) !important;
        border-radius: 8px !important;
        width: 100% !important;
    }
    div.stButton > button:hover {
        background-color: rgba(57, 255, 20, 0.18) !important;
        color: #ffffff !important;
        border-color: #39ff14 !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📅 Calendário Dinâmico de Aulas")
st.markdown("Selecione os filtros na lateral. **Clique em qualquer dia do calendário** para carregar os dados diretamente no formulário abaixo.")

excel_file = "Quantidade_de_Aulas_por_Dia_Novas_Disciplinas.xlsx"

# --- SISTEMA DE UPLOAD DE ABAS INTEGRADAS BLINDADO ---
with st.expander("📂 Clique aqui para ADICIONAR novas aulas dadas à tabela existente (Upload Excel)"):
    arquivo_updated = st.file_uploader("Arraste as novas aulas dadas aqui", type=["xlsx"])
    if arquivo_updated is not None:
        try:
            abas_finais = {}
            if os.path.exists(excel_file):
                try:
                    xls_antigo = pd.ExcelFile(excel_file)
                    for nome_aba in xls_antigo.sheet_names:
                        df_carregado = pd.read_excel(excel_file, sheet_name=nome_aba)
                        if not df_carregado.empty:
                            abas_finais[nome_aba] = df_carregado
                except:
                    pass

            xls_novo = pd.ExcelFile(arquivo_updated)
            for nome_aba in xls_novo.sheet_names:
                df_nova_aba = pd.read_excel(arquivo_updated, sheet_name=nome_aba)
                
                if not df_nova_aba.empty and 'Data' in df_nova_aba.columns:
                    df_nova_aba['Data'] = pd.to_datetime(df_nova_aba['Data'], dayfirst=True, errors='coerce')
                    df_nova_aba.dropna(subset=['Data'], inplace=True)
                    
                    if nome_aba in abas_finais:
                        df_antiga_aba = abas_finais[nome_aba]
                        df_antiga_aba['Data'] = pd.to_datetime(df_antiga_aba['Data'], dayfirst=True, errors='coerce')
                        
                        df_unificado = pd.concat([df_antiga_aba, df_nova_aba], ignore_index=True)
                        df_unificado.drop_duplicates(subset=['Data', 'Disciplina'], keep='last', inplace=True)
                        abas_finais[nome_aba] = df_unificado
                    else:
                        df_nova_aba.drop_duplicates(subset=['Data', 'Disciplina'], keep='last', inplace=True)
                        abas_finais[nome_aba] = df_nova_aba

            if not abas_finais:
                st.error("⚠️ O arquivo enviado não contém uma coluna válida chamada 'Data' ou está totalmente vazio.")
            else:
                with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                    for nome_aba, df_gravar in abas_finais.items():
                        df_gravar['Data'] = pd.to_datetime(df_gravar['Data'], errors='coerce')
                        df_gravar['Data'] = df_gravar['Data'].dt.strftime('%Y-%m-%d')
                        df_gravar.to_excel(writer, sheet_name=nome_aba, index=False)
                        
                st.success("✓ Dados salvos com sucesso! Todas as turmas foram integradas.")
                st.rerun()
        except Exception as e:
            st.error(f"Erro ao salvar arquivo: {e}")


# -------------------------------------------------------------
# CONTINUAÇÃO DO CÓDIGO (COLE LOGO ABAIXO DA PARTE 1 NO MESMO ARQUIVO)
# -------------------------------------------------------------

# Bloco de segurança para abrir o arquivo integrado
try:
    xls = pd.ExcelFile(excel_file)
    turmas_disponiveis = sorted(xls.sheet_names)
except:
    st.warning("Aguardando arquivo de dados padrão ou upload inicial...")
    st.stop()

# --- FILTROS SIDEBAR ---
st.sidebar.header("Filtros")
turma_selecionada = st.sidebar.selectbox("Selecione a Turma", turmas_disponiveis)

df_turma = pd.read_excel(excel_file, sheet_name=turma_selecionada)
df_turma["Data"] = pd.to_datetime(df_turma["Data"], errors='coerce')

disciplinas = sorted(df_turma["Disciplina"].dropna().unique().tolist())
disciplina_selecionada = st.sidebar.selectbox("Selecione a Disciplina", disciplinas)

col_m1, col_m2 = st.sidebar.columns(2)
with col_m1:
    mes = st.selectbox("Mês", range(1, 13), format_func=lambda x: MESES_PT[x], index=9)
with col_m2:
    ano = st.number_input("Ano", value=2026, min_value=2024, max_value=2030)

if mes != st.session_state.mes_anterior or ano != st.session_state.ano_anterior:
    st.session_state.dia_selecionado = None
    st.session_state.mes_anterior = mes
    st.session_state.ano_anterior = ano

# --- PROCESSAMENTO DOS REGISTROS ---
df_filtrado_disc = df_turma[df_turma["Disciplina"] == disciplina_selecionada]
df_ano = df_filtrado_disc[df_filtrado_disc["Data"].dt.year == ano]
total_periodos_ano = len(df_ano)

df_mes = df_ano[df_ano["Data"].dt.month == mes]
total_periodos_mes = len(df_mes)

# Interface de Métricas (Top)
st.markdown(f"""
    <table style='width:100%; border:none; margin-bottom:20px;'>
        <tr>
            <td style='width:50%; border:none;'>
                <div class='card-metrica-topo'>
                    <span style='font-size:14px; color:#a7f3d0;'>Total no Mês ({MESES_PT[mes]})</span><br>
                    <span style='font-size:32px; font-weight:bold; color:#39ff14;'>{total_periodos_mes} pd</span>
                </div>
            </td>
            <td style='width:50%; border:none;'>
                <div class='card-metrica-topo'>
                    <span style='font-size:14px; color:#a7f3d0;'>Total no Ano ({ano})</span><br>
                    <span style='font-size:32px; font-weight:bold; color:#39ff14;'>{total_periodos_ano} pd</span>
                </div>
            </td>
        </tr>
    </table>
""", unsafe_allow_html=True)

st.markdown(f"### Turma: {turma_selecionada} | Disciplina: {disciplina_selecionada}")
st.markdown(f"#### {MESES_PT[mes]} de {ano}")

aulas_por_dia = {}
for idx, row in df_mes.iterrows():
    if pd.notna(row["Data"]):
        d = row["Data"].day
        aulas_por_dia[d] = aulas_por_dia.get(d, 0) + 1

# --- CONSTRUÇÃO DA GRADE DO CALENDÁRIO ---
cal = calendar.Calendar(firstweekday=0)
semanas = cal.monthdayscalendar(ano, mes)

dias_semana_labels = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
col_headers = st.columns(7)
for c_idx, label in enumerate(dias_semana_labels):
    with col_headers[c_idx]:
        st.markdown(f"<div class='btn-cal-header'><button disabled>{label}</button></div>", unsafe_allow_html=True)

for semana in semanas:
    cols_dias = st.columns(7)
    for c_idx, dia_num in enumerate(semana):
        with cols_dias[c_idx]:
            if dia_num == 0:
                st.markdown("<div class='btn-cal-vazio'><button disabled style='opacity:0;'></button></div>", unsafe_allow_html=True)
            else:
                if dia_num in aulas_por_dia:
                    label_botao = f"{dia_num:02d}\n{aulas_por_dia[dia_num]} pd"
                    classe_css = "btn-cal-neon"
                else:
                    label_botao = f"{dia_num:02d}"
                    classe_css = "btn-cal-vazio"
                
                st.markdown(f"<div class='{classe_css}'>", unsafe_allow_html=True)
                if st.button(label_botao, key=f"btn_dia_{dia_num}_{mes}_{ano}"):
                    st.session_state.dia_selecionado = dia_num
                st.markdown("</div>", unsafe_allow_html=True)

# --- FORMULÁRIO DE LANÇAMENTO INFERIOR ---
st.write("---")
dia_escolhido = st.session_state.dia_selecionado

if dia_escolhido is not None:
    st.markdown(f"<div class='caixa-dia-foco'>⚡ Dia Selecionado para Gerenciamento: {dia_escolhido:02d}/{mes:02d}/{ano}</div>", unsafe_allow_html=True)
    data_alvo = pd.to_datetime(f"{ano}-{mes}-{dia_escolhido}")
    registro_existente = df_mes[df_mes["Data"] == data_alvo]
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        nova_disciplina = st.text_input("Disciplina do Lançamento", value=disciplina_selecionada)
    with col_f2:
        periodos_sugeridos = int(len(registro_existente)) if not registro_existente.empty else 1
        num_periodos = st.number_input("Quantidade de Períodos", min_value=1, max_value=10, value=max(1, periodos_sugeridos))
        
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        if st.button("💾 Salvar/Alterar Registro"):
            df_limpo = df_turma[~((df_turma["Data"] == data_alvo) & (df_turma["Disciplina"] == nova_disciplina))]
            novas_linhas = [{"Data": data_alvo, "Disciplina": nova_disciplina} for _ in range(num_periodos)]
            df_final_turma = pd.concat([df_limpo, pd.DataFrame(novas_linhas)], ignore_index=True)
            
            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                for nome_aba in turmas_disponiveis:
                    if nome_aba == turma_selecionada:
                        df_final_turma["Data"] = df_final_turma["Data"].dt.strftime('%Y-%m-%d')
                        df_final_turma.to_excel(writer, sheet_name=nome_aba, index=False)
                    else:
                        pd.read_excel(excel_file, sheet_name=nome_aba).to_excel(writer, sheet_name=nome_aba, index=False)
            st.success("✓ Registro atualizado!")
            st.rerun()
            
    with col_b2:
        if st.button("🗑️ Deletar Aula do Calendário"):
            df_restante = df_turma[~((df_turma["Data"] == data_alvo) & (df_turma["Disciplina"] == disciplina_selecionada))]
            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                for nome_aba in turmas_disponiveis:
                    if nome_aba == turma_selecionada:
                        df_restante["Data"] = df_restante["Data"].dt.strftime('%Y-%m-%d')
                        df_restante.to_excel(writer, sheet_name=nome_aba, index=False)
                    else:
                        pd.read_excel(excel_file, sheet_name=nome_aba).to_excel(writer, sheet_name=nome_aba, index=False)
            st.session_state.dia_selecionado = None
            st.rerun()
else:
    st.info("💡 Clique em qualquer botão de dia na grade do calendário acima para gerenciar os dados.")
