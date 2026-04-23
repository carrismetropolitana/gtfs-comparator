"""
Este módulo gere a exportação dos resultados de análise e validação GTFS para ficheiros Excel.

Funcionalidades principais:
- Exporta a sequência de paragens por pattern_id, incluindo stop_id e stop_name.
- Gera ficheiros Excel auxiliares para outputs específicos, como total de circulações e VKM.
- Consolida todos os resultados de análise num único ficheiro Excel.
- Cria automaticamente sheets distintas para cada tipo de comparação e análise.
- Verifica a existência e o conteúdo de cada DataFrame antes de o exportar.
- Insere mensagens de aviso nos sheets quando não existem dados disponíveis.
- Organiza os resultados por áreas funcionais (alertas, resumos, comparações e análises).
- Guarda comparações entre planos de Oferta e Operação (calendários, paragens, extensões e rotas).
- Inclui análises de circulações por hora e por data.
- Exporta sequências de paragens separadamente para cada plano.
- Estrutura resumos finais independentes para o Plano de Oferta e para o Plano de Operação.

Outputs:
- 1 ficheiro Excel consolidado com múltiplos sheets de análise e validação.
- Sheets específicos para alertas, resumos globais, comparações entre planos e outputs detalhados.
- Ficheiros Excel auxiliares para outputs adicionais (sequência de paragens, circulações e VKM).
"""

import pandas as pd
import numpy as np
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.utils import get_column_letter

# ========================================================================================================================================================
# 1️⃣ Output extra - Sequência de Paragens
# ========================================================================================================================================================

def export_stop_sequence(df_seq, stops_df, output_path, sheet_name="Sequência Paragens"):
    """
    Exporta um ficheiro Excel com uma tabela com a sequencia de paragens (+ stop_id e stop_name) por pattern_id
    """
    df_export = df_seq.copy()
    df_export = df_export.merge(stops_df[['stop_id', 'stop_name']], on='stop_id', how='left')

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df_export.to_excel(writer, sheet_name=sheet_name, index=False)

# ========================================================================================================================================================
# 2️⃣ Output extra - Total de Circulações e Veículos KM
# ========================================================================================================================================================

def export_total_circulacoes_vkm(df, output_excel_path, sheet_name="Total circulações e VKM"):
    """
    Exporta um DataFrame para um ficheiro Excel novo, com o nome do sheet definido.
    """
    with pd.ExcelWriter(output_excel_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)

# ========================================================================================================================================================
# 3️⃣ circulações por hora por semestre
# ========================================================================================================================================================

def save_circulacoes_por_hora_por_trimestre(writer, df: pd.DataFrame):
    """
    Divide o DataFrame de circulações por hora em trimestres
    para garantir que nenhuma folha ultrapassa o limite do Excel.
    """
    if df is None or df.empty:
        return

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    trimestres = {
        "Circulações por hora (T1)": [1, 2, 3],
        "Circulações por hora (T2)": [4, 5, 6],
        "Circulações por hora (T3)": [7, 8, 9],
        "Circulações por hora (T4)": [10, 11, 12],
    }

    for sheet_name, meses in trimestres.items():
        df_trim = df[df["date"].dt.month.isin(meses)].copy()

        if df_trim.empty:
            continue

        # Formata a data para evitar 00:00:00
        df_trim["date"] = df_trim["date"].dt.strftime("%Y-%m-%d")

        df_trim.to_excel(
            writer,
            sheet_name=sheet_name,
            index=False
        )


# ========================================================================================================================================================
# 3️⃣ Comparação de circulações por data entre planos (sheet auxiliar)
# ========================================================================================================================================================

