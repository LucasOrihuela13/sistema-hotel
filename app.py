import streamlit as st
import datetime
import time
from funcoes import reservar_quarto, listar_reservas, buscar_quartos_ocupados, cancelar_reserva

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sistema de Hotel", layout="wide", page_icon="🏨")

# Esconde menu padrão para dar cara de App profissional
# Adicionei 'initial_sidebar_state="expanded"' para garantir que ela comece aberta
st.set_page_config(
    page_title="Sistema de Hotel", 
    layout="wide", 
    page_icon="🏨",
    initial_sidebar_state="expanded" 
)

# Esconde menu e rodapé, mas MANTÉM o botão de navegação
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            /* header {visibility: hidden;}  <-- ESSA LINHA FOI REMOVIDA */
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- SISTEMA DE LOGIN ---
def check_password():
    """Retorna True se o usuário tiver a senha correta."""
    if st.session_state.get('password_correct', False):
        return True

    st.header("🔒 Acesso Restrito - Hotel")
    senha_digitada = st.text_input("Digite a senha de acesso", type="password")
    
    if st.button("Entrar"):
        # 1. Tenta buscar a senha no secrets
        senha_secreta = None
        try:
            # Tenta buscar na seção [geral]
            senha_secreta = st.secrets["geral"]["senha_site"]
        except (KeyError, FileNotFoundError):
            # Se não achar, tenta buscar na raiz (caso o secrets esteja antigo)
            senha_secreta = st.secrets.get("senha_site")

        # 2. Verifica se a senha foi encontrada no arquivo
        if not senha_secreta:
            st.error("Erro: Senha não configurada no secrets.toml. Verifique o arquivo.")
            return False

        # 3. Compara as senhas (FORA do try/except para o rerun funcionar)
        if senha_digitada == senha_secreta:  
            st.session_state['password_correct'] = True
            st.rerun() # Agora sim, o rerun acontece livremente!
        else:
            st.error("Senha incorreta.")
            
    return False

if not check_password():
    st.stop()

# --- INÍCIO DO SISTEMA ---
st.title("🏨 Sistema de Gerenciamento de Hotel")

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("Recepção")
    
    # 1. SELETOR GLOBAL (FORA DO FORMULÁRIO)
    # Ao mudar aqui, a tabela lá embaixo atualiza instantaneamente
    quarto_selecionado = st.selectbox(
        "Selecione o Quarto para Gerenciar:", 
        [1, 2, 3, 4, 5, 6]
    )
    
    st.divider() # Linha visual
    
    st.subheader("Fazer Nova Reserva")
    
    # 2. FORMULÁRIO DE CADASTRO
    with st.form("form_reserva", clear_on_submit=False, enter_to_submit=False):
        st.info(f"Reservando: **Quarto {quarto_selecionado}**")
        
        # Dados do Cliente
        nome_cliente = st.text_input("Nome do Cliente")
        
        # --- NOVOS CAMPOS ---
        telefone = st.text_input("Telefone / WhatsApp", placeholder="(XX) 9XXXX-XXXX")
        qtd_pessoas = st.number_input("Qtd. Hóspedes", min_value=1, value=1, step=1)
        # --------------------
        
        col1, col2 = st.columns(2)
        with col1:
            data_entrada = st.date_input(
                "Data Entrada", 
                datetime.date.today(),
                format="DD/MM/YYYY"
            )
        with col2:
            data_saida = st.date_input(
                "Data Saída", 
                datetime.date.today() + datetime.timedelta(days=1),
                format="DD/MM/YYYY"
            )
        
        valor_diaria = st.number_input("Valor da Diária (R$)", min_value=0.0, value=100.0, step=10.0)

        # Botão de envio
        enviado = st.form_submit_button("Confirmar Reserva")

    # LÓGICA DE ENVIO
    if enviado:
        hoje = datetime.date.today()
        
        # 3. VALIDAÇÕES DE SEGURANÇA
        if data_entrada < hoje:
            st.error("❌ Erro: Não é possível fazer reservas no passado!")
        elif data_saida <= data_entrada:
            st.error("❌ Erro: A data de saída deve ser depois da entrada!")
        elif not nome_cliente:
            st.error("❌ Erro: Digite o nome do cliente!")
        else:
            entrada_str = data_entrada.strftime("%Y-%m-%d")
            saida_str = data_saida.strftime("%Y-%m-%d")
            
            # Feedback de carregamento
            with st.spinner("Conectando ao banco de dados..."):
                # Passando os novos parâmetros para a função atualizada
                sucesso, mensagem = reservar_quarto(
                    quarto_selecionado, 
                    nome_cliente, 
                    telefone,     # <--- Novo
                    qtd_pessoas,  # <--- Novo
                    entrada_str, 
                    saida_str, 
                    valor_diaria
                )
            
            if sucesso:
                # Datas bonitas na mensagem
                entrada_br = data_entrada.strftime("%d/%m/%Y")
                saida_br = data_saida.strftime("%d/%m/%Y")
                st.success(f"✅ {mensagem} ({entrada_br} até {saida_br})")
                time.sleep(2) # Pausa para leitura
                st.rerun()
            else:
                st.error(mensagem)

# --- PAINEL PRINCIPAL (DASHBOARD) ---

st.subheader("Estado Atual dos Quartos (Hoje)")

