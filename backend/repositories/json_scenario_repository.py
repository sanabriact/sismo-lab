import json

class JsonScenarioRepository:

    # Initialize the repository with an empty error message
    def __init__(self):
        self.error = ""

    # -------------------------------------------------------------------------
    # Loading and parsing scenarios
    # -------------------------------------------------------------------------

    # Load a scenario from a JSON file, or return None and store the error if it fails
    def load(self, filepath):
        self.error = ""

        try:
            with open(filepath, "r", encoding="utf-8-sig") as file:
                return json.load(file, object_pairs_hook=self._rejectDuplicateKeys)
        except json.JSONDecodeError as e:
            self.error = f"Invalid JSON at line {e.lineno}, column {e.colno}: {e.msg}"
            print(f"--> ERROR JSON: {self.error}")
        except ValueError as e:  # Duplicate keys found
            self.error = str(e)
            print(f"--> ERROR CLAVE DUPLICADA: {self.error}")
        except OSError as e:  # File not found or no permissions
            self.error = f"Could not read file: {e}"
            print(f"--> ERROR ARCHIVO / RUTA: {self.error}")

        return None

    # Parse scenario text using the same duplicate-key rule as file loads
    def parse_text(self, content):
        return json.loads(
            content.lstrip("\ufeff"),
            object_pairs_hook=self._rejectDuplicateKeys,
        )

    # -------------------------------------------------------------------------
    # Duplicate key validation
    # -------------------------------------------------------------------------

    # Build a dictionary from key-value pairs and raise an error if a key is repeated
    @staticmethod
    def _rejectDuplicateKeys(archive):
        result = {}
        seen_keys = set()
        for key, value in archive:
            if key in seen_keys:
                raise ValueError(f"Duplicate key in JSON: '{key}'")
            seen_keys.add(key)
            result[key] = value
        return result