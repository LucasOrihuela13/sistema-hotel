# 🏨 Sistema de Gerenciamento de Hotel

Um sistema web completo e responsivo desenvolvido em Python para gerenciar as reservas e a ocupação de um hotel de 6 quartos. O aplicativo foi projetado para ser utilizado na recepção do hotel, oferecendo uma interface rápida, segura e amigável tanto para desktops quanto para dispositivos móveis (tablets e smartphones).

## ✨ Funcionalidades

* **🔒 Autenticação de Usuário:** Acesso restrito por senha configurável via variáveis de ambiente.
* **📊 Dashboard em Tempo Real:** Visualização instantânea do status de todos os quartos (Livre/Ocupado) considerando o fuso horário local (UTC-3).
* **📝 Gestão de Reservas:**
  * Cadastro de clientes com nome, telefone/WhatsApp e quantidade de hóspedes.
  * Cálculo automático do valor total da estadia.
  * Proteção contra *double-booking* (reservas duplicadas ou quartos já ocupados).
  * Bloqueio de datas retroativas.
* **📅 Controle e Histórico:**
  * Visualização de reservas ativas e futuras em tabelas otimizadas para mobile.
  * Cancelamento de reservas em poucos cliques.
  * Histórico completo de reservas passadas.
* **🔄 Sincronização Sob Demanda:** Botão de refresh rápido para garantir que os dados estejam sempre atualizados caso haja múltiplos acessos.

## 🛠️ Tecnologias Utilizadas

* **Frontend & Backend:** [Streamlit](https://streamlit.io/) (Python)
* **Banco de Dados:** PostgreSQL hospedado na nuvem via [Supabase](https://supabase.com/)
* **Conector de Banco:** `psycopg2`
* **Deploy:** Streamlit Community Cloud

## 🗄️ Estrutura do Banco de Dados (SQL)

O sistema utiliza uma tabela principal chamada `reservas`. Para criar a estrutura do banco, execute o seguinte script no seu banco PostgreSQL:

```sql
CREATE TABLE reservas (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    quarto_id INTEGER NOT NULL,
    cliente_nome TEXT NOT NULL,
    telefone TEXT,
    qtd_pessoas INTEGER DEFAULT 1,
    data_entrada DATE NOT NULL,
    data_saida DATE NOT NULL,
    valor_total NUMERIC(10, 2)
);

-- Segurança de Nível de Linha (RLS) configurada para bloquear acessos anônimos via API pública
ALTER TABLE reservas ENABLE ROW LEVEL SECURITY;

Como Executar o Projeto Localmente
1. Clonar o repositório

git clone [https://github.com/SEU_USUARIO/sistema-hotel.git](https://github.com/SEU_USUARIO/sistema-hotel.git)
cd sistema-hotel

2. Criar e ativar um ambiente virtual (Recomendado)

python -m venv venv
# No Windows:
venv\Scripts\activate
# No Linux/Mac:
source venv/bin/activate

3. Instalar as dependências

pip install -r requirements.txt

4. Configurar as Variáveis de Ambiente
Crie uma pasta chamada .streamlit na raiz do projeto e dentro dela crie um arquivo chamado secrets.toml. Preencha com os dados do seu banco Supabase e a senha do sistema:

[postgres]
host = "aws-0-sa-east-1.pooler.supabase.com"
port = 6543
dbname = "postgres"
user = "postgres.seu_projeto"
password = "sua_senha_do_banco"

[geral]
senha_site = "senha_da_recepcao123"

5. Iniciar o aplicativo

streamlit run app.py

Deploy
O projeto está configurado para Continuous Deployment (CD) via Streamlit Cloud. Qualquer push feito na branch main atualizará automaticamente a versão em produção.
A API REST pública do Supabase foi desativada via RLS, garantindo que o banco seja acessado estritamente pelas credenciais de backend configuradas no Streamlit Cloud.