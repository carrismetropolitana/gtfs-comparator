import pandas as pd
import numpy as np

# #============================================================
# # Output extra - Sequência de Paragens
# #============================================================
# def export_stop_sequence(df_seq, stops_df, output_path, sheet_name):
#     """
#     Exporta uma cópia de df_seq para Excel adicionando a coluna stop_name.
#     """
#     df_export = df_seq.copy()

#     df_export = df_export.merge(
#         stops_df[['stop_id', 'stop_name']],
#         on='stop_id',
#         how='left'
#     )

#     with pd.ExcelWriter(output_path, engine='openpyxl', mode='a') as writer:
#         df_export.to_excel(writer, sheet_name=sheet_name, index=False)


# #============================================================
# # Output extra - Total de Circulações e Veículos KM
# #============================================================

# def export_total_circulacoes_vkm(df, output_excel_path, sheet_name="Total circulações e VKM"):
#     """
#     Exporta um DataFrame para um ficheiro Excel novo, com o nome do sheet definido.
#     """
#     with pd.ExcelWriter(output_excel_path, engine="openpyxl") as writer:
#         df.to_excel(writer, sheet_name=sheet_name, index=False)

#============================================================
# Output extra - Sequência de Paragens
#============================================================
def export_stop_sequence(df_seq, stops_df, output_path, sheet_name="Sequência Paragens"):
    """
    Exporta uma cópia de df_seq para Excel adicionando a coluna stop_name.
    """
    df_export = df_seq.copy()
    df_export = df_export.merge(
        stops_df[['stop_id', 'stop_name']],
        on='stop_id',
        how='left'
    )

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df_export.to_excel(writer, sheet_name=sheet_name, index=False)


#============================================================
# Output extra - Total de Circulações e Veículos KM
#============================================================
def export_total_circulacoes_vkm(df, output_excel_path, sheet_name="Total circulações e VKM"):
    """
    Exporta um DataFrame para um ficheiro Excel novo, com o nome do sheet definido.
    """
    with pd.ExcelWriter(output_excel_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)


def save_to_excel(
    excel_file_path: str,
    alerts_df: pd.DataFrame,
    grand_total_df: pd.DataFrame,
    analysis_period_df: pd.DataFrame,
    merged_all: pd.DataFrame,
    compare_calendars: pd.DataFrame = None,
    stops_comparison_result: pd.DataFrame = None,
    extension_comparison_result: pd.DataFrame = None,
    merged_routes: pd.DataFrame = None,
    stop_sequence_oferta: pd.DataFrame = None,
    stop_sequence_operacao: pd.DataFrame = None,
    resumo_oferta_final: pd.DataFrame = None,
    resumo_operacao_final: pd.DataFrame = None,
    pivot_dates_oferta: pd.DataFrame = None,
    pivot_dates_operacao: pd.DataFrame = None,
    circulacoes_por_hora: pd.DataFrame = None
):
    """
    Salva todos os resultados em diferentes sheets de um ficheiro Excel.
    Verifica se cada DataFrame existe e não está vazio antes de escrever.
    """
    with pd.ExcelWriter(excel_file_path, engine='openpyxl') as writer:

        def safe_to_excel(df, sheet_name):
            if df is not None and not df.empty:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
            else:
                pd.DataFrame(
                    {"Aviso": [f"Nenhum dado disponível para {sheet_name}"]}
                ).to_excel(writer, sheet_name=sheet_name, index=False)

        # ==================================================
        # ALERTAS
        # ==================================================
        safe_to_excel(alerts_df, 'ALERTAS')

        # ==================================================
        # RESUMO
        # ==================================================
        if grand_total_df is not None and analysis_period_df is not None:
            grand_total_df.to_excel(
                writer, sheet_name='RESUMO', index=False, startrow=0
            )
            analysis_period_df.to_excel(
                writer,
                sheet_name='RESUMO',
                index=False,
                startrow=len(grand_total_df) + 2
            )
        else:
            safe_to_excel(grand_total_df, 'RESUMO')

        # ==================================================
        # Comparação circulações e VKM  (renomeado)
        # ==================================================
        safe_to_excel(merged_all, 'Comparação circulações e VKM')

        # ==================================================
        # Comparações
        # ==================================================
        safe_to_excel(compare_calendars, 'Comparação calendarios')
        safe_to_excel(stops_comparison_result, 'Comparação paragens')
        safe_to_excel(extension_comparison_result, 'Comparação extensões')
        safe_to_excel(merged_routes, 'Comparação rotas')

        # ==================================================
        # Circulações por hora  👈 NOVO
        # ==================================================
        safe_to_excel(circulacoes_por_hora, 'Circulações por hora')

        # ==================================================
        # Sequências de paragens
        # ==================================================
        safe_to_excel(stop_sequence_oferta, 'Sequencia paragens POferta')
        safe_to_excel(stop_sequence_operacao, 'Sequencia paragens POperação')

        # ==================================================
        # Resumos planos
        # ==================================================
        safe_to_excel(resumo_oferta_final, 'Resumo Plano Oferta')
        safe_to_excel(resumo_operacao_final, 'Resumo Plano Operação')

        # ==================================================
        # Circulações por data
        # ==================================================
        safe_to_excel(pivot_dates_oferta, 'Circulações por Data POferta')
        safe_to_excel(pivot_dates_operacao, 'Circulações por Data POperação')

    print(f"Resultados guardados em {excel_file_path}")
