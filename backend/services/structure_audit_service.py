from backend.services.audit_state import AuditState

class StructureAuditService:
    def audit_avl(self, tree, mode="normal"):
        state = AuditState(tree, mode)

        self._audit_node(
            node=tree.root,
            lower_key=None,
            upper_key=None,
            expected_parent=None,
            state=state,
        )

        self._audit_index(state)

        return state.build_result()

    def _audit_node(
        self,
        node,
        lower_key,
        upper_key,
        expected_parent,
        state,
    ):
        if node is None:
            return -1

        if self._was_visited(node, state):
            state.add_issue(
                event_id=None,
                issue_type="shared_reference",
                message="El mismo nodo aparece más de una vez en el árbol.",
            )
            return -1

        state.visited_nodes.add(id(node))

        key = node.getValue().getKey()
        event_id = self._get_event_id(key)

        valid_key = self._audit_key(key, event_id, state)
        self._audit_parent(node, expected_parent, event_id, state)

        if valid_key:
            self._audit_order(
                key,
                lower_key,
                upper_key,
                event_id,
                state,
            )

        child_lower_key = lower_key
        child_upper_key = upper_key

        if valid_key:
            child_lower_key = key
            child_upper_key = key

        left_height = self._audit_node(
            node=node.getLeftChild(),
            lower_key=lower_key,
            upper_key=child_upper_key,
            expected_parent=node,
            state=state,
        )

        right_height = self._audit_node(
            node=node.getRightChild(),
            lower_key=child_lower_key,
            upper_key=upper_key,
            expected_parent=node,
            state=state,
        )

        calculated_height = 1 + max(left_height, right_height)
        balance_factor = left_height - right_height

        self._audit_height(
            node,
            event_id,
            calculated_height,
            state,
        )

        self._audit_balance(
            event_id,
            balance_factor,
            state,
        )

        self._audit_node_index(
            node,
            event_id,
            state,
        )

        return calculated_height

    def _was_visited(self, node, state):
        return id(node) in state.visited_nodes

    def _get_event_id(self, key):
        if not self._is_valid_key(key):
            return None

        return key[2]

    def _is_valid_key(self, key):
        return isinstance(key, tuple) and len(key) == 3

    def _audit_key(self, key, event_id, state):
        if not self._is_valid_key(key):
            state.add_issue(
                event_id=None,
                issue_type="invalid_key",
                message="La clave K debe ser una tupla de tres valores.",
            )
            return False

        self._audit_unique_id(event_id, state)
        self._audit_unique_key(key, event_id, state)

        return True

    def _audit_unique_id(self, event_id, state):
        if event_id in state.event_ids:
            state.add_issue(
                event_id=event_id,
                issue_type="duplicate_id",
                message="El id del evento está repetido en el árbol.",
            )

        state.event_ids.add(event_id)

    def _audit_unique_key(self, key, event_id, state):
        if key in state.keys:
            state.add_issue(
                event_id=event_id,
                issue_type="duplicate_key",
                message="La clave K está repetida en el árbol.",
            )

        state.keys.add(key)

    def _audit_parent(self, node, expected_parent, event_id, state):
        if node.getParent() is expected_parent:
            return

        state.add_issue(
            event_id=event_id,
            issue_type="parent_link",
            message="La referencia al padre no coincide con la topología.",
        )

    def _audit_order(
        self,
        key,
        lower_key,
        upper_key,
        event_id,
        state,
    ):
        if lower_key is not None and key <= lower_key:
            state.add_issue(
                event_id=event_id,
                issue_type="global_order",
                message="La clave K incumple su límite inferior global.",
            )

        if upper_key is not None and key >= upper_key:
            state.add_issue(
                event_id=event_id,
                issue_type="global_order",
                message="La clave K incumple su límite superior global.",
            )

    def _audit_height(
        self,
        node,
        event_id,
        calculated_height,
        state,
    ):
        stored_height = node.getHeight()

        if stored_height == calculated_height:
            return

        state.add_height_issue(
            event_id=event_id,
            stored=stored_height,
            calculated=calculated_height,
        )

    def _audit_balance(
        self,
        event_id,
        balance_factor,
        state,
    ):
        absolute_balance = abs(balance_factor)

        if absolute_balance > state.max_imbalance:
            state.max_imbalance = absolute_balance

        if absolute_balance <= 1:
            return

        if state.mode == "stress":
            state.add_imbalance_warning(
                event_id,
                balance_factor,
            )
            return

        state.add_balance_issue(
            event_id,
            balance_factor,
        )

    def _audit_node_index(self, node, event_id, state):
        if event_id is None:
            return

        indexed_node = state.tree.index.get(event_id)

        if indexed_node is node:
            return

        state.add_issue(
            event_id=event_id,
            issue_type="index_reference",
            message="El índice no apunta al nodo correcto.",
        )

    def _audit_index(self, state):
        for event_id, node in state.tree.index.items():
            if id(node) in state.visited_nodes:
                continue

            state.add_issue(
                event_id=event_id,
                issue_type="orphan_index_entry",
                message=(
                    "El índice contiene un nodo que no es alcanzable "
                    "desde la raíz."
                ),
            )