hoje = datetime.date.today()
hoje_str = hoje.strftime("%Y-%m-%d")
amanha_str = (hoje + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

# Consulta otimizada para pintar os quadradinhos
lista_ocupados = buscar_quartos_ocupados(hoje_str, amanha_str)

cols = st.columns(6)

for i in range(6):
    numero_quarto = i + 1
    livre_hoje = numero_quarto not in lista_ocupados
    
    with cols[i]:
        if livre_hoje:
            st.success(f"**Quarto {numero_quarto}**\n\nLIVRE")
        else:
            st.error(f"**Quarto {numero_quarto}**\n\nOCUPADO")

# --- TABELA DE RESERVAS E CANCELAMENTO ---

st.write("---") 
st.header("Gerenciamento de Reservas")

tab_ativas, tab_historico = st.tabs(["📅 Reservas Ativas/Futuras", "📂 Histórico Completo"])

# --- ABA 1: RESERVAS ATIVAS ---
with tab_ativas:
    # --- CONTROLE DE FILTRO ---
    col_filtro, col_vazia = st.columns([2, 3])
    with col_filtro:
        tipo_filtro = st.radio(
            "Filtrar lista por:",
            ["Todos os Quartos", f"Apenas Quarto {quarto_selecionado} (Selecionado)"],
            horizontal=True
        )
    
    if tipo_filtro == "Todos os Quartos":
        id_busca = None
    else:
        id_busca = quarto_selecionado

    # Busca no banco
    dados_ativos = listar_reservas(id_busca, apenas_historico=False)
    
    if dados_ativos:
        tabela_ativas = []
        for item in dados_ativos:
            val_formatado = f"R$ {item[6]:.2f}" if len(item) > 6 and item[6] is not None else "R$ 0.00"
            
            tel_cliente = item[7] if len(item) > 7 and item[7] else "-"
            num_pessoas = item[8] if len(item) > 8 and item[8] else 1

            tabela_ativas.append({
                # "ID": item[0],  <-- REMOVIDO DAQUI (Só visualmente)
                "Quarto": item[2],
                "Cliente": item[3],
                "Contato": tel_cliente,
                "Hóspedes": num_pessoas, # Encurtei "Pessoas" para "Hóspedes" ou "Qtd" ajuda no mobile
                "Entrada": item[4].strftime("%d/%m"), # DICA: Tirei o ano (/2026) para economizar espaço
                "Saída": item[5].strftime("%d/%m"),   # DICA: Tirei o ano aqui também
                "Valor": val_formatado # Encurtei "Valor Total" para "Valor"
            })
            
        # MUDANÇA PRINCIPAL AQUI:
        # Usamos dataframe com hide_index=True (some o 0) e use_container_width (ocupa a tela toda)
        st.dataframe(tabela_ativas, hide_index=True, use_container_width=True)
        
        # --- ÁREA DE CANCELAMENTO ---
        st.warning("Zona de Cancelamento")
        c1, c2 = st.columns([3, 1])
        with c1:
            # A lógica continua funcionando porque usa 'dados_ativos' (que tem o ID),
            # e não 'tabela_ativas' (que é só para mostrar).
            ids_disponiveis = [d[0] for d in dados_ativos]
            
            # Aqui mantemos o ID visível para você saber qual cancelar
            mapa_rotulos = {d[0]: f"ID {d[0]} - {d[3]} (Quarto {d[2]})" for d in dados_ativos}
            
            id_cancelar = st.selectbox(
                "Selecione a reserva para cancelar:", 
                ids_disponiveis,
                format_func=lambda x: mapa_rotulos.get(x, x)
            )
            
        with c2:
            st.write("")
            st.write("") 
            if st.button("🗑️ Cancelar"):
                with st.spinner("Cancelando..."):
                    sucesso, msg = cancelar_reserva(id_cancelar)
                
                if sucesso:
                    st.success(msg)
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(msg)
    else:
        st.info("Nenhuma reserva encontrada para este filtro.")

# --- ABA 2: HISTÓRICO ---
with tab_historico:
    # Repetimos a lógica do filtro para o histórico
    col_hist, _ = st.columns([2, 3])
    with col_hist:
        filtro_hist = st.radio(
            "Ver histórico de:",
            ["Todos os Quartos", f"Apenas Quarto {quarto_selecionado}"],
            horizontal=True,
            key="radio_hist" # Key única para não conflitar com o de cima
        )
        
    if filtro_hist == "Todos os Quartos":
        id_busca_hist = None
    else:
        id_busca_hist = quarto_selecionado

    dados_hist = listar_reservas(id_busca_hist, apenas_historico=True)
    
    if dados_hist:
        tabela_hist = []
        for item in dados_hist:
            val_formatado = f"R$ {item[6]:.2f}" if len(item) > 6 and item[6] is not None else "R$ 0.00"
            
            tel_cliente = item[7] if len(item) > 7 and item[7] else "-"
            # Não mostramos qtd_pessoas no histórico para economizar espaço, 
            # mas se quiser é só adicionar igual fizemos acima.
            
            tabela_hist.append({
                "ID": item[0],
                "Quarto": item[2],
                "Cliente": item[3],
                "Contato": tel_cliente,      # <--- Exibindo no histórico
                "Entrou em": item[4].strftime("%d/%m/%Y"),
                "Saiu em": item[5].strftime("%d/%m/%Y"),
                "Valor Pago": val_formatado
            })
        
        st.dataframe(tabela_hist, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum histórico encontrado.")