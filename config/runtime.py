_config = None

def init_config(config_dict):
    global _config
    _config = config_dict

def get(key):
    if _config is None:
        raise RuntimeError(
            "Configuração não inicializada. "
            "Chama configurar() no run_analysis.py primeiro."
        )
    return _config[key]
