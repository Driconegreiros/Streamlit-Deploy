import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Processos Judiciais",
    page_icon="📊",
    layout="wide"
)

# Título do dashboard
st.title("📊 Dashboard de Análise de Processos Judiciais")
st.markdown("---")

# Carregar os dados
@st.cache_data
def load_data():
    # Lendo o arquivo CSV (ajuste o caminho se necessário)
    df = pd.read_csv('Dataset.csv')
    
    # Limpeza básica dos dados
    # Remover linhas com Processo vazio (apenas se for completamente vazio)
    df = df.dropna(subset=['Processo'], how='all')
    
    # Converter Ano para numérico, lidando com valores não numéricos
    df['Ano'] = pd.to_numeric(df['Ano'], errors='coerce')
    
    # Remover anos inválidos (menores que 1900 ou maiores que 2100)
    df = df[(df['Ano'] >= 1900) & (df['Ano'] <= 2100)]
    
    # Converter anos para inteiros para evitar frações
    df['Ano'] = df['Ano'].fillna(0).astype(int)
    df = df[df['Ano'] > 0]
    
    return df

df = load_data()

# Sidebar com filtros
st.sidebar.header("🔍 Filtros")

# Filtro por ano
min_year = int(df['Ano'].min())
max_year = int(df['Ano'].max())
year_range = st.sidebar.slider(
    "Selecione o intervalo de anos:",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year)
)

# Filtro por Comarca
comarcas = ['Todos'] + sorted(df['Comarca'].dropna().unique().tolist())
selected_comarca = st.sidebar.selectbox("Selecione a Comarca:", comarcas)

# Aplicar filtros
filtered_df = df.copy()
filtered_df = filtered_df[(filtered_df['Ano'] >= year_range[0]) & 
                          (filtered_df['Ano'] <= year_range[1])]

if selected_comarca != 'Todos':
    filtered_df = filtered_df[filtered_df['Comarca'] == selected_comarca]

# Mostrar estatísticas básicas
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total de Processos", f"{len(filtered_df):,}".replace(",", "."))
    
with col2:
    st.metric("Período Analisado", f"{year_range[0]} - {year_range[1]}")
    
with col3:
    unique_years = filtered_df['Ano'].nunique()
    st.metric("Anos Abrangidos", unique_years)
    
with col4:
    if selected_comarca == 'Todos':
        st.metric("Comarcas", df['Comarca'].nunique())
    else:
        st.metric("Comarca Selecionada", selected_comarca)

st.markdown("---")

# 1. EVOLUÇÃO TEMPORAL
st.header("📈 Evolução Temporal da Quantidade de Processos")

# Agrupar por ano (garantindo que seja inteiro)
yearly_counts = filtered_df['Ano'].astype(int).value_counts().sort_index()
yearly_df = pd.DataFrame({
    'Ano': yearly_counts.index.astype(int),
    'Quantidade': yearly_counts.values
})

# Criar gráfico de linhas
fig1 = go.Figure()

fig1.add_trace(go.Scatter(
    x=yearly_df['Ano'],
    y=yearly_df['Quantidade'],
    mode='lines+markers',
    name='Processos',
    line=dict(color='#1f77b4', width=3),
    marker=dict(size=8, color='#1f77b4'),
    fill='tozeroy',
    fillcolor='rgba(31, 119, 180, 0.1)',
    hovertemplate='<b>Ano: %{x}</b><br>Quantidade: %{y:,}<extra></extra>'.replace(",", ".")
))

