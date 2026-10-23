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

    /* Força o botão de edição a seguir o padrão secundário cinza escuro */
    div.stButton > button[data-baseweb="button"] {
        background-color: #1E1E2f !important;
        color: #FFFFFF !important;
        border: 1px solid #4A4A5A !important;
    }

    div.stRadio > div {
        gap: 12px !important;
    }
    div.stRadio label {
        padding-top: 6px !important;
        padding-bottom: 6px !important;
    }

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

    /* Estilo para deixar produtos inativos com fundo cinza */
    .produto-inativo-expander div[data-testid="stExpander"] {
        background-color: #2b2b2b !important;
        border-color: #444444 !important;
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
  dados_padrao = {
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

  if os.path.exists(DB_FILE):
    try:
      with open(DB_FILE, "r", encoding="utf-8") as f:
        conteudo = f.read().strip()
        if not conteudo:
          return dados_padrao
        dados = json.loads(conteudo)
        for p in dados.get("produtos_salvos", []):
          if "categoria" not in p:
            p["categoria"] = "Utilitários & Ferramentas"
          if "sku" not in p:
            p["sku"] = ""
          if "status" not in p:
            p["status"] = "Ativo"

        fils_convertidos = {}
        for k, v in dados.get("filamentos", {}).items():
          if isinstance(v, (int, float)):
            fils_convertidos[k] = {"marca": "Genérica", "preco": float(v)}
          else:
            fils_convertidos[k] = v
        dados["filamentos"] = fils_convertidos
        return dados
    except (json.JSONDecodeError, Exception):
      return dados_padrao

  return dados_padrao


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

  editando_idx = st.session_state.get("editando_produto_idx", None)
  prod_em_edicao = None
  if editando_idx is not None and editando_idx < len(dados["produtos_salvos"]):
    prod_em_edicao = dados["produtos_salvos"][editando_idx]
    st.info(f"✏️ Editando o produto: **{prod_em_edicao['titulo']}** (SKU: {prod_em_edicao['sku']})")
    if st.button("❌ Cancelar Edição"):
      st.session_state["editando_produto_idx"] = None
      if "ultimo_calculo" in st.session_state:
        del st.session_state["ultimo_calculo"]
      st.rerun()

  if not dados["filamentos"] or not dados["impressoras"]:
    st.warning(
        "⚠️ Cadastre pelo menos um filamento e uma impressora no menu lateral"
        " antes de calcular."
    )
  else:
    st.subheader("1. Equipamento e Insumo")
    
    impressoras_lista = list(dados["impressoras"].keys())
    imp_default_idx = 0
    if prod_em_edicao:
      imp_salva = prod_em_edicao["detalhes"].get("impressora", "")
      if imp_salva in impressoras_lista:
        imp_default_idx = impressoras_lista.index(imp_salva)

    col_imp1, col_imp2 = st.columns([2, 2])
    with col_imp1:
      imp_selecionada = st.selectbox(
          "Impressora", impressoras_lista, index=imp_default_idx
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

    st.subheader("2. Parâmetros de Impressão")
    
    lote_default = 1
    horas_default = 4
    min_default = 0
    if prod_em_edicao:
      lote_default = int(prod_em_edicao["detalhes"].get("qtd_pecas_mesa", 1))
      tempo_h_salvo = prod_em_edicao["detalhes"].get("tempo_h", 4.0)
      horas_default = int(tempo_h_salvo)
      min_default = int(round((tempo_h_salvo - horas_default) * 60))

    col_p1, col_p2, col_p3 = st.columns([2, 2, 2])
    with col_p1:
      qtd_pecas_mesa = st.number_input(
          "Unidades impressas de uma vez na mesa (Lote)",
          min_value=1,
          value=lote_default,
          step=1,
      )
    with col_p2:
      horas_imp = st.number_input(
          "Horas de Impressão", min_value=0, value=horas_default, step=1
      )
    with col_p3:
      minutos_imp = st.number_input(
          "Minutos de Impressão", min_value=0, max_value=59, value=min_default, step=1
      )

    tempo_h = horas_imp + (minutos_imp / 60.0)
    if tempo_h <= 0:
      tempo_h = 0.01

    st.write("Quantidade total de filamento na mesa:")

    mapa_fil_formatado = {
        f"{info['marca']} - {nome}": nome
        for nome, info in dados["filamentos"].items()
    }
    lista_formatada = list(mapa_fil_formatado.keys())

    if "filamentos_lista_calc" not in st.session_state or prod_em_edicao and f"edit_carregado_{editando_idx}" not in st.session_state:
      if prod_em_edicao:
        fils_usados = prod_em_edicao["detalhes"].get("filamentos_usados", [])
        st.session_state["filamentos_lista_calc"] = []
        for i, fu in enumerate(fils_usados):
          st.session_state["filamentos_lista_calc"].append({"id": i, "nome": fu["nome"], "gramas": fu["gramas"]})
        st.session_state["calc_contador_id"] = len(fils_usados)
        st.session_state[f"edit_carregado_{editando_idx}"] = True
      else:
        st.session_state["filamentos_lista_calc"] = [{"id": 0}]
        st.session_state["calc_contador_id"] = 1

    filamentos_escolhidos_calc = []

    for idx, item in enumerate(st.session_state["filamentos_lista_calc"]):
      item_id = item["id"]
      col_f_esq, col_f_dir = st.columns([3, 2.6])

      default_fil_idx = 0
      if "nome" in item:
        for f_fmt, f_real in mapa_fil_formatado.items():
          if f_real == item["nome"]:
            if f_fmt in lista_formatada:
              default_fil_idx = lista_formatada.index(f_fmt)
            break

      with col_f_esq:
        fil_formatado_escolhido = st.selectbox(
            f"Filamento #{idx+1}",
            lista_formatada,
            index=default_fil_idx,
            key=f"calc_fil_{item_id}",
        )
      
      nome_real_fil = mapa_fil_formatado[fil_formatado_escolhido]
      preco_kg_fil = dados["filamentos"][nome_real_fil]["preco"]

      gramas_val_default = item.get("gramas", 50.0 if idx == 0 else 0.0)

      with col_f_dir:
        sub_col_qtd, sub_col_del = st.columns([3.2, 1])
        with sub_col_qtd:
          gramas_fil = st.number_input(
              f"Quantidade (g)",
              min_value=0.0,
              value=float(gramas_val_default),
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

    st.subheader("3. Embalagens e Materiais por Unidade")
    st.write("Selecione os itens e quantidades por peça:")
    
    extras_salvos = {}
    if prod_em_edicao:
      for ext in prod_em_edicao["detalhes"].get("extras", []):
        extras_salvos[ext["nome"]] = ext["qtd"]

    materiais_escolhidos = []
    if dados["embalagens"]:
      cols_emb = st.columns(4)
      col_idx = 0
      for emb, preco_emb in dados["embalagens"].items():
        with cols_emb[col_idx % 4]:
          ja_usado = emb in extras_salvos
          usar = st.checkbox(f"{emb} (R$ {preco_emb:.2f} un)", value=ja_usado, key=f"chk_{emb}")
          if usar:
            qtd_default_mat = extras_salvos.get(emb, 1)
            qtd_mat = st.number_input(
                f"Qtd de {emb}", min_value=1, value=int(qtd_default_mat), key=f"qtd_{emb}"
            )
            materiais_escolhidos.append(
                {"nome": emb, "preco_unit": preco_emb, "qtd": qtd_mat}
            )
        col_idx += 1
    else:
      st.write("Nenhuma embalagem cadastrada.")

    st.divider()

    # --- 4. MÃO DE OBRA ---
    st.subheader("4. Mão de Obra")
    
    hh_valor_default = 20.0
    hh_tempo_default = 0.0
    if prod_em_edicao:
      hh_valor_default = float(prod_em_edicao["detalhes"].get("hh_valor", 20.0))
      hh_tempo_default = float(prod_em_edicao["detalhes"].get("hh_tempo", 0.0))

    col_mo1, col_mo2 = st.columns(2)
    with col_mo1:
      valor_hh = st.number_input(
          "Valor de HH (R$/h)",
          min_value=0.0,
          value=hh_valor_default,
          format="%.2f",
          key="input_valor_hh"
      )
    with col_mo2:
      tempo_hh = st.number_input(
          "Tempo de HH (h) [Acabamento / Trabalho Adicional]",
          min_value=0.0,
          value=hh_tempo_default,
          step=0.25,
          format="%.2f",
          key="input_tempo_hh"
      )

    st.divider()

    # --- 5. MARGENS E TAXAS ---
    st.subheader("5. Margens e Taxas")
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

      custo_mo_total = valor_hh * tempo_hh
      custo_mo_unit = custo_mo_total / qtd_pecas_mesa

      custo_producao = (
          custo_material_unit
          + custo_energia_unit
          + custo_maquina_unit
          + custo_extras_unit
          + custo_mo_unit
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
              "hh_valor": valor_hh,
              "hh_tempo": tempo_hh,
              "custo_mo_unit": custo_mo_unit,
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
    
    preco_def_default = float(round(calc["preco_venda_calculado"], 2))
    if prod_em_edicao:
      preco_def_default = float(prod_em_edicao.get("preco_definido", preco_def_default))

    col_def1, col_def2 = st.columns(2)
    with col_def1:
      preco_definido = st.number_input(
          "Preço Final Definido por Unidade (R$)",
          min_value=0.0,
          value=preco_def_default,
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
      # Correção absoluta contra o bug do LaTeX usando st.text puro para Mão de Obra
      hh_t = det.get('hh_tempo', 0)
      hh_v = det.get('hh_valor', 20)
      c_mo = det.get('custo_mo_unit', 0)
      st.text(f"- Mão de Obra: {hh_t}h a R$ {hh_v:.2f}/h (R$ {c_mo:.2f} unit.)")

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
    
    titulo_default = ""
    cat_default_idx = 0
    status_default_idx = 0
    if prod_em_edicao:
      titulo_default = prod_em_edicao["titulo"]
      cat_salva = prod_em_edicao.get("categoria", CATEGORIAS_PRODUTOS[0])
      if cat_salva in CATEGORIAS_PRODUTOS:
        cat_default_idx = CATEGORIAS_PRODUTOS.index(cat_salva)
      if prod_em_edicao.get("status", "Ativo") == "Inativo":
        status_default_idx = 1

    col_salv1, col_salv2, col_salv3, col_salv4 = st.columns([3, 2, 2, 2])
    with col_salv1:
      nome_produto = st.text_input("Título:", value=titulo_default)
    with col_salv2:
      categoria_escolhida = st.selectbox(
          "Categoria:", CATEGORIAS_PRODUTOS, index=cat_default_idx, key="select_cat_salvar"
      )
    with col_salv3:
      if prod_em_edicao:
        sku_final = prod_em_edicao["sku"]
      else:
        sku_final = gerar_proximo_sku(categoria_escolhida, dados["produtos_salvos"])
      st.text_input("SKU:", value=sku_final, disabled=True)
    with col_salv4:
      status_produto = st.selectbox("Status:", ["Ativo", "Inativo"], index=status_default_idx, key="select_status_salvar")

    btn_label = "Atualizar Produto" if prod_em_edicao else "Salvar"
    if st.button(btn_label, key="btn_salvar_prod"):
      if nome_produto.strip() == "":
        st.error("Por favor, digite um título para o produto.")
      else:
        novo_prod = {
            "titulo": nome_produto,
            "sku": sku_final,
            "categoria": categoria_escolhida,
            "status": status_produto,
            "preco_definido": preco_definido,
            "lucro_real_pct": lucro_real_pct,
            "lucro_real_reais": lucro_real_reais,
            "custo": calc["custo_producao"],
            "preco_calculado": calc["preco_venda_calculado"],
            "lucro_calc_pct": calc["lucro_calc_pct"],
            "detalhes": calc["detalhes"],
        }
        
        if prod_em_edicao:
          dados["produtos_salvos"][editando_idx] = novo_prod
          st.session_state["editando_produto_idx"] = None
          st.success(f"Produto atualizado com sucesso! SKU mantido: {sku_final}")
        else:
          dados["produtos_salvos"].append(novo_prod)
          st.success(f"Produto salvo com sucesso! SKU gerado: {sku_final}")
          
        salvar_dados(dados)
        if "ultimo_calculo" in st.session_state:
          del st.session_state["ultimo_calculo"]
        if "filamentos_lista_calc" in st.session_state:
          del st.session_state["filamentos_lista_calc"]


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

  st.write("**Filtrar por Status:**")
  col_st1, col_st2 = st.columns(2)
  with col_st1:
    filtro_ativo = st.checkbox("Ativos", value=True, key="filtro_status_ativo")
  with col_st2:
    filtro_inativo = st.checkbox("Inativos", value=True, key="filtro_status_inativo")

  st.write("")
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
      prod_status = p.get("status", "Ativo")

      match_status = False
      if prod_status == "Ativo" and filtro_ativo:
        match_status = True
      elif prod_status == "Inativo" and filtro_inativo:
        match_status = True

      match_cat = prod_cat in categorias_selecionadas
      match_pesquisa = (
          not termo_pesquisa 
          or termo_pesquisa in p["titulo"].lower() 
          or termo_pesquisa in p.get("sku", "").lower()
      )
      if match_status and match_cat and match_pesquisa:
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
        status_prod = prod.get("status", "Ativo")

        titulo_str = prod["titulo"]
        sku_str = sku_prod if sku_prod else "N/A"
        preco_str = f"R$ {preco_mostrado:.2f}"

        if status_prod == "Inativo":
          st.markdown('<div class="produto-inativo-expander">', unsafe_allow_html=True)

        with st.expander(f"{titulo_str} - {sku_str} - {preco_str}"):
          novo_status_escolhido = st.selectbox(
              "Status do Produto", 
              ["Ativo", "Inativo"], 
              index=0 if status_prod == "Ativo" else 1, 
              key=f"status_direto_{idx}"
          )
          
          if novo_status_escolhido != status_prod:
            dados["produtos_salvos"][idx]["status"] = novo_status_escolhido
            salvar_dados(dados)
            st.rerun()

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
          
          hh_t_prod = det_prod.get('hh_tempo', 0)
          hh_v_prod = det_prod.get('hh_valor', 20)
          c_mo_prod = det_prod.get('custo_mo_unit', 0)
          st.text(f"Mão de Obra: {hh_t_prod}h a R$ {hh_v_prod:.2f}/h (R$ {c_mo_prod:.2f} unit.)")
          
          extras_lista = det_prod.get("extras", [])
          if extras_lista:
            st.write("**Materiais Extras / Embalagens Utilizados:**")
            for ext in extras_lista:
              st.write(f"- {ext['nome']}: {ext['qtd']} un (R$ {ext['preco_unit']:.2f} cada)")
          else:
            st.write("**Materiais Extras / Embalagens:** Nenhum extra selecionado.")

          st.write("")
          # Botão de editar padrão com type="secondary"
          if status_prod == "Ativo":
            if st.button("✏️ Editar Produto", key=f"edit_prod_{idx}", type="secondary"):
              st.session_state["editando_produto_idx"] = idx
              if "filamentos_lista_calc" in st.session_state:
                del st.session_state["filamentos_lista_calc"]
              st.rerun()
          else:
            st.info("ℹ️ Produto inativo (modo histórico). Mude o status acima para Ativo caso deseje editá-lo.")

        if status_prod == "Inativo":
          st.markdown('</div>', unsafe_allow_html=True)


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
