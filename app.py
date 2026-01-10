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

# --- TABELA DE RESERVAS E CANCELAMENTO (MANTIDA ORIGINAL) ---

st.subheader(f"📅 Agenda de Reservas: Quarto {quarto_selecionado}")

dados = listar_reservas(quarto_selecionado)

if dados:
    tabela_dados = []
    for item in dados:
        # item[5] é a coluna valor_total vinda do banco
        valor_formatado = f"R$ {item[5]:.2f}" if len(item) > 5 and item[5] is not None else "R$ 0.00"
        
        tabela_dados.append({
            "ID": item[0],
            "Cliente": item[2],
            "Entrada": item[3].strftime("%d/%m/%Y"), # Formatação visual na tabela também
            "Saída": item[4].strftime("%d/%m/%Y"),
            "Valor Total": valor_formatado
        })
    st.table(tabela_dados)
    
    # --- ÁREA DE CANCELAMENTO ---
    st.warning("Zona de Cancelamento")
    
    col_cancel1, col_cancel2 = st.columns([3, 1])
    
    with col_cancel1:
        lista_ids = [item[0] for item in dados]
        id_para_cancelar = st.selectbox("Selecione o ID da reserva para cancelar:", lista_ids)
        
    with col_cancel2:
        st.write("") 
        st.write("") 
        if st.button("🗑️ Cancelar Reserva"):
            sucesso, msg = cancelar_reserva(id_para_cancelar)
            if sucesso:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)
                
else:
    st.info(f"Nenhuma reserva futura encontrada para o Quarto {quarto_selecionado}.")