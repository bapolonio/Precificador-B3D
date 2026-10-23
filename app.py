import json
import os
import streamlit as st

# Configuração da página
st.set_page_config(page_title="Precificador B3D", page_icon="🖨️", layout="wide")

# --- ARQUIVO DE BANCO DE DADOS LOCAL ---
DB_FILE = "dados_b3d.json"


def carregar_dados():
  if os.path.exists(DB_FILE):
    with open(DB_FILE, "r", encoding="utf-8") as f:
      return json.load(f)
  return {
      "filamentos": {
          "PLA Padrão": 85.0,
          "PETG": 90.0,
          "ABS": 95.0,
          "Velvet": 110.0,
      },
      "impressoras": {
          "Bambu Lab A1": {"depreciacao": 1.20, "consumo": 150.0},
          "Bambu Lab P2S": {"depreciacao": 1.80, "consumo": 200.0},
      },
      "kw_h": 0.85,
      "embalagens": {"Caixa Padrão": 3.50, "Plástico Bolha": 1.00},
      "produtos_salvos": [],
  }


def salvar_dados(dados):
  with open(DB_FILE, "w", encoding="utf-8") as f:
    json.dump(dados, f, ensure_ascii=False, indent=4)


# Inicializa os dados
dados = carregar_dados()

# --- MENU LATERAL ---
st.sidebar.title("🖨️ B3D - Painel")
menu = st.sidebar.selectbox(
    "Navegação",
    [
        "🧮 Calculadora (Início)",
        "📦 Produtos Salvos",
        "🧵 Filamentos",
        "🖨️ Impressoras",
        "⚡ Energia",
        "🎁 Embalagens e Materiais",
    ],
)

