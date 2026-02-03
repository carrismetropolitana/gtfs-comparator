"""
Este módulo define a interface de linha de comandos para configurar a análise.
Recolhe interativamente os caminhos, ficheiros GTFS, intervalo temporal e opções de exportação, validando os dados introduzidos e devolvendo todas as configurações
num único dicionário para utilização durante a execução.

"""

# ========================================================================================================================================================
# Importa a biblioteca Click para criar interfaces de linha de comandos
# ========================================================================================================================================================

import click
from pathlib import Path
from datetime import datetime

# ========================================================================================================================================================
# Função para validar se a data está no formato YYYYMMDD
# ========================================================================================================================================================

def validar_data(value):
    """Valida se a data está no formato YYYYMMDD"""
    try:
        datetime.strptime(value, "%Y%m%d")
        return value
    except ValueError:
        raise click.BadParameter("🚨 Formato inválido! Use YYYYMMDD.")

# ========================================================================================================================================================
# Função principal para recolher as configurações apenas nesta execução
# ========================================================================================================================================================

def configurar():
    """Recolhe as configurações apenas para esta execução"""

    click.echo("🛠️ Defina as configurações da sua análise\n")
    
    # -------------------------------------------------------------------------------------------
    # Solicita ao utilizador o caminho para a pasta com ficheiros GTFS
    # -------------------------------------------------------------------------------------------

    target_folder = click.prompt("📂 Adicione o caminho para a pasta onde tem os ficheiros GTFS guardados", type=click.Path(exists=True, file_okay=False, path_type=Path))

    # -------------------------------------------------------------------------------------------
    # Indentificação dos ficheiros GTFS
    # -------------------------------------------------------------------------------------------

    gtfs_offerplan_name = click.prompt("📝 Coloque o nome do ficheiro GTFS de Oferta")
    gtfs_operationplan_name = click.prompt("📝 Coloque o nome do ficheiro GTFS de Operação")

    # -------------------------------------------------------------------------------------------
    # Datas de análise
    # -------------------------------------------------------------------------------------------
    while True:
        start_date = click.prompt("📅 Adicione a data de início da sua analise no formato YYYYMMDD")
        try:
            start_date = validar_data(start_date)
            break
        except click.BadParameter as e:
            click.echo(f"❌ {e}")

    while True:
        end_date = click.prompt("📅 Adicione a data de fim da sua analise no formato YYYYMMDD")
        try:
            end_date = validar_data(end_date)
            break
        except click.BadParameter as e:
            click.echo(f"❌ {e}")

    # -------------------------------------------------------------------------------------------
    # Exportação - Comparador de Planos
    # -------------------------------------------------------------------------------------------
    
    export_result = click.confirm("📤 Pretende exportar o ficheiro que resulta da comparação de planos?", default=True)
    result_name = click.prompt("📝 Adicione o nome que pretende para guardar a comparação de planos")

    # -------------------------------------------------------------------------------------------
    # Exportação - Sequência de paragens
    # -------------------------------------------------------------------------------------------

    export_stop_sequence = click.confirm("📤 Pretende exportar o ficheiro resultado da análise da sequência de paragens?", default=False)
    export_stop_sequence_filename = None
    if export_stop_sequence: export_stop_sequence_filename = click.prompt("📝 Adicione o nome que pretende para guardar o ficheiro que resulta da análise à sequência de paragens")

    # -------------------------------------------------------------------------------------------
    # Exportação - Total de circulações e VKMs
    # -------------------------------------------------------------------------------------------
 
    export_total_circulations = click.confirm("📤 Pretende exportar o ficheiro resultado da análise do Total de Circulações e VKM?", default=False)
    export_total_circulations_vkm_filename = None
    if export_total_circulations: export_total_circulations_vkm_filename = click.prompt("📝 Adicione o nome que pretende para guardar o ficheiro que resulta da análise ao Total de Circulações e VKM")

    # -------------------------------------------------------------------------------------------
    # Devolve dicionário com todas as configurações
    # -------------------------------------------------------------------------------------------

    return {
        "TARGET_FOLDER": str(target_folder),
        "GTFS_OFFERPLAN_NAME": gtfs_offerplan_name,
        "GTFS_OPERATIONPLAN_NAME": gtfs_operationplan_name,
        "START_DATE": start_date,
        "END_DATE": end_date,
        "RESULT_NAME": result_name,
        "EXPORT_RESULT": export_result,
        "EXPORT_STOP_SEQUENCE": export_stop_sequence,
        "EXPORT_TOTAL_CIRCULATIONS_VKM": export_total_circulations,
        "EXPORT_STOP_SEQUENCE_FILENAME": export_stop_sequence_filename,
        "EXPORT_TOTAL_CIRCULATIONS_VKM_FILENAME": export_total_circulations_vkm_filename,
    }
