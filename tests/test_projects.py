"""API tests – Projects router (100 % coverage target)."""
import pytest


class TestProjectCRUD:

    def test_list_projects_empty(self, client):
        r = client.get("/api/projects/")
        assert r.status_code == 200
        assert r.json() == []

    def test_create_project_minimal(self, client):
        r = client.post("/api/projects/", json={"key": "PROJ", "name": "My Project"})
        assert r.status_code == 201
        data = r.json()
        assert data["key"] == "PROJ"
        assert data["name"] == "My Project"
        assert data["description"] == ""
        assert data["git_base_url"] == ""
        assert "id" in data
        assert "created_at" in data

    def test_create_project_full(self, client):
        r = client.post("/api/projects/", json={
            "key": "full",
            "name": "Full Project",
            "description": "A full project",
            "git_base_url": "https://github.com/org/repo",
        })
        assert r.status_code == 201
        data = r.json()
        assert data["key"] == "FULL"           # key is uppercased
        assert data["description"] == "A full project"
        assert data["git_base_url"] == "https://github.com/org/repo"

    def test_create_project_key_uppercased(self, client):
        r = client.post("/api/projects/", json={"key": "lower", "name": "N"})
        assert r.json()["key"] == "LOWER"

    def test_create_project_duplicate_key_fails(self, client):
        client.post("/api/projects/", json={"key": "DUP", "name": "First"})
        r = client.post("/api/projects/", json={"key": "DUP", "name": "Second"})
        assert r.status_code == 400
        assert "already exists" in r.json()["detail"]

    def test_list_projects_returns_all(self, client):
        client.post("/api/projects/", json={"key": "A", "name": "A"})
        client.post("/api/projects/", json={"key": "B", "name": "B"})
        r = client.get("/api/projects/")
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_get_project_by_id(self, client, project):
        r = client.get(f"/api/projects/{project['id']}")
        assert r.status_code == 200
        assert r.json()["key"] == "TEST"

    def test_get_project_not_found(self, client):
        r = client.get("/api/projects/99999")
        assert r.status_code == 404

    def test_update_project(self, client, project):
        r = client.put(f"/api/projects/{project['id']}", json={
            "key": "TEST",
            "name": "Updated Name",
            "description": "New desc",
            "git_base_url": "https://new.git",
        })
        assert r.status_code == 200
        assert r.json()["name"] == "Updated Name"
        assert r.json()["description"] == "New desc"

    def test_update_project_not_found(self, client):
        r = client.put("/api/projects/99999", json={"key": "X", "name": "X"})
        assert r.status_code == 404

    def test_delete_project(self, client, project):
        r = client.delete(f"/api/projects/{project['id']}")
        assert r.status_code == 204
        r2 = client.get(f"/api/projects/{project['id']}")
        assert r2.status_code == 404

    def test_delete_project_not_found(self, client):
        r = client.delete("/api/projects/99999")
        assert r.status_code == 404

    def test_delete_project_cascades_tickets(self, client, project, requirement):
        tk = client.post("/api/tickets/", json={
            "project_id": project["id"], "title": "T", "requirement_ids": []
        })
        assert tk.status_code == 201
        client.delete(f"/api/projects/{project['id']}")
        # requirement and ticket should be gone
        assert client.get(f"/api/tickets/{tk.json()['id']}").status_code == 404
