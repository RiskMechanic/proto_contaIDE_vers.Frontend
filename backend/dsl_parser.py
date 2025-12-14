# backend/dsl_parser.py
import re

COMMANDS = [
    "scrivi", "saldo", "movimenti", "mastrino", "bilancio",
    "conti", "causali", "aiuto", "split", "unsplit",
]

def parse_command(cmd: str):
    tokens = cmd.split()
    if not tokens:
        return {"action": "none", "error": "❌ Nessun comando inserito."}
    action = tokens[0].lower()
    date = tokens[1] if len(tokens) > 1 else None
    params = {kv.split(":")[0]: kv.split(":")[1] for kv in tokens[2:] if ":" in kv}
    return {"action": action, "date": date, "params": params}

def _extract_two_ints(text: str):
    # Finds all integers in the text; returns first two if present
    nums = re.findall(r"\b\d+\b", text)
    if len(nums) >= 2:
        return int(nums[0]), int(nums[1])
    return None

def execute_command(text: str):
    text = text.strip()
    if not text:
        return "❌ Nessun comando inserito."

    tokens = text.split()
    cmd = tokens[0].lower()
    args_text = text[len(tokens[0]):].strip()

    # unsplit
    if cmd == "unsplit":
        return {"action": "unsplit"}

    # split: accept "split 1 3", "split 1 and 3", "split 1, 3", etc.
    if cmd == "split":
        pair = _extract_two_ints(args_text)
        if pair:
            left, right = pair
            return {"action": "split", "left": left, "right": right}
        return "❌ Errore: usa due numeri di tab (es. 'split 1 3')."

    # base commands (placeholders)
    if cmd == "saldo":
        return "Saldo Cassa: 0"
    elif cmd == "bilancio":
        return "Bilancio vuoto"
    elif cmd == "aiuto":
        args = args_text.split()
        if args:
            target = args[0].lower()
            if target in COMMANDS:
                return f"ℹ️ Help per '{target}': uso base del comando."
            else:
                return f"❌ Comando '{target}' non riconosciuto."
        else:
            return "Comandi disponibili: " + ", ".join(COMMANDS)

    elif cmd in COMMANDS:
        return f"Eseguito comando: {cmd}"

    return f"❌ Comando non riconosciuto: {text}"
