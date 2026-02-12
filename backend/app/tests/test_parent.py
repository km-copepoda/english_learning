from datetime import datetime, timezone, timedelta

from app.models import LearningRecord, User
from app.auth import hash_password, create_access_token


class TestParent:
    def test_list_children(self, client, parent_headers, child_user):
        res = client.get("/api/parent/children", headers=parent_headers)
        assert res.status_code == 200
        data = res.json()
        assert any(c["username"] == "testchild" for c in data)

    def test_list_children_empty(self, client, db):
        user = User(
            email="empty@test.com",
            username="emptyparent",
            hashed_password=hash_password("pass"),
            role="parent",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        token = create_access_token(data={"sub": user.username})
        res = client.get("/api/parent/children", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        assert res.json() == []

    def test_create_child_success(self, client, parent_headers):
        res = client.post("/api/parent/children", headers=parent_headers, json={
            "username": "newchild1",
            "password": "childpass",
        })
        assert res.status_code == 201
        assert res.json()["username"] == "newchild1"

    def test_create_child_duplicate_username(self, client, parent_headers, child_user):
        res = client.post("/api/parent/children", headers=parent_headers, json={
            "username": "testchild",
            "password": "childpass",
        })
        assert res.status_code == 400

    def test_delete_child(self, client, parent_headers, db):
        # Create a child to delete
        res = client.post("/api/parent/children", headers=parent_headers, json={
            "username": "deletechild",
            "password": "childpass",
        })
        child_id = res.json()["id"]
        res = client.delete(f"/api/parent/children/{child_id}", headers=parent_headers)
        assert res.status_code == 200
        # Verify gone
        res = client.get("/api/parent/children", headers=parent_headers)
        assert not any(c["username"] == "deletechild" for c in res.json())

    def test_delete_other_parent_child(self, client, db, child_user):
        other = User(
            email="other@test.com",
            username="otherparent",
            hashed_password=hash_password("pass"),
            role="parent",
        )
        db.add(other)
        db.commit()
        db.refresh(other)
        token = create_access_token(data={"sub": other.username})
        res = client.delete(
            f"/api/parent/children/{child_user.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 404
        assert "子アカウントが見つかりません" in res.json()["detail"]

    def test_update_child_password(self, client, parent_headers, db):
        res = client.post("/api/parent/children", headers=parent_headers, json={
            "username": "pwchild",
            "password": "oldpass",
        })
        cid = res.json()["id"]
        res = client.put(
            f"/api/parent/children/{cid}/password",
            headers=parent_headers,
            json={"password": "newpass"},
        )
        assert res.status_code == 200
        # Login with new password
        res = client.post("/api/auth/login", json={
            "username": "pwchild",
            "password": "newpass",
        })
        assert res.status_code == 200

    def test_child_stats(self, client, parent_headers, child_id, db, sample_words):
        # Create records for 2025-02-28 UTC (JST: 2025-03-01 if after 15:00 UTC)
        # Use 2025-02-28 06:00 UTC = 2025-02-28 15:00 JST
        dt = datetime(2025, 2, 28, 6, 0, 0, tzinfo=timezone.utc)
        records = [
            LearningRecord(child_id=child_id, word_id=sample_words[0].id,
                          is_correct=True, used_hint=False, session_type="today", answered_at=dt),
            LearningRecord(child_id=child_id, word_id=sample_words[1].id,
                          is_correct=False, used_hint=False, session_type="today", answered_at=dt),
            LearningRecord(child_id=child_id, word_id=sample_words[2].id,
                          is_correct=True, used_hint=False, session_type="review", answered_at=dt),
        ]
        db.add_all(records)
        db.commit()

        res = client.get(
            f"/api/parent/children/{child_id}/stats?year=2025&month=2",
            headers=parent_headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 28  # Feb 2025 has 28 days
        # Find Feb 28
        feb28 = next(d for d in data if d["date"] == "2025-02-28")
        assert feb28["today_correct"] >= 1
        assert feb28["today_incorrect"] >= 1

    def test_child_stats_empty(self, client, parent_headers, db):
        res = client.post("/api/parent/children", headers=parent_headers, json={
            "username": "statsempty",
            "password": "pass",
        })
        cid = res.json()["id"]
        res = client.get(
            f"/api/parent/children/{cid}/stats?year=2025&month=1",
            headers=parent_headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 31  # Jan has 31 days
        assert all(d["today_correct"] == 0 for d in data)

    def test_child_weak_words_limit(self, client, parent_headers, child_id, db, sample_words):
        # apple: already has correct record from test_child_stats
        # Add incorrect records to make it weak
        for _ in range(5):
            db.add(LearningRecord(
                child_id=child_id, word_id=sample_words[0].id,
                is_correct=False, used_hint=False, session_type="today",
                answered_at=datetime.now(timezone.utc),
            ))
        db.commit()

        res = client.get(
            f"/api/parent/children/{child_id}/weak-words",
            headers=parent_headers,
        )
        assert res.status_code == 200
        data = res.json()
        # Should only include words with accuracy < 0.9
        for w in data:
            assert w["accuracy"] < 0.9

    def test_child_weak_words_has_hint_count(self, client, parent_headers, child_id, db, sample_words):
        # Create new word for clean test
        from app.models import Word
        word = db.query(Word).filter(Word.english == "banana").first()
        # Clear existing records for banana
        db.query(LearningRecord).filter(
            LearningRecord.child_id == child_id,
            LearningRecord.word_id == word.id,
        ).delete()
        db.commit()

        # 3 correct (1 without hint, 2 with hint) + 2 incorrect = 5 total
        records = [
            LearningRecord(child_id=child_id, word_id=word.id,
                          is_correct=True, used_hint=False, session_type="today",
                          answered_at=datetime.now(timezone.utc)),
            LearningRecord(child_id=child_id, word_id=word.id,
                          is_correct=True, used_hint=True, session_type="today",
                          answered_at=datetime.now(timezone.utc)),
            LearningRecord(child_id=child_id, word_id=word.id,
                          is_correct=True, used_hint=True, session_type="today",
                          answered_at=datetime.now(timezone.utc)),
            LearningRecord(child_id=child_id, word_id=word.id,
                          is_correct=False, used_hint=False, session_type="today",
                          answered_at=datetime.now(timezone.utc)),
            LearningRecord(child_id=child_id, word_id=word.id,
                          is_correct=False, used_hint=False, session_type="today",
                          answered_at=datetime.now(timezone.utc)),
        ]
        db.add_all(records)
        db.commit()

        res = client.get(
            f"/api/parent/children/{child_id}/weak-words",
            headers=parent_headers,
        )
        data = res.json()
        banana = next((w for w in data if w["english"] == "banana"), None)
        assert banana is not None
        assert banana["hint_count"] == 2
        assert banana["total_attempts"] == 5
        assert banana["correct_count"] == 3

    def test_parent_endpoints_require_parent_role(self, client, child_headers):
        res = client.get("/api/parent/children", headers=child_headers)
        assert res.status_code == 403
        res = client.post("/api/parent/children", headers=child_headers, json={
            "username": "x", "password": "x",
        })
        assert res.status_code == 403