fig1.update_layout(
    title='Evolução Anual da Quantidade de Processos',
    xaxis_title='Ano',
    yaxis_title='Quantidade de Processos',
    hovermode='x unified',
    template='plotly_white',
    height=400,
    showlegend=False,
    xaxis=dict(
        type='category',
        tickmode='linear',
        dtick=1 if len(yearly_df) <= 20 else max(1, len(yearly_df) // 10)
    ),
    yaxis=dict(
        tickformat=',.0f'
    )
)

st.plotly_chart(fig1, use_container_width=True)

# 2. TOP 10 APENAS DOS ASSUNTOS (MAIOR NO TOPO, TONALIDADE AZUL)
st.header("🏆 TOP 10 - Assuntos Mais Frequentes")

# Pegar os top 10 assuntos
top_assuntos = filtered_df['Assunto'].value_counts().head(10)
top_assuntos_df = pd.DataFrame({
    'Assunto': top_assuntos.index,
    'Quantidade': top_assuntos.values
})

# Ordenar do MAIOR para o MENOR (maior no topo)
top_assuntos_df = top_assuntos_df.sort_values('Quantidade', ascending=True)  # Para gráfico horizontal

# Formatar números
top_assuntos_df['Quantidade_formatada'] = top_assuntos_df['Quantidade'].apply(
    lambda x: f"{x:,}".replace(",", ".")
)

# Truncar labels muito longos
top_assuntos_df['Assunto_display'] = top_assuntos_df['Assunto'].apply(
    lambda x: (x[:40] + '...') if len(x) > 40 else x
)

# Criar gradiente de cores AZUL (mais forte no topo para maior, mais fraco na base para menor)
n = len(top_assuntos_df)
colors = []
for i in range(n):
    # Gradiente de AZUL: mais forte no topo (maior valor), mais fraco na base (menor valor)
    intensity = 0.3 + 0.7 * ((n-1-i) / (n-1)) if n > 1 else 1.0  # Mais forte no topo
    # Converter para cor hexadecimal - usando azul (1f77b4)
    red = int(31 * intensity)    # Base 1f77b4 (31, 119, 180)
    green = int(119 * intensity)
    blue = int(180 * intensity)
    colors.append(f'rgb({red}, {green}, {blue})')

# Criar gráfico melhorado
fig2 = go.Figure()

fig2.add_trace(go.Bar(
    y=top_assuntos_df['Assunto_display'],
    x=top_assuntos_df['Quantidade'],
    orientation='h',
    marker=dict(
        color=colors,
        line=dict(color='rgba(0,0,0,0.5)', width=1)
    ),
    text=top_assuntos_df['Quantidade_formatada'],
    textposition='outside',
    textfont=dict(size=12, color='black', family='Arial, sans-serif'),
    hovertemplate='<b>%{customdata}</b><br>Quantidade: %{x:,}<extra></extra>'.replace(",", "."),
    customdata=top_assuntos_df['Assunto'],
    textangle=0
))

# Configurar layout - MAIOR NO TOPO
fig2.update_layout(
    title={
        'text': 'TOP 10 Assuntos Mais Frequentes',
        'y': 0.95,
        'x': 0.5,
        'xanchor': 'center',
        'yanchor': 'top',
        'font': dict(size=18, color='black', family='Arial, sans-serif')
    },
    yaxis=dict(
        title='',
        tickfont=dict(size=12, family='Arial, sans-serif'),
        automargin=True,
        categoryorder='total descending',  # MAIOR NO TOPO ← CORRETO
        autorange='reversed',  # Para gráfico horizontal
        gridcolor='rgba(128,128,128,0.1)'
    ),
    xaxis=dict(
        title='Quantidade de Processos',
        title_font=dict(size=14, family='Arial, sans-serif'),
        showgrid=True,
        gridcolor='rgba(128,128,128,0.2)',
        tickformat=',.0f',
        range=[0, top_assuntos_df['Quantidade'].max() * 1.2]
    ),
    height=600,
    margin=dict(l=10, r=200, t=80, b=80),
    template='plotly_white',
    showlegend=False,
    plot_bgcolor='white',
    paper_bgcolor='white'
)

# Adicionar linha de grade horizontal
fig2.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.1)')

st.plotly_chart(fig2, use_container_width=True)

# 3. RELAÇÃO ENTRE CLASSE E ASSUNTO
st.header("🔗 Relação entre Classe e Assunto")

# Criar dropdowns para seleção
col1, col2 = st.columns(2)

with col1:
    # Dropdown para selecionar classe
    classes_list = sorted(filtered_df['Classe'].unique().tolist())
    selected_classe_rel = st.selectbox(
        "Selecione uma Classe para análise:",
        classes_list,
        index=classes_list.index("Procedimento Comum") if "Procedimento Comum" in classes_list else 0
    )

