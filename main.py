import os
import sys

os.environ["GRPC_VERBOSITY"] = "NONE"
os.environ["GRPC_TRACE"] = ""
sys.stderr = open(os.devnull, "w")

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import initialize_agent, Tool
from ldap_tools import get_current_user_info, get_user_groups, list_all_users, list_all_groups, search_privileged_accounts

# ---------------- Auto-Generación (BEGIN) ----------------
import importlib
import shutil

GENERATED_FILE = "generated_tools.py"
BACKUP_FILE = "ldap_tools.py.bak"
LDAP_TOOLS_MODULE = "ldap_tools"

def ensure_backup():
    """Crear backup de ldap_tools.py si no existe."""
    if not os.path.exists(BACKUP_FILE):
        shutil.copyfile(f"{LDAP_TOOLS_MODULE}.py", BACKUP_FILE)

def restore_backup():
    """Restaurar ldap_tools.py desde backup (overwrite)."""
    if os.path.exists(BACKUP_FILE):
        shutil.copyfile(BACKUP_FILE, f"{LDAP_TOOLS_MODULE}.py")
    if os.path.exists(GENERATED_FILE):
        os.remove(GENERATED_FILE)

def init_generated_file():
    """Crear generated_tools.py si no existe con template mínimo."""
    if not os.path.exists(GENERATED_FILE):
        with open(GENERATED_FILE, "w", encoding="utf-8") as f:
            f.write(
                "# Archivo de herramientas generadas dinámicamente\n"
                "from ldap_tools import connect, BASE_DN_GROUPS, SUBTREE\n\n"
            )

def reload_module_by_name(name: str):
    """Importa o recarga un módulo por nombre y lo deja en globals()."""
    if name in globals():
        return importlib.reload(globals()[name])
    mod = importlib.import_module(name)
    globals()[name] = mod
    return mod

def generate_tool_code(func_name: str, params: str, body_lines: list, doc: str = "") -> str:
    """
    Construye la definición de una función a partir de una lista de líneas.
    """
    safe_name = "".join(c for c in func_name if (c.isalnum() or c == "_"))
    indented_body = "\n".join("    " + line for line in body_lines) if body_lines else "    pass"
    docstring = f'    """{doc}"""\n' if doc else ""
    return f"\ndef {safe_name}({params}):\n{docstring}{indented_body}\n"

def append_generated_tool(func_name: str, params: str, body_lines: list, doc: str = ""):
    """
    Añade la función al archivo generated_tools.py y recarga el módulo.
    Devuelve el nombre de la función añadida.
    """
    forbidden = ["import ", "exec(", "eval(", "os.system", "subprocess", "open("]
    joined = "\n".join(body_lines).lower()
    for f in forbidden:
        if f in joined:
            raise ValueError(f"Body contains forbidden token: {f}")

    code = generate_tool_code(func_name, params, body_lines, doc)
    with open(GENERATED_FILE, "a", encoding="utf-8") as f:
        f.write(code)
    return reload_module_by_name("generated_tools")

def load_generated_tools_as_tools():
    """
    Recarga generated_tools.py y devuelve una lista de objetos Tool() listos para
    extender la lista 'tools' del agente.
    """
    try:
        mod = reload_module_by_name("generated_tools")
    except Exception:
        return []

    tools_list = []
    for attr in dir(mod):
        if attr.startswith("_"):
            continue
        obj = getattr(mod, attr)
        if callable(obj):
            def make_func(fn):
                return (lambda arg=None, fn=fn: str(fn(arg) if arg is not None else fn()))
            t = Tool(
                name=f"{attr}",
                func=make_func(obj),
                description=f"Tool generada dinámicamente: {attr}"
            )
            tools_list.append(t)
    return tools_list

def reset_generated_and_restore_original(tools_container, original_tools_snapshot):
    """
    Restaura ldap_tools.py desde backup, elimina generated file, y restaura
    la lista original de tools en 'tools_container' usando original_tools_snapshot.
    - tools_container: la lista 'tools' que usas para initialize_agent (se modifica in-place).
    - original_tools_snapshot: copia de seguridad de las tools originales (lista).
    """
    restore_backup()
    try:
        reload_module_by_name(LDAP_TOOLS_MODULE)
    except Exception:
        pass

    if os.path.exists(GENERATED_FILE):
        os.remove(GENERATED_FILE)
    init_generated_file()

    tools_container.clear()
    tools_container.extend(list(original_tools_snapshot))
    return True

ensure_backup()
init_generated_file()

import inspect
import traceback

