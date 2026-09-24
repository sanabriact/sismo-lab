import json
import os
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)),"data")
class JSONRepository:
    def __init__(self, filename):
        self.path = os.path.join(DATA_DIR,filename)

    def _read(self):
        if not os.path.exists(self.path):
            return {}
        with open(self.path,"r",encoding="utf-8") as file:
            return json.load(file)

    def _write(self,data):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path,"w",encoding="utf-8") as file:  
            json.dump(data, file, indent=4, ensure_ascii=False)            
            return True
        return False