import json
import os
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st

# Configuração da página e layout
st.set_page_config(page_title="Precificador B3D", page_icon="💲", layout="wide")

# --- ESTILIZAÇÃO CSS ---
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
    </style>
""",
    unsafe_allow_html=True,
)

CATEGORIAS_DICT = {
    "Casa & Decoração": "HOM",
    "Organização & Setup": "SET",
    "Colecionáveis & Figures": "COL",
    "Jogos & Entretenimento": "GAM",
    "Utilitários & Ferramentas": "UTI",
    "Brinquedos & Sensoriais": "TOY",
}
CATEGORIAS_PRODUTOS = list(CATEGORIAS_DICT.keys())


# --- CONEXÃO COM O GOOGLE SHEETS ---
def conectar_gsheets():
  try:
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    if "gcp_service_account" in st.secrets:
      creds_dict = dict(st.secrets["gcp_service_account"])
      creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
      gc = gspread.authorize(creds)
    else:
      # Caso queira testar localmente com arquivo
      gc = gspread.service_account(filename="credentials.json")

    sh = gc.open("Banco_Precificação B3D")
    try:
      worksheet = sh.worksheet("Dados")
    except gspread.exceptions.WorksheetNotFound:
      worksheet = sh.add_worksheet(title="Dados", rows=100, cols=20)
    return worksheet
  except Exception as e:
    st.error(f"Erro ao conectar com o Google Sheets: {e}")
    return None


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

  try:
    sheet = conectar_gsheets()
    if sheet:
      conteudo_json = sheet.cell(1, 1).value
      if conteudo_json and str(conteudo_json).strip():
        dados = json.loads(str(conteudo_json))

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
  except Exception:
    pass

  return dados_padrao


def salvar_dados(dados):
  try:
    sheet = conectar_gsheets()
    if sheet:
      json_str = json.dumps(dados, ensure_ascii=False)
      sheet.update(values=[[json_str]], range_name="A1")
      return True
  except Exception as e:
    st.error(f"Erro ao salvar no Google Sheets: {e}")
  return False


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

# --- FERRAMENTA PARA RESTAURAR BACKUP ---
st.sidebar.divider()
st.sidebar.subheader("🔄 Restaurar Backup")
arquivo_submetido = st.sidebar.file_uploader(
    "Enviar arquivo JSON de backup", type=["json"]
)
if arquivo_submetido is not None:
  try:
    conteudo_carregado = json.load(arquivo_submetido)
    if "produtos_salvos" in conteudo_carregado:
      sucesso = salvar_dados(conteudo_carregado)
      if sucesso:
        st.sidebar.success(
            "Backup enviado para o Google Sheets com sucesso! Clique abaixo"
            " para recarregar."
        )
        if st.sidebar.button("🔄 Atualizar Página Agora"):
          st.rerun()
    else:
      st.sidebar.error("O arquivo JSON não parece ser um backup válido.")
  except Exception as e:
    st.sidebar.error(f"Erro ao ler arquivo: {e}")


def gerar_proximo_sku(categoria, produtos_salvos):
  sigla = CATEGORIAS_DICT.get(categoria, "UTI")
  prefixo = f"B3{sigla}"

  maior_num = 0
  for p in produtos_salvos:
    sku_existente = p.get("sku", "")
    if sku_existente.startswith(prefixo):
      try:
        num_str = sku_existente[len(prefixo) :]
        num = int(num_str)
        if num > maior_num:
          maior_num = num
      except ValueError:
        pass

  proximo_num = maior_num + 1
  return f"{prefixo}{proximo_num:04d}"


# ==========================================
# 1. CALCULADORA DE PRECIFICAÇÃO
# ==========================================
if menu == "Calculadora":
  st.title("🖩 Calculadora de Precificação")

  editando_idx = st.session_state.get("editando_produto_idx", None)
  prod_em_edicao = None
  if editando_idx is not None and editando_idx < len(dados["produtos_salvos"]):
    prod_em_edicao = dados["produtos_salvos"][editando_idx]
    st.info(
        f"✏️ Editando o produto: **{prod_em_edicao['titulo']}** (SKU:"
        f" {prod_em_edicao['sku']})"
    )
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

    if (
        "filamentos_lista_calc" not in st.session_state
        or prod_em_edicao
        and f"edit_carregado_{editando_idx}" not in st.session_state
    ):
      if prod_em_edicao:
        fils_usados = prod_em_edicao["detalhes"].get("filamentos_usados", [])
        st.session_state["filamentos_lista_calc"] = []
        for i, fu in enumerate(fils_usados):
          st.session_state["filamentos_lista_calc"].append(
              {"id": i, "nome": fu["nome"], "gramas": fu["gramas"]}
          )
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
              f"Quantidade Total (g)",
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
    st.subheader("3. Embalagens e Materiais Adicionais")

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
          usar = st.checkbox(
              f"{emb} (R$ {preco_emb:.2f} un)", value=ja_usado, key=f"chk_{emb}"
          )
          if usar:
            qtd_default_mat = extras_salvos.get(emb, 1)
            qtd_mat = st.number_input(
                f"Qtd de {emb} (lote todo)",
                min_value=1,
                value=int(qtd_default_mat),
                key=f"qtd_{emb}",
                step=1,
            )
            materiais_escolhidos.append(
                {"nome": emb, "preco_unit": preco_emb, "qtd": qtd_mat}
            )
        col_idx += 1

    st.divider()
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
          key="input_valor_hh",
      )
    with col_mo2:
      tempo_hh = st.number_input(
          "Tempo total de HH (h) [Acabamento para o lote todo]",
          min_value=0.0,
          value=hh_tempo_default,
          step=0.25,
          format="%.2f",
          key="input_tempo_hh",
      )

    st.divider()
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
      custo_material_total_lote = sum(
          (f["preco_kg"] / 1000) * f["gramas"] for f in filamentos_escolhidos_calc
      )
      peso_total_g = sum(f["gramas"] for f in filamentos_escolhidos_calc)

      consumo_kwh = (consumo_atual / 1000) * tempo_h
      custo_energia_total = consumo_kwh * kw_h_atual
      custo_maquina_total = depreciacao_atual * tempo_h

      custo_material_unit = custo_material_total_lote / qtd_pecas_mesa
      custo_energia_unit = custo_energia_total / qtd_pecas_mesa
      custo_maquina_unit = custo_maquina_total / qtd_pecas_mesa

      custo_extras_total_lote = sum(
          item["preco_unit"] * item["qtd"] for item in materiais_escolhidos
      )
      custo_extras_unit = custo_extras_total_lote / qtd_pecas_mesa

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
              "tempo_formatado": (
                  f"{int(tempo_h)}h {int((tempo_h % 1) * 60)}min"
              ),
              "custo_material_unit": custo_material_unit,
              "custo_energia_unit": custo_energia_unit,
              "custo_maquina_unit": custo_maquina_unit,
              "custo_extras_unit": custo_extras_unit,
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
      preco_def_default = float(
          prod_em_edicao.get("preco_definido", preco_def_default)
      )

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
          "Categoria:",
          CATEGORIAS_PRODUTOS,
          index=cat_default_idx,
          key="select_cat_salvar",
      )
    with col_salv3:
      if prod_em_edicao:
        sku_final = prod_em_edicao["sku"]
      else:
        sku_final = gerar_proximo_sku(
            categoria_escolhida, dados["produtos_salvos"]
        )
      st.text_input("SKU:", value=sku_final, disabled=True)
    with col_salv4:
      status_produto = st.selectbox(
          "Status:",
          ["Ativo", "Inativo"],
          index=status_default_idx,
          key="select_status_salvar",
      )

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

  if not dados["produtos_salvos"]:
    st.info("Nenhum produto salvo ainda.")
  else:
    for idx, prod in enumerate(dados["produtos_salvos"]):
      preco_mostrado = prod.get("preco_definido", 0.0)
      with st.expander(
          f"{prod['titulo']} - {prod.get('sku', 'N/A')} - R$ {preco_mostrado:.2f}"
      ):
        st.write(
            f"**Categoria:** {prod.get('categoria', 'Geral')} | **Status:**"
            f" {prod.get('status', 'Ativo')}"
        )
        st.write(f"**Custo:** R$ {prod['custo']:.2f}")


# ==========================================
# 3. FILAMENTOS
# ==========================================
elif menu == "Filamentos":
  st.title("🧵 Filamentos")
  with st.form("form_filamento"):
    marca_input = st.text_input("Marca:")
    nome_input = st.text_input("Nome:")
    preco_input = st.number_input("Preço/Kg:", min_value=0.0, value=85.0)
    if st.form_submit_button("Salvar"):
      if nome_input.strip() and marca_input.strip():
        dados["filamentos"][nome_input.strip()] = {
            "marca": marca_input.strip(),
            "preco": preco_input,
        }
        salvar_dados(dados)
        st.success("Salvo com sucesso!")
        st.rerun()

  for fil, info in dados["filamentos"].items():
    st.write(f"**{info['marca']} - {fil}**: R$ {info['preco']:.2f}/kg")


# ==========================================
# 4. IMPRESSORAS
# ==========================================
elif menu == "Impressoras":
  st.title("🖨️ Impressoras")
  for imp, info in dados["impressoras"].items():
    st.write(f"**{imp}**: Dep: R${info['depreciacao']:.2f}/h | {info['consumo']}W")


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
    if st.form_submit_button("Salvar"):
      dados["kw_h"] = novo_kwh
      salvar_dados(dados)
      st.success("Atualizado com sucesso!")


# ==========================================
# 6. EMBALAGENS E MATERIAIS
# ==========================================
elif menu == "Embalagens e Materiais":
  st.title("🎁 Embalagens e Materiais Adicionais")
  for emb, preco in dados["embalagens"].items():
    st.write(f"**{emb}**: R$ {preco:.2f} un")
