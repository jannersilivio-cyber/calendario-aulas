import calendar
from datetime import datetime
import os
import pandas as pd
import streamlit as st

# Configuração da página do aplicativo
st.set_page_config(
    page_title="Calendário Dinâmico de Aulas", layout="centered"
)

# Inicializar o estado do dia selecionado se não existir
if "dia_selecionado" not in st.session_state:
    st.session_state.dia_selecionado = None

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
# INJEÇÃO DE CSS REFINADO (FIX DO AZUL SAFIRA LOCAL + LARANJA)
# -------------------------------------------------------------
st.markdown("""
    <style>
    /* Configuração de fundo escuro profundo */
    .stApp {
        background-color: #050a07 !important;
    }
    
    /* Textos principais e títulos do sistema */
    h1, h2, h3, p, span, label {
        color: #f0fdf4 !important;
    }
    
    /* FIX DE ALINHAMENTO: Força todas as colunas de 7 dias a terem o mesmo comportamento e grid */
    [data-testid="stHorizontalBlock"] {
        gap: 8px !important;
        padding-left: 0px !important;
        padding-right: 0px !important;
    }
    
    div.btn-cal-header, div.btn-cal-neon, div.btn-cal-vazio {
        width: 100% !important;
    }

    /* ESTILO DO CABEÇALHO DA SEMANA */
    div.btn-cal-header button {
        background-color: transparent !important;
        color: #39ff14 !important;
        border: none !important;
        font-weight: bold !important;
        font-size: 16px !important;
        height: 45px !important;
        width: 100% !important;
        text-align: center !important;
        opacity: 1 !important;
        box-shadow: none !important;
        transform: none !important;
        cursor: default !important;
    }
    
    /* 🟢 SELETOR NEON: Botões com aula */
    div.btn-cal-neon button, div.btn-cal-neon button[data-testid="baseButton-secondary"] {
        background-color: rgba(57, 255, 20, 0.08) !important;
        backdrop-filter: blur(8px) !important;
        -webkit-backdrop-filter: blur(8px) !important;
        color: #ffffff !important;
        border: 1px solid rgba(57, 255, 20, 0.4) !important;
        border-radius: 8px !important;
        width: 100% !important;
        height: 75px !important;
        padding: 4px 0px !important;
        font-size: 22px !important;
        line-height: 1.1 !important;
        font-weight: bold !important;
        white-space: pre-wrap !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        align-items: center !important;
        box-shadow: 0 0 14px rgba(57, 255, 20, 0.3), inset 0 0 8px rgba(57, 255, 20, 0.1) !important;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    }
    div.btn-cal-neon button:hover, div.btn-cal-neon button[data-testid="baseButton-secondary"]:hover {
        background-color: rgba(57, 255, 20, 0.22) !important;
        border-color: #39ff14 !important;
        box-shadow: 0 0 24px rgba(57, 255, 20, 0.6), 0 0 34px rgba(57, 255, 20, 0.3) !important;
        transform: scale(1.04) !important;
    }

    /* 🔵 CAPTURA LOCAL FORÇADA: DIAS VAZIOS (Efeito Vidro Azul Safira Elétrico) */
    div.btn-cal-vazio button, div[class*="st-key-btn_vazio_"] button, div.btn-cal-vazio button[data-testid="baseButton-secondary"] {
        background-color: rgba(0, 150, 255, 0.12) !important; /* Fundo azul safira nítido */
        backdrop-filter: blur(8px) !important;
        -webkit-backdrop-filter: blur(8px) !important;
        color: #d1e6ff !important;
        border: 1px solid rgba(0, 150, 255, 0.45) !important; /* Borda azul perceptível */
        border-radius: 8px !important;
        width: 100% !important;
        height: 75px !important;
        font-size: 22px !important;
        font-weight: bold !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        box-shadow: 0 0 8px rgba(0, 150, 255, 0.1) !important;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    }
    div.btn-cal-vazio button:hover, div[class*="st-key-btn_vazio_"] button:hover {
        background-color: rgba(0, 150, 255, 0.25) !important;
        color: #ffffff !important;
        border-color: #00ccff !important;
        box-shadow: 0 0 22px rgba(0, 204, 255, 0.6) !important;
        transform: translateY(-2px) !important;
    }
    
    /* 🟠 DESTAQUE CYBERPUNK: Caixa do Dia Selecionado no Painel de Ajustes */
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
    
    /* BLOCO DE MÉTRICAS DO TOPO */
    .card-metrica-topo {
        background-color: rgba(255, 255, 255, 0.02) !important;
        backdrop-filter: blur(6px) !important;
        border: 1px solid rgba(57, 255, 20, 0.2) !important;
        border-radius: 8px;
        padding: 12px;
        text-align: center;
    }
    
    /* Botões do painel inferior */
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

# Nome do arquivo local padrão
excel_file = "Quantidade_de_Aulas_por_Dia_Novas_Disciplinas.xlsx"

# 📁 Controle de Upload e Anexação de dados
with st.expander("📁 Clique aqui para ADICIONAR novas aulas dadas à tabela existente (Upload Excel)"):
    arquivo_updated = st.file_uploader("Arraste as novas aulas dadas aqui", type=["xlsx"])
    if arquivo_updated is not None:
        try:
            xls_novo = pd.ExcelFile(arquivo_updated)
            turmas_novas = xls_novo.sheet_names
            dados_consolidados = {}
            if os.path.exists(excel_file):
                xls_antigo = pd.ExcelFile(excel_file)
                for t in xls_antigo.sheet_names:
                    dados_consolidados[t] = pd.read_excel(excel_file, sheet_name=t)
            for t in turmas_novas:
                df_n = pd.read_excel(arquivo_updated, sheet_name=t)
                df_n["Data"] = pd.to_datetime(df_n["Data"])
                if t in dados_consolidados:
                    df_c = pd.concat([dados_consolidados[t], df_n], ignore_index=True)
                    dados_consolidados[t] = df_c.drop_duplicates(subset=["Data", "Disciplina"], keep="last")
                else:
                    dados_consolidados[t] = df_n.drop_duplicates(subset=["Data", "Disciplina"], keep="last")
            with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
                for t, df_f in dados_consolidados.items():
                    df_f["Data"] = pd.to_datetime(df_f["Data"]).dt.strftime("%Y-%m-%d")
                    df_f.to_excel(writer, sheet_name=t, index=False)
            st.success("Novos dados consolidados com sucesso!")
        except Exception as e:
            st.error(f"Erro no processamento: {e}")

try:
    xls = pd.ExcelFile(excel_file)
    turmas_disponiveis = xls.sheet_names
except:
    st.stop()
# 2. Controles de Seleção na Barra Lateral (Sidebar)
st.sidebar.header("Filtros")
turma_selecionada = st.sidebar.selectbox("Selecione a Turma", turmas_disponiveis)

df_turma = pd.read_excel(excel_file, sheet_name=turma_selecionada)
df_turma["Data"] = pd.to_datetime(df_turma["Data"])

disciplinas = sorted(df_turma["Disciplina"].dropna().unique().tolist())
disciplina_selecionada = st.sidebar.selectbox("Selecione a Disciplina", disciplinas)

col_m1, col_m2 = st.sidebar.columns(2)
with col_m1:
    mes = st.selectbox("Mês", range(1, 13), format_func=lambda x: MESES_PT[x], index=9)
with col_m2:
    ano = st.number_input("Ano", value=2026, min_value=2024, max_value=2030)

col_qtd = "Quantidade de Aulas" if "Quantidade de Aulas" in df_turma.columns else "Quantidade"

# Salvar alterações
def salvar_banco_dados(df_atualizado, turma):
    all_sheets = {}
    with pd.ExcelFile(excel_file) as reader:
        for s in reader.sheet_names:
            all_sheets[s] = df_atualizado if s == turma else pd.read_excel(excel_file, sheet_name=s)
    with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
        for s, df_save in all_sheets.items():
            df_save["Data"] = pd.to_datetime(df_save["Data"]).dt.strftime("%Y-%m-%d")
            df_save.to_excel(writer, sheet_name=s, index=False)

# Filtragem de dados
df_filtrado = df_turma[(df_turma["Disciplina"] == disciplina_selecionada) & (df_turma["Data"].dt.month == mes) & (df_turma["Data"].dt.year == ano)].copy()
aulas_por_dia = {}
if not df_filtrado.empty:
    df_filtrado["Dia"] = df_filtrado["Data"].dt.day
    aulas_por_dia = df_filtrado.groupby("Dia")[col_qtd].sum().to_dict()

# Painel de Métricas Superior
df_ano_total = df_turma[(df_turma["Disciplina"] == disciplina_selecionada) & (df_turma["Data"].dt.year == ano)]
total_aulas_mes = df_filtrado[col_qtd].sum() if not df_filtrado.empty else 0
total_aulas_ano = df_ano_total[col_qtd].sum() if not df_ano_total.empty else 0

col_ind1, col_ind2 = st.columns(2)
with col_ind1:
    st.markdown(f"<div class='card-metrica-topo'><span style='font-size: 14px; color: #a7f3d0;'>Total no Mês ({MESES_PT[mes]})</span><br><span style='font-size: 24px; color: #39ff14; font-weight: bold;'>{int(total_aulas_mes)} pd</span></div>", unsafe_allow_html=True)
with col_ind2:
    st.markdown(f"<div class='card-metrica-topo'><span style='font-size: 14px; color: #a7f3d0;'>Total no Ano ({ano})</span><br><span style='font-size: 24px; color: #39ff14; font-weight: bold;'>{int(total_aulas_ano)} pd</span></div>", unsafe_allow_html=True)

st.subheader(f"Turma: {turma_selecionada} | Disciplina: {disciplina_selecionada}")
st.markdown(f"### {MESES_PT[mes]} de {ano}")

cal = calendar.Calendar(firstweekday=0)
mes_matriz = cal.monthdayscalendar(ano, mes)
dias_semana = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

# Renderizar cabeçalho da semana usando a mesma proporção st.columns(7) para obter alinhamento perfeito
cols_header = st.columns(7)
for i, dia_nome in enumerate(dias_semana):
    with cols_header[i]:
        st.markdown("<div class='btn-cal-header'>", unsafe_allow_html=True)
        st.button(dia_nome, key=f"head_{dia_nome}", disabled=True)
        st.markdown("</div>", unsafe_allow_html=True)

# Renderizar Grade Interativa do Calendário
for semana in mes_matriz:
    cols_dias = st.columns(7)
    for i, dia in enumerate(semana):
        with cols_dias[i].container():
            if dia == 0:
                st.markdown("&nbsp;")
            else:
                if dia in aulas_por_dia:
                    qtd_pd = int(aulas_por_dia[dia])
                    st.markdown("<div class='btn-cal-neon'>", unsafe_allow_html=True)
                    label_com_aula = f"{dia}\n\n({qtd_pd} pd)"
                    if st.button(label_com_aula, key=f"btn_dia_{dia}"):
                        st.session_state.dia_selecionado = dia
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='btn-cal-vazio'>", unsafe_allow_html=True)
                    if st.button(f"{dia}", key=f"btn_vazio_{dia}"):
                        st.session_state.dia_selecionado = dia
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

# 🛠️ PAINEL INTERATIVO DE GERENCIAMENTO (CONECTADO E SINCRONIZADO VIA CLIQUE)
st.subheader("🛠️ Painel de Lançamento e Ajustes")

if st.session_state.dia_selecionado is not None:
    dia_foco = st.session_state.dia_selecionado
    st.markdown(f"<div class='caixa-dia-foco'>📆 Dia selecionado no calendário: {dia_foco} de {MESES_PT[mes]}</div>", unsafe_allow_html=True)
    
    if dia_foco in aulas_por_dia:
        periodos_atuais = int(aulas_por_dia[dia_foco])
        st.markdown(f"Status: Esse dia possui **{periodos_atuais} períodos** registrados de {disciplina_selecionada}.")
        
        novo_valor_periodos = st.number_input("Alterar quantidade de períodos para:", min_value=1, max_value=10, value=periodos_atuais, key="num_direct_edit")
        
        col_act1, col_edit_sp = st.columns(2)
        with col_act1:
            if st.button("💾 Gravar Alteração"):
                data_alvo = pd.to_datetime(f"{ano}-{mes}-{dia_foco}")
                df_turma.loc[(df_turma["Data"] == data_alvo) & (df_turma["Disciplina"] == disciplina_selecionada), col_qtd] = novo_valor_periodos
                salvar_banco_dados(df_turma, turma_selecionada)
                st.success("Lançamento atualizado com sucesso!")
                st.session_state.dia_selecionado = None
                st.rerun()
        with col_edit_sp:
            if st.button("🗑️ Excluir Aula Deste Dia", type="primary"):
                data_alvo = pd.to_datetime(f"{ano}-{mes}-{dia_foco}")
                df_removido = df_turma[~((df_turma["Data"] == data_alvo) & (df_turma["Disciplina"] == disciplina_selecionada))]
                salvar_banco_dados(df_removido, turma_selecionada)
                st.success("Lançamento removido do Excel!")
                st.session_state.dia_selecionado = None
                st.rerun()
    else:
        st.markdown(f"Status: Não há aulas de {disciplina_selecionada} registradas neste dia.")
        periodos_novos = st.number_input("Inserir quantidade de períodos dados:", min_value=1, max_value=10, value=1, key="num_direct_inc")
        
        if st.button("🚀 Registrar Nova Aula"):
            data_nova = pd.to_datetime(f"{ano}-{mes}-{dia_foco}")
            nova_linha = {"Data": data_nova, "Disciplina": disciplina_selecionada, col_qtd: periodos_novos}
            salvar_banco_dados(pd.concat([df_turma, pd.DataFrame([nova_linha])], ignore_index=True), turma_selecionada)
            st.success("Nova aula cadastrada com sucesso!")
            st.session_state.dia_selecionado = None
            st.rerun()
else:
    st.info("💡 Clique em cima de qualquer dia do calendário acima para abrir as opções de incluir, alterar ou excluir períodos de aula.")
