import io


class TestAdmin:
    def test_import_words(self, client, parent_headers):
        csv_content = "english,japanese,english_katakana,section\nhello,こんにちは,ハロー,3\nworld,世界,ワールド,3\nsky,空,スカイ,3"
        files = {"file": ("words.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
        res = client.post("/api/admin/import-words", headers=parent_headers, files=files)
        assert res.status_code == 200
        assert "3件" in res.json()["detail"]

    def test_import_words_duplicate_skip(self, client, parent_headers, sample_words):
        # Import same words as sample_words
        csv_content = "english,japanese,english_katakana,section\napple,りんご,アップル,1\nbanana,バナナ,バナナ,1\ncat,猫,キャット,1"
        files = {"file": ("words.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
        res = client.post("/api/admin/import-words", headers=parent_headers, files=files)
        assert res.status_code == 200
        assert "スキップ" in res.json()["detail"]

    def test_import_words_require_parent(self, client, child_headers):
        csv_content = "english,japanese,english_katakana,section\ntest,テスト,テスト,1"
        files = {"file": ("words.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
        res = client.post("/api/admin/import-words", headers=child_headers, files=files)
        assert res.status_code == 403

    def test_import_words_no_auth(self, client):
        csv_content = "english,japanese,english_katakana,section\ntest,テスト,テスト,1"
        files = {"file": ("words.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
        res = client.post("/api/admin/import-words", files=files)
        assert res.status_code == 401
