class TestAuth:
    def test_register_parent(self, client):
        res = client.post("/api/auth/register", json={
            "email": "new@test.com",
            "username": "newparent",
            "password": "pass123",
        })
        assert res.status_code == 200
        data = res.json()
        assert data["username"] == "newparent"
        assert data["role"] == "parent"
        assert data["email"] == "new@test.com"

    def test_register_duplicate_username(self, client):
        client.post("/api/auth/register", json={
            "email": "dup1@test.com",
            "username": "dupuser",
            "password": "pass123",
        })
        res = client.post("/api/auth/register", json={
            "email": "dup2@test.com",
            "username": "dupuser",
            "password": "pass123",
        })
        assert res.status_code == 400
        assert "ユーザー名" in res.json()["detail"]

    def test_register_duplicate_email(self, client):
        client.post("/api/auth/register", json={
            "email": "same@test.com",
            "username": "user_email1",
            "password": "pass123",
        })
        res = client.post("/api/auth/register", json={
            "email": "same@test.com",
            "username": "user_email2",
            "password": "pass123",
        })
        assert res.status_code == 400
        assert "メールアドレス" in res.json()["detail"]

    def test_login_success(self, client, parent_user):
        res = client.post("/api/auth/login", json={
            "username": "testparent",
            "password": "parentpass",
        })
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, parent_user):
        res = client.post("/api/auth/login", json={
            "username": "testparent",
            "password": "wrongpass",
        })
        assert res.status_code == 401

    def test_login_nonexistent_user(self, client):
        res = client.post("/api/auth/login", json={
            "username": "nouser",
            "password": "pass",
        })
        assert res.status_code == 401

    def test_get_me_no_token(self, client):
        res = client.get("/api/auth/me")
        assert res.status_code == 401

    def test_get_me_success(self, client, parent_headers):
        res = client.get("/api/auth/me", headers=parent_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["username"] == "testparent"
        assert data["role"] == "parent"

    def test_get_me_child(self, client, child_headers):
        res = client.get("/api/auth/me", headers=child_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["username"] == "testchild"
        assert data["role"] == "child"
