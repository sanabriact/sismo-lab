# Convert legacy scenario data into the current internal shape
class ScenarioDataNormalizer:

    # -------------------------------------------------------------------------
    # Event normalization
    # -------------------------------------------------------------------------

    # Normalize key-based events and keep API-shaped events unchanged
    @staticmethod
    def insertion_event(item, station_ids):
        if not isinstance(item, dict) or "key" not in item:
            return item

        # Validate the key and the reporting stations
        key = item["key"]
        if not isinstance(key, (list, tuple)) or len(key) != 3:
            raise ValueError("'key' debe contener prioridad, magnitud e id")

        reporting_stations = item.get("reporting_stations", [])
        if not isinstance(reporting_stations, list):
            raise TypeError("'reporting_stations' debe ser una lista")

        # Pick the first reporting station or fall back to any known station
        station = (
            reporting_stations[0]
            if reporting_stations
            else next(iter(station_ids), None)
        )
        if station is None:
            raise ValueError("el evento debe referenciar una estación")

        return {
            "id": key[2],
            "magnitude": key[1],
            "depth": item.get("depth"),
            "epicenter_x": item.get("epicenter_x"),
            "epicenter_y": item.get("epicenter_y"),
            "datetime": item.get("datetime"),
            "revision": item.get("revision", 1),
            "station": station,
        }

    # -------------------------------------------------------------------------
    # Topology normalization
    # -------------------------------------------------------------------------

    # Normalize compact tree nodes to the persistence node shape
    @staticmethod
    def topology_tree(tree):
        if not isinstance(tree, dict) or "root" not in tree:
            raise ValueError("la topología debe contener un root")

        # Normalize a node recursively and return it with its height
        def normalize_node(node):
            if node is None:
                return None, -1
            if not isinstance(node, dict) or "event" not in node:
                raise ValueError("cada nodo debe contener un event")

            left, left_height = normalize_node(node.get("left_child"))
            right, right_height = normalize_node(node.get("right_child"))
            height = 1 + max(left_height, right_height)
            return {
                "value": node["event"],
                "height": height,
                "left_child": left,
                "right_child": right,
                "node_creation_time": None,
            }, height

        root, _ = normalize_node(tree["root"])
        return {"root": root}