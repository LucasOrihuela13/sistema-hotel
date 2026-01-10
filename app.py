import streamlit as st
import datetime
import time
# Importamos as funções do backend
from funcoes import reservar_quarto, listar_reservas, verificar_disponibilidade, cancelar_reserva, buscar_quartos_ocupados

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sistema de Hotel", layout="wide")

# --- SISTEMA DE LOGIN ---
def check_password():
    """Retorna True se o usuário tiver a senha correta."""
    if st.session_state.get('password_correct', False):
        return True

    st.header("🔒 Acesso Restrito - Hotel")
    senha_digitada = st.text_input("Digite a senha de acesso", type="password")
    
    if st.button("Entrar"):
        # Garante que busca na seção [geral] conforme seu secrets atual
        senha_secreta = st.secrets["geral"]["senha_site"]
        if senha_digitada == senha_secreta:  
            st.session_state['password_correct'] = True
            st.rerun()
        else:
            st.error("Senha incorreta.")
    return False

if not check_password():
    st.stop()

# --- INÍCIO DO SISTEMA ---
st.title("🏨 Sistema de Gerenciamento de Hotel")

# --- BARRA LATERAL (NOVA RESERVA) ---
with st.sidebar:
    st.header("Nova Reserva")
    
    # 1. CRIAÇÃO DO FORMULÁRIO (Resolve latência e cliques múltiplos)
    with st.form("form_reserva"):
        quarto_selecionado = st.selectbox("Escolha o Quarto", [1, 2, 3, 4, 5, 6])
        nome_cliente = st.text_input("Nome do Cliente")
        
        col1, col2 = st.columns(2)
        with col1:
            # 2. DATA FORMATADA (DD/MM/YYYY)
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

        # Botão de envio vinculado ao formulário
        enviado = st.form_submit_button("Confirmar Reserva")

    # LÓGICA DE ENVIO (Só roda ao clicar)
    if enviado:
        hoje = datetime.date.today()
        
        # 3. VALIDAÇÕES DE SEGURANÇA (Datas passadas e lógicas)
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
                sucesso, mensagem = reservar_quarto(
                    quarto_selecionado, 
                    nome_cliente, 
                    entrada_str, 
                    saida_str, 
                    valor_diaria
                )
            
            if sucesso:
                # 4. DATAS BONITAS NA MENSAGEM DE SUCESSO
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

# Consulta otimizada
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

# --- ÁREA DE LISTAGEM COM ABAS ---
st.write("---") 
st.header("Gerenciamento de Reservas") # Mudei o título para ficar genérico

tab_ativas, tab_historico = st.tabs(["📅 Reservas Ativas/Futuras", "📂 Histórico Completo"])

# --- ABA 1: RESERVAS ATIVAS ---
with tab_ativas:
    # --- NOVO: CONTROLE DE FILTRO ---
    col_filtro, col_vazia = st.columns([2, 3])
    with col_filtro:
        tipo_filtro = st.radio(
            "Filtrar lista por:",
            ["Todos os Quartos", f"Apenas Quarto {quarto_selecionado} (Selecionado)"],
            horizontal=True
        )
    
    # Define o ID para busca com base na escolha
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
            
            tabela_ativas.append({
                "ID": item[0],
                "Quarto": item[2], # Importante ver o número do quarto agora!
                "Cliente": item[3],
                "Entrada": item[4].strftime("%d/%m/%Y"),
                "Saída": item[5].strftime("%d/%m/%Y"),
                "Valor Total": val_formatado
            })
        st.table(tabela_ativas)
        
        # --- ÁREA DE CANCELAMENTO ---
        st.warning("Zona de Cancelamento")
        c1, c2 = st.columns([3, 1])
        with c1:
            # Lista IDs disponíveis na visualização atual
            ids_disponiveis = [d[0] for d in dados_ativos]
            # Formata o selectbox para mostrar "ID - Cliente (Quarto)"
            # Isso ajuda a não apagar a reserva errada na visão geral
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
    # Repetimos a lógica do filtro para o histórico também
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
            
            tabela_hist.append({
                "ID": item[0],
                "Quarto": item[2],
                "Cliente": item[3],
                "Entrou em": item[4].strftime("%d/%m/%Y"),
                "Saiu em": item[5].strftime("%d/%m/%Y"),
                "Valor Pago": val_formatado
            })
        
        st.dataframe(tabela_hist, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum histórico encontrado.")