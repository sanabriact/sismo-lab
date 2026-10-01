class AuditState:
    """
    Guarda el resultado mientras se recorre el árbol.
    Esta clase no modifica el AVL.
    """

    def __init__(self, tree, mode):
        self.tree = tree
        self.mode = mode

        self.issues = []
        self.warnings = []
        self.node_reports = {}

        self.visited_nodes = set()
        self.event_ids = set()
        self.keys = set()
        self.max_imbalance = 0

    def add_issue(self, event_id, issue_type, message):
        issue = {
            "id": event_id,
            "type": issue_type,
            "message": message,
        }

        self.issues.append(issue)
        self.get_node_report(event_id)["issues"].append(issue)

    def add_height_issue(self, event_id, stored, calculated):
        issue = {
            "id": event_id,
            "type": "height",
            "message": (
                f"Altura almacenada: {stored}. "
                f"Altura recalculada: {calculated}."
            ),
            "stored": stored,
            "calculated": calculated,
        }

        self.issues.append(issue)
        self.get_node_report(event_id)["issues"].append(issue)

    def add_balance_issue(self, event_id, balance_factor):
        issue = {
            "id": event_id,
            "type": "balance",
            "message": (
                "El factor de balance debe estar entre -1 y 1. "
                f"Valor actual: {balance_factor}."
            ),
            "balance_factor": balance_factor,
        }

        self.issues.append(issue)
        self.get_node_report(event_id)["issues"].append(issue)

    def add_imbalance_warning(self, event_id, balance_factor):
        warning = {
            "id": event_id,
            "type": "expected_imbalance",
            "message": (
                "Desbalance esperado en modo estrés. "
                f"Factor de balance: {balance_factor}."
            ),
            "balance_factor": balance_factor,
        }

        self.warnings.append(warning)
        self.get_node_report(event_id)["warnings"].append(warning)

    def get_node_report(self, event_id):
        report_key = str(event_id)

        if report_key not in self.node_reports:
            self.node_reports[report_key] = {
                "id": event_id,
                "issues": [],
                "warnings": [],
            }

        return self.node_reports[report_key]

    def build_result(self):
        balanced = self.max_imbalance <= 1
        has_structure_errors = len(self.issues) > 0

        if self.mode == "stress":
            ok = not has_structure_errors
        else:
            ok = not has_structure_errors and balanced

        return {
            "ok": ok,
            "balanced": balanced,
            "max_imbalance": self.max_imbalance,
            "issues": self.issues,
            "warnings": self.warnings,
            "node_reports": list(self.node_reports.values()),
        }