# ==========================================
# 1. PÁGINA INICIAL: CALCULADORA DE PRECIFICAÇÃO
# ==========================================
if menu == "🧮 Calculadora (Início)":
  st.title("🧮 Calculadora de Precificação - B3D")
  st.write("Preencha os dados da peça para calcular o preço de venda ideal.")

  if not dados["filamentos"] or not dados["impressoras"]:
    st.warning(
        "⚠️ Cadastre pelo menos um filamento e uma impressora no menu lateral"
        " antes de calcular."
    )
  else:
    col_esq, col_dir = st.columns(2)

    with col_esq:
      st.subheader("1. Seleção de Equipamento e Insumo")
      # Seleção de Impressora (Preenche automático)
      imp_selecionada = st.selectbox(
          "Selecione a Impressora", list(dados["impressoras"].keys())
      )
      depreciacao_atual = dados["impressoras"][imp_selecionada]["depreciacao"]
      consumo_atual = dados["impressoras"][imp_selecionada]["consumo"]

      st.info(
          f"🔹 Depreciação: **R$ {depreciacao_atual:.2f}/h** | Consumo:"
          f" **{consumo_atual}W**"
      )

      # Seleção de Filamento (Preenche automático)
      fil_selecionado = st.selectbox(
          "Selecione o Filamento", list(dados["filamentos"].keys())
      )
      preco_kg_atual = dados["filamentos"][fil_selecionado]

      st.info(f"🔹 Preço do Kg ({fil_selecionado}): **R$ {preco_kg_atual:.2f}**")

      st.subheader("2. Parâmetros de Impressoração")
      tempo_h = st.number_input(
          "Tempo de Impressão (horas)",
          min_value=0.1,
          value=4.0,
          format="%.2f",
      )
      peso_g = st.number_input(
          "Quantidade de Filamento (gramas)", min_value=0.1, value=50.0
      )

    with col_dir:
      st.subheader("3. Materiais Adicionais (Embalagens/Extras)")
      materiais_escolhidos = []
      if dados["embalagens"]:
        st.write("Selecione os itens e quantidades extras:")
        for emb, preco_emb in dados["embalagens"].items():
          usar = st.checkbox(f"{emb} (R$ {preco_emb:.2f} un)", key=f"chk_{emb}")
          if usar:
            qtd = st.number_input(
                f"Quantidade de {emb}", min_value=1, value=1, key=f"qtd_{emb}"
            )
            materiais_escolhidos.append(
                {"nome": emb, "preco_unit": preco_emb, "qtd": qtd}
            )
      else:
        st.write(
            "Nenhuma embalagem cadastrada. Cadastre no menu lateral se"
            " precisar."
        )

      st.subheader("4. Margens e Taxas")
      kw_h_atual = dados["kw_h"]
      taxa_comissao = (
          st.slider(
              "Comissão do Site / Marketplace (%)", 0.0, 30.0, 12.0, format="%.1f%%"
          )
          / 100
      )
      lucro_desejado = (
          st.slider(
              "Margem de Lucro Desejada (%)", 10.0, 300.0, 100.0, format="%.1f%%"
          )
          / 100
      )

    # --- BOTÃO DE CALCULAR ---
    if st.button(
        "🚀 Calcular Preço", type="primary", use_container_width=True
    ):
      # Custos
      custo_material = (preco_kg_atual / 1000) * peso_g
      consumo_kwh = (consumo_atual / 1000) * tempo_h
      custo_energia = consumo_kwh * kw_h_atual
      custo_maquina = depreciacao_atual * tempo_h

      custo_extras_total = sum(
          item["preco_unit"] * item["qtd"] for item in materiais_escolhidos
      )

      custo_producao = (
          custo_material + custo_energia + custo_maquina + custo_extras_total
      )

      # Lucro sobre o custo de produção
      subtotal_com_lucro = custo_producao * (1 + lucro_desejado)

      # Invertendo a taxa de comissão para garantir que o desconto do site venha do preço final
      if taxa_comissao >= 1.0:
        taxa_comissao = 0.99  # Proteção contra divisão por zero

      preco_venda_final = subtotal_com_lucro / (1 - taxa_comissao)
      valor_comissao = preco_venda_final * taxa_comissao

      # Guarda na session_state para exibir e permitir salvar
      st.session_state["ultimo_calculo"] = {
          "custo_producao": custo_producao,
          "preco_venda_final": preco_venda_final,
          "lucro_reais": preco_venda_final - custo_producao - valor_comissao,
          "detalhes": {
              "impressora": imp_selecionada,
              "filamento": fil_selecionado,
              "peso_g": peso_g,
              "tempo_h": tempo_h,
              "custo_material": custo_material,
              "custo_energia": custo_energia,
              "custo_maquina": custo_maquina,
              "extras": materiais_escolhidos,
              "comissao_site": valor_comissao,
          },
      }

    # Se já foi calculado, mostra o resultado e a opção de salvar
    if "ultimo_calculo" in st.session_state:
      calc = st.session_state["ultimo_calculo"]
      st.divider()
      st.subheader("📊 Resultado da Precificação")

      r1, r2, r3 = st.columns(3)
      r1.metric("Custo de Produção Total", f"R$ {calc['custo_producao']:.2f}")
      r2.metric("Lucro Estimado", f"R$ {calc['lucro_reais']:.2f}")
      r3.metric(
          "💎 Preço Final de Venda", f"R$ {calc['preco_venda_final']:.2f}"
      )

      with st.expander("🔍 Ver Detalhamento dos Custos"):
        det = calc["detalhes"]
        st.write(f"- **Impressora usada:** {det['impressora']}")
        st.write(
            f"- **Filamento ({det['filamento']} - {det['peso_g']}g):** R$"
            f" {det['custo_material']:.2f}"
        )
        st.write(f"- **Energia elétrica:** R$ {det['custo_energia']:.2f}")
        st.write(f"- **Depreciação de Máquina:** R$ {det['custo_maquina']:.2f}")
        for ext in det["extras"]:
          st.write(
              f"- **{ext['nome']} ({ext['qtd']}x):** R$"
              f" {ext['preco_unit'] * ext['qtd']:.2f}"
          )
        st.write(f"- **Taxa/Comissão do Site:** R$ {det['comissao_site']:.2f}")

      st.divider()
      st.subheader("💾 Salvar Produto")
      nome_produto = st.text_input("Título / Nome do Produto para Salvar")
      if st.button("Salvar no Histórico de Produtos"):
        if nome_produto.strip() == "":
          st.error("Por favor, digite um título para o produto.")
        else:
          novo_prod = {
              "titulo": nome_produto,
              "preco_venda": calc["preco_venda_final"],
              "custo": calc["custo_producao"],
              "detalhes": calc["detalhes"],
          }
          dados["produtos_salvos"].append(novo_prod)
          salvar_dados(dados)
          st.success(f"Produto '{nome_produto}' salvo com sucesso!")


