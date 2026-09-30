import json

class JsonScenarioRepository:

    def __init__(self):
        self.error = ""

    def load(self, filepath):
        self.error = ""

        try:
            with open(filepath, "r", encoding="utf-8") as file:
                return json.load(file, object_pairs_hook=self._rejectDuplicateKeys)
        except json.JSONDecodeError as e:
            self.error = f"Invalid JSON at line {e.lineno}, column {e.colno}: {e.msg}"
        except ValueError as e:  # duplicate keys
            self.error = str(e)
        except OSError as e:  # file not found, no permission, etc.
            self.error = f"Could not read file: {e}"

        return None

    @staticmethod
    def _rejectDuplicateKeys(archive):
        result = {}
        for key, value in archive:
            if key in result:
                raise ValueError(f"Duplicate key in JSON: '{key}'")
            result[key] = value
        return result
