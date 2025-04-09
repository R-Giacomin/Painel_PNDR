import streamlit as st
import duckdb
from openai import OpenAI
import google.genai as genai
from google.genai import types
import openai  # Ou use google.generativeai para Gemini
import pandas as pd
import plotly.express as px
import folium
import altair as alt
from streamlit_folium import folium_static
import requests
import json
import os
from dotenv import load_dotenv

#######################
# Carregar credenciais
# Load the environment variables
load_dotenv()

# Access the environment variable
openai.api_key = os.environ.get('OPENAI_API_KEY')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
# Configuração do cliente Gemini
client = genai.Client(api_key=GEMINI_API_KEY)

#######################
# Page configuration
st.set_page_config(
    page_title="Consulta Indicadores PNDR",
    page_icon="PNDR.png",
    layout="wide",
    initial_sidebar_state="expanded")

alt.themes.enable("default")

#######################
# Carregar dados do IBGE
@st.cache_data
def get_br_municipio():
    url = "https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR?formato=application/vnd.geo+json&qualidade=maxima&intrarregiao=municipio"
    return requests.get(url).json()

# Uso da função
geojson_data = get_br_municipio()

#######################
# Funções auxiliares

def query_llm(question):
    """Chama a LLM para interpretar a pergunta e gerar SQL."""
    
    schema_info = """
    Tabelas e suas colunas:

    recortes_geograficos(codigo_ibge BIGINT, município VARCHAR, estado VARCHAR, região VARCHAR, faixa_de_fronteira INTEGER, participacao_semiarido VARCHAR, regiao_intermediaria VARCHAR, tipologia VARCHAR, participacao_sudene VARCHAR, regiao_imediata VARCHAR, participacao_amazonia_legal VARCHAR, longitude DOUBLE, latitude DOUBLE, geometry VARCHAR)
    valoresmeta(mdata_id BIGINT, geoloc_id BIGINT, local_id BIGINT, refdate TIMESTAMP, value DOUBLE, orig_name VARCHAR, data_name VARCHAR, local_name VARCHAR) 

    Relações entre as tabelas (Chaves Estrangeiras):

    recortes_geograficos.codigo_ibge -> valoresmeta.geoloc_id
    """

    prompt = f"""
    Você é um assistente SQL especializado em consultas para DuckDB. 
    Seu objetivo é gerar queries SQL corretas para responder perguntas sobre indicadores municipais.

    📌 **Schema do DuckDB:**
    {schema_info}

    📌 **Regras para gerar SQL:**
    - **Retorne uma query SQL válida para DuckDB.**
    - Utilize apenas tabelas e colunas existentes, de preferência as tabelas recortes_geograficos e valoresmeta.
    - A tabela recortes_geograficos contém informações sobre municípios e seus recortes territoriais, como semiárido, Região Intermediária, Tipologia da PNDR, Sudene, Região Imediata, Amazônia Legal, Estados/UF ou Região.
    - A tabela valoresmeta contém informações sobre os indicadores, incluindo o valor (value) e a data de referência (refdate).
    - Utilize sempre LEFT JOIN entre as tabelas recortes_geograficos e valoresmeta, unindo-as pela coluna `codigo_ibge` e `geoloc_id` respectivamente.
    - Ao filtrar por algum recorte geográfico ou indicador, utilize sempre a busca aproximada (LIKE) para garantir que o usuário receba resultados relevantes, a não ser que o usuário peça pelo termo exato.
    - Se o usuário solicitar por um município específico, retorne os dados desse município.
    - Se o usuário solicitar por um recorte geográfico ou administrativo, retorne a lista de municípios deste recorte.
    - Se o usuário solicitar por um indicador e não especificar o recorte geográfico, retorne os valores do indicador para todos os municípios.
    - Se o usuário não solicitar uma data específica, retorne os dados mais recentes disponíveis.
    - Se o usuário solicitar uma data específica, retorne os dados apenas para o ano dessa data.
    - Se o usuário solicitar por um município, procure na coluna `município` da tabela recortes_geograficos.
    - Os Estado estão descrito pelo nome por extenso na coluna `estado`.
    - Os municípios estão descritos pelo nome por extenso na coluna `municipio`.

    📌 **Exemplos de queries válidas:**
    🔹 **Retornar a lista de todos os municípios com código IBGE e todos os recortes geográficos e administrativos**
    SELECT * FROM recortes_geograficos

    🔹 **Retornar a lista dos municípios com o indicador Diferencial Salarial Médio Feminino para 2021**
    SELECT
        r.codigo_ibge,
        r.município,
        r.estado,
        v.value,
        strftime('%Y', v.refdate) AS ano,
        v.data_name,
    FROM
        valoresmeta AS v
    LEFT JOIN
        recortes_geograficos AS r ON r.codigo_ibge = v.geoloc_id
    WHERE
        v.data_name LIKE '%Diferencial Salarial Médio Feminino%'
        AND strftime('%Y', v.refdate) = '2021';

        🔹 **Retornar a lista dos municípios com o indicador de Desmatamento da região imediata de Toledo para 2020**
    SELECT
        r.codigo_ibge,
        r.município,
        r.estado,
        r.regiao_imediata,
        v.value,
        strftime('%Y', v.refdate) AS ano,
        v.data_name,
    FROM
        valoresmeta AS v
    LEFT JOIN
        recortes_geograficos AS r ON r.codigo_ibge = v.geoloc_id
    WHERE
        r.regiao_imediata LIKE '%Toledo%'
        AND v.data_name LIKE '%Desmatamento%'
        AND strftime('%Y', v.refdate) = '2020';

        🔹 **Retornar a lista dos municípios com o indicador de Desmatamento da região imediata de Toledo**
    SELECT
    r.codigo_ibge,
    r.município,
    r.estado,
    r.regiao_imediata,
    v.value,
    strftime('%Y', v.refdate) AS ano,
    v.data_name
FROM
    valoresmeta AS v
LEFT JOIN
    recortes_geograficos AS r ON r.codigo_ibge = v.geoloc_id
WHERE
    r.regiao_imediata LIKE '%Toledo%'
    AND v.data_name LIKE '%Desmatamento%'
    AND v.refdate = (
        SELECT
            MAX(refdate)
        FROM
            valoresmeta
        WHERE
            geoloc_id = v.geoloc_id
            AND data_name = v.data_name
    );

        🔹 **crie uma lista do indicador Taxa de Variação Populacional para o estado de sergipe**
    SELECT
    r.codigo_ibge,
    r.município,
    r.estado,
    v.value,
    strftime('%Y', v.refdate) AS ano,
    v.data_name
FROM
    valoresmeta AS v
LEFT JOIN
    recortes_geograficos AS r ON r.codigo_ibge = v.geoloc_id
WHERE
    r.estado LIKE '%Sergipe%'
    AND v.data_name LIKE '%Taxa de Variação Populacional%'
    AND v.refdate = (
        SELECT
            MAX(refdate)
        FROM
            valoresmeta
        WHERE
            geoloc_id = v.geoloc_id
            AND data_name = v.data_name
    );
        
        🔹 **Criar um mapa do Paraná com o indicador de Sustentabilidade Fiscal dos Municípios para 2019**
    SELECT
        r.codigo_ibge,
        r.município,
        r.estado,
        v.value,
        strftime('%Y', v.refdate) AS ano,
        v.data_name,
        r.latitude,
        r.longitude
    FROM
        valoresmeta AS v
    LEFT JOIN
        recortes_geograficos AS r ON r.codigo_ibge = v.geoloc_id
    WHERE
        r.estado LIKE '%Paraná%'
        AND v.data_name LIKE '%Sustentabilidade Fiscal dos Municípios%'
        AND strftime('%Y', v.refdate) = '2019';
    
    📌 **Agora gere uma query SQL para responder a seguinte pergunta do usuário:**
    Pergunta: {question}
    **Retorne apenas a query SQL sem aspas, sem nenhum comentário ou explicação.**
    """
    
    client = OpenAI()
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": prompt}]
    )
    return completion.choices[0].message.content.strip()

