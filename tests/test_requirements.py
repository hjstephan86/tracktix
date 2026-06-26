"""API tests – Requirements router."""


class TestRequirementCRUD:

    def test_list_requirements_empty(self, client):
        r = client.get("/api/requirements/")
        assert r.status_code == 200
        assert r.json() == []

    def test_create_requirement(self, client, project):
        r = client.post("/api/requirements/", json={
            "project_id": project["id"],
            "key": "SRS-001",
            "title": "System shall do X",
            "description": "Full text",
            "url": "https://spec.example.com/1",
        })
        assert r.status_code == 201
        d = r.json()
        assert d["key"] == "SRS-001"
        assert d["url"] == "https://spec.example.com/1"
        assert d["project_id"] == project["id"]

    def test_create_requirement_minimal(self, client, project):
        r = client.post("/api/requirements/", json={
            "project_id": project["id"],
            "key": "MIN-1",
            "title": "Minimal req",
        })
        assert r.status_code == 201
        assert r.json()["url"] == ""
        assert r.json()["description"] == ""

    def test_list_requirements_filter_by_project(self, client, project):
        p2 = client.post("/api/projects/", json={"key": "P2", "name": "P2"}).json()
        client.post("/api/requirements/", json={"project_id": project["id"], "key": "A-1", "title": "A"})
        client.post("/api/requirements/", json={"project_id": p2["id"], "key": "B-1", "title": "B"})

        r = client.get(f"/api/requirements/?project_id={project['id']}")
        assert r.status_code == 200
        keys = [x["key"] for x in r.json()]
        assert "A-1" in keys
        assert "B-1" not in keys

    def test_list_requirements_all(self, client, project):
        client.post("/api/requirements/", json={"project_id": project["id"], "key": "X-1", "title": "X"})
        client.post("/api/requirements/", json={"project_id": project["id"], "key": "X-2", "title": "Y"})
        r = client.get("/api/requirements/")
        assert len(r.json()) == 2

    def test_get_requirement(self, client, requirement):
        r = client.get(f"/api/requirements/{requirement['id']}")
        assert r.status_code == 200
        assert r.json()["key"] == "SRS-001"

    def test_get_requirement_not_found(self, client):
        r = client.get("/api/requirements/99999")
        assert r.status_code == 404

    def test_update_requirement(self, client, requirement):
        r = client.put(f"/api/requirements/{requirement['id']}", json={
            "project_id": requirement["project_id"],
            "key": "SRS-001-REV",
            "title": "Updated title",
            "description": "Updated",
            "url": "https://new.url",
        })
        assert r.status_code == 200
        assert r.json()["key"] == "SRS-001-REV"
        assert r.json()["url"] == "https://new.url"

    def test_update_requirement_not_found(self, client, project):
        r = client.put("/api/requirements/99999", json={
            "project_id": project["id"], "key": "X", "title": "X"
        })
        assert r.status_code == 404

    def test_delete_requirement(self, client, requirement):
        r = client.delete(f"/api/requirements/{requirement['id']}")
        assert r.status_code == 204
        assert client.get(f"/api/requirements/{requirement['id']}").status_code == 404

    def test_delete_requirement_not_found(self, client):
        r = client.delete("/api/requirements/99999")
        assert r.status_code == 404
