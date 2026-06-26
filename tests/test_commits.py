"""API tests – Commits router."""


class TestCommitCRUD:

    def test_list_commits_empty(self, client):
        assert client.get("/api/commits/").json() == []

    def test_create_commit_full(self, client, person):
        r = client.post("/api/commits/", json={
            "sha": "deadbeef1234",
            "message": "fix: correct off-by-one error",
            "author_id": person["id"],
            "git_url": "https://github.com/u/r/commit/deadbeef1234",
            "committed_at": "2024-05-15T08:30:00Z",
        })
        assert r.status_code == 201
        d = r.json()
        assert d["sha"] == "deadbeef1234"
        assert d["author"]["username"] == "jdoe"
        assert d["git_url"] == "https://github.com/u/r/commit/deadbeef1234"

    def test_create_commit_minimal(self, client):
        r = client.post("/api/commits/", json={"sha": "abc123"})
        assert r.status_code == 201
        assert r.json()["author"] is None
        assert r.json()["message"] == ""

    def test_create_commit_no_author(self, client):
        r = client.post("/api/commits/", json={
            "sha": "nonauthor",
            "message": "commit without author",
            "committed_at": None,
        })
        assert r.status_code == 201
        assert r.json()["author"] is None

    def test_list_commits(self, client, person):
        client.post("/api/commits/", json={"sha": "aaa"})
        client.post("/api/commits/", json={"sha": "bbb"})
        r = client.get("/api/commits/")
        assert len(r.json()) == 2

    def test_get_commit(self, client, commit):
        r = client.get(f"/api/commits/{commit['id']}")
        assert r.status_code == 200
        assert r.json()["sha"] == commit["sha"]

    def test_get_commit_not_found(self, client):
        assert client.get("/api/commits/99999").status_code == 404

    def test_delete_commit(self, client, commit):
        r = client.delete(f"/api/commits/{commit['id']}")
        assert r.status_code == 204
        assert client.get(f"/api/commits/{commit['id']}").status_code == 404

    def test_delete_commit_not_found(self, client):
        assert client.delete("/api/commits/99999").status_code == 404

    def test_link_commit_to_tickets(self, client, commit, ticket):
        r = client.post(f"/api/commits/{commit['id']}/link-tickets", json={"ids": [ticket["id"]]})
        assert r.status_code == 200
        # The endpoint returns the Commit; verify the ticket appears in ticket's commits via the ticket endpoint
        ticket_data = client.get(f"/api/tickets/{ticket['id']}").json()
        commit_ids = [c["id"] for c in ticket_data["commits"]]
        assert commit["id"] in commit_ids

    def test_link_commit_to_tickets_not_found(self, client):
        r = client.post("/api/commits/99999/link-tickets", json={"ids": []})
        assert r.status_code == 404
