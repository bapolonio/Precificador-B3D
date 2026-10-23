import json
import os
import streamlit as st

# Configuração da página e layout
st.set_page_config(page_title="Precificador B3D", page_icon="🖨️", layout="wide")

# --- ESTILIZAÇÃO CSS (Remove espaço do topo, botões e ajustes visuais) ---
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
    }
    div.stButton > button {
        background-color: #B2DE55 !important;
        color: #1E1E1E !important;
        font-weight: 800 !important;
        font-size: 20px !important;
        border: none !important;
        padding: 0.75rem 1rem !important;
    }
    div.stButton > button:hover {
        background-color: #9ec944 !important;
        color: #1E1E1E !important;
    }
    div.stRadio > div {
        gap: 12px !important;
    }
    div.stRadio label {
        padding-top: 6px !important;
        padding-bottom: 6px !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- ARQUIVO DE BANCO DE DADOS LOCAL ---
DB_FILE = "dados_b3d.json"

# Categorias oficiais de produtos
CATEGORIAS_PRODUTOS = [
    "Casa & Decoração",
    "Organização & Setup",
    "Colecionáveis & Figures",
    "Jogos & Entretenimento",
    "Utilitários & Ferramentas",
    "Brinquedos & Sensoriais",
]


def carregar_dados():
  if os.path.exists(DB_FILE):
    with open(DB_FILE, "r", encoding="utf-8") as f:
      dados = json.load(f)
      for p in dados.get("produtos_salvos", []):
        if "categoria" not in p:
          p["categoria"] = "Utilitários & Ferramentas"
      return dados
  return {
      "filamentos": {
          "PLA Padrão": 85.0,
          "PETG": 90.0,
          "ABS": 95.0,
          "Velvet": 110.0,
      },
      "impressoras": {
          "Bambu Lab A1": {"depreciacao": 0.80, "consumo": 150.0},
          "Bambu Lab P2S": {"depreciacao": 1.00, "consumo": 200.0},
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
if os.path.exists("logo.png"):
  st.sidebar.image("logo.png", use_container_width=True)

st.sidebar.title("Menu")

menu_opcoes = [
    "Calculadora",
    "Filamentos",
    "Impressoras",
    "Energia",
    "Embalagens e Materiais",
    "Produtos",
]
menu = st.sidebar.radio("MenuPrincipal", menu_opcoes, label_visibility="collapsed")

categoria_selecionada_filtro = "Todos"
if menu == "Produtos":
  st.sidebar.markdown("---")
  st.sidebar.subheader("📂 Categorias")
  opcoes_cat_filtro = ["Todos"] + CATEGORIAS_PRODUTOS
  categoria_selecionada_filtro = st.sidebar.radio(
      "FiltroCat", opcoes_cat_filtro, label_visibility="collapsed"
  )

# ==========================================
# 1. PÁGINA INICIAL: CALCULADORA DE PRECIFICAÇÃO
# ==========================================
if menu == "Calculadora":
  st.title("🖨️ Calculadora de Precificação - B3D")
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
      imp_selecionada = st.selectbox(
          "Selecione a Impressora", list(dados["impressoras"].keys())
      )
      depreciacao_atual = dados["impressoras"][imp_selecionada]["depreciacao"]
      consumo_atual = dados["impressoras"][imp_selecionada]["consumo"]

      st.info(
          f"🔹 Depreciação: **R$ {depreciacao_atual:.2f}/h** | Consumo:"
          f" **{consumo_atual}W**"
      )

      fil_selecionado = st.selectbox(
          "Selecione o Filamento", list(dados["filamentos"].keys())
      )
      preco_kg_atual = dados["filamentos"][fil_selecionado]

      st.info(f"🔹 Preço do Kg ({fil_selecionado}): **R$ {preco_kg_atual:.2f}**")

      st.subheader("2. Parâmetros de Impressão")

      qtd_pecas_mesa = st.number_input(
          "Unidades impressas de uma vez na mesa (Lote)",
          min_value=1,
          value=1,
          step=1,
      )

      col_h1, col_h2 = st.columns(2)
      with col_h1:
        horas_imp = st.number_input(
            "Horas de Impressão", min_value=0, value=4, step=1
        )
      with col_h2:
        minutos_imp = st.number_input(
            "Minutos de Impressão", min_value=0, max_value=59, value=0, step=1
        )

      tempo_h = horas_imp + (minutos_imp / 60.0)
      if tempo_h <= 0:
        tempo_h = 0.01

      peso_g = st.number_input(
          "Quantidade Total de Filamento para a mesa (gramas)",
          min_value=0.1,
          value=50.0,
      )

    with col_dir:
      st.subheader(
          "3. Materiais Adicionais por Unidade (Embalagens/Extras)"
      )
      materiais_escolhidos = []
      if dados["embalagens"]:
        st.write("Selecione os itens e quantidades por peça:")
        for emb, preco_emb in dados["embalagens"].items():
          usar = st.checkbox(f"{emb} (R$ {preco_emb:.2f} un)", key=f"chk_{emb}")
          if usar:
            qtd_mat = st.number_input(
                f"Qtd de {emb} por peça", min_value=1, value=1, key=f"qtd_{emb}"
            )
            materiais_escolhidos.append(
                {"nome": emb, "preco_unit": preco_emb, "qtd": qtd_mat}
            )
      else:
        st.write("Nenhuma embalagem cadastrada.")

      st.subheader("4. Margens e Taxas")
      kw_h_atual = dados["kw_h"]

      taxa_comissao = st.number_input(
          "Comissão do Site / Marketplace (%)",
          min_value=0.0,
          max_value=50.0,
          value=12.0,
          format="%.1f",
          key="com_input",
      )
      taxa_comissao_dec = taxa_comissao / 100.0

      lucro_desejado = st.number_input(
          "Margem de Lucro Desejada (%)",
          min_value=0.0,
          max_value=500.0,
          value=100.0,
          format="%.1f",
          key="lucro_input",
      )
      lucro_desejado_dec = lucro_desejado / 100.0

    # --- BOTÃO DE CALCULAR ---
    if st.button("Calcular Preço", type="primary", use_container_width=True):
      custo_material_total = (preco_kg_atual / 1000) * peso_g
      consumo_kwh = (consumo_atual / 1000) * tempo_h
      custo_energia_total = consumo_kwh * kw_h_atual
      custo_maquina_total = depreciacao_atual * tempo_h

      custo_material_unit = custo_material_total / qtd_pecas_mesa
      custo_energia_unit = custo_energia_total / qtd_pecas_mesa
      custo_maquina_unit = custo_maquina_total / qtd_pecas_mesa

      custo_extras_unit = sum(
          item["preco_unit"] * item["qtd"] for item in materiais_escolhidos
      )

      custo_producao = (
          custo_material_unit
          + custo_energia_unit
          + custo_maquina_unit
          + custo_extras_unit
      )

      subtotal_com_lucro = custo_producao * (1 + lucro_desejado_dec)

      if taxa_comissao_dec >= 1.0:
        taxa_comissao_dec = 0.99

      preco_venda_calculado = subtotal_com_lucro / (1 - taxa_comissao_dec)
      valor_comissao_calc = preco_venda_calculado * taxa_comissao_dec
      lucro_calc_reais = (
          preco_venda_calculado - custo_producao - valor_comissao_calc
      )

      st.session_state["ultimo_calculo"] = {
          "custo_producao": custo_producao,
          "preco_venda_calculado": preco_venda_calculado,
          "lucro_calc_reais": lucro_calc_reais,
          "lucro_calc_pct": lucro_desejado,
          "taxa_comissao_pct": taxa_comissao,
          "detalhes": {
              "impressora": imp_selecionada,
              "filamento": fil_selecionado,
              "qtd_pecas_mesa": qtd_pecas_mesa,
              "peso_total_g": peso_g,
              "tempo_h": tempo_h,
              "tempo_formatado": f"{horas_imp}h {minutos_imp}min",
              "custo_material_unit": custo_material_unit,
              "custo_energia_unit": custo_energia_unit,
              "custo_maquina_unit": custo_maquina_unit,
              "extras": materiais_escolhidos,
          },
      }

  if "ultimo_calculo" in st.session_state:
    calc = st.session_state["ultimo_calculo"]
    st.divider()
    st.subheader("📊 Resultado da Precificação (Por Unidade)")

    r1, r2, r3 = st.columns(3)
    r1.metric("Custo de Produção (Unit.)", f"R$ {calc['custo_producao']:.2f}")
    r2.metric(
        f"Preço Calculado Unit. ({calc['lucro_calc_pct']:.0f}% Lucro)",
        f"R$ {calc['preco_venda_calculado']:.2f}",
    )

    st.markdown("### 💎 Definição Manual do Preço Final (Unitário)")
    col_def1, col_def2 = st.columns(2)
    with col_def1:
      preco_definido = st.number_input(
          "Preço Final Definido por Unidade (R$)",
          min_value=0.0,
          value=float(round(calc["preco_venda_calculado"], 2)),
          format="%.2f",
          key="input_preco_def",
      )

    taxa_com_dec = calc["taxa_comissao_pct"] / 100.0
    liquido_apos_comissao = preco_definido * (1 - taxa_com_dec)
    lucro_real_reais = liquido_apos_comissao - calc["custo_producao"]
    lucro_real_pct = (
        (lucro_real_reais / calc["custo_producao"]) * 100
        if calc["custo_producao"] > 0
        else 0.0
    )

    with col_def2:
      st.metric(
          "Margem de Lucro Real Obtida (Unit.)",
          f"{lucro_real_pct:.1f}%",
          delta=f"R$ {lucro_real_reais:.2f} de lucro líquido por peça",
      )

    with st.expander("🔍 Ver Detalhamento dos Custos Unitários"):
      det = calc["detalhes"]
      tempo_str_exp = det.get("tempo_formatado", f"{det['tempo_h']:.2f}h")
      st.write(
          f"- **Lote na Mesa:** {det['qtd_pecas_mesa']} peça(s) impressas juntas"
      )
      st.write(f"- **Impressora usada:** {det['impressora']}")
      st.write(f"- **Tempo Total da Mesa:** {tempo_str_exp}")
      st.write(
          f"- **Filamento por peça ({det['peso_total_g']}g /"
          f" {det['qtd_pecas_mesa']}un):** R$ {det['custo_material_unit']:.2f}"
      )
      st.write(
          f"- **Energia elétrica (por peça):** R$ {det['custo_energia_unit']:.2f}"
      )
      st.write(
          f"- **Depreciação de Máquina (por peça):** R$"
          f" {det['custo_maquina_unit']:.2f}"
      )
      for ext in det["extras"]:
        st.write(
            f"- **{ext['nome']} ({ext['qtd']}x por peça):** R$"
            f" {ext['preco_unit'] * ext['qtd']:.2f}"
        )
      st.write(
          f"- **Comissão do Site ({calc['taxa_comissao_pct']}%):** R$"
          f" {preco_definido * taxa_com_dec:.2f}"
      )

    st.divider()
    st.subheader("💾 Salvar Produto")
    nome_produto = st.text_input("Título / Nome do Produto para Salvar")
    categoria_escolhida = st.selectbox(
        "Categoria do Produto", CATEGORIAS_PRODUTOS, key="select_cat_salvar"
    )

    if st.button("Salvar no Histórico de Produtos", key="btn_salvar_prod"):
      if nome_produto.strip() == "":
        st.error("Por favor, digite um título para o produto.")
      else:
        novo_prod = {
            "titulo": nome_produto,
            "categoria": categoria_escolhida,
            "preco_definido": preco_definido,
            "lucro_real_pct": lucro_real_pct,
            "lucro_real_reais": lucro_real_reais,
            "custo": calc["custo_producao"],
            "preco_calculado": calc["preco_venda_calculado"],
            "lucro_calc_pct": calc["lucro_calc_pct"],
            "detalhes": calc["detalhes"],
        }
        dados["produtos_salvos"].append(novo_prod)
        salvar_dados(dados)
        st.success(
            f"Produto '{nome_produto}' salvo na categoria '{categoria_escolhida}'"
            " com sucesso!"
        )


# ==========================================
# 2. PRODUTOS SALVOS
# ==========================================
elif menu == "Produtos":
  # Cabeçalho com Título na Esquerda e Botão de Backup na Direita
  col_tit, col_btn = st.columns([3, 1])
  with col_tit:
    st.title("📦 Produtos Salvos")
  with col_btn:
    st.write("")  # Pequeno ajuste vertical
    json_str = json.dumps(dados, ensure_ascii=False, indent=4)
    st.download_button(
        label="📥 Fazer Backup (JSON)",
        data=json_str,
        file_name="dados_b3d_backup.json",
        mime="application/json",
        use_container_width=True,
    )

  st.divider()

  # --- FILTRO POR CATEGORIA (Caixas de seleção em 2 colunas) ---
  st.write("**Filtrar por Categoria:**")

  # Inicializa o estado das checkboxes se não existirem
  if "cat_todos" not in st.session_state:
    st.session_state["cat_todos"] = True
    for cat in CATEGORIAS_PRODUTOS:
      st.session_state[f"cat_{cat}"] = True


  # Função chamada ao clicar em "Todos"
  def toggle_todos():
    estado_atual = st.session_state["cat_todos"]
    for cat in CATEGORIAS_PRODUTOS:
      st.session_state[f"cat_{cat}"] = estado_atual


  col_f1, col_f2 = st.columns(2)

  with col_f1:
    todos_checkbox = st.checkbox(
        "📋 Todos", key="cat_todos", on_change=toggle_todos
    )
    # Primeiras 3 categorias reais na coluna 1
    cat_col1 = CATEGORIAS_PRODUTOS[0:3]
    cat_checks = {}
    for cat in cat_col1:
      cat_checks[cat] = st.checkbox(cat, key=f"cat_{cat}")

  with col_f2:
    st.write("")  # Espaçamento para alinhar visualmente com a coluna 1
    # Restantes categorias na coluna 2
    cat_col2 = CATEGORIAS_PRODUTOS[3:6]
    for cat in cat_col2:
      cat_checks[cat] = st.checkbox(cat, key=f"cat_{cat}")

  # Se o usuário marcar todas individualmente, marca o "Todos"
  todas_marcadas = all(st.session_state[f"cat_{cat}"] for cat in CATEGORIAS_PRODUTOS)
  if todas_marcadas and not st.session_state["cat_todos"]:
    st.session_state["cat_todos"] = True

  # --- CAMPO DE PESQUISA (Logo abaixo do filtro) ---
  st.divider()
  termo_pesquisa = st.text_input(
      "🔍 Pesquisar produto pelo nome...", ""
  ).strip().lower()

  st.divider()

  if not dados["produtos_salvos"]:
    st.info("Nenhum produto salvo ainda.")
  else:
    # Descobre quais categorias estão selecionadas
    categorias_selecionadas = [
        cat for cat in CATEGORIAS_PRODUTOS if st.session_state.get(f"cat_{cat}", True)
    ]

    produtos_filtrados = []
    for p in dados["produtos_salvos"]:
      prod_cat = p.get("categoria", "Utilitários & Ferramentas")
      match_cat = prod_cat in categorias_selecionadas
      match_pesquisa = (
          not termo_pesquisa or termo_pesquisa in p["titulo"].lower()
      )
      if match_cat and match_pesquisa:
        produtos_filtrados.append(p)

    if not produtos_filtrados:
      st.warning(
          "Nenhum produto encontrado com os filtros e termos de pesquisa"
          " informados."
      )
    else:
      for idx, prod in enumerate(dados["produtos_salvos"]):
        if prod not in produtos_filtrados:
          continue

        preco_mostrado = prod.get("preco_definido", prod.get("preco_venda", 0.0))
        cat_prod = prod.get("categoria", "Utilitários & Ferramentas")

        with st.expander(
            f"📌 [{cat_prod}] {prod['titulo']} — **R$ {preco_mostrado:.2f} (Unit.)**"
        ):
          st.write(f"**Categoria:** {cat_prod}")
          st.write(f"**Preço Final Definido (Unit.):** R$ {preco_mostrado:.2f}")
          st.write(
              f"**Margem de Lucro Real:** {prod.get('lucro_real_pct', 0.0):.1f}%"
              f" (R$ {prod.get('lucro_real_reais', 0.0):.2f} por peça)"
          )
          st.divider()
          st.write(f"**Custo de Produção (Unit.):** R$ {prod['custo']:.2f}")
          st.write(
              f"**Preço Calculado Original (Unit.):** R$"
              f" {prod.get('preco_calculado', 0.0):.2f} ({prod.get('lucro_calc_pct', 0.0):.0f}% de lucro)"
          )
          det_prod = prod["detalhes"]
          tempo_str = det_prod.get(
              "tempo_formatado", f"{det_prod['tempo_h']:.2f}h"
          )
          st.write(
              f"**Impressora:** {det_prod['impressora']} | **Filamento:**"
              f" {det_prod['filamento']} | **Lote na Mesa:**"
              f" {det_prod.get('qtd_pecas_mesa', 1)} un | **Tempo:** {tempo_str}"
          )

          if st.button(f"Excluir produto #{idx+1}", key=f"del_prod_{idx}"):
            dados["produtos_salvos"].pop(idx)
            salvar_dados(dados)
            st.rerun()


# ==========================================
# 3. FILAMENTOS
# ==========================================
elif menu == "Filamentos":
  st.title("🧵 Gerenciamento de Filamentos")

  if "editando_fil" not in st.session_state:
    st.session_state["editando_fil"] = None

  with st.form("form_filamento"):
    edit_key = st.session_state["editando_fil"]
    val_nome = edit_key if edit_key else ""
    val_preco = dados["filamentos"][edit_key] if edit_key else 85.0

    nome_input = st.text_input("Nome do Filamento", value=val_nome)
    preco_input = st.number_input(
        "Preço do Quilo (R$)", min_value=0.0, value=float(val_preco)
    )
    btn_txt = (
        "Atualizar Filamento" if edit_key else "Adicionar Novo Filamento"
    )
    submit_fil = st.form_submit_button(btn_txt)

    if submit_fil:
      if nome_input.strip() != "":
        if edit_key and edit_key != nome_input.strip():
          del dados["filamentos"][edit_key]
        dados["filamentos"][nome_input.strip()] = preco_input
        salvar_dados(dados)
        st.session_state["editando_fil"] = None
        st.success("Filamento salvo com sucesso!")
        st.rerun()
      else:
        st.error("O nome não pode estar em branco.")

  st.divider()
  st.subheader("📋 Filamentos Cadastrados:")
  if dados["filamentos"]:
    for fil, preco in list(dados["filamentos"].items()):
      c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
      c1.write(f"**{fil}**")
      c2.write(f"R$ {preco:.2f} / kg")
      if c3.button("Editar", key=f"edit_fil_{fil}"):
        st.session_state["editando_fil"] = fil
        st.rerun()
      if c4.button("Excluir", key=f"del_fil_{fil}"):
        del dados["filamentos"][fil]
        salvar_dados(dados)
        st.rerun()
  else:
    st.info("Nenhum filamento cadastrado.")


# ==========================================
# 4. IMPRESSORAS
# ==========================================
elif menu == "Impressoras":
  st.title("🖨️ Gerenciamento de Impressoras")

  if "editando_imp" not in st.session_state:
    st.session_state["editando_imp"] = None

  with st.form("form_impressora"):
    edit_imp = st.session_state["editando_imp"]
    val_nome_imp = edit_imp if edit_imp else ""
    val_dep = (
        dados["impressoras"][edit_imp]["depreciacao"] if edit_imp else 0.80
    )
    val_cons = dados["impressoras"][edit_imp]["consumo"] if edit_imp else 150.0

    nome_imp_in = st.text_input("Nome da Impressora", value=val_nome_imp)
    dep_in = st.number_input(
        "Depreciação (R$/h)", min_value=0.0, value=float(val_dep), format="%.2f"
    )
    cons_in = st.number_input("Consumo (Watts)", min_value=0.0, value=val_cons)
    btn_imp_txt = (
        "Atualizar Impressora" if edit_imp else "Cadastrar Impressora"
    )
    submit_imp = st.form_submit_button(btn_imp_txt)

    if submit_imp:
      if nome_imp_in.strip() != "":
        if edit_imp and edit_imp != nome_imp_in.strip():
          del dados["impressoras"][edit_imp]
        dados["impressoras"][nome_imp_in.strip()] = {
            "depreciacao": dep_in,
            "consumo": cons_in,
        }
        salvar_dados(dados)
        st.session_state["editando_imp"] = None
        st.success("Impressora salva com sucesso!")
        st.rerun()
      else:
        st.error("O nome não pode estar em branco.")

  st.divider()
  st.subheader("📋 Impressoras Cadastradas:")
  if dados["impressoras"]:
    for imp, info in list(dados["impressoras"].items()):
      ci1, ci2, ci3, ci4 = st.columns([3, 3, 1, 1])
      ci1.write(f"**{imp}**")
      ci2.write(f"Dep: R${info['depreciacao']:.2f}/h | {info['consumo']}W")
      if ci3.button("Editar", key=f"edit_imp_{imp}"):
        st.session_state["editando_imp"] = imp
        st.rerun()
      if ci4.button("Excluir", key=f"del_imp_{imp}"):
        del dados["impressoras"][imp]
        salvar_dados(dados)
        st.rerun()
  else:
    st.info("Nenhuma impressora cadastrada.")


# ==========================================
# 5. ENERGIA
# ==========================================
elif menu == "Energia":
  st.title("⚡ Custo de Energia Elétrica")
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
elif menu == "Embalagens e Materiais":
  st.title("🎁 Embalagens e Materiais Adicionais")

  if "editando_emb" not in st.session_state:
    st.session_state["editando_emb"] = None

  with st.form("form_embalagem"):
    edit_emb = st.session_state["editando_emb"]
    val_nome_emb = edit_emb if edit_emb else ""
    val_preco_emb = dados["embalagens"][edit_emb] if edit_emb else 2.00

    nome_emb_in = st.text_input("Nome do Material", value=val_nome_emb)
    preco_emb_in = st.number_input(
        "Preço Unitário (R$)", min_value=0.0, value=float(val_preco_emb)
    )
    btn_emb_txt = "Atualizar Material" if edit_emb else "Cadastrar Material"
    submit_emb = st.form_submit_button(btn_emb_txt)

    if submit_emb:
      if nome_emb_in.strip() != "":
        if edit_emb and edit_emb != nome_emb_in.strip():
          del dados["embalagens"][edit_emb]
        dados["embalagens"][nome_emb_in.strip()] = preco_emb_in
        salvar_dados(dados)
        st.session_state["editando_emb"] = None
        st.success("Material salvo com sucesso!")
        st.rerun()
      else:
        st.error("O nome não pode estar em branco.")

  st.divider()
  st.subheader("📋 Materiais Cadastrados:")
  if dados["embalagens"]:
    for emb, preco in list(dados["embalagens"].items()):
      ce1, ce2, ce3, ce4 = st.columns([3, 2, 1, 1])
      ce1.write(f"**{emb}**")
      ce2.write(f"R$ {preco:.2f} un")
      if ce3.button("Editar", key=f"edit_emb_{emb}"):
        st.session_state["editando_emb"] = emb
        st.rerun()
      if ce4.button("Excluir", key=f"del_emb_{emb}"):
        del dados["embalagens"][emb]
        salvar_dados(dados)
        st.rerun()
  else:
    st.info("Nenhum material cadastrado.")