with col2:
    # Dropdown para selecionar assunto
    assuntos_list = sorted(filtered_df['Assunto'].unique().tolist())
    selected_assunto_rel = st.selectbox(
        "Selecione um Assunto para análise:",
        assuntos_list,
        index=assuntos_list.index("Concurso público") if "Concurso público" in assuntos_list else 0
    )

# Criar dois gráficos lado a lado
col1, col2 = st.columns(2)

with col1:
    # Gráfico 1: Assuntos para a Classe selecionada (MAIOR NO TOPO)
    classe_data = filtered_df[filtered_df['Classe'] == selected_classe_rel]
    
    if not classe_data.empty:
        # Pegar os top 10 assuntos para esta classe
        top_assuntos_classe = classe_data['Assunto'].value_counts().head(10)
        
        # Criar DataFrame - manter ordem do maior para o menor
        assuntos_df = pd.DataFrame({
            'Assunto': top_assuntos_classe.index,
            'Quantidade': top_assuntos_classe.values
        })
        
        # Ordenar para gráfico (maior no topo)
        assuntos_df = assuntos_df.sort_values('Quantidade', ascending=True)
        
        # Formatar números
        assuntos_df['Quantidade_formatada'] = assuntos_df['Quantidade'].apply(
            lambda x: f"{x:,}".replace(",", ".")
        )
        
        # Truncar labels
        assuntos_df['Assunto_display'] = assuntos_df['Assunto'].apply(
            lambda x: (x[:30] + '...') if len(x) > 30 else x
        )
        
        # Criar gráfico
        fig3a = go.Figure()
        
        fig3a.add_trace(go.Bar(
            y=assuntos_df['Assunto_display'],
            x=assuntos_df['Quantidade'],
            orientation='h',
            marker=dict(
                color='#3498db',
                line=dict(color='rgba(0,0,0,0.3)', width=1)
            ),
            text=assuntos_df['Quantidade_formatada'],
            textposition='auto',
            textfont=dict(size=11, color='black'),
            hovertemplate='<b>%{customdata}</b><br>Quantidade: %{x:,}<extra></extra>'.replace(",", "."),
            customdata=assuntos_df['Assunto']
        ))
        
        fig3a.update_layout(
            title=f'Top Assuntos para: {selected_classe_rel}',
            yaxis=dict(
                title='',
                tickfont=dict(size=10),
                automargin=True,
                categoryorder='total descending',  # Maior no TOPO
                autorange='reversed'  # Para gráfico horizontal
            ),
            xaxis=dict(
                title='Quantidade',
                showgrid=True,
                gridcolor='rgba(128,128,128,0.2)',
                tickformat=',.0f'
            ),
            height=400,
            margin=dict(l=10, r=10, t=50, b=50),
            template='plotly_white',
            showlegend=False
        )
        
        st.plotly_chart(fig3a, use_container_width=True)
    else:
        st.info(f"Nenhum dado encontrado para a classe: {selected_classe_rel}")

