from pathlib import Path

LUA_DIR = Path(__file__).parent


def load_lua_script(name: str) -> str:
    return (LUA_DIR / name).read_text()