def _add_trips_date_comparison_sheet(writer, pivot_oferta, pivot_operacao):
    """
    Adiciona um sheet ao ficheiro Excel que compara as circulações por data entre os dois planos.
    Células com valores diferentes são destacadas a vermelho com o formato "POferta / POperação".
    Células com valores iguais ficam em branco.
    """
    if pivot_oferta is None or pivot_oferta.empty or pivot_operacao is None or pivot_operacao.empty:
        return

    sheet_name = "Comparação Circulações por Data"
    red_fill = PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")
    white_font = Font(color="FFFFFF", bold=True)
    center_align = Alignment(horizontal="center", vertical="center")

    oferta = pivot_oferta.set_index("pattern_id")
    operacao = pivot_operacao.set_index("pattern_id")

    all_patterns = sorted(set(oferta.index) | set(operacao.index))
    all_dates = sorted(set(oferta.columns) | set(operacao.columns), key=lambda d: pd.to_datetime(d, format="%d/%m/%Y"))

    oferta = oferta.reindex(index=all_patterns, columns=all_dates, fill_value=0)
    operacao = operacao.reindex(index=all_patterns, columns=all_dates, fill_value=0)

    comparison = pd.DataFrame("", index=all_patterns, columns=all_dates)
    diff_mask = pd.DataFrame(False, index=all_patterns, columns=all_dates)

    for col in all_dates:
        val_o = oferta[col]
        val_op = operacao[col]
        mask = val_o != val_op
        comparison.loc[mask, col] = val_o[mask].astype(str) + " / " + val_op[mask].astype(str)
        diff_mask.loc[mask, col] = True

    comparison = comparison.reset_index()
    comparison.to_excel(writer, sheet_name=sheet_name, index=False)

    ws = writer.sheets[sheet_name]

    for row_idx, pattern in enumerate(all_patterns):
        excel_row = row_idx + 2  # row 1 = header
        for col_idx, col in enumerate(all_dates):
            excel_col = col_idx + 2  # col 1 = pattern_id
            if diff_mask.loc[pattern, col]:
                cell = ws.cell(row=excel_row, column=excel_col)
                cell.fill = red_fill
                cell.font = white_font
                cell.alignment = center_align

    for col_cells in ws.columns:
        max_length = max((len(str(cell.value)) if cell.value else 0) for cell in col_cells)
        ws.column_dimensions[get_column_letter(col_cells[0].column)].width = max(max_length + 2, 12)


# ========================================================================================================================================================
# 4️⃣ Output principal - Guarda um ficheiro Excel, com todas as comparações
# ========================================================================================================================================================

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
    Guarda todos os resultados em diferentes sheets de um ficheiro Excel.
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

        # -------------------------------------------------------------------------------------------
        # Alertas
        # -------------------------------------------------------------------------------------------
        
        safe_to_excel(alerts_df, 'ALERTAS')

        # -------------------------------------------------------------------------------------------
        # Resumo
        # -------------------------------------------------------------------------------------------

        if grand_total_df is not None and analysis_period_df is not None:
            grand_total_df.to_excel(writer, sheet_name='RESUMO', index=False, startrow=0)
            analysis_period_df.to_excel( writer, sheet_name='RESUMO', index=False, startrow=len(grand_total_df) + 2)
        else:
            safe_to_excel(grand_total_df, 'RESUMO')

        # -------------------------------------------------------------------------------------------
        # Comparação de circulações e VKM
        # -------------------------------------------------------------------------------------------
        
        safe_to_excel(merged_all, 'Comparação circulações e VKM')

        # -------------------------------------------------------------------------------------------
        # Comparações
        # -------------------------------------------------------------------------------------------
        
        safe_to_excel(compare_calendars, 'Comparação calendarios')
        safe_to_excel(stops_comparison_result, 'Comparação paragens')
        safe_to_excel(extension_comparison_result, 'Comparação extensões')
        safe_to_excel(merged_routes, 'Comparação rotas')

        # -------------------------------------------------------------------------------------------
        # Circulações por hora
        # -------------------------------------------------------------------------------------------

        save_circulacoes_por_hora_por_trimestre(writer, circulacoes_por_hora)

        # -------------------------------------------------------------------------------------------
        # Sequências de paragens
        # -------------------------------------------------------------------------------------------

        safe_to_excel(stop_sequence_oferta, 'Sequencia paragens POferta')
        safe_to_excel(stop_sequence_operacao, 'Sequencia paragens POperação')

        # -------------------------------------------------------------------------------------------
        # Resumos planos
        # -------------------------------------------------------------------------------------------

        safe_to_excel(resumo_oferta_final, 'Resumo Plano Oferta')
        safe_to_excel(resumo_operacao_final, 'Resumo Plano Operação')

        # -------------------------------------------------------------------------------------------
        # Circulações por data
        # -------------------------------------------------------------------------------------------

        safe_to_excel(pivot_dates_oferta, 'Circulações por Data POferta')
        safe_to_excel(pivot_dates_operacao, 'Circulações por Data POperação')

        # -------------------------------------------------------------------------------------------
        # Comparação de circulações por data entre planos
        # -------------------------------------------------------------------------------------------

        _add_trips_date_comparison_sheet(writer, pivot_dates_oferta, pivot_dates_operacao)