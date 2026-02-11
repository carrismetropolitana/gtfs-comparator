"""
Este módulo valida e compara o número total de circulações anuais entre o Plano de Oferta e o Plano de Operação.

Funcionalidades principais:
- Recebe uma tabela consolidada de métricas globais por percurso, período do ano e dia tipo (resultado do processo de summaries).
- Normaliza e valida os campos numéricos correspondentes ao número total de circulações anuais nos dois planos (Oferta e Operação).
- Calcula a diferença absoluta de circulações entre o Plano de Oferta e o Plano de Operação.
- Identifica discrepâncias entre os planos, considerando qualquer diferença diferente de zero como inconsistente do ponto de vista contratual.
- Gera alertas automáticos quando o número total de circulações na Operação difere do previsto na Oferta, classificando as ocorrências como MUITO GRAVE.
- Inclui contexto detalhado nos alertas (Percurso, Período do Ano e Dia Tipo).

Outputs:
- Atualização da tabela consolidada com uma coluna adicional de diferença de circulações (dif_circ).
- Atualização da tabela de alertas com todas as discrepâncias detetadas entre Oferta e Operação, incluindo contexto detalhado por percurso, período e dia tipo.

"""

import pandas as pd
from analysis.alerts import add_alert

# ========================================================================================================================================================
# 1️⃣ Compara total de circulações entre planos 
# ========================================================================================================================================================

def compare_total_circulations(merged_all, alerts_df):
  
    merged_all["Num total circulações ano_POferta"] = pd.to_numeric(
        merged_all["Num total circulações ano_POferta"], errors="coerce"
    )
    merged_all["Num total circulações ano_POperação"] = pd.to_numeric(
        merged_all["Num total circulações ano_POperação"], errors="coerce"
    )

    merged_all["dif_circ"] = (
        merged_all["Num total circulações ano_POperação"]
        - merged_all["Num total circulações ano_POferta"]
    )

    # -------------------------------------------------------------------------------------------
    # Gera alertas para todas as linhas onde a diferença de circulações é diferente de zero
    # -------------------------------------------------------------------------------------------

    for _, row in merged_all[merged_all["dif_circ"] != 0].iterrows():
        contexto = f"{row['Percurso']} | Periodo {row['Periodo do ano']} | Dia tipo {row['Dia tipo']}"

        alerts_df = add_alert(
            alerts_df,
            "PLANO DE OPERAÇÃO",
            "Número total de circulações",
            "MUITO GRAVE",
            "Número total de circulações diferente do Plano de Oferta nos percursos:",
            contexto
        )

    return merged_all, alerts_df
