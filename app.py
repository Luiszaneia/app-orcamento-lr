from datetime import datetime, timedelta
import os
import json
import streamlit as st

# Tenta importar FPDF para gerar o PDF
try:
    from fpdf import FPDF
    FPDF_DISPONIVEL = True
except ImportError:
    FPDF_DISPONIVEL = False

# Configuração da página
st.set_page_config(
    page_title="LR Higienização - Orçamentos", page_icon="🛋️", layout="centered"
)

# --- ARQUIVOS DE CONFIGURAÇÃO E DADOS PERSISTENTES ---
ARQUIVO_PRECOS = "tabela_precos.json"
ARQUIVO_HISTORICO = "orcamentos_salvos.json"

PRECOS_PADRAO = {
    "Sofá 2 Lugares (Padrão)": 140.00,
    "Sofá 3 Lugares (Padrão)": 180.00,
    "Sofá Retrátil/Reclinável (2 a 3 lugares)": 220.00,
    "Sofá de Canto / L (até 5 lugares)": 280.00,
    "Colchão Solteiro": 110.00,
    "Colchão Casal Padrão": 150.00,
    "Colchão Queen / King": 190.00,
    "Poltrona Simples": 80.00,
    "Cadeira de Jantar (Assento + Encosto)": 35.00,
    "Tapete (por m²)": 25.00,
    "Higienização Interna de Veículo (Bancos)": 200.00,
}

FATOR_SUJIDADE = {
    "Leve (Manutenção / Poeira)": 1.0,
    "Moderada (Manchas leves / Uso diário)": 1.15,
    "Pesada (Urina pet, mofo, manchas antigas)": 1.35,
}

def carregar_dados(arquivo, padrao):
    if os.path.exists(arquivo):
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return padrao
    return padrao

def salvar_dados(arquivo, dados):
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

if "tabela_precos" not in st.session_state:
    st.session_state.tabela_precos = carregar_dados(ARQUIVO_PRECOS, PRECOS_PADRAO)

if "historico_orcamentos" not in st.session_state:
    st.session_state.historico_orcamentos = carregar_dados(ARQUIVO_HISTORICO, [])

if "itens_orcamento" not in st.session_state:
    st.session_state.itens_orcamento = []

# --- MENU LATERAL (NAVEGAÇÃO) ---
st.sidebar.title("🧭 Navegação")
menu = st.sidebar.radio("Escolha a opção:", ["Gerar Orçamento", "📋 Histórico de Orçamentos", "⚙️ Configurar Preços e Serviços"])