with col2:
    # Gráfico 2: Classes para o Assunto selecionado (MAIOR NO TOPO)
    assunto_data = filtered_df[filtered_df['Assunto'] == selected_assunto_rel]
    
    if not assunto_data.empty:
        # Pegar as top 10 classes para este assunto
        top_classes_assunto = assunto_data['Classe'].value_counts().head(10)
        
        # Criar DataFrame - manter ordem do maior para o menor
        classes_df = pd.DataFrame({
            'Classe': top_classes_assunto.index,
            'Quantidade': top_classes_assunto.values
        })
        
        # Ordenar para gráfico (maior no topo)
        classes_df = classes_df.sort_values('Quantidade', ascending=True)
        
        # Formatar números
        classes_df['Quantidade_formatada'] = classes_df['Quantidade'].apply(
            lambda x: f"{x:,}".replace(",", ".")
        )
        
        # Truncar labels
        classes_df['Classe_display'] = classes_df['Classe'].apply(
            lambda x: (x[:30] + '...') if len(x) > 30 else x
        )
        
        # Criar gráfico
        fig3b = go.Figure()
        
        fig3b.add_trace(go.Bar(
            y=classes_df['Classe_display'],
            x=classes_df['Quantidade'],
            orientation='h',
            marker=dict(
                color='#e74c3c',
                line=dict(color='rgba(0,0,0,0.3)', width=1)
            ),
            text=classes_df['Quantidade_formatada'],
            textposition='auto',
            textfont=dict(size=11, color='black'),
            hovertemplate='<b>%{customdata}</b><br>Quantidade: %{x:,}<extra></extra>'.replace(",", "."),
            customdata=classes_df['Classe']
        ))
        
        fig3b.update_layout(
            title=f'Top Classes para: {selected_assunto_rel}',
            yaxis=dict(
                title='',
                tickfont=dict(size=10),
                automargin=True,
                categoryorder='total descending',  # Maior no TOPO
                autorange='reversed'  # Para gráfico horizontal
            ),
            xaxis=dict(
                title='Quantidade',
                showgrid=True,
                gridcolor='rgba(128,128,128,0.2)',
                tickformat=',.0f'
            ),
            height=400,
            margin=dict(l=10, r=10, t=50, b=50),
            template='plotly_white',
            showlegend=False
        )
        
        st.plotly_chart(fig3b, use_container_width=True)
    else:
        st.info(f"Nenhum dado encontrado para o assunto: {selected_assunto_rel}")

# 4. ANÁLISE DE ASSUNTOS DETALHADA
st.header("📋 Análise Detalhada por Assunto")

# Selecionar um assunto para análise detalhada
top_assuntos_list = filtered_df['Assunto'].value_counts().head(10).index.tolist()
selected_assunto = st.selectbox("Selecione um Assunto para análise detalhada:", top_assuntos_list)

if selected_assunto:
    # Filtrar dados para o assunto selecionado
    assunto_data = filtered_df[filtered_df['Assunto'] == selected_assunto]
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Distribuição por ano para o assunto selecionado
        assunto_por_ano = assunto_data['Ano'].value_counts().sort_index()
        fig4 = px.bar(
            x=assunto_por_ano.index,
            y=assunto_por_ano.values,
            title=f'Evolução do Assunto: {selected_assunto}',
            labels={'x': 'Ano', 'y': 'Quantidade de Processos'},
            color_discrete_sequence=['#FF6B6B']
        )
        
        fig4.update_layout(
            height=350,
            template='plotly_white',
            xaxis=dict(tickmode='linear'),
            yaxis_title='Número de Processos'
        )
        fig4.update_traces(
            hovertemplate='<b>Ano: %{x}</b><br>Quantidade: %{y:,}<extra></extra>'.replace(",", "."),
            text=assunto_por_ano.values,
            texttemplate='%{y:,}'.replace(",", "."),
            textposition='outside'
        )
        st.plotly_chart(fig4, use_container_width=True)
    
    with col2:
        # Distribuição por classe para o assunto selecionado
        assunto_por_classe = assunto_data['Classe'].value_counts().head(10)
        
        # Criar DataFrame mantendo ordem do maior para o menor
        classe_dist_df = pd.DataFrame({
            'Classe': assunto_por_classe.index,
            'Quantidade': assunto_por_classe.values
        })
        
        # Ordenar para gráfico (maior no topo)
        classe_dist_df = classe_dist_df.sort_values('Quantidade', ascending=True)
        
        # Formatar números
        classe_dist_df['Quantidade_formatada'] = classe_dist_df['Quantidade'].apply(
            lambda x: f"{x:,}".replace(",", ".")
        )
        
        # Truncar labels se necessário
        classe_dist_df['Classe_display'] = classe_dist_df['Classe'].apply(
            lambda x: (x[:35] + '...') if len(x) > 35 else x
        )
        
        # Criar gráfico
        fig5 = go.Figure()
        
        fig5.add_trace(go.Bar(
            y=classe_dist_df['Classe_display'],
            x=classe_dist_df['Quantidade'],
            orientation='h',
            marker=dict(
                color='#4ECDC4',
                line=dict(color='rgba(0,0,0,0.3)', width=1)
            ),
            text=classe_dist_df['Quantidade_formatada'],
            textposition='auto',
            textfont=dict(size=11, color='black'),
            hovertemplate='<b>%{customdata}</b><br>Quantidade: %{x:,}<extra></extra>'.replace(",", "."),
            customdata=classe_dist_df['Classe']
        ))
        
        fig5.update_layout(
            title=f'Classes para o Assunto: {selected_assunto}',
            yaxis=dict(
                title='',
                tickfont=dict(size=11),
                automargin=True,
                categoryorder='total descending',  # Maior no TOPO
                autorange='reversed'  # Para gráfico horizontal
            ),
            xaxis=dict(
                title='Quantidade de Processos',
                showgrid=True,
                gridcolor='rgba(128,128,128,0.2)',
                tickformat=',.0f'
            ),
            height=350,
            margin=dict(l=10, r=150, t=50, b=50),
            template='plotly_white',
            showlegend=False
        )
        
        st.plotly_chart(fig5, use_container_width=True)

