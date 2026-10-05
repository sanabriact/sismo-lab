import json
import os

# Directory where the JSON data files are stored
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)),"data")

class JSONRepository:

    # Initialize the repository with the full path of its JSON file
    def __init__(self, filename):
        self.path = os.path.join(DATA_DIR,filename)

    # -------------------------------------------------------------------------
    # Reading and writing the JSON file
    # -------------------------------------------------------------------------

    # Read the JSON file and return its content, or an empty dictionary if it does not exist
    def _read(self):
        if not os.path.exists(self.path):
            return {}
        with open(self.path,"r",encoding="utf-8") as file:
            return json.load(file)

    # Write the data to the JSON file and return whether it was saved
    def _write(self,data):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        # The data is serialized before opening the file: if data is not serializable,
        # the JSON that already exists on disk is not truncated.
        content = json.dumps(data, indent=4, ensure_ascii=False)
        with open(self.path,"w",encoding="utf-8") as file:
            file.write(content)
            return True
        return False