# ==========================================
# 2. PRODUTOS SALVOS
# ==========================================
elif menu == "📦 Produtos Salvos":
  st.title("📦 Produtos Precificados e Salvos")
  st.write("Aqui fica o histórico de todos os produtos que você salvou.")

  if not dados["produtos_salvos"]:
    st.info("Nenhum produto salvo ainda. Faça um cálculo na tela inicial!")
  else:
    if st.button("🗑️ Limpar Todos os Produtos"):
      dados["produtos_salvos"] = []
      salvar_dados(dados)
      st.rerun()

    for idx, prod in enumerate(dados["produtos_salvos"]):
      with st.expander(
          f"📌 {prod['titulo']} — **R$ {prod['preco_venda']:.2f}**"
      ):
        st.write(f"**Custo de Produção:** R$ {prod['custo']:.2f}")
        st.write(
            f"**Impressora:** {prod['detalhes']['impressora']} | **Filamento:**"
            f" {prod['detalhes']['filamento']}"
        )
        st.write(
            f"**Peso:** {prod['detalhes']['peso_g']}g | **Tempo:**"
            f" {prod['detalhes']['tempo_h']}h"
        )
        if st.button(f"Excluir produto #{idx+1}", key=f"del_prod_{idx}"):
          dados["produtos_salvos"].pop(idx)
          salvar_dados(dados)
          st.rerun()


# ==========================================
# 3. FILAMENTOS
# ==========================================
elif menu == "🧵 Filamentos":
  st.title("🧵 Gerenciamento de Filamentos")
  st.write("Cadastre e gerencie os tipos de filamento e o preço por quilo.")

  with st.form("form_filamento"):
    novo_nome = st.text_input("Nome do Filamento (ex: PLA Velvet, Silk, etc.)")
    novo_preco = st.number_input(
        "Preço do Quilo (R$)", min_value=0.0, value=85.0
    )
    submit_fil = st.form_submit_button("Adicionar / Atualizar Filamento")

    if submit_fil:
      if novo_nome.strip() != "":
        dados["filamentos"][novo_nome.strip()] = novo_preco
        salvar_dados(dados)
        st.success(f"Filamento '{novo_nome}' cadastrado/atualizado com sucesso!")
        st.rerun()
      else:
        st.error("O nome do filamento não pode estar em branco.")

  st.divider()
  st.subheader("📋 Filamentos Cadastrados atualmente:")
  if dados["filamentos"]:
    for fil, preco in list(dados["filamentos"].items()):
      col_f1, col_f2, col_f3 = st.columns([3, 2, 1])
      col_f1.write(f"**{fil}**")
      col_f2.write(f"R$ {preco:.2f} / kg")
      if col_f3.button("Excluir", key=f"del_fil_{fil}"):
        del dados["filamentos"][fil]
        salvar_dados(dados)
        st.rerun()
  else:
    st.info("Nenhum filamento cadastrado.")


