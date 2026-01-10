import psycopg2
import streamlit as st
from datetime import datetime

# --- CONEXÃO COM A NUVEM (SUPABASE) ---
def conectar():
    db_config = st.secrets["postgres"]
    
    return psycopg2.connect(
        host=db_config["host"],
        user=db_config["user"],
        password=db_config["password"],
        dbname=db_config["dbname"],
        port=db_config["port"]
    )

# --- BUSCA DE QUARTOS ---
# Consulta o banco toda vez que a página carrega.
def buscar_quartos_ocupados(data_entrada, data_saida):
    conn = conectar()
    cursor = conn.cursor()
    
    query = """
        SELECT DISTINCT quarto_id FROM reservas
        WHERE data_entrada < %s
        AND data_saida > %s
    """
    
    cursor.execute(query, (data_saida, data_entrada))
    quartos_ocupados = [item[0] for item in cursor.fetchall()]
    
    cursor.close()
    conn.close()
    
    return quartos_ocupados

# --- VERIFICAÇÃO DE DISPONIBILIDADE ---
def verificar_disponibilidade(quarto_id, data_entrada, data_saida):
    conn = conectar()
    cursor = conn.cursor()
    
    query = """
        SELECT count(*) FROM reservas
        WHERE quarto_id = %s
        AND data_entrada < %s
        AND data_saida > %s
    """
    
    cursor.execute(query, (quarto_id, data_saida, data_entrada))
    resultado = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    
    return resultado == 0

# --- FAZER RESERVA (COM ANTI-SPAM) ---
def reservar_quarto(quarto_id, nome_cliente, data_entrada, data_saida, valor_diaria):
    conn = conectar()
    cursor = conn.cursor()
    
    try:
        # 1. Checagem de Disponibilidade
        if not verificar_disponibilidade(quarto_id, data_entrada, data_saida):
            return False, "❌ O quarto foi ocupado por outra pessoa neste exato momento!"

        # 2. Checagem Anti-Duplicidade
        query_spam = """
            SELECT id FROM reservas 
            WHERE quarto_id = %s AND data_entrada = %s AND cliente_nome = %s
        """
        cursor.execute(query_spam, (quarto_id, data_entrada, nome_cliente))
        if cursor.fetchone():
            return False, "⚠️ Essa reserva já foi processada! (Evitamos a duplicação)"

        # 3. Cálculo do Valor Total
        d1 = datetime.strptime(data_entrada, "%Y-%m-%d")
        d2 = datetime.strptime(data_saida, "%Y-%m-%d")
        dias = (d2 - d1).days
        if dias == 0: dias = 1
        
        valor_total = dias * float(valor_diaria)
        
        # 4. Gravação no Banco (Usando cliente_nome correto)
        query_insert = """
            INSERT INTO reservas (quarto_id, cliente_nome, data_entrada, data_saida, valor_total)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query_insert, (quarto_id, nome_cliente, data_entrada, data_saida, valor_total))
        
        conn.commit()
        status = True
        mensagem = f"✅ Reserva Confirmada! Total: R$ {valor_total:.2f}"

    except Exception as e:
        conn.rollback()
        status = False
        mensagem = f"Erro ao gravar no banco: {e}"
        
    finally:
        cursor.close()
        conn.close()
        
    return status, mensagem

# --- LISTAR RESERVAS ---
def listar_reservas(quarto_id=None, apenas_historico=False):
    conn = conectar()
    cursor = conn.cursor()
    
    hoje = datetime.now().date()
    
    # Começamos uma query base
    # O "WHERE 1=1" é um truque para poder adicionar "ANDs" depois sem medo
    query = "SELECT * FROM reservas WHERE 1=1"
    params = []

    # FILTRO 1: Quarto Específico
    if quarto_id:
        query += " AND quarto_id = %s"
        params.append(quarto_id)

    # FILTRO 2: Separação de Tempo
    if apenas_historico:
        # Histórico = Data de Saída já passou
        query += " AND data_saida < %s"
        params.append(hoje)
        # Ordena do mais recente para o mais antigo
        query += " ORDER BY data_saida DESC"
    else:
        # Ativas = Data de Saída é hoje ou no futuro
        query += " AND data_saida >= %s"
        params.append(hoje)
        # Ordena da data mais próxima para a mais distante
        query += " ORDER BY data_entrada ASC"

    cursor.execute(query, tuple(params))
    dados = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return dados

# --- CANCELAR RESERVA ---
def cancelar_reserva(reserva_id):
    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM reservas WHERE id = %s", (reserva_id,))
        conn.commit()
        status = True
        mensagem = "✅ Reserva cancelada com sucesso!"
    except Exception as e:
        conn.rollback()
        status = False
        mensagem = f"Erro ao cancelar: {e}"
    finally:
        cursor.close()
        conn.close()
    return status, mensagem