import json
import os

# Carica dataset esterno (JSON) con tips
def load_tips():
    dataset_path = os.path.join(os.path.dirname(__file__), "help_tips.json")
    if not os.path.exists(dataset_path):
        # Dataset minimo di default
        return {
            "acquisto": "📘 Registrazione acquisto: comando add, esempio add ...",
            "fattura": "📗 Emissione fattura: comando add, esempio add ...",
            "giroconto": "📊 Giroconto IVA: comando adj, esempio adj ..."
        }
    with open(dataset_path, "r", encoding="utf-8") as f:
        return json.load(f)

# Sinonimi → mappa plurali o varianti alla chiave principale
SYNONYMS = {
    "acquisti": "acquisto",
    "fatture": "fattura",
    "giroconti": "giroconto"
}

TIPS = load_tips()

def get_help_text(query: str) -> str:
    query = query.strip().lower()

    if query == "":
        return "💡 Digita un termine per vedere suggerimenti."

    # Risolvi sinonimi
    if query in SYNONYMS:
        query = SYNONYMS[query]

    # Ricerca diretta
    if query in TIPS:
        return TIPS[query]

    # Autosuggerimento: trova termini che iniziano con query
    suggestions = [key for key in TIPS.keys() if key.startswith(query)]
    if suggestions:
        return "🔍 Forse cercavi: " + ", ".join(suggestions)

    return f"❌ Errore: comando '{query}' non trovato."