# ==========================================
# 4. IMPRESSORAS
# ==========================================
elif menu == "🖨️ Impressoras":
  st.title("🖨️ Gerenciamento de Impressoras")
  st.write("Cadastre suas impressoras, coeficientes de depreciação e consumo.")

  with st.form("form_impressora"):
    nome_imp = st.text_input("Nome da Impressora (ex: Bambu Lab A1)")
    dep_imp = st.number_input(
        "Coeficiente de Depreciação / Manutenção (R$/h)",
        min_value=0.0,
        value=1.50,
        format="%.2f",
    )
    cons_imp = st.number_input(
        "Consumo de Energia (Watts)", min_value=0.0, value=150.0
    )
    submit_imp = st.form_submit_button("Cadastrar Impressora")

    if submit_imp:
      if nome_imp.strip() != "":
        dados["impressoras"][nome_imp.strip()] = {
            "depreciacao": dep_imp,
            "consumo": cons_imp,
        }
        salvar_dados(dados)
        st.success(f"Impressora '{nome_imp}' cadastrada com sucesso!")
        st.rerun()
      else:
        st.error("O nome da impressora não pode estar em branco.")

  st.divider()
  st.subheader("📋 Impressoras Cadastradas:")
  if dados["impressoras"]:
    for imp, info in list(dados["impressoras"].items()):
      col_i1, col_i2, col_i3 = st.columns([3, 3, 1])
      col_i1.write(f"**{imp}**")
      col_i2.write(
          f"Depreciação: R$ {info['depreciacao']:.2f}/h | Consumo:"
          f" {info['consumo']}W"
      )
      if col_i3.button("Excluir", key=f"del_imp_{imp}"):
        del dados["impressoras"][imp]
        salvar_dados(dados)
        st.rerun()
  else:
    st.info("Nenhuma impressora cadastrada.")


# ==========================================
# 5. ENERGIA
# ==========================================
elif menu == "⚡ Energia":
  st.title("⚡ Custo de Energia Elétrica")
  st.write("Defina o valor atual do kW/h cobrado na sua conta de luz.")

  novo_kwh = st.number_input(
      "Custo da Energia (R$ / kWh)",
      min_value=0.0,
      value=float(dados["kw_h"]),
      format="%.2f",
  )
  if st.button("Salvar Custo de Energia"):
    dados["kw_h"] = novo_kwh
    salvar_dados(dados)
    st.success(f"Custo de energia atualizado para R$ {novo_kwh:.2f} / kWh!")


# ==========================================
# 6. EMBALAGENS E MATERIAIS
# ==========================================
elif menu == "🎁 Embalagens e Materiais":
  st.title("🎁 Embalagens e Materiais Adicionais")
  st.write(
      "Cadastre caixas, plásticos, brindes ou extras para adicionar aos"
      " produtos."
  )

  with st.form("form_embalagem"):
    nome_emb = st.text_input("Nome do Material ou Embalagem (ex: Caixa Kraft)")
    preco_emb = st.number_input(
        "Preço Unitário (R$)", min_value=0.0, value=2.00, format="%.2f"
    )
    submit_emb = st.form_submit_button("Cadastrar Material")

    if submit_emb:
      if nome_emb.strip() != "":
        dados["embalagens"][nome_emb.strip()] = preco_emb
        salvar_dados(dados)
        st.success(f"Material '{nome_emb}' cadastrado com sucesso!")
        st.rerun()
      else:
        st.error("O nome do material não pode estar em branco.")

  st.divider()
  st.subheader("📋 Materiais Cadastrados:")
  if dados["embalagens"]:
    for emb, preco in list(dados["embalagens"].items()):
      col_e1, col_e2, col_e3 = st.columns([3, 2, 1])
      col_e1.write(f"**{emb}**")
      col_e2.write(f"R$ {preco:.2f} un")
      if col_e3.button("Excluir", key=f"del_emb_{emb}"):
        del dados["embalagens"][emb]
        salvar_dados(dados)
        st.rerun()
  else:
    st.info("Nenhum material cadastrado.")
