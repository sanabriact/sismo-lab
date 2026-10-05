# ------------------------------------------------------------------
# t es t b st s tr uc tu re
# ------------------------------------------------------------------

"""Focused tests for the unbalanced BST implementation."""

from datetime import datetime, timezone

from backend.models.event import Event
from backend.structures.bst import BST


def make_event(event_id, magnitude=2.0):
    return Event(
        event_id,
        magnitude,
        10.0,
        10.0,
        10.0,
        datetime(2026, 9, 7, 10, 0, tzinfo=timezone.utc),
        1,
        1,
    )


def test_bst_insertion_keeps_order_without_rotations_and_updates_heights():
    tree = BST()
    for event_id in (1, 2, 3, 4):
        assert tree.insert(make_event(event_id)) is True

    assert [event.getKey()[2] for event in tree.inorder()] == [1, 2, 3, 4]
    assert tree.root.getValue().getKey()[2] == 1
    assert tree.root.getHeight() == 3
    assert tree.root.getRightChild().getHeight() == 2


def test_bst_rejects_duplicate_identity_even_when_the_key_changes():
    tree = BST()
    assert tree.insert(make_event(10, 2.0)) is True
    assert tree.insert(make_event(10, 6.0)) is False
    assert len(tree.index) == 1


def test_bst_two_child_delete_preserves_the_remaining_index_and_order():
    tree = BST()
    for event_id in (4, 2, 6, 1, 3, 5, 7):
        assert tree.insert(make_event(event_id)) is True

    assert tree.delete(4) is True
    assert 4 not in tree.index
    assert set(tree.index) == {1, 2, 3, 5, 6, 7}
    assert [event.getKey()[2] for event in tree.inorder()] == [1, 2, 3, 5, 6, 7]


def test_bst_visual_patch_does_not_crash_after_delete():
    tree = BST()
    tree.begin_visual_operation()
    for event_id in (2, 1, 3):
        assert tree.insert(make_event(event_id)) is True
    tree.delete(2)

    patch = tree.finish_visual_operation()

    assert patch["operation"] == "delete"
    assert patch["removedIds"] == [2]
    assert patch["rootId"] == 1

