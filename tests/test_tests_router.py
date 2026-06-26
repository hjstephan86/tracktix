"""API tests – Tests router."""


class TestTestCRUD:

    def test_list_tests_empty(self, client):
        assert client.get("/api/tests/").json() == []

    def test_create_test_full(self, client, person):
        r = client.post("/api/tests/", json={
            "title": "Integration test for API endpoint",
            "description": "Tests /api/tickets/ POST",
            "test_type": "integration",
            "result": "passed",
            "tester_id": person["id"],
            "run_at": "2024-06-10T14:00:00Z",
        })
        assert r.status_code == 201
        d = r.json()
        assert d["title"] == "Integration test for API endpoint"
        assert d["test_type"] == "integration"
        assert d["result"] == "passed"
        assert d["tester"]["username"] == "jdoe"

    def test_create_test_minimal(self, client):
        r = client.post("/api/tests/", json={"title": "Minimal test"})
        assert r.status_code == 201
        assert r.json()["result"] == "pending"
        assert r.json()["test_type"] == "unit"
        assert r.json()["tester"] is None

    def test_create_test_system_type(self, client):
        r = client.post("/api/tests/", json={"title": "System test", "test_type": "system"})
        assert r.status_code == 201
        assert r.json()["test_type"] == "system"

    def test_create_test_failed_result(self, client):
        r = client.post("/api/tests/", json={"title": "Failing test", "result": "failed"})
        assert r.status_code == 201
        assert r.json()["result"] == "failed"

    def test_list_tests(self, client):
        client.post("/api/tests/", json={"title": "T1"})
        client.post("/api/tests/", json={"title": "T2"})
        assert len(client.get("/api/tests/").json()) == 2

    def test_get_test(self, client, test_obj):
        r = client.get(f"/api/tests/{test_obj['id']}")
        assert r.status_code == 200
        assert r.json()["title"] == test_obj["title"]

    def test_get_test_not_found(self, client):
        assert client.get("/api/tests/99999").status_code == 404

    def test_update_test(self, client, test_obj):
        r = client.put(f"/api/tests/{test_obj['id']}", json={
            "title": "Updated test",
            "description": "New desc",
            "test_type": "system",
            "result": "failed",
            "tester_id": None,
            "run_at": None,
        })
        assert r.status_code == 200
        assert r.json()["result"] == "failed"
        assert r.json()["test_type"] == "system"

    def test_update_test_not_found(self, client):
        r = client.put("/api/tests/99999", json={"title": "x", "test_type": "unit", "result": "pending"})
        assert r.status_code == 404

    def test_delete_test(self, client, test_obj):
        r = client.delete(f"/api/tests/{test_obj['id']}")
        assert r.status_code == 204
        assert client.get(f"/api/tests/{test_obj['id']}").status_code == 404

    def test_delete_test_not_found(self, client):
        assert client.delete("/api/tests/99999").status_code == 404

    def test_link_test_to_tickets(self, client, test_obj, ticket):
        r = client.post(f"/api/tests/{test_obj['id']}/link-tickets", json={"ids": [ticket["id"]]})
        assert r.status_code == 200
        # Verify via ticket endpoint
        ticket_data = client.get(f"/api/tickets/{ticket['id']}").json()
        test_ids = [t["id"] for t in ticket_data["tests"]]
        assert test_obj["id"] in test_ids

    def test_link_test_to_tickets_not_found(self, client):
        r = client.post("/api/tests/99999/link-tickets", json={"ids": []})
        assert r.status_code == 404