# 5. VISUALIZAÇÃO DOS DADOS
st.header("🔍 Visualização dos Dados")

# Expander para visualizar os dados brutos
with st.expander("📋 Visualizar Dados Filtrados"):
    # Mostrar apenas as colunas mais importantes
    display_columns = ['Processo', 'Classe', 'Assunto', 'Comarca', 'Ano']
    display_df = filtered_df[display_columns].sort_values('Ano', ascending=False).head(100)
    
    # Formatar números na exibição
    st.dataframe(
        display_df,
        use_container_width=True,
        height=300
    )

# Informações sobre o dataset
st.sidebar.markdown("---")
st.sidebar.header("ℹ️ Sobre os Dados")
st.sidebar.info(f"""
**Total de registros:** {len(df):,}".replace(",", ".")
**Período:** {int(df['Ano'].min())} - {int(df['Ano'].max())}
**Classes únicas:** {df['Classe'].nunique()}
**Assuntos únicos:** {df['Assunto'].nunique()}
**Comarcas:** {df['Comarca'].nunique()}
""")

# ============================================
# MAPA DO AMAZONAS (CORES PROPORCIONAIS AOS PROCESSOS)
# ============================================
st.markdown("---")
st.header("🗺️ Mapa do Amazonas - Distribuição de Processos por Município")

