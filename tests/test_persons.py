"""API tests – Persons router."""


class TestPersonCRUD:

    def test_list_persons_empty(self, client):
        assert client.get("/api/persons/").json() == []

    def test_create_person_full(self, client):
        r = client.post("/api/persons/", json={
            "username": "alice",
            "full_name": "Alice Smith",
            "email": "alice@example.com",
            "git_server": "https://github.com/alice",
        })
        assert r.status_code == 201
        d = r.json()
        assert d["username"] == "alice"
        assert d["email"] == "alice@example.com"
        assert d["git_server"] == "https://github.com/alice"

    def test_create_person_minimal(self, client):
        r = client.post("/api/persons/", json={"username": "bob"})
        assert r.status_code == 201
        assert r.json()["full_name"] == ""
        assert r.json()["email"] == ""

    def test_create_person_duplicate_username_fails(self, client):
        client.post("/api/persons/", json={"username": "dup"})
        r = client.post("/api/persons/", json={"username": "dup"})
        assert r.status_code == 400
        assert "already exists" in r.json()["detail"]

    def test_list_persons_sorted(self, client):
        client.post("/api/persons/", json={"username": "zebra"})
        client.post("/api/persons/", json={"username": "alpha"})
        names = [p["username"] for p in client.get("/api/persons/").json()]
        assert names == sorted(names)

    def test_get_person(self, client, person):
        r = client.get(f"/api/persons/{person['id']}")
        assert r.status_code == 200
        assert r.json()["username"] == "jdoe"

    def test_get_person_not_found(self, client):
        assert client.get("/api/persons/99999").status_code == 404

    def test_update_person(self, client, person):
        r = client.put(f"/api/persons/{person['id']}", json={
            "username": "jdoe",
            "full_name": "John Doe Updated",
            "email": "john@new.com",
            "git_server": "https://gitlab.com/jdoe",
        })
        assert r.status_code == 200
        assert r.json()["full_name"] == "John Doe Updated"
        assert r.json()["git_server"] == "https://gitlab.com/jdoe"

    def test_update_person_not_found(self, client):
        r = client.put("/api/persons/99999", json={"username": "x"})
        assert r.status_code == 404

    def test_delete_person(self, client, person):
        r = client.delete(f"/api/persons/{person['id']}")
        assert r.status_code == 204
        assert client.get(f"/api/persons/{person['id']}").status_code == 404

    def test_delete_person_not_found(self, client):
        assert client.delete("/api/persons/99999").status_code == 404
