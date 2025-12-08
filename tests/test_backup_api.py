import os

import pytest


def test_safe_export_sqlite_rejects_traversal(tmp_path):
    from adapters.backup import safe_export_sqlite

    src = tmp_path / "media.db"
    src.write_text("dummy")
    dest_dir = tmp_path / "out"
    dest_dir.mkdir()

    out = safe_export_sqlite(str(src), str(dest_dir), filename="ok_backup")
    assert os.path.isfile(out)

    with pytest.raises(ValueError):
        safe_export_sqlite(str(src), str(dest_dir), filename="../../evil")