# Dicionário com coordenadas dos municípios do Amazonas
coordenadas_municipios = {
    'Manaus': {'lat': -3.1190, 'lon': -60.0217},
    'Parintins': {'lat': -2.6287, 'lon': -56.7359},
    'Itacoatiara': {'lat': -3.1386, 'lon': -58.4449},
    'Manacapuru': {'lat': -3.2903, 'lon': -60.6216},
    'Coari': {'lat': -4.0856, 'lon': -63.1414},
    'Tefé': {'lat': -3.3684, 'lon': -64.7193},
    'Tabatinga': {'lat': -4.2316, 'lon': -69.9383},
    'Maués': {'lat': -3.3839, 'lon': -57.7187},
    'Humaitá': {'lat': -7.5117, 'lon': -63.0328},
    'Lábrea': {'lat': -7.2585, 'lon': -64.7977},
    'São Gabriel da Cachoeira': {'lat': -0.1302, 'lon': -67.0890},
    'Benjamin Constant': {'lat': -4.3833, 'lon': -70.0333},
    'Borba': {'lat': -4.3878, 'lon': -59.5939},
    'Autazes': {'lat': -3.5853, 'lon': -59.1256},
    'Nova Olinda do Norte': {'lat': -3.8889, 'lon': -59.0944},
    'Careiro': {'lat': -3.7681, 'lon': -60.3692},
    'Iranduba': {'lat': -3.2847, 'lon': -60.1858},
    'Presidente Figueiredo': {'lat': -2.0342, 'lon': -60.0234},
    'Rio Preto da Eva': {'lat': -2.6981, 'lon': -59.7019},
    'Novo Airão': {'lat': -2.6361, 'lon': -60.9436},
    'Santa Isabel do Rio Negro': {'lat': -0.4139, 'lon': -65.0192},
    'Barcelos': {'lat': -0.9750, 'lon': -62.9239},
    'Novo Aripuanã': {'lat': -5.1258, 'lon': -60.3797},
    'Apuí': {'lat': -7.1964, 'lon': -59.8914},
    'Manicoré': {'lat': -5.8092, 'lon': -61.3003},
    'Beruri': {'lat': -3.8983, 'lon': -61.3733},
    'Anori': {'lat': -3.7461, 'lon': -61.6442},
    'Codajás': {'lat': -3.8369, 'lon': -62.0569},
    'Caapiranga': {'lat': -3.3153, 'lon': -61.2206},
    'Urucurituba': {'lat': -3.1286, 'lon': -58.1553},
    'Urucará': {'lat': -2.5364, 'lon': -57.7600},
    'São Sebastião do Uatumã': {'lat': -2.5714, 'lon': -57.8714},
    'Itapiranga': {'lat': -2.7489, 'lon': -58.0219},
    'Silves': {'lat': -2.8392, 'lon': -58.2092},
    'Barreirinha': {'lat': -2.7939, 'lon': -57.0703},
    'Boa Vista do Ramos': {'lat': -2.9714, 'lon': -57.5900},
    'Nhamundá': {'lat': -2.1864, 'lon': -56.7131},
    'Fonte Boa': {'lat': -2.5142, 'lon': -66.0919},
    'Japurá': {'lat': -1.8264, 'lon': -66.5989},
    'Maraã': {'lat': -1.8561, 'lon': -65.5806},
    'Uarini': {'lat': -2.9900, 'lon': -65.1083},
    'Alvarães': {'lat': -3.2211, 'lon': -64.8042},
    'Carauari': {'lat': -4.8828, 'lon': -66.8958},
    'Ipixuna': {'lat': -7.0508, 'lon': -71.6950},
    'Eirunepé': {'lat': -6.6619, 'lon': -69.8742},
    'Envira': {'lat': -7.4325, 'lon': -70.0225},
    'Guajará': {'lat': -7.5464, 'lon': -72.5842},
    'Atalaia do Norte': {'lat': -4.3703, 'lon': -70.1917},
    'Santo Antônio do Içá': {'lat': -3.1022, 'lon': -67.9400},
    'Amaturá': {'lat': -3.3647, 'lon': -68.1978},
    'São Paulo de Olivença': {'lat': -3.3783, 'lon': -68.8725},
    'Tonantins': {'lat': -2.8731, 'lon': -67.8019},
    'Jutaí': {'lat': -2.7469, 'lon': -66.7669},
    'Boca do Acre': {'lat': -8.7525, 'lon': -67.3983},
    'Pauini': {'lat': -7.7139, 'lon': -66.9764},
    'Canutama': {'lat': -6.5342, 'lon': -64.3836},
    'Tapauá': {'lat': -5.6261, 'lon': -63.1825}
}

# Lista de tribunais para ignorar (não são municípios)
tribunais = [
    'Tribunal De Justiça',
    'Turmas Recursais dos Juizados Especiais',
    'Supremo Tribunal Federal',
    'Seção Judiciária do Amazonas',
    'Tribunal Regional Federal da 1ª Região',
    'Superior Tribunal De Justiça',
    'Tribunal De Justiça Militar',
    'Tribunal Regional Federal',
    'Tribunal Regional do Trabalho',
    'TST',
    'STJ',
    'STF',
    'TJM',
    'TRF',
    'TRT',
    'Comarca De Brasília'
]

# Função para extrair apenas o nome do município
def extrair_municipio(comarca):
    if pd.isna(comarca):
        return None
    
    comarca_str = str(comarca)
    
    # Verificar se é tribunal (ignorar)
    for tribunal in tribunais:
        if tribunal in comarca_str:
            return None
    
    # Remover "Comarca de " do início
    if comarca_str.startswith('Comarca de '):
        return comarca_str.replace('Comarca de ', '').strip()
    elif comarca_str.startswith('Comarca De '):
        return comarca_str.replace('Comarca De ', '').strip()
    else:
        return comarca_str

# Criar uma coluna com o nome do município extraído
filtered_df['Municipio'] = filtered_df['Comarca'].apply(extrair_municipio)

# Contar processos por município (ignorando tribunais)
municipio_counts = filtered_df[filtered_df['Municipio'].notna()]['Municipio'].value_counts().reset_index()
municipio_counts.columns = ['Municipio', 'Quantidade']

