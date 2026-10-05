import json

class JsonScenarioRepository:

    def __init__(self):
        self.error = ""

    def load(self, filepath):
        self.error = ""

        try:
            with open(filepath, "r", encoding="utf-8-sig") as file:
                return json.load(file, object_pairs_hook=self._rejectDuplicateKeys)
        except json.JSONDecodeError as e:
            self.error = f"Invalid JSON at line {e.lineno}, column {e.colno}: {e.msg}"
            print(f"--> ERROR JSON: {self.error}")
        except ValueError as e:  # Claves duplicadas encontradas
            self.error = str(e)
            print(f"--> ERROR CLAVE DUPLICADA: {self.error}")
        except OSError as e:  # Archivo no encontrado o sin permisos
            self.error = f"Could not read file: {e}"
            print(f"--> ERROR ARCHIVO / RUTA: {self.error}")

        return None

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