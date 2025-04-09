# Ferramenta de Consulta ao Painel de Indicadores da PNDR

**Acesso à ferramenta:** [Consulta ao Painel de Indicadores da PNDR](https://painelpndr.streamlit.app/)

**Código Fonte:** [https://github.com/R-Giacomin/Painel_PNDR](https://github.com/R-Giacomin/Painel_PNDR)

## Introdução

A **Política Nacional de Desenvolvimento Regional (PNDR)** tem como finalidade primordial a redução das desigualdades econômicas e sociais entre as diversas regiões brasileiras. Seus resultados esperados incluem o crescimento econômico sustentável, a geração de renda e a melhoria da qualidade de vida da população em todo o território nacional.

Os objetivos da PNDR estão intrinsecamente relacionados ao desenvolvimento econômico e social, considerando as particularidades e necessidades específicas de cada região, o que evidencia a importância crucial desta política para a coesão territorial e o bem-estar da população.

A PNDR serve como base e diretriz para as demais políticas, programas e ações implementadas pelo Ministério do Desenvolvimento Regional (MIDR), dentro do objetivo macro de fornecer instrumentos eficazes para mitigar as disparidades econômicas e sociais existentes nas regiões do Brasil.

O **Sistema Nacional de Informações do Desenvolvimento Regional (SNIDR)** tem o objetivo de assegurar o monitoramento e a avaliação contínua da PNDR, bem como o acompanhamento da dinâmica regional brasileira. Para alcançar esse objetivo, foram definidos indicadores específicos que compõem o Painel de Indicadores da PNDR. Este painel busca consolidar um conjunto abrangente de dados, com um recorte territorial focado no nível municipal, permitindo uma análise da evolução ao longo do tempo e a construção de cenários prospectivos. O intuito principal é tornar mais efetivo o planejamento e a implementação de políticas direcionadas ao desenvolvimento regional.

O Painel de Indicadores foi estruturado de forma a possibilitar a identificação da situação regional atual e sua evolução temporal, dentro de cada um dos eixos orientadores da PNDR, bem como em relação aos seus quatro objetivos principais, conforme estabelecido no Decreto nº 11.962/2024.

A ferramenta de Consulta ao Painel de Indicadores da PNDR foi desenvolvida com o objetivo principal de **facilitar o acesso e a consulta aos indicadores do Painel tanto por cidadãos quanto por administradores públicos**. Através de um simples "prompt" (comando de texto), a ferramenta permite gerar tabelas informativas, gráficos visuais e mapas georreferenciados para recortes territoriais e períodos de tempo específicos, democratizando o acesso à informação e otimizando a análise para a tomada de decisões.

## Metodologia

Os indicadores que alimentam a ferramenta estão armazenados em um Banco de Dados PostgreSQL, hospedado em um servidor na rede interna do ministério. Para viabilizar a disponibilização dos dados na plataforma Streamlit Cloud, foi necessária a criação de uma cópia do banco de dados, uma vez que o acesso ao servidor original é restrito à rede interna do ministério por questões de segurança e infraestrutura. A solução adotada foi a utilização do DuckDB, um banco de dados analítico in-process, que permite o armazenamento e a consulta eficiente dos dados diretamente na aplicação Streamlit.

Com o banco de dados estruturado no DuckDB, a etapa seguinte consistiu no desenvolvimento de uma arquitetura baseada em **Large Language Models (LLM)** para interpretar as perguntas dos usuários e gerar automaticamente as consultas em linguagem SQL correspondentes. Para garantir a precisão e a relevância das consultas geradas, o modelo LLM recebe informações contextuais cruciais, incluindo:

* Orientações e regras específicas para a interpretação das perguntas.
* O _schema_ (estrutura) do banco de dados DuckDB, detalhando as tabelas, colunas e seus tipos.
* Exemplos práticos de consultas e seus respectivos resultados esperados.
* A questão formulada pelo usuário na interface da ferramenta.

Na sequência do processo, um segundo modelo LLM é utilizado para analisar, de forma orientada, a tabela de resultados retornada pela consulta SQL executada no DuckDB. Esta análise pode envolver a sumarização dos dados, a identificação de tendências ou a preparação dos dados para a visualização.

De forma complementar, a ferramenta integra funcionalidades para a geração automática de gráficos de barra, úteis para a comparação de valores entre diferentes categorias ou períodos, e de mapas georreferenciados, que permitem a visualização espacial dos indicadores em diferentes recortes territoriais.

Finalmente, foi desenvolvida a interface do usuário utilizando a biblioteca Streamlit, incluindo orientações claras e concisas para auxiliar os usuários a utilizarem a ferramenta de forma eficiente e a explorarem todo o potencial dos dados disponíveis.

## Funcionamento

Ao acessar a ferramenta, o usuário é direcionado a uma página inicial que apresenta orientações detalhadas sobre o uso da plataforma, uma descrição dos dados disponíveis no Painel de Indicadores da PNDR e exemplos práticos de consultas que podem ser realizadas. Esses exemplos visam inspirar os usuários e demonstrar a versatilidade da ferramenta na extração de informações relevantes.

**Limitações Conhecidas:**

Apesar das orientações fornecidas, a ferramenta ainda pode apresentar erros em algumas situações específicas, principalmente devido a:

* **Homônimos ou grafia incorreta:** Nomes de recortes geográficos (como municípios e estados) ou de indicadores que possuam grafias semelhantes ou erros de digitação por parte do usuário podem levar a consultas mal direcionadas.
* **Consultas complexas:** Ao incluir múltiplos períodos de tempo ou mais de um indicador na mesma consulta, a geração da tabela de resultados pode ocorrer sem problemas, porém, a visualização através de gráficos ou mapas pode apresentar erros ou resultados inesperados devido à complexidade da representação.

É importante que os usuários estejam cientes dessas limitações ao utilizar a ferramenta e revisem cuidadosamente os resultados gerados.

## Resultados e Impacto Esperado

Espera-se que a ferramenta de Consulta ao Painel de Indicadores da PNDR promova significativamente a disseminação do conhecimento sobre a PNDR, seus objetivos e sua importância para o desenvolvimento regional. Ao facilitar o acesso aos dados e a sua visualização de forma intuitiva, a ferramenta deve contribuir para:

* **Maior transparência:** Tornar as informações sobre o desenvolvimento regional mais acessíveis ao público em geral.
* **Melhor monitoramento e avaliação da PNDR:** Fornecer aos gestores públicos e pesquisadores um instrumento ágil e eficiente para acompanhar a evolução dos indicadores e avaliar o impacto das políticas implementadas.
* **Suporte à tomada de decisões:** Oferecer informações relevantes e visualizações claras para auxiliar na formulação e no aprimoramento de políticas públicas voltadas ao desenvolvimento regional.
* **Engajamento da sociedade civil:** Facilitar o acesso à informação para que cidadãos, organizações da sociedade civil e outros atores possam acompanhar e participar do debate sobre o desenvolvimento regional.
* **Otimização do trabalho:** Reduzir o tempo e o esforço necessários para a obtenção e análise de dados sobre a PNDR, permitindo que os profissionais se concentrem em tarefas de maior valor agregado.
