import json
import os
import streamlit as st

# Configuração da página e layout
st.set_page_config(page_title="Precificador B3D", page_icon="💲", layout="wide")

# --- ESTILIZAÇÃO CSS (Alinhamento, Compactação e Ajustes Visuais) ---
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
    }
    .btn-backup-container {
        margin-top: 14px;
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
    
    div.row-widget.stButton > button[kind="secondary"] {
        background-color: #1E1E2f !important;
        color: #FFFFFF !important;
        border: 1px solid #4A4A5A !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
    }
    div.row-widget.stButton > button[kind="secondary"]:hover {
        background-color: #2a2a3f !important;
        border-color: #6a6a7a !important;
        color: #FFFFFF !important;
    }

    div.stRadio > div {
        gap: 12px !important;
    }
    div.stRadio label {
        padding-top: 6px !important;
        padding-bottom: 6px !important;
    }

    /* Alterando a cor padrão de seleção para verde (#2BDE55) em checkboxes e radios */
    input[type="checkbox"]:checked {
        background-color: #2BDE55 !important;
        border-color: #2BDE55 !important;
    }
    
    div[data-baseweb="checkbox"] div[aria-checked="true"],
    div[data-baseweb="radio"] div[aria-checked="true"] div {
        background-color: #2BDE55 !important;
        border-color: #2BDE55 !important;
    }
    
    .stCheckbox [data-baseweb="checkbox"] [hidden]:checked + div,
    .stRadio [data-baseweb="radio"] input:checked + div {
        background-color: #2BDE55 !important;
        border-color: #2BDE55 !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- ARQUIVO DE BANCO DE DADOS LOCAL ---
DB_FILE = "dados_b3d.json"

CATEGORIAS_DICT = {
    "Casa & Decoração": "HOM",
    "Organização & Setup": "SET",
    "Colecionáveis & Figures": "COL",
    "Jogos & Entretenimento": "GAM",
    "Utilitários & Ferramentas": "UTI",
    "Brinquedos & Sensoriais": "TOY",
}
CATEGORIAS_PRODUTOS = list(CATEGORIAS_DICT.keys())


def carregar_dados():
  if os.path.exists(DB_FILE):
    with open(DB_FILE, "r", encoding="utf-8") as f:
      dados = json.load(f)
      for p in dados.get("produtos_salvos", []):
        if "categoria" not in p:
          p["categoria"] = "Utilitários & Ferramentas"
        if "sku" not in p:
          p["sku"] = ""

      fils_convertidos = {}
      for k, v in dados.get("filamentos", {}).items():
        if isinstance(v, (int, float)):
          fils_convertidos[k] = {"marca": "Genérica", "preco": float(v)}
        else:
          fils_convertidos[k] = v
      dados["filamentos"] = fils_convertidos
      return dados

  return {
      "filamentos": {
          "PLA Padrão": {"marca": "Genérica", "preco": 85.0},
          "PETG": {"marca": "Genérica", "preco": 90.0},
          "ABS": {"marca": "Genérica", "preco": 95.0},
          "Velvet": {"marca": "Genérica", "preco": 110.0},
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


def gerar_proximo_sku(categoria, produtos_salvos):
  sigla = CATEGORIAS_DICT.get(categoria, "UTI")
  prefixo = f"B3{sigla}"

  maior_num = 0
  for p in produtos_salvos:
    sku_existente = p.get("sku", "")
    if sku_existente.startswith(prefixo):
      try:
        num_str = sku_existente[len(prefixo):]
        num = int(num_str)
        if num > maior_num:
          maior_num = num
      except ValueError:
        pass

  proximo_num = maior_num + 1
  return f"{prefixo}{proximo_num:04d}"


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

# ==========================================
# 1. PÁGINA INICIAL: CALCULADORA DE PRECIFICAÇÃO
# ==========================================
if menu == "Calculadora":
  st.title("🖩 Calculadora de Precificação")

  if not dados["filamentos"] or not dados["impressoras"]:
    st.warning(
        "⚠️ Cadastre pelo menos um filamento e uma impressora no menu lateral"
        " antes de calcular."
    )
  else:
    # --- 1. EQUIPAMENTO E INSUMO ---
    st.subheader("1. Equipamento e Insumo")
    col_imp1, col_imp2 = st.columns([2, 2])
    with col_imp1:
      imp_selecionada = st.selectbox(
          "Impressora", list(dados["impressoras"].keys())
      )
    with col_imp2:
      depreciacao_atual = dados["impressoras"][imp_selecionada]["depreciacao"]
      consumo_atual = dados["impressoras"][imp_selecionada]["consumo"]
      st.write("")
      st.info(
          f"🔹 Depreciação: **R$ {depreciacao_atual:.2f}/h** | Consumo:"
          f" **{consumo_atual}W**"
      )

    st.divider()

    # --- 2. PARÂMETROS DE IMPRESSÃO ---
    st.subheader("2. Parâmetros de Impressão")
    col_p1, col_p2, col_p3 = st.columns([2, 2, 2])
    with col_p1:
      qtd_pecas_mesa = st.number_input(
          "Unidades impressas de uma vez na mesa (Lote)",
          min_value=1,
          value=1,
          step=1,
      )
    with col_p2:
      horas_imp = st.number_input(
          "Horas de Impressão", min_value=0, value=4, step=1
      )
    with col_p3:
      minutos_imp = st.number_input(
          "Minutos de Impressão", min_value=0, max_value=59, value=0, step=1
      )

    tempo_h = horas_imp + (minutos_imp / 60.0)
    if tempo_h <= 0:
      tempo_h = 0.01

    st.write("Quantidade total de filamento na mesa:")

    if "filamentos_lista_calc" not in st.session_state:
      st.session_state["filamentos_lista_calc"] = [{"id": 0}]
      st.session_state["calc_contador_id"] = 1

    mapa_fil_formatado = {
        f"{info['marca']} - {nome}": nome
        for nome, info in dados["filamentos"].items()
    }
    lista_formatada = list(mapa_fil_formatado.keys())

    filamentos_escolhidos_calc = []

    for idx, item in enumerate(st.session_state["filamentos_lista_calc"]):
      item_id = item["id"]
      col_f_esq, col_f_dir = st.columns([3, 2.6])

      with col_f_esq:
        fil_formatado_escolhido = st.selectbox(
            f"Filamento #{idx+1}",
            lista_formatada,
            key=f"calc_fil_{item_id}",
        )
      
      nome_real_fil = mapa_fil_formatado[fil_formatado_escolhido]
      preco_kg_fil = dados["filamentos"][nome_real_fil]["preco"]

      with col_f_dir:
        sub_col_qtd, sub_col_del = st.columns([3.2, 1])
        with sub_col_qtd:
          gramas_fil = st.number_input(
              f"Quantidade (g)",
              min_value=0.0,
              value=50.0 if idx == 0 else 0.0,
              key=f"calc_gramas_{item_id}",
          )
        with sub_col_del:
          st.write("") 
          st.write("")
          if len(st.session_state["filamentos_lista_calc"]) > 1:
            if st.button("🗑️", key=f"del_linha_{item_id}", help="Remover"):
              st.session_state["filamentos_lista_calc"].pop(idx)
              st.rerun()

      filamentos_escolhidos_calc.append({
          "nome": nome_real_fil,
          "preco_kg": preco_kg_fil,
          "gramas": gramas_fil,
      })

    if st.button("Adicionar Filamento", type="secondary"):
      novo_id = st.session_state["calc_contador_id"]
      st.session_state["filamentos_lista_calc"].append({"id": novo_id})
      st.session_state["calc_contador_id"] += 1
      st.rerun()

    st.divider()

    # --- 3. EMBALAGENS E MATERIAIS ---
    st.subheader("3. Embalagens e Materiais por Unidade")
    st.write("Selecione os itens e quantidades por peça:")
    
    materiais_escolhidos = []
    if dados["embalagens"]:
      cols_emb = st.columns(4)
      col_idx = 0
      for emb, preco_emb in dados["embalagens"].items():
        with cols_emb[col_idx % 4]:
          usar = st.checkbox(f"{emb} (R$ {preco_emb:.2f} un)", key=f"chk_{emb}")
          if usar:
            qtd_mat = st.number_input(
                f"Qtd de {emb}", min_value=1, value=1, key=f"qtd_{emb}"
            )
            materiais_escolhidos.append(
                {"nome": emb, "preco_unit": preco_emb, "qtd": qtd_mat}
            )
        col_idx += 1
    else:
      st.write("Nenhuma embalagem cadastrada.")

    st.divider()

    # --- 4. MARGENS E TAXAS ---
    st.subheader("4. Margens e Taxas")
    kw_h_atual = dados["kw_h"]

    col_m1, col_m2 = st.columns(2)
    with col_m1:
      taxa_comissao = st.number_input(
          "Comissão do Site / Marketplace (%)",
          min_value=0.0,
          max_value=50.0,
          value=2.0,
          format="%.1f",
          key="com_input",
      )
    with col_m2:
      lucro_desejado = st.number_input(
          "Margem de Lucro Desejada (%)",
          min_value=0.0,
          max_value=500.0,
          value=100.0,
          format="%.1f",
          key="lucro_input",
      )

    taxa_comissao_dec = taxa_comissao / 100.0
    lucro_desejado_dec = lucro_desejado / 100.0

    st.write("")
    # --- BOTÃO DE CALCULAR ---
    if st.button("Calcular Preço", type="primary", use_container_width=True):
      custo_material_total = sum(
          (f["preco_kg"] / 1000) * f["gramas"] for f in filamentos_escolhidos_calc
      )
      peso_total_g = sum(f["gramas"] for f in filamentos_escolhidos_calc)

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
              "filamentos_usados": filamentos_escolhidos_calc,
              "qtd_pecas_mesa": qtd_pecas_mesa,
              "peso_total_g": peso_total_g,
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
      st.write(f"- **Peso Total de Filamento:** {det['peso_total_g']}g")
      for fil_u in det["filamentos_usados"]:
        st.write(
            f"  - {fil_u['nome']} ({fil_u['gramas']}g): R$ "
            f"{(fil_u['preco_kg'] / 1000) * fil_u['gramas']:.2f}"
        )
      st.write(
          f"- **Filamento por peça (Unitário):** R$"
          f" {det['custo_material_unit']:.2f}"
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
    
    # Ordem solicitada: Título, Categoria e SKU (automático)
    col_salv1, col_salv2, col_salv3 = st.columns([3, 2, 2])
    with col_salv1:
      nome_produto = st.text_input("Título:")
    with col_salv2:
      categoria_escolhida = st.selectbox(
          "Categoria:", CATEGORIAS_PRODUTOS, key="select_cat_salvar"
      )
    with col_salv3:
      sku_automatico = gerar_proximo_sku(categoria_escolhida, dados["produtos_salvos"])
      sku_produto = st.text_input("SKU:", value=sku_automatico, disabled=True)

    if st.button("Salvar", key="btn_salvar_prod"):
      if nome_produto.strip() == "":
        st.error("Por favor, digite um título para o produto.")
      else:
        novo_prod = {
            "titulo": nome_produto,
            "sku": sku_automatico,
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
        st.success(f"Produto salvo com sucesso! SKU gerado: {sku_automatico}")


# ==========================================
# 2. PRODUTOS
# ==========================================
elif menu == "Produtos":
  col_tit, col_btn = st.columns([3, 1])
  with col_tit:
    st.title("📦 Produtos")
  with col_btn:
    st.markdown('<div class="btn-backup-container">', unsafe_allow_html=True)
    json_str = json.dumps(dados, ensure_ascii=False, indent=4)
    st.download_button(
        label="📥 Fazer Backup (JSON)",
        data=json_str,
        file_name="dados_b3d_backup.json",
        mime="application/json",
        use_container_width=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

  st.divider()

  st.write("**Filtrar por Categoria:**")

  if "cat_todos" not in st.session_state:
    st.session_state["cat_todos"] = True
    for cat in CATEGORIAS_PRODUTOS:
      st.session_state[f"cat_{cat}"] = True


  def toggle_todos():
    estado_atual = st.session_state["cat_todos"]
    for cat in CATEGORIAS_PRODUTOS:
      st.session_state[f"cat_{cat}"] = estado_atual


  col_f1, col_f2, col_f3, col_f4 = st.columns(4)

  with col_f1:
    st.checkbox("Selecionar Todos", key="cat_todos", on_change=toggle_todos)
    if len(CATEGORIAS_PRODUTOS) > 0:
      st.checkbox(CATEGORIAS_PRODUTOS[0], key=f"cat_{CATEGORIAS_PRODUTOS[0]}")

  with col_f2:
    if len(CATEGORIAS_PRODUTOS) > 1:
      st.checkbox(CATEGORIAS_PRODUTOS[1], key=f"cat_{CATEGORIAS_PRODUTOS[1]}")
    if len(CATEGORIAS_PRODUTOS) > 2:
      st.checkbox(CATEGORIAS_PRODUTOS[2], key=f"cat_{CATEGORIAS_PRODUTOS[2]}")

  with col_f3:
    if len(CATEGORIAS_PRODUTOS) > 3:
      st.checkbox(CATEGORIAS_PRODUTOS[3], key=f"cat_{CATEGORIAS_PRODUTOS[3]}")
    if len(CATEGORIAS_PRODUTOS) > 4:
      st.checkbox(CATEGORIAS_PRODUTOS[4], key=f"cat_{CATEGORIAS_PRODUTOS[4]}")

  with col_f4:
    if len(CATEGORIAS_PRODUTOS) > 5:
      st.checkbox(CATEGORIAS_PRODUTOS[5], key=f"cat_{CATEGORIAS_PRODUTOS[5]}")

  todas_marcadas = all(st.session_state[f"cat_{cat}"] for cat in CATEGORIAS_PRODUTOS)
  if todas_marcadas and not st.session_state["cat_todos"]:
    st.session_state["cat_todos"] = True

  termo_pesquisa = st.text_input(
      "🔍 Pesquisar produto pelo nome ou SKU...", ""
  ).strip().lower()

  st.divider()

  if not dados["produtos_salvos"]:
    st.info("Nenhum produto salvo ainda.")
  else:
    categorias_selecionadas = [
        cat for cat in CATEGORIAS_PRODUTOS if st.session_state.get(f"cat_{cat}", True)
    ]

    produtos_filtrados = []
    for p in dados["produtos_salvos"]:
      prod_cat = p.get("categoria", "Utilitários & Ferramentas")
      match_cat = prod_cat in categorias_selecionadas
      match_pesquisa = (
          not termo_pesquisa 
          or termo_pesquisa in p["titulo"].lower() 
          or termo_pesquisa in p.get("sku", "").lower()
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
        sku_prod = prod.get("sku", "")
        sku_str = f" [SKU: {sku_prod}]" if sku_prod else ""

        with st.expander(
            f"📌 [{cat_prod}] {prod['titulo']}{sku_str} — **R$ {preco_mostrado:.2f} (Unit.)**"
        ):
          st.write(f"**Categoria:** {cat_prod} | **SKU:** {sku_prod if sku_prod else 'N/A'}")
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
              f"**Impressora:** {det_prod['impressora']} | **Lote na Mesa:**"
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
  st.title("🧵 Filamentos")

  if "editando_fil" not in st.session_state:
    st.session_state["editando_fil"] = None

  with st.form("form_filamento"):
    edit_key = st.session_state["editando_fil"]
    val_nome = edit_key if edit_key else ""
    val_marca = (
        dados["filamentos"][edit_key]["marca"]
        if edit_key and edit_key in dados["filamentos"]
        else "Genérica"
    )
    val_preco = (
        dados["filamentos"][edit_key]["preco"]
        if edit_key and edit_key in dados["filamentos"]
        else 85.0
    )

    col_f_in1, col_f_in2, col_f_in3 = st.columns([2, 2, 2])
    with col_f_in1:
      marca_input = st.text_input("Marca:", value=val_marca)
    with col_f_in2:
      nome_input = st.text_input("Nome:", value=val_nome)
    with col_f_in3:
      preco_input = st.number_input(
          "Preço/Kg:", min_value=0.0, value=float(val_preco)
      )

    st.write("")
    btn_txt = "Atualizar" if edit_key else "Salvar"
    submit_fil = st.form_submit_button(btn_txt)

    if submit_fil:
      if nome_input.strip() != "" and marca_input.strip() != "":
        if edit_key and edit_key != nome_input.strip():
          del dados["filamentos"][edit_key]
        dados["filamentos"][nome_input.strip()] = {
            "marca": marca_input.strip(),
            "preco": preco_input,
        }
        salvar_dados(dados)
        st.session_state["editando_fil"] = None
        st.success("Filamento salvo com sucesso!")
        st.rerun()
      else:
        st.error("Preencha a Marca e o Nome do filamento.")

  st.divider()

  if dados["filamentos"]:
    for fil, info in list(dados["filamentos"].items()):
      col_l1, col_l2, col_l3, col_l4 = st.columns([3, 2, 0.5, 0.5])
      with col_l1:
        st.write(f"**{info['marca']} - {fil}**")
      with col_l2:
        st.write(f"R$ {info['preco']:.2f} / kg")
      with col_l3:
        if st.button("✏️", key=f"edit_fil_{fil}", help="Editar filamento"):
          st.session_state["editando_fil"] = fil
          st.rerun()
      with col_l4:
        if st.button("🗑️", key=f"del_fil_{fil}", help="Excluir filamento"):
          del dados["filamentos"][fil]
          salvar_dados(dados)
          st.rerun()
  else:
    st.info("Nenhum filamento cadastrado.")


# ==========================================
# 4. IMPRESSORAS
# ==========================================
elif menu == "Impressoras":
  st.title("🖨️ Impressoras")

  if "editando_imp" not in st.session_state:
    st.session_state["editando_imp"] = None

  with st.form("form_impressora"):
    edit_imp = st.session_state["editando_imp"]
    val_nome_imp = edit_imp if edit_imp else ""
    val_dep = (
        dados["impressoras"][edit_imp]["depreciacao"] if edit_imp else 0.80
    )
    val_cons = dados["impressoras"][edit_imp]["consumo"] if edit_imp else 150.0

    col_imp_in1, col_imp_in2, col_imp_in3 = st.columns([2, 2, 2])
    with col_imp_in1:
      nome_imp_in = st.text_input("Nome:", value=val_nome_imp)
    with col_imp_in2:
      dep_in = st.number_input(
          "Depreciação R$/h:", min_value=0.0, value=float(val_dep), format="%.2f"
      )
    with col_imp_in3:
      cons_in = st.number_input("Consumo (W):", min_value=0.0, value=val_cons)

    st.write("")
    btn_imp_txt = "Atualizar" if edit_imp else "Salvar"
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

  if dados["impressoras"]:
    for imp, info in list(dados["impressoras"].items()):
      col_il1, col_il2, col_il3, col_il4 = st.columns([3, 2, 0.5, 0.5])
      with col_il1:
        st.write(f"**{imp}**")
      with col_il2:
        st.write(f"Dep: R${info['depreciacao']:.2f}/h | {info['consumo']}W")
      with col_il3:
        if st.button("✏️", key=f"edit_imp_{imp}", help="Editar"):
          st.session_state["editando_imp"] = imp
          st.rerun()
      with col_il4:
        if st.button("🗑️", key=f"del_imp_{imp}", help="Excluir"):
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
  
  with st.form("form_energia"):
    novo_kwh = st.number_input(
        "Custo da Energia (R$ / kWh)",
        min_value=0.0,
        value=float(dados["kw_h"]),
        format="%.2f",
    )
    submit_energia = st.form_submit_button("Salvar")

    if submit_energia:
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

    col_emb_in1, col_emb_in2 = st.columns([3, 3])
    with col_emb_in1:
      nome_emb_in = st.text_input("Nome:", value=val_nome_emb)
    with col_emb_in2:
      preco_emb_in = st.number_input(
          "Preço Unitário (R$):", min_value=0.0, value=float(val_preco_emb)
      )

    st.write("")
    btn_emb_txt = "Atualizar Material" if edit_emb else "Salvar"
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

  if dados["embalagens"]:
    for emb, preco in list(dados["embalagens"].items()):
      ce1, ce2, ce3, ce4 = st.columns([3, 2, 0.5, 0.5])
      with ce1:
        st.write(f"**{emb}**")
      with ce2:
        st.write(f"R$ {preco:.2f} un")
      with ce3:
        if st.button("✏️", key=f"edit_emb_{emb}", help="Editar"):
          st.session_state["editando_emb"] = emb
          st.rerun()
      with ce4:
        if st.button("🗑️", key=f"del_emb_{emb}", help="Excluir"):
          del dados["embalagens"][emb]
          salvar_dados(dados)
          st.rerun()
  else:
    st.info("Nenhum material cadastrado.")
