import pytest

from app.rag.loaders import EmptyDocumentError, UnsupportedFileError, load_document


def test_load_txt(tmp_path):
    f = tmp_path / "notes.txt"
    f.write_text("Hello world.\nSecond line.")
    pages = load_document(str(f), ".txt")
    assert len(pages) == 1
    assert pages[0]["page"] == 1
    assert "Hello world" in pages[0]["text"]


def test_load_empty_txt_raises(tmp_path):
    f = tmp_path / "empty.txt"
    f.write_text("   \n  ")
    with pytest.raises(EmptyDocumentError):
        load_document(str(f), ".txt")


def test_load_csv(tmp_path):
    f = tmp_path / "data.csv"
    f.write_text("name,score\nAlice,90\nBob,85\n")
    pages = load_document(str(f), ".csv")
    assert "Alice" in pages[0]["text"]
    assert "Row 1" in pages[0]["text"]


def test_unsupported_extension_raises(tmp_path):
    f = tmp_path / "file.exe"
    f.write_text("binary-ish content")
    with pytest.raises(UnsupportedFileError):
        load_document(str(f), ".exe")