def fetch_data(sql):
    """Executa a query no banco de dados DuckDB."""
    conn = duckdb.connect("data/dados_reduzido.db")
    # Instalar e carregar a extensão espacial
    df = conn.execute(sql).fetchdf()
    conn.close()
    return df

def analyze_data(df):
    """Envia os dados para a LLM para análise e insights."""
    json_data = df.to_json(orient='records')
    response = client.models.generate_content(
    model="gemini-2.0-flash",
    config=types.GenerateContentConfig(
        system_instruction="""Você é um especialista em desenvolvimento regional no Brasil, analise os seguintes dados e forneça insights relevantes sobre o aspecto do desenvolvimento regional que eles representam.
    Considere a importância dos dados, possíveis tendências, correlações e implicações para políticas públicas.
    Na sua análise considere o disposto no Relatório de Monitoramento da PNDR de 2023 disponível no link para entender quais são os objetivos de 1 a 4, o que são os indicadores compostos e as fómulas de cálculo dos indicadores: https://www.gov.br/mdr/pt-br/assuntos/desenvolvimento-regional/nucleo-de-inteligencia-regional/acompanhamento-dinamica/RelatorioMonitoramento20232.pdf"""),
    contents=f"Analise os seguintes dados {json_data}"
    )
    return(response.text)

