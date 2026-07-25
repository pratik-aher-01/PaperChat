"""Tests for the browser acquisition page scroller."""

from unittest.mock import MagicMock, call

from app.acquisition.browser import (
    _collect_lazy_rendered_messages,
    _scroll_to_top,
    _visible_message_snapshots,
    _walk_chat_surface_down,
)


def test_visible_message_snapshots_parses_evaluated_items() -> None:
    """_visible_message_snapshots extracts keys and html from page evaluation."""
    page = MagicMock()
    page.evaluate.return_value = [
        {"key": "id:m1", "html": '<div data-message-id="m1">Msg 1</div>'},
        {"key": "id:m2", "html": '<div data-message-id="m2">Msg 2</div>'},
    ]

    snapshots = _visible_message_snapshots(page)

    assert len(snapshots) == 2
    assert snapshots[0]["key"] == "id:m1"
    assert snapshots[1]["html"] == '<div data-message-id="m2">Msg 2</div>'


def test_scroll_to_top_stops_when_position_is_at_top() -> None:
    """_scroll_to_top repeatedly scrolls up until position reaches top edge."""
    page = MagicMock()
    page.evaluate.side_effect = [
        {"position": 1000, "extent": 5000, "viewport": 800},
        {"position": 400, "extent": 5000, "viewport": 800},
        {"position": 0, "extent": 5000, "viewport": 800},
        {"position": 0, "extent": 5000, "viewport": 800},
        {"position": 0, "extent": 5000, "viewport": 800},
    ]

    _scroll_to_top(page)

    assert page.keyboard.press.call_count == 5
    page.keyboard.press.assert_has_calls([call("Home")] * 5)


def test_walk_chat_surface_down_collects_unseen_messages_until_bottom() -> None:
    """_walk_chat_surface_down steps down through pages collecting unique messages."""
    page = MagicMock()
    # Mocking scroll state progression
    page.evaluate.side_effect = [
        # Step 1: snapshots call then scroll call
        [{"key": "id:m1", "html": "<div>Msg 1</div>"}],
        {"position": 0, "extent": 2000, "viewport": 1000},
        # Step 2: snapshots call then scroll call
        [{"key": "id:m1", "html": "<div>Msg 1</div>"}, {"key": "id:m2", "html": "<div>Msg 2</div>"}],
        {"position": 1000, "extent": 2000, "viewport": 1000},
        # Step 3 (at edge, stable 1): snapshots then scroll
        [{"key": "id:m2", "html": "<div>Msg 2</div>"}],
        {"position": 1000, "extent": 2000, "viewport": 1000},
        # Step 4 (stable 2): snapshots then scroll
        [{"key": "id:m2", "html": "<div>Msg 2</div>"}],
        {"position": 1000, "extent": 2000, "viewport": 1000},
        # Step 5 (stable 3): snapshots then scroll
        [{"key": "id:m2", "html": "<div>Msg 2</div>"}],
        {"position": 1000, "extent": 2000, "viewport": 1000},
        # Step 6 (stable 4 -> break): snapshots then scroll
        [{"key": "id:m2", "html": "<div>Msg 2</div>"}],
        {"position": 1000, "extent": 2000, "viewport": 1000},
        # Final collection at bottom
        [{"key": "id:m2", "html": "<div>Msg 2</div>"}],
    ]

    seen = set()
    messages = []
    _walk_chat_surface_down(page, seen=seen, messages=messages)

    assert messages == ["<div>Msg 1</div>", "<div>Msg 2</div>"]
    assert "id:m1" in seen
    assert "id:m2" in seen


def test_collect_lazy_rendered_messages_collects_full_thread_in_order() -> None:
    """_collect_lazy_rendered_messages scrolls to top then walks down to capture full thread."""
    page = MagicMock()
    # 1. _scroll_to_top evaluation
    # 2. initial snapshots at top
    # 3. _walk_chat_surface_down evaluations
    page.evaluate.side_effect = [
        # _scroll_to_top
        {"position": 0, "extent": 1000, "viewport": 800},
        {"position": 0, "extent": 1000, "viewport": 800},
        {"position": 0, "extent": 1000, "viewport": 800},
        # initial snapshot at top
        [{"key": "id:m1", "html": "<div>Top Msg 1</div>"}],
        # walk down step 1 snapshots + scroll
        [{"key": "id:m1", "html": "<div>Top Msg 1</div>"}, {"key": "id:m2", "html": "<div>Msg 2</div>"}],
        {"position": 200, "extent": 1000, "viewport": 800},
        # walk down step 2 snapshots + scroll (at edge)
        [{"key": "id:m2", "html": "<div>Msg 2</div>"}, {"key": "id:m3", "html": "<div>Bottom Msg 3</div>"}],
        {"position": 200, "extent": 1000, "viewport": 800},
        # walk down step 3
        [{"key": "id:m3", "html": "<div>Bottom Msg 3</div>"}],
        {"position": 200, "extent": 1000, "viewport": 800},
        # walk down step 4
        [{"key": "id:m3", "html": "<div>Bottom Msg 3</div>"}],
        {"position": 200, "extent": 1000, "viewport": 800},
        # walk down step 5 (stable 4 -> break)
        [{"key": "id:m3", "html": "<div>Bottom Msg 3</div>"}],
        {"position": 200, "extent": 1000, "viewport": 800},
        # final collection
        [{"key": "id:m3", "html": "<div>Bottom Msg 3</div>"}],
    ]

    messages = _collect_lazy_rendered_messages(page)

    assert messages == ["<div>Top Msg 1</div>", "<div>Msg 2</div>", "<div>Bottom Msg 3</div>"]