def append_generated_tool_and_execute(func_name: str, params: str, body_lines: list, doc: str = "", exec_arg=None):
    """
    1) Valida y añade la función a generated_tools.py
    2) Recarga generated_tools.py
    3) Obtiene la función recién creada y la ejecuta
    - exec_arg: valor opcional que se pasará como único argumento si la función acepta 1 param.
    - Devuelve el resultado de la ejecución (convertido a str para que el agente lo muestre).
    """
    forbidden = ["import ", "exec(", "eval(", "os.system", "subprocess", "open(", "__import__", "socket"]
    joined = "\n".join(body_lines).lower()
    for f in forbidden:
        if f in joined:
            raise ValueError(f"Body contains forbidden token: {f}")

    append_generated_tool(func_name, params, body_lines, doc)

    try:
        mod = reload_module_by_name("generated_tools")
    except Exception as e:
        return f"Error recargando generated_tools: {e}\n{traceback.format_exc()}"

    if not hasattr(mod, func_name):
        return f"No se encontró la función {func_name} en generated_tools tras recarga."

    fn = getattr(mod, func_name)
    if not callable(fn):
        return f"El objeto {func_name} no es callable."

    try:
        sig = inspect.signature(fn)
        params_count = len([p for p in sig.parameters.values() if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD) and p.default is inspect._empty])
    except Exception:
        params_count = None

    try:
        if params_count == 0 or params_count is None:
            result = fn()
        else:
            result = fn(exec_arg)
    except TypeError:
        try:
            result = fn()
        except Exception as e:
            return f"Error ejecutando la función {func_name}: {e}\n{traceback.format_exc()}"
    except Exception as e:
        return f"Error ejecutando la función {func_name}: {e}\n{traceback.format_exc()}"

    try:
        return str(result)
    except Exception:
        return repr(result)
        
def handle_generate_and_run_spec(spec_str: str):
    """
    Parseador simple para specs. Formato esperado (todas partes opcionales salvo name/body):
      name:<func_name>;params:<params>;body:<line1>|<line2>|...;doc:<docstring>;arg:<exec_arg>
    """
    if not spec_str:
        return "Spec vacía. Debes enviar la spec como string."

    parts = {}
    for part in spec_str.split(";"):
        if ":" not in part:
            continue
        k, v = part.split(":", 1)
        parts[k.strip().lower()] = v.strip()

    func_name = parts.get("name") or "generated_tool"
    params = parts.get("params", "")
    body_raw = parts.get("body", "")
    doc = parts.get("doc", "")
    exec_arg = parts.get("arg", None)

    if "|" in body_raw:
        body_lines = [line for line in (l.strip() for l in body_raw.split("|")) if line]
    else:
        body_lines = [line for line in (l.strip() for l in body_raw.split("\\n")) if line]

    if not body_lines:
        return "El body está vacío. Debes pasar al menos una línea de código."

    try:
        result = append_generated_tool_and_execute(func_name, params, body_lines, doc=doc, exec_arg=exec_arg)
        new_tools = load_generated_tools_as_tools()
        existing_names = {t.name for t in tools}
        for nt in new_tools:
            if nt.name not in existing_names:
                tools.append(nt)
        return result
    except Exception as e:
        return f"Error al generar/ejecutar la tool: {e}\n{traceback.format_exc()}"
        
# ---------------- Auto-Generación (BEGIN) ----------------

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    api_key=os.getenv("GOOGLE_API_KEY")
)

tools = [
    Tool(
        name="get_current_user_info",
        func=lambda _: str(get_current_user_info()),
        description="Devuelve la información del usuario actualmente autenticado en LDAP."
    ),
    Tool(
        name="get_user_groups",
        func=lambda username_str=None: str(get_user_groups(username_str)),
        description="Devuelve los grupos a los que pertenece un usuario específico de LDAP. Se usa pasando el nombre del usuario."
    ),
    Tool(
        name="list_all_users",
        func=lambda _: str(list_all_users()),
        description="Enumera todos los usuarios visibles en el dominio LDAP."
    ),
    Tool(
        name="list_all_groups",
        func=lambda _: str(list_all_groups()),
        description="Lista todos los grupos disponibles en LDAP."
    ),
    Tool(
        name="search_privileged_accounts",
        func=lambda _: str(search_privileged_accounts()),
        description="Busca cuentas sensibles, privilegiadas, con altos permisos o de servicio comunes."
    ),
    Tool(
        name="generate_and_run_tool",
        func=lambda spec_str=None: str(handle_generate_and_run_spec(spec_str)),
        description=(
            "Genera y ejecuta una nueva herramienta."
        )
    )
]

original_tools_snapshot = list(tools)

tools.extend(load_generated_tools_as_tools())

reset_generated_and_restore_original(tools, original_tools_snapshot)

agent = initialize_agent(
    tools,
    llm,
    agent="zero-shot-react-description",
    verbose=False,
    handle_parsing_errors=True
)

def run_agent():
    print("Agente de consulta LDAP con LLM iniciado. Podés escribir en lenguaje natural (exit para salir).\n")
    while True:
        query = input(">> ")
        if query.lower() in ("exit", "quit"):
            print("Cerrando agente...")
            break
        try:
            response = agent.invoke(query)
            print(response["output"])
        except Exception as e:
            print(f"Error ejecutando la consulta: {e}")

if __name__ == "__main__":
    run_agent()