def plot_data(df):
    """Cria gráficos com Plotly."""
    st.write("### Visualização dos Dados")
    fig = px.bar(df, x="município", y="value")  
    st.plotly_chart(fig)

def create_map(df, geojson_data):
    """Cria mapas com Folium se houver coordenadas."""
    if {'latitude', 'longitude'}.issubset(df.columns):
        st.write("### Mapa do Indicador")
        df = df.rename(columns={'codigo_ibge': 'codarea'})
        m = folium.Map(location=[df['latitude'].mean(), df['longitude'].mean()], zoom_start=5)
        folium.Choropleth(
            geo_data=geojson_data, 
            name="Indicador",
            data=df,
            columns=["codarea", "value"],
            legend_name="Indicador",
            key_on="feature.properties.codarea",
            nan_fill_color="white",
            nan_fill_opacity=0.4,
            fill_color="YlGn",
            fill_opacity=0.8,
            line_weight=0.1,
        ).add_to(m)
        # Adiciona um layer control para alternar entre os mapas
        folium.LayerControl().add_to(m)
        folium_static(m)
        
#######################
# Streamlit App

col = st.columns((5, 3), gap='medium')

with col[1]:
    st.header(":heavy_check_mark: Instruções", divider="gray")
    st.markdown("**1.** Os indicadores são calculados **apenas** para o nível :orange-badge[⚠️ municipal].")
    st.markdown("**2.** A maioria dos indicadores têm dados apenas para o período de 2015 a 2022.")
    st.markdown("**3.** Ao realizar uma consulta para um município, procure especificar o nome do estado também, para evitar homônimos.")
    st.markdown("**4.** Se pedir para criar um :violet-badge[:bar_chart: gráfico] ou :green-badge[:world_map: mapa] especifique o **indicador** e o **ano**.")
    st.markdown("**5.** Se o ano não for especificado, a consulta vai retornar dados do último ano disponível.")
    st.markdown("**6.** Se o município não for especificado, a consulta vai retornar dados de todos os municípios do recorte geográfico informado.")
    st.markdown("**7.** Se o recorte geográfico não for especificado, a consulta vai retornar dados de todos os municípios.")
    st.markdown("**8.** Se o indicador não for especificado, a consulta vai retornar dados de todos os indicadores.")
    st.markdown("**9.** Preferencialmente, procure o indicador na tabela abaixo :mag_right: e copie e cole seu nome na consulta.")

    st.write("**A tabela a seguir apresenta os indicadores utilizados na PNDR, divididos em objetivos e eixos. Cada indicador é descrito com seu respectivo nome e descrição.**")
    with st.container(height=300):
        # Tabela em formato Markdown
        tabela_markdown = """
        | Objetivo/Eixo | Descrição do Objetivo/Eixo                                         | Indicador                                                                                                                      |
        |---------------|--------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------|
        | Objetivo 1    | Convergência de renda                                              |  Diferencial entre Salário Médio no Mercado Formal e Mediana Nacional                                                          |
        | Objetivo 1    | Convergência de renda                                              |  Diferencial entre Índice de Desenvolvimento da Educação Básica (Ideb) e Mediana Nacional                                      |
        | Objetivo 1    | Convergência de renda                                              |  Diferencial entre Número de Profissionais de Saúde por Habitante e Mediana Nacional                                           |
        | Objetivo 1    | Convergência de renda                                              | Indicador Composto do Objetivo 1                                                                                               |
        | Objetivo 2    | Cidades Intermediadoras                                            |  Índice de Centralidade                                                                                                        |
        | Objetivo 2    | Cidades Intermediadoras                                            |  Razão de Primazia Populacional Estadual                                                                                       |
        | Objetivo 2    | Cidades Intermediadoras                                            |  Razão de Primazia Econômica Estadual                                                                                          |
        | Objetivo 2    | Cidades Intermediadoras                                            | Indicador Composto do Objetivo 2                                                                                               |
        | Objetivo 3    | Competitividade                                                    |  Percentual de vínculos formais com ensino superior                                                                            |
        | Objetivo 3    | Competitividade                                                    |  Salário Médio no Mercado Formal                                                                                               |
        | Objetivo 3    | Competitividade                                                    |  Taxa de Variação Populacional no Município                                                                                    |
        | Objetivo 3    | Competitividade                                                    | Indicador Composto do Objetivo 3                                                                                               |
        | Objetivo 4    | Diversificação                                                     |  Índice de Especialização do Emprego em Atividades Agrícolas                                                                   |
        | Objetivo 4    | Diversificação                                                     |  Índice de Especialização do Emprego em Mineração                                                                              |
        | Objetivo 4    | Diversificação                                                     |  Coeficiente de Diversificação Econômica                                                                                       |
        | Objetivo 4    | Diversificação                                                     | Indicador Composto do Objetivo 4                                                                                               |
        | Eixo 1        | Educação e capacitação professional                                |  Percentual de escolas com acesso a esgotamento sanitário                                                                      |
        | Eixo 1        | Educação e capacitação professional                                |  Percentual de escolas com acesso à internet                                                                                   |
        | Eixo 1        | Educação e capacitação professional                                |  Índice de matrículas em Educação Profissional e Tecnológica                                                                   |
        | Eixo 1        | Educação e capacitação professional                                |  Índice de Desenvolvimento da Educação Básica (Ideb)                                                                           |
        | Eixo 1        | Educação e capacitação professional                                |  Índice Composto de Educação e Capacitação Professional                                                                        |
        | Eixo 2        | Ciência, tecnologia e inovação                                     |  Número de micro e pequenas empresas relacionadas ao setor de biotecnologia e saúde humana por milhão de habitantes            |
        | Eixo 2        | Ciência, tecnologia e inovação                                     |  Número de empregos relacionados ao desenvolvimento científico e tecnológico por milhão de habitantes                          |
        | Eixo 2        | Ciência, tecnologia e inovação                                     |  Número de empregos em estabelecimentos relacionadas ao desenvolvimento científico e tecnológico por milhão de habitantes      |
        | Eixo 2        | Ciência, tecnologia e inovação                                     |  Número de depósitos de patentes por 100 mil habitantes                                                                        |
        | Eixo 2        | Ciência, tecnologia e inovação                                     |  Índice Composto de Ciência, Tecnologia e Inovação                                                                             |
        | Eixo 3        | Desenvolvimento produtivo                                          |  Índice de Complexidade Econômica                                                                                              |
        | Eixo 3        | Desenvolvimento produtivo                                          |  Participação do setor industrial no emprego formal                                                                            |
        | Eixo 3        | Desenvolvimento produtivo                                          |  Salário médio no mercado formal                                                                                               |
        | Eixo 3        | Desenvolvimento produtivo                                          |  Escala produtiva                                                                                                              |
        | Eixo 3        | Desenvolvimento produtivo                                          |  Índice Composto de Desenvolvimento Produtivo                                                                                  |
        | Eixo 4        | Infraestrutura                                                     |  Índice de Atendimento Urbano de Água (IN023)                                                                                  |
        | Eixo 4        | Infraestrutura                                                     |  Percentual de Acessos de Internet de Alta Velocidade no Município                                                             |
        | Eixo 4        | Infraestrutura                                                     |  Número de Internações Hospitalares por Doenças Relacionadas ao Saneamento Ambiental Inadequado (DRSAI), por 10 mil habitantes |
        | Eixo 4        | Infraestrutura                                                     |  Despesas nas áreas de habitação e recuperação de áreas degradadas per capita                                                  |
        | Eixo 4        | Infraestrutura                                                     |  Índice Composto de Infraestrutura                                                                                             |
        | Eixo 5        | Desenvolvimento social e acesso a serviços                         |  Desnutrição                                                                                                                   |
        | Eixo 5        | Desenvolvimento social e acesso a serviços                         |  Percentual de Famílias de Baixa Renda no Cadastro Único                                                                       |
        | Eixo 5        | Desenvolvimento social e acesso a serviços                         |  Distorção Idade-Série                                                                                                         |
        | Eixo 5        | Desenvolvimento social e acesso a serviços                         |  Diferencial Salarial Médio Feminino no Mercado de Trabalho Formal                                                             |
        | Eixo 5        | Desenvolvimento social e acesso a serviços                         |  Índice Composto de Desenvolvimento Social e Acesso a Serviços                                                                 |
        | Eixo 6        | Sustentabilidade                                                   |  Número de Empregos em Estabelecimentos Relacionados a Reciclagem e Gestão de Resíduos                                         |
        | Eixo 6        | Sustentabilidade                                                   |  Percentual de Área Desmatada no Município                                                                                     |
        | Eixo 6        | Sustentabilidade                                                   |  Taxa de Desmatamento (km2/ano)                                                                                                |
        | Eixo 6        | Sustentabilidade                                                   |  Emissões Líquidas de Gases de Efeito Estufa (CO2 Equivalente) da Agropecuária e Processos Industriais.                        |
        | Eixo 6        | Sustentabilidade                                                   |  Índice Composto de Sustentabilidade                                                                                           |
        | Eixo 7        | Fortalecimento das capacidades governativas dos entes subnacionais |  Percentual de dirigentes municipais com ensino superior completo na administração pública.                                    |
        | Eixo 7        | Fortalecimento das capacidades governativas dos entes subnacionais |  Percentual de servidores municipais com ensino superior completo na administração pública                                     |
        | Eixo 7        | Fortalecimento das capacidades governativas dos entes subnacionais |  Salário médio municipal de servidores da administração pública                                                                |
        | Eixo 7        | Fortalecimento das capacidades governativas dos entes subnacionais |  Índice de Sustentabilidade Fiscal dos Municípios                                                                              |
        | Eixo 7        | Fortalecimento das capacidades governativas dos entes subnacionais |  Índice Composto de Fortalecimento das Capacidades Governativas dos Entes Subnacionais                                         |
        """
        # Exibir a tabela no Streamlit
        st.markdown(tabela_markdown, unsafe_allow_html=True)

    st.markdown("**Os recortes geográficos e administrativos disponíveis para consulta são os seguintes:**")
    st.markdown("**1.** Municípios")
    st.markdown("**2.** Estados/UF")
    st.markdown("**3.** Região")
    st.markdown("**4.** Região Imediata")
    st.markdown("**5.** Região Intermediária")
    st.markdown("**6.** Faixa de Fronteira")
    st.markdown("**7.** Participação no Semiárido")
    st.markdown("**8.** Participação na Amazônia Legal")
    st.markdown("**9.** Participação na Sudene")
    st.markdown("**10.** Tipologia da PNDR")


