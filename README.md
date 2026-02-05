# Comparador de Planos - GTFS

Este comparador tem como objetivo identificar alterações/diferenças entre a oferta a operação através de ficheiros GTFS, gerando alertas.


## Visão Geral do Comparador
- Este programa analisa o GTFS (General Transit Feed Specification) de oferta e o GTFS de operação e exporta os resultados desta análise para um ficheiro Excel, auxiliando assim a validação da oferta planeada com a aquela que será a operação.
- O script principal é o `run_analysis.py`, que coordena a configuração, o carregamento dos dados, a análise, os alertas e a exportação.
- Toda a lógica central é modularizada no módulo `analysis/`, com cada ficheiro a tratar uma tarefa específica de comparação ou exportação.


## Componentes principais
- **Configuração**: Configuração interativa, apenas para a sessão, através de `config/cli.py` (`configurar()`), com acesso global gerido por `config/runtime.py` (`init_config`, `get`).
- **Módulos de análise**: cada ficheiro em `analysis/` (por exemplo, `compare_routes.py`, `compare_extension.py`, `summaries.py`) implementa uma única responsabilidade, retornando DataFrames e atualizando um DataFrame de alertas partilhado.
- **Alerta**: Todas as inconsistências e erros são registados num DataFrame central usando auxiliares de `analysis/alerts.py`.
- **Exportações**: Os resultados são gravados no Excel usando `analysis/exports.py`, com várias folhas e ficheiros extras opcionais para sequências de paragem e resumos de circulação


## Fluxo de trabalho do programador
- **Configuração**: Crie um ambiente virtual e instale as dependências do `requirements.txt` (pandas, numpy, openpyxl).
- **Execução**: Execute `python run_analysis.py` e siga as instruções da CLI para configuração. 
- **Resultados**: Os principais resultados são guardados em ficheiros Excel na pasta de destino especificada pelo utilizador.

## Convenções do projeto
- **Nomenclatura em português**: A maior parte do código, comentários e instruções da CLI estão em português. Os nomes das variáveis e funções são descritivas e específicas do domínio.
- **DataFrames**: Todo o processamento de dados é baseado em pandas. Cada etapa da análise devolve ou atualiza DataFrames.
- **Sem caminhos codificados**: Todos os caminhos e nomes de ficheiros são fornecidos interativamente em tempo de execução.
- **Responsabilidade única**: Cada módulo em `analysis/` deve lidar apenas com um aspeto da comparação ou exportação.
- **Gravidade do alerta**: os alertas são classificados por gravidade (por exemplo, «MUITO GRAVE») e incluem sempre o contexto do plano.


## Exemplos
- Para adicionar uma nova comparação, crie um novo módulo em `analysis/`, certifique-se de que ele devolve DataFrames e atualize `run_analysis.py` para integrá-lo.
- To add a new export, extend `analysis/exports.py` and call it conditionally in `run_analysis.py`.

## Ficheiros principais
- `run_analysis.py`: Ponto de entrada principal e gestor do fluxo de trabalho.
- `config/cli.py`, `config/runtime.py`: Configuração interativa e estado global.
- `analysis/`: Toda a lógica de comparação, alerta e exportação

## Integração externan
- Não são utilizadas APIs externas ou bases de dados persistentes. Todos os dados são locais e fornecidos pelo utilizador em tempo de execução.

