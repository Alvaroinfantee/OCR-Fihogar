import logging
from typing import Any

def classify_with_o1_model(text: str, api_key: str, json_schema: str) -> Any:
    """Dummy classification function.

    Parameters
    ----------
    text : str
        Text to classify.
    api_key : str
        API key for the classification service (currently unused).
    json_schema : str
        Schema description for the classification output.

    Returns
    -------
    dict
        Placeholder dictionary with the text length and schema key count.
    """
    logging.warning("Using stub classify_with_o1_model; implement actual logic.")
    return {
        "text_length": len(text),
        "schema_keys": len([line for line in json_schema.splitlines() if ':' in line])
    }