# ==========================================
# ABA 1: GERAR ORÇAMENTO
# ==========================================
if menu == "Gerar Orçamento":
    st.title("🛋️ LR Higienização")
    st.subheader("Gerador de Orçamentos Profissionais")
    st.markdown("---")

    # 1. Dados do Cliente e Técnico Responsável
    st.markdown("### 1. Dados do Atendimento")
    col1, col2 = st.columns(2)
    with col1:
        nome_cliente = st.text_input("Nome do Cliente", placeholder="Ex: Maria Silva")
        telefone = st.text_input("WhatsApp do Cliente", placeholder="(16) 99999-9999")
    with col2:
        endereco = st.text_input("Bairro / Endereço", placeholder="Ex: Centro - Luiz Antônio")
        tecnico_responsavel = st.text_input("Técnico Responsável", value="Luis Ramão", placeholder="Nome do operador")

    col3, col4 = st.columns(2)
    with col3:
        validade_dias = st.number_input("Validade do Orçamento (dias)", min_value=1, max_value=30, value=7)

    st.markdown("---")

    # 2. Upload de Imagens
    st.markdown("### 2. Imagens (Logotipo e Foto do Item)")
    col_logo, col_foto = st.columns(2)
    
    with col_logo:
        logo_arquivo = st.file_uploader("Logotipo da Empresa (PNG/JPG):", type=["jpg", "jpeg", "png"], key="logo_up")
        if logo_arquivo is not None:
            st.image(logo_arquivo, caption="Logo carregada", width=150)

    with col_foto:
        foto_arquivo = st.file_uploader("Foto do Estofado/Colchão:", type=["jpg", "jpeg", "png"], key="foto_up")
        if foto_arquivo is not None:
            st.image(foto_arquivo, caption="Foto do item anexada", width=150)

    st.markdown("---")

    # 3. Adicionar Itens ao Orçamento
    st.markdown("### 3. Adicionar Peças / Serviços")
    
    lista_servicos_disponiveis = list(st.session_state.tabela_precos.keys())
    
    col_item, col_qtd, col_suj = st.columns([3, 1, 2])
    with col_item:
        servico_selecionado = st.selectbox("Selecione o item:", lista_servicos_disponiveis)
    with col_qtd:
        quantidade = st.number_input("Qtd / m²", min_value=1, max_value=50, value=1)
    with col_suj:
        nivel_sujidade = st.selectbox("Nível de Sujidade:", list(FATOR_SUJIDADE.keys()))

    preco_base_tabela = st.session_state.tabela_precos[servico_selecionado]
    multiplicador = FATOR_SUJIDADE[nivel_sujidade]
    valor_sugerido = preco_base_tabela * multiplicador

    usar_valor_manual = st.checkbox("Ajustar valor unitário manualmente?")
    if usar_valor_manual:
        valor_unitario_calculado = st.number_input("Valor Unitário (R$):", min_value=0.0, value=float(valor_sugerido), step=5.0)
    else:
        valor_unitario_calculado = valor_sugerido
        st.caption(f"Valor unitário padrão calculado: **R$ {valor_unitario_calculado:.2f}**")

    subtotal_item = valor_unitario_calculado * quantidade

    if st.button("➕ Adicionar Item ao Orçamento", use_container_width=True):
        st.session_state.itens_orcamento.append({
            "item": servico_selecionado,
            "qtd": quantidade,
            "sujidade": nivel_sujidade.split(" ")[0],
            "unitario": valor_unitario_calculado,
            "total": subtotal_item,
        })
        st.success(f"{quantidade}x {servico_selecionado} adicionado!")

    # 4. Resumo dos Itens Adicionados
    if st.session_state.itens_orcamento:
        st.markdown("---")
        st.markdown("### 4. Itens no Orçamento")

        total_servicos = 0
        for idx, item in enumerate(st.session_state.itens_orcamento):
            c1, c2, c3 = st.columns([4, 2, 1])
            c1.write(f"**{item['qtd']}x** {item['item']} *(R$ {item['unitario']:.2f} un)*")
            c2.write(f"R$ {item['total']:.2f}")
            if c3.button("🗑️", key=f"del_{idx}"):
                st.session_state.itens_orcamento.pop(idx)
                st.rerun()
            total_servicos += item["total"]

        st.markdown("---")

        # 5. Ajustes Finais
        st.markdown("### 5. Fechamento e Valores")
        col_desl, col_desc = st.columns(2)
        with col_desl:
            taxa_deslocamento = st.number_input("Taxa de Deslocamento (R$)", min_value=0.0, step=5.0, value=0.0)
        with col_desc:
            desconto = st.number_input("Desconto Especial (R$)", min_value=0.0, step=5.0, value=0.0)

        valor_final = max(0.0, total_servicos + taxa_deslocamento - desconto)

        st.metric(label="💰 VALOR TOTAL DO ORÇAMENTO", value=f"R$ {valor_final:.2f}")

        # 6. Salvar no Histórico e Geração de Proposta
        st.markdown("---")
        st.markdown("### 6. Proposta Pronta para Envio")

        data_hoje = datetime.now().strftime("%d/%m/%Y")
        data_validade = (datetime.now() + timedelta(days=validade_dias)).strftime("%d/%m/%Y")

        lista_texto_itens = ""
        for item in st.session_state.itens_orcamento:
            lista_texto_itens += f"▪ {item['qtd']}x {item['item']} (Sujidade: {item['sujidade']}) — R$ {item['total']:.2f}\n"

        texto_whatsapp = f"""*ORÇAMENTO - LR HIGIENIZAÇÃO* 🛋️✨
*Data:* {data_hoje} | *Válido até:* {data_validade}
*Cliente:* {nome_cliente if nome_cliente else 'Não informado'}
*Local:* {endereco if endereco else 'A combinar'}
*Técnico Responsável:* {tecnico_responsavel}

*SERVIÇOS INCLUSOS:*
{lista_texto_itens}
*Detalhes do Processo:*
✅ Higienização profunda com extração a vácuo
✅ Produtos bactericidas e fungicidas profissionais (Linha Vonixx/Easytech)
✅ Eliminação de ácaros, fungos, bactérias e odores

*RESUMO DE VALORES:*
Subtotal dos serviços: R$ {total_servicos:.2f}
Deslocamento: R$ {taxa_deslocamento:.2f}
Desconto: - R$ {desconto:.2f}
*VALOR TOTAL: R$ {valor_final:.2f}*

_Formas de pagamento: Pix, Dinheiro ou Cartão._
Qualquer dúvida, estou à disposição!"""

        st.text_area("Copie o texto e envie no WhatsApp do cliente:", value=texto_whatsapp, height=300)

        col_salvar, col_limpar, col_baixar = st.columns(3)
        
        with col_salvar:
            if st.button("💾 Salvar no Histórico", use_container_width=True):
                novo_registro = {
                    "id": datetime.now().strftime("%Y%m%d%H%M%S"),
                    "data": data_hoje,
                    "cliente": nome_cliente if nome_cliente else "Não informado",
                    "telefone": telefone if telefone else "Não informado",
                    "endereco": endereco if endereco else "A combinar",
                    "tecnico": tecnico_responsavel,
                    "total": valor_final,
                    "itens": st.session_state.itens_orcamento
                }
                st.session_state.historico_orcamentos.append(novo_registro)
                salvar_dados(ARQUIVO_HISTORICO, st.session_state.historico_orcamentos)
                st.success("Orçamento salvo com sucesso no histórico!")

        with col_limpar:
            if st.button("🧹 Novo Orçamento", use_container_width=True):
                st.session_state.itens_orcamento = []
                st.rerun()
        
        with col_baixar:
            if FPDF_DISPONIVEL:
                class PDF(FPDF):
                    def header(self):
                        if logo_arquivo is not None:
                            temp_logo_path = "temp_logo.png"
                            with open(temp_logo_path, "wb") as f:
                                f.write(logo_arquivo.getbuffer())
                            self.image(temp_logo_path, 10, 8, 25)
                        
                        self.set_font("helvetica", "B", 15)
                        self.set_text_color(25, 25, 112)
                        self.cell(0, 8, "LR HIGIENIZACAO PROFISSIONAL", 0, 1, "C")
                        self.set_font("helvetica", "", 9)
                        self.set_text_color(100, 100, 100)
                        self.cell(0, 4, "Limpeza, Sanitizacao e Tratamento de Estofados", 0, 1, "C")
                        self.ln(8)
                        self.set_draw_color(200, 200, 200)
                        self.line(10, self.get_y(), 200, self.get_y())
                        self.ln(5)

                    def footer(self):
                        self.set_y(-15)
                        self.set_font("helvetica", "I", 8)
                        self.set_text_color(120, 120, 120)
                        self.cell(0, 10, f"Documento gerado por LR Higienizacao | Pagina {self.page_no()}", 0, 0, "C")

                pdf = PDF()
                pdf.add_page()
                pdf.set_font("helvetica", "", 10)
                
                pdf.set_fill_color(245, 247, 250)
                pdf.rect(10, pdf.get_y(), 190, 26, 'F')
                pdf.set_xy(12, pdf.get_y() + 3)
                pdf.set_font("helvetica", "B", 10)
                pdf.cell(90, 5, f"Cliente: {nome_cliente if nome_cliente else 'Nao informado'}", 0, 0)
                pdf.cell(90, 5, f"Data: {data_hoje}", 0, 1)
                pdf.set_font("helvetica", "", 10)
                pdf.set_x(12)
                pdf.cell(90, 5, f"Endereco: {endereco if endereco else 'A combinar'}", 0, 0)
                pdf.cell(90, 5, f"Validade: {data_validade}", 0, 1)
                pdf.set_x(12)
                pdf.cell(90, 5, f"Tecnico Responsavel: {tecnico_responsavel}", 0, 1)
                pdf.ln(10)

                pdf.set_font("helvetica", "B", 11)
                pdf.set_text_color(25, 25, 112)
                pdf.cell(0, 6, "ITENS DO ORCAMENTO", 0, 1, "L")
                pdf.ln(2)

                pdf.set_font("helvetica", "B", 9)
                pdf.set_fill_color(230, 235, 245)
                pdf.cell(100, 7, "  Descricao do Servico / Pecas", 1, 0, "L", True)
                pdf.cell(30, 7, "Sujidade", 1, 0, "C", True)
                pdf.cell(60, 7, "Subtotal", 1, 1, "R", True)

                pdf.set_font("helvetica", "", 9)
                pdf.set_text_color(0, 0, 0)
                for item in st.session_state.itens_orcamento:
                    pdf.cell(100, 7, f"  {item['qtd']}x {item['item']}", 1, 0, "L")
                    pdf.cell(30, 7, f"{item['sujidade']}", 1, 0, "C")
                    pdf.cell(60, 7, f"R$ {item['total']:.2f}  ", 1, 1, "R")
                
                pdf.ln(5)

                x_inicio = 110
                pdf.set_x(x_inicio)
                pdf.cell(50, 6, "Subtotal Serviços:", 0, 0, "L")
                pdf.cell(30, 6, f"R$ {total_servicos:.2f}", 0, 1, "R")
                
                pdf.set_x(x_inicio)
                pdf.cell(50, 6, "Taxa de Deslocamento:", 0, 0, "L")
                pdf.cell(30, 6, f"R$ {taxa_deslocamento:.2f}", 0, 1, "R")
                
                if desconto > 0:
                    pdf.set_x(x_inicio)
                    pdf.cell(50, 6, "Desconto Aplicado:", 0, 0, "L")
                    pdf.cell(30, 6, f"- R$ {desconto:.2f}", 0, 1, "R")

                pdf.ln(2)
                pdf.set_x(x_inicio)
                pdf.set_font("helvetica", "B", 11)
                pdf.set_text_color(25, 25, 112)
                pdf.cell(50, 8, "VALOR TOTAL:", 0, 0, "L")
                pdf.cell(30, 8, f"R$ {valor_final:.2f}", 0, 1, "R")

                if foto_arquivo is not None:
                    pdf.ln(10)
                    pdf.set_font("helvetica", "B", 10)
                    pdf.set_text_color(0, 0, 0)
                    pdf.cell(0, 6, "Registro Fotográfico do Item:", 0, 1, "L")
                    temp_foto_path = "temp_foto.png"
                    with open(temp_foto_path, "wb") as f:
                        f.write(foto_arquivo.getbuffer())
                    pdf.image(temp_foto_path, 10, pdf.get_y() + 2, 50)

                pdf_output = bytes(pdf.output())
                
                st.download_button(
                    label="📄 Baixar PDF",
                    data=pdf_output,
                    file_name=f"Orcamento_{nome_cliente.replace(' ', '_') if nome_cliente else 'Cliente'}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            else:
                st.info("Instale o fpdf2 para gerar PDF.")

    else:
        st.info("Adicione pelo menos um item acima para calcular e gerar o orçamento.")

# ==========================================
# ABA 2: HISTÓRICO DE ORÇAMENTOS
# ==========================================
elif menu == "📋 Histórico de Orçamentos":
    st.title("📋 Histórico de Orçamentos Realizados")
    st.markdown("Consulte os orçamentos salvos anteriormente ou exclua os que não precisar mais.")
    st.markdown("---")

    if not st.session_state.historico_orcamentos:
        st.info("Nenhum orçamento salvo no histórico ainda.")
    else:
        for idx, orc in enumerate(st.session_state.historico_orcamentos):
            with st.expander(f"📅 {orc['data']} — Cliente: **{orc['cliente']}** (Total: R$ {orc['total']:.2f})"):
                st.write(f"📞 **Telefone:** {orc['telefone']}")
                st.write(f"📍 **Endereço:** {orc['endereco']}")
                st.write(f"👨‍🔧 **Técnico:** {orc['tecnico']}")
                st.markdown("**Itens do Orçamento:**")
                for it in orc['itens']:
                    st.markdown(f"- {it['qtd']}x {it['item']} (Sujidade: {it['sujidade']}) — R$ {it['total']:.2f}")
                
                if st.button(f"🗑️ Excluir Orçamento de {orc['cliente']}", key=f"del_hist_{idx}"):
                    st.session_state.historico_orcamentos.pop(idx)
                    salvar_dados(ARQUIVO_HISTORICO, st.session_state.historico_orcamentos)
                    st.success("Orçamento excluído do histórico com sucesso!")
                    st.rerun()

# ==========================================
# ABA 3: CONFIGURAR PREÇOS E ITENS
# ==========================================
elif menu == "⚙️ Configurar Preços e Serviços":
    st.title("⚙️ Gerenciar Tabela de Preços")
    st.markdown("Altere os valores base dos seus serviços ou adicione novos itens à vontade.")
    st.markdown("---")

    st.subheader("Editar Preços Atuais")
    tabela_atualizada = {}
    for nome_servico, preco_atual in st.session_state.tabela_precos.items():
        novo_preco = st.number_input(f"Preço para: {nome_servico} (R$)", min_value=0.0, value=float(preco_atual), step=5.0, key=f"preco_{nome_servico}")
        tabela_atualizada[nome_servico] = novo_preco

    if st.button("💾 Salvar Alterações de Preços"):
        st.session_state.tabela_precos = tabela_atualizada
        salvar_dados(ARQUIVO_PRECOS, tabela_atualizada)
        st.success("Tabela de preços atualizada com sucesso!")

    st.markdown("---")
    
    st.subheader("Adicionar Novo Tipo de Serviço")
    novo_nome = st.text_input("Nome do Novo Serviço/Item", placeholder="Ex: Puff Grande")
    novo_valor = st.number_input("Valor Base (R$)", min_value=0.0, value=60.0, step=5.0)

    if st.button("➕ Adicionar Novo Item à Tabela"):
        if novo_nome and novo_nome not in st.session_state.tabela_precos:
            st.session_state.tabela_precos[novo_nome] = novo_valor
            salvar_dados(ARQUIVO_PRECOS, st.session_state.tabela_precos)
            st.success(f"Serviço '{novo_nome}' adicionado com sucesso!")
            st.rerun()
        else:
            st.error("Digite um nome válido ou que já não exista na lista.")