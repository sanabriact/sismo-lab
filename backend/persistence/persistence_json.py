import json
class PersistenceJSON:
    def save(self,object, route):
        toJson = object.toDict()
        with open(route,"w",encoding="utf-8") as archive:
            json.dump(toJson,archive, indent=4, ensure_ascii=False)