# Mostrar estatísticas
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Municípios com processos", len(municipio_counts))
with col2:
    if not municipio_counts.empty:
        total_processos = municipio_counts['Quantidade'].sum()
        st.metric("Total de processos", f"{total_processos:,}".replace(",", "."))
    else:
        st.metric("Total de processos", "0")
with col3:
    if not municipio_counts.empty and len(municipio_counts) > 0:
        st.metric("Média por município", f"{municipio_counts['Quantidade'].mean():,.0f}".replace(",", "."))
    else:
        st.metric("Média por município", "0")

if not municipio_counts.empty:
    # Preparar dados para o mapa
    map_data = []
    for municipio in municipio_counts['Municipio']:
        if municipio in coordenadas_municipios:
            quantidade = municipio_counts[municipio_counts['Municipio'] == municipio]['Quantidade'].values[0]
            map_data.append({
                'Municipio': municipio,
                'lat': coordenadas_municipios[municipio]['lat'],
                'lon': coordenadas_municipios[municipio]['lon'],
                'Quantidade': quantidade
            })
    
    if map_data:
        map_df = pd.DataFrame(map_data)
        
        # ===== NOVO CÓDIGO PARA DEBUG E AJUSTE DAS CORES =====
        st.subheader("📊 Diagnóstico das Cores")
        
        # Mostrar estatísticas dos valores
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Mínimo", f"{map_df['Quantidade'].min():,}".replace(",", "."))
        with col2:
            st.metric("Máximo", f"{map_df['Quantidade'].max():,}".replace(",", "."))
        with col3:
            st.metric("Média", f"{map_df['Quantidade'].mean():,.0f}".replace(",", "."))
        with col4:
            st.metric("Mediana", f"{map_df['Quantidade'].median():,.0f}".replace(",", "."))
        
        # Mostrar distribuição dos valores
        st.write("**Distribuição dos valores:**")
        st.dataframe(map_df[['Municipio', 'Quantidade']].sort_values('Quantidade', ascending=False).head(10))
        
        # ===== FIM DO CÓDIGO DE DEBUG =====
        
        # Calcular tamanho dos marcadores (proporcional à quantidade)
        min_size = 20
        max_size = 80
        if len(map_df) > 1:
            map_df['size'] = min_size + (map_df['Quantidade'] - map_df['Quantidade'].min()) / (map_df['Quantidade'].max() - map_df['Quantidade'].min()) * (max_size - min_size)
        else:
            map_df['size'] = max_size
        
        # Calcular tamanho dos marcadores (proporcional à quantidade)
        min_size = 20
        max_size = 80
        if len(map_df) > 1:
            map_df['size'] = min_size + (map_df['Quantidade'] - map_df['Quantidade'].min()) / (map_df['Quantidade'].max() - map_df['Quantidade'].min()) * (max_size - min_size)
        else:
            map_df['size'] = max_size
        
        # Criar figura
        fig_mapa = go.Figure()
        
                
               # Adicionar marcadores com borda preta e preenchimento colorido proporcional
        fig_mapa.add_trace(go.Scattergeo(
            lon=map_df['lon'],
            lat=map_df['lat'],
            mode='markers+text',
            marker=dict(
                size=map_df['size'],
                color=map_df['Quantidade'],
                colorscale='Blues',
                showscale=True,
                colorbar=dict(
                    title="Quantidade de Processos",  # REMOVIDO o <br> e titleside
                    thickness=15,
                    len=0.5,
                    x=0.95,
                    y=0.5,
                    tickformat=',.0f'
                    # REMOVIDO: titleside='right'
                ),
                line=dict(width=2, color='black'),
                opacity=0.9,
                symbol='circle',
                # Usar escala logarítmica se houver grande variação
                cmax=np.log10(map_df['Quantidade'].max()) if map_df['Quantidade'].max() > 0 else 1,
                cmin=np.log10(map_df['Quantidade'].min()) if map_df['Quantidade'].min() > 0 else 0
                # REMOVIDO: coloraxis=None
            ),
            text=map_df['Municipio'],
            textposition="top center",
            textfont=dict(size=10, color='black', family='Arial'),
            hovertext=map_df.apply(lambda row: f"<b>{row['Municipio']}</b><br>Processos: {row['Quantidade']:,}".replace(",", "."), axis=1),
            hoverinfo='text',
            name=''
        ))

                # Configurar layout - VISÃO PANORÂMICA E ESTÁTICA
        fig_mapa.update_layout(
            title={
                'text': 'Distribuição de Processos por Município - Amazonas',
                'y': 0.98,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(size=16)
            },
            geo=dict(
                scope='south america',
                projection_type='mercator',
                showland=True,
                landcolor='white',
                coastlinecolor='lightgray',
                coastlinewidth=0.5,
                showcountries=True,
                countrycolor='lightgray',
                countrywidth=0.5,
                showsubunits=True,
                subunitcolor='lightgray',
                subunitwidth=0.5,
                showframe=True,
                framecolor='black',
                framewidth=1,
                bgcolor='white',
                # VISÃO PANORÂMICA - limites máximos do Amazonas
                lonaxis_range=[-74, -56],  # Oeste a Leste
                lataxis_range=[-10, 2.5],  # Sul a Norte
                center=dict(lon=-65, lat=-4),  # Centro ajustado para visão completa
                projection_scale=0.8,  # Zoom reduzido para visão panorâmica
                # TORNAR ESTÁTICO - desabilitar interações de zoom e pan
                fitbounds=False,
                visible=False
            ),
            height=650,
            margin=dict(l=0, r=0, t=50, b=0),
            paper_bgcolor='white',
            plot_bgcolor='white',
            showlegend=False,
            # DESABILITAR TODAS AS INTERAÇÕES
            dragmode=False,
            hovermode='closest',
            # Remover botões de zoom/pan
            modebar=dict(
                bgcolor='rgba(0,0,0,0)',
                color='rgba(0,0,0,0)',
                activecolor='rgba(0,0,0,0)',
                orientation='v'
            ),
            # Configurações para tornar estático
            uirevision='static'
        )
        
        # Plotar com configurações estáticas
        st.plotly_chart(
            fig_mapa, 
            use_container_width=True, 
            config={
                'scrollZoom': False,           # Desabilita zoom com scroll
                'displayModeBar': False,       # Remove a barra de ferramentas
                'staticPlot': True,             # Torna o plot completamente estático
                'doubleClick': False,           # Desabilita double click
                'showTips': False,               # Desabilita dicas
                'displaylogo': False             # Remove logo Plotly
            }
        )        
        
        # Mostrar legenda adicional com os valores mínimo e máximo
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"🔵 **Mais processos:** {map_df.loc[map_df['Quantidade'].idxmax(), 'Municipio']} ({map_df['Quantidade'].max():,} processos)".replace(",", "."))
        with col2:
            st.info(f"⚪ **Menos processos:** {map_df.loc[map_df['Quantidade'].idxmin(), 'Municipio']} ({map_df['Quantidade'].min():,} processos)".replace(",", "."))
        
        # Mostrar tabela com os dados dos municípios
        with st.expander("📋 Ver dados detalhados por município"):
            # Ordenar por quantidade (decrescente)
            municipios_ordenados = map_df.sort_values('Quantidade', ascending=False).reset_index(drop=True)
            municipios_ordenados['Quantidade'] = municipios_ordenados['Quantidade'].apply(lambda x: f"{x:,}".replace(",", "."))
            st.dataframe(
                municipios_ordenados[['Municipio', 'Quantidade']],
                use_container_width=True,
                height=400
            )
    else:
        st.warning("Nenhum município com coordenadas encontrado nos dados filtrados.")
else:
    st.warning("Não há dados de municípios para os filtros selecionados.")


# Notas
st.markdown("---")
st.caption("""
**Notas:**
- Os dados foram filtrados para remover anos inválidos (<1900 ou >2100)
- Processos sem número foram removidos da análise
- As análises são atualizadas dinamicamente com base nos filtros selecionados
- Valores numéricos formatados com separador de milhar (.)
- TOP 10 Assuntos: Maior quantidade no TOPO com gradiente de cores AZUL (mais forte no topo)
""")