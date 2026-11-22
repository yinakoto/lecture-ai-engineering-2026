"""第5回 宿題（実装）：検索結果に前後ページを足す処理のテスト（APIキー不要）。

search() はAPIで質問を埋め込むので、ここでは検索結果を固定値に差し替えて確かめる。
"""

import json

import pytest

from app import retrieval, tools


def _hit(page_id: str, distance: float = 0.1) -> dict:
    """教材JSONの実在ページを、検索結果の形（distance付き）にする。"""
    page = retrieval.read_page(page_id)
    return {**page, "distance": distance}


def test_window_zero_returns_search_results_unchanged():
    hits = [_hit("lec02-main-p052")]
    assert retrieval.add_neighbor_pages(hits, 0) == hits


def test_adds_previous_and_next_page_after_search_results():
    results = retrieval.add_neighbor_pages([_hit("lec02-main-p052")], 1)
    assert [r["page_id"] for r in results] == ["lec02-main-p052", "lec02-main-p051", "lec02-main-p053"]
    assert results[0]["source"] == "search" and results[0]["distance"] == 0.1
    assert all(r["source"] == "neighbor" and r["neighbor_of"] == "lec02-main-p052" for r in results[1:])
    assert all("distance" not in r for r in results[1:])
    assert all(r["content"] for r in results)


def test_no_duplicates_when_hits_are_adjacent():
    hits = [_hit("lec03-main-p039", 0.1), _hit("lec03-main-p040", 0.2)]
    ids = [r["page_id"] for r in retrieval.add_neighbor_pages(hits, 1)]
    assert len(ids) == len(set(ids))
    assert ids == ["lec03-main-p039", "lec03-main-p040", "lec03-main-p038", "lec03-main-p041"]


def test_does_not_cross_documents_at_first_and_last_page():
    first = retrieval.add_neighbor_pages([_hit("lec02-main-p001")], 1)
    assert [r["page_id"] for r in first] == ["lec02-main-p001", "lec02-main-p002"]
    last_page = max(p["page"] for p in retrieval.load_pages() if p["document_id"] == "lec01-main")
    last_id = f"lec01-main-p{last_page:03d}"
    last = retrieval.add_neighbor_pages([_hit(last_id)], 1)
    assert {r["document_id"] for r in last} == {"lec01-main"}
    assert [r["page"] for r in last] == [last_page, last_page - 1]


def test_negative_window_is_rejected():
    with pytest.raises(ValueError):
        retrieval.add_neighbor_pages([_hit("lec02-main-p052")], -1)


def test_search_materials_tool_uses_neighbor_setting(monkeypatch):
    monkeypatch.setattr("app.retrieval.search", lambda *args, **kwargs: [_hit("lec02-main-p052")])
    # 既定（AIE_RAG_NEIGHBORS 未設定）は通常の検索と同じ
    monkeypatch.setattr("app.retrieval.search_with_neighbors.__defaults__", (0,))
    base = json.loads(tools.search_materials("LoRA"))["results"]
    assert [r["page_id"] for r in base] == ["lec02-main-p052"] and "source" not in base[0]
    # AIE_RAG_NEIGHBORS=1 と同じ設定
    monkeypatch.setattr("app.retrieval.search_with_neighbors.__defaults__", (1,))
    expanded = json.loads(tools.search_materials("LoRA"))["results"]
    assert [r["page_id"] for r in expanded] == ["lec02-main-p052", "lec02-main-p051", "lec02-main-p053"]
