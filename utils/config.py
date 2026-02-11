import json
def get_host(key: str, default: str) -> str:
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
            return config.get(key, default)
    except FileNotFoundError:
        return default
def get_port(key: str, default: int) -> int:
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
            return config.get(key, default)
    except FileNotFoundError:
        return default