with col[0]:
    with st.container():
        col = st.columns((1, 3), gap='medium')
        with col[0]:
            st.image("PNDR.png", width=300)
        with col[1]:
            st.title(":blue[SISTEMA NACIONAL DE INFORMAÇÃO DO DESENVOLVIMENTO REGIONAL (SNIDR)]")

    st.write("A Política Nacional de Desenvolvimento Regional (PNDR) é uma política pública que visa promover o desenvolvimento regional no Brasil, com foco na redução das desigualdades sociais e econômicas entre os municípios.")
    st.write("O painel de indicadores da PNDR é uma ferramenta que permite visualizar e analisar os indicadores relacionados a essa política, facilitando a tomada de decisões e o acompanhamento dos resultados.")
    url = "https://www.gov.br/mdr/pt-br/assuntos/desenvolvimento-regional/politica-nacional-de-desenvolvimento-regional"
    st.write("Saiba mais em [PNDR](%s)" % url)
    st.header("Exemplos de consultas", divider="gray")
    st.markdown("**1.** Qual o indicador de Sustentabilidade Fiscal dos municípios da Bahia para 2022?")
    st.markdown("**2.** Crie um gráfico do indicador de Desmatamento paro o Pará em 2021")
    st.markdown("**3.** Como está o indicador de Desnutrição no Maranhão?")
    st.markdown("**4.** Crie um mapa do indicador Salário Médio no Mercado Formal para o Paraná em 2020")
    st.markdown("**5.** Como está o Indicador Coeficiente de Diversificação Econômica na região imediata de Toledo?")
    st.markdown("**6.** Quais os dados do Índice de Centralidade para o Mato Grosso em 2021, considere o temo exato 'Mato Grosso'? :gray-badge[pedir pelo termo exato para evitar Mato Grosso do Sul]") 


    def main():
        st.title("🔍 Consulta ao Painel de Indicadores da PNDR")
        user_question = st.text_input("Digite o que você gostaria de consultar no Painel de Indicadores da PNDR:")
        
        if st.button("Consultar") and user_question:
            with st.spinner("Gerando consulta..."):
                sql_query = query_llm(user_question)
                #st.code(sql_query, language='sql')
            
            with st.spinner("Buscando dados..."):
                df = fetch_data(sql_query)
                st.write("### Dados Filtrados")
                st.dataframe(df)
            
            with st.spinner("Analisando dados..."):
                insights = analyze_data(df)
                st.write("### Insights gerados por IA")
                st.write(insights)
            
            plot_data(df)
            #create_map(df)
            create_map(df, geojson_data)

    if __name__ == "__main__":
        main()
