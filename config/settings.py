"""
Este módulo define as constantes de configuração usadas na análise GTFS.

Funcionalidades principais:
- Define o caminho base onde estão armazenados os ficheiros GTFS a analisar.
- Especifica os nomes dos ficheiros GTFS para os planos de Oferta e Operação.
- Define o período de análise (data de início e data de fim) no formato YYYYMMDD.
- Define o nome base do ficheiro de resultados gerado pelo processo de análise.
- Configura nomes padrão para ficheiros de exportação adicionais:
  - Sequência de paragens
  - Total de circulações e VKM

Outputs:
- Conjunto de constantes reutilizáveis que orientam o carregamento dos dados e a geração dos ficheiros de saída.
"""

from pathlib import Path 

# ========================================================================================================================================================
# 2️⃣ Caminho para os ficheiros GTFS
# ========================================================================================================================================================

TARGET_FOLDER = Path(r'C:\Users\InêsClemente\Downloads\A4_Dezembro_2025')

# ========================================================================================================================================================
# 2️⃣ Nome dos ficheiros GTFS
# ========================================================================================================================================================

GTFS_OFFERPLAN_NAME = 'GTFS_44_REF_v29_202512181606'
GTFS_OPERATIONPLAN_NAME = '20251218_44_YEAR_04_27'

# ========================================================================================================================================================
# 2️⃣ Perído a analisar
# ========================================================================================================================================================

START_DATE = '20251220'
END_DATE = '20260115'

# ========================================================================================================================================================
# 2️⃣ Nome do ficheiro
# ========================================================================================================================================================

RESULT_NAME = 'A4_analise_plano_mensal_janeiro_2026_teste'

# ========================================================================================================================================================
# 2️⃣ Outputs extra
# ========================================================================================================================================================

# -------------------------------------------------------------------------------------------
# 📌 Nome do ficheiro de exportação da sequência de paragens
# -------------------------------------------------------------------------------------------

EXPORT_STOP_SEQUENCE_FILENAME = "Paragens_Sequência_A4"

# -------------------------------------------------------------------------------------------
# 📌 Nome do ficheiro de exportação do Total de Circulações e VKM
# -------------------------------------------------------------------------------------------
 
EXPORT_TOTAL_CIRCULATIONS_VKM_FILENAME = "Total de Circulações e VKM"