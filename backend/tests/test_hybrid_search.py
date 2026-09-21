from app.rag.hybrid_search import merge_results


def test_chunk_found_by_both_methods_ranks_highest():
    semantic = {"a": 0.9, "b": 0.5, "c": 0.1}
    keyword = {"a": 10.0, "d": 8.0}
    results = merge_results(semantic, keyword, semantic_weight=0.7, keyword_weight=0.3)
    assert results[0].chunk_id == "a"  # found by both -> highest combined score


def test_semantic_only_hit_still_included():
    semantic = {"x": 0.8}
    keyword = {}
    results = merge_results(semantic, keyword)
    assert len(results) == 1
    assert results[0].chunk_id == "x"
    assert results[0].final_score > 0


def test_keyword_only_hit_still_included():
    semantic = {}
    keyword = {"y": 5.0}
    results = merge_results(semantic, keyword)
    assert len(results) == 1
    assert results[0].chunk_id == "y"


def test_no_hits_returns_empty_list():
    assert merge_results({}, {}) == []


def test_weights_change_the_ranking():
    semantic = {"a": 1.0, "b": 0.0}
    keyword = {"a": 0.0, "b": 1.0}
    semantic_first = merge_results(semantic, keyword, semantic_weight=1.0, keyword_weight=0.0)
    keyword_first = merge_results(semantic, keyword, semantic_weight=0.0, keyword_weight=1.0)
    assert semantic_first[0].chunk_id == "a"
    assert keyword_first[0].chunk_id == "b"
