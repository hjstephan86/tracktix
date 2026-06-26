"""API tests – Tickets router (core of the system)."""
import pytest


class TestTicketCRUD:

    def test_list_tickets_empty(self, client):
        assert client.get("/api/tickets/").json() == []

    def test_create_ticket_minimal(self, client, project):
        r = client.post("/api/tickets/", json={
            "project_id": project["id"],
            "title": "Simple ticket",
            "requirement_ids": [],
        })
        assert r.status_code == 201
        d = r.json()
        assert d["key"] == "TEST-1"
        assert d["title"] == "Simple ticket"
        assert d["status"] == "open"
        assert d["priority"] == "medium"
        assert d["requirements"] == []
        assert d["commits"] == []
        assert d["tests"] == []
        assert d["comments"] == []

    def test_create_ticket_key_increments(self, client, project):
        t1 = client.post("/api/tickets/", json={"project_id": project["id"], "title": "T1", "requirement_ids": []}).json()
        t2 = client.post("/api/tickets/", json={"project_id": project["id"], "title": "T2", "requirement_ids": []}).json()
        assert t1["key"] == "TEST-1"
        assert t2["key"] == "TEST-2"

    def test_create_ticket_with_requirements(self, client, project, requirement):
        r = client.post("/api/tickets/", json={
            "project_id": project["id"],
            "title": "Ticket with req",
            "requirement_ids": [requirement["id"]],
        })
        assert r.status_code == 201
        reqs = r.json()["requirements"]
        assert len(reqs) == 1
        assert reqs[0]["key"] == "SRS-001"

    def test_create_ticket_with_assignee(self, client, project, person):
        r = client.post("/api/tickets/", json={
            "project_id": project["id"],
            "title": "Assigned ticket",
            "requirement_ids": [],
            "assignee_id": person["id"],
        })
        assert r.status_code == 201
        assert r.json()["assignee"]["username"] == "jdoe"

    def test_create_ticket_all_statuses(self, client, project):
        for status in ["open", "in_progress", "in_review", "testing", "closed", "rejected"]:
            r = client.post("/api/tickets/", json={
                "project_id": project["id"],
                "title": f"Ticket {status}",
                "status": status,
                "requirement_ids": [],
            })
            assert r.status_code == 201
            assert r.json()["status"] == status

    def test_create_ticket_all_priorities(self, client, project):
        for prio in ["low", "medium", "high", "critical"]:
            r = client.post("/api/tickets/", json={
                "project_id": project["id"],
                "title": f"Prio {prio}",
                "priority": prio,
                "requirement_ids": [],
            })
            assert r.status_code == 201
            assert r.json()["priority"] == prio

    def test_create_ticket_project_not_found(self, client):
        r = client.post("/api/tickets/", json={
            "project_id": 99999, "title": "X", "requirement_ids": []
        })
        assert r.status_code == 404

    def test_get_ticket(self, client, ticket):
        r = client.get(f"/api/tickets/{ticket['id']}")
        assert r.status_code == 200
        assert r.json()["id"] == ticket["id"]

    def test_get_ticket_not_found(self, client):
        assert client.get("/api/tickets/99999").status_code == 404

    def test_list_tickets_filter_by_project(self, client, project):
        p2 = client.post("/api/projects/", json={"key": "P2", "name": "P2"}).json()
        client.post("/api/tickets/", json={"project_id": project["id"], "title": "T1", "requirement_ids": []})
        client.post("/api/tickets/", json={"project_id": p2["id"],      "title": "T2", "requirement_ids": []})

        r = client.get(f"/api/tickets/?project_id={project['id']}")
        assert all(t["project_id"] == project["id"] for t in r.json())
        assert len(r.json()) == 1

    def test_list_tickets_filter_by_status(self, client, project):
        client.post("/api/tickets/", json={"project_id": project["id"], "title": "T1", "status": "open",   "requirement_ids": []})
        client.post("/api/tickets/", json={"project_id": project["id"], "title": "T2", "status": "closed", "requirement_ids": []})
        r = client.get("/api/tickets/?status=open")
        assert all(t["status"] == "open" for t in r.json())

    def test_list_tickets_filter_by_priority(self, client, project):
        client.post("/api/tickets/", json={"project_id": project["id"], "title": "T1", "priority": "high",   "requirement_ids": []})
        client.post("/api/tickets/", json={"project_id": project["id"], "title": "T2", "priority": "medium", "requirement_ids": []})
        r = client.get("/api/tickets/?priority=high")
        assert all(t["priority"] == "high" for t in r.json())

    def test_list_tickets_filter_by_assignee(self, client, project, person):
        client.post("/api/tickets/", json={"project_id": project["id"], "title": "Assigned", "assignee_id": person["id"], "requirement_ids": []})
        client.post("/api/tickets/", json={"project_id": project["id"], "title": "Unassigned", "requirement_ids": []})
        r = client.get(f"/api/tickets/?assignee_id={person['id']}")
        assert len(r.json()) == 1
        assert r.json()[0]["assignee"]["id"] == person["id"]

    def test_list_tickets_search_by_title(self, client, project):
        client.post("/api/tickets/", json={"project_id": project["id"], "title": "Login bug fix", "requirement_ids": []})
        client.post("/api/tickets/", json={"project_id": project["id"], "title": "Dashboard feature", "requirement_ids": []})
        r = client.get("/api/tickets/?search=login")
        assert len(r.json()) == 1
        assert "Login" in r.json()[0]["title"]

    def test_list_tickets_search_by_description(self, client, project):
        client.post("/api/tickets/", json={"project_id": project["id"], "title": "T", "description": "unique_xyz_desc", "requirement_ids": []})
        client.post("/api/tickets/", json={"project_id": project["id"], "title": "U", "description": "other", "requirement_ids": []})
        r = client.get("/api/tickets/?search=unique_xyz")
        assert len(r.json()) == 1

    def test_list_tickets_search_by_key(self, client, project):
        client.post("/api/tickets/", json={"project_id": project["id"], "title": "T1", "requirement_ids": []})
        r = client.get("/api/tickets/?search=TEST-1")
        assert len(r.json()) == 1

    def test_update_ticket_status(self, client, ticket):
        r = client.put(f"/api/tickets/{ticket['id']}", json={"status": "in_progress"})
        assert r.status_code == 200
        assert r.json()["status"] == "in_progress"

    def test_update_ticket_title(self, client, ticket):
        r = client.put(f"/api/tickets/{ticket['id']}", json={"title": "New title"})
        assert r.status_code == 200
        assert r.json()["title"] == "New title"

    def test_update_ticket_requirements(self, client, ticket, project):
        r2 = client.post("/api/requirements/", json={
            "project_id": project["id"], "key": "SRS-002", "title": "Req2"
        }).json()
        r = client.put(f"/api/tickets/{ticket['id']}", json={"requirement_ids": [r2["id"]]})
        assert r.status_code == 200
        req_keys = [req["key"] for req in r.json()["requirements"]]
        assert "SRS-002" in req_keys

    def test_update_ticket_clear_requirements(self, client, ticket):
        r = client.put(f"/api/tickets/{ticket['id']}", json={"requirement_ids": []})
        assert r.status_code == 200
        assert r.json()["requirements"] == []

    def test_update_ticket_not_found(self, client):
        r = client.put("/api/tickets/99999", json={"title": "x"})
        assert r.status_code == 404

    def test_delete_ticket(self, client, ticket):
        r = client.delete(f"/api/tickets/{ticket['id']}")
        assert r.status_code == 204
        assert client.get(f"/api/tickets/{ticket['id']}").status_code == 404

    def test_delete_ticket_not_found(self, client):
        assert client.delete("/api/tickets/99999").status_code == 404


class TestTicketCommitLinks:

    def test_link_commit_to_ticket(self, client, ticket, commit):
        r = client.post(f"/api/tickets/{ticket['id']}/commits", json={"ids": [commit["id"]]})
        assert r.status_code == 200
        assert any(c["id"] == commit["id"] for c in r.json()["commits"])

    def test_link_commit_idempotent(self, client, ticket, commit):
        client.post(f"/api/tickets/{ticket['id']}/commits", json={"ids": [commit["id"]]})
        r = client.post(f"/api/tickets/{ticket['id']}/commits", json={"ids": [commit["id"]]})
        assert r.status_code == 200
        # should not duplicate
        assert len([c for c in r.json()["commits"] if c["id"] == commit["id"]]) == 1

    def test_link_commit_ticket_not_found(self, client, commit):
        r = client.post("/api/tickets/99999/commits", json={"ids": [commit["id"]]})
        assert r.status_code == 404

    def test_unlink_commit(self, client, ticket, commit):
        client.post(f"/api/tickets/{ticket['id']}/commits", json={"ids": [commit["id"]]})
        r = client.delete(f"/api/tickets/{ticket['id']}/commits/{commit['id']}")
        assert r.status_code == 200
        assert all(c["id"] != commit["id"] for c in r.json()["commits"])

    def test_unlink_commit_ticket_not_found(self, client, commit):
        r = client.delete(f"/api/tickets/99999/commits/{commit['id']}")
        assert r.status_code == 404


class TestTicketTestLinks:

    def test_link_test_to_ticket(self, client, ticket, test_obj):
        r = client.post(f"/api/tickets/{ticket['id']}/tests", json={"ids": [test_obj["id"]]})
        assert r.status_code == 200
        assert any(t["id"] == test_obj["id"] for t in r.json()["tests"])

    def test_link_test_idempotent(self, client, ticket, test_obj):
        client.post(f"/api/tickets/{ticket['id']}/tests", json={"ids": [test_obj["id"]]})
        r = client.post(f"/api/tickets/{ticket['id']}/tests", json={"ids": [test_obj["id"]]})
        assert len([t for t in r.json()["tests"] if t["id"] == test_obj["id"]]) == 1

    def test_link_test_ticket_not_found(self, client, test_obj):
        r = client.post("/api/tickets/99999/tests", json={"ids": [test_obj["id"]]})
        assert r.status_code == 404

    def test_unlink_test(self, client, ticket, test_obj):
        client.post(f"/api/tickets/{ticket['id']}/tests", json={"ids": [test_obj["id"]]})
        r = client.delete(f"/api/tickets/{ticket['id']}/tests/{test_obj['id']}")
        assert r.status_code == 200
        assert all(t["id"] != test_obj["id"] for t in r.json()["tests"])

    def test_unlink_test_ticket_not_found(self, client, test_obj):
        r = client.delete(f"/api/tickets/99999/tests/{test_obj['id']}")
        assert r.status_code == 404


class TestTicketComments:

    def test_add_comment_anonymous(self, client, ticket):
        r = client.post(f"/api/tickets/{ticket['id']}/comments", json={"body": "Anonym comment"})
        assert r.status_code == 201
        d = r.json()
        assert d["body"] == "Anonym comment"
        assert d["author"] is None
        assert d["ticket_id"] == ticket["id"]

    def test_add_comment_with_author(self, client, ticket, person):
        r = client.post(f"/api/tickets/{ticket['id']}/comments", json={
            "body": "Reviewed and confirmed", "author_id": person["id"]
        })
        assert r.status_code == 201
        assert r.json()["author"]["username"] == "jdoe"

    def test_comments_appear_in_ticket(self, client, ticket):
        client.post(f"/api/tickets/{ticket['id']}/comments", json={"body": "First"})
        client.post(f"/api/tickets/{ticket['id']}/comments", json={"body": "Second"})
        ticket_data = client.get(f"/api/tickets/{ticket['id']}").json()
        bodies = [c["body"] for c in ticket_data["comments"]]
        assert "First" in bodies
        assert "Second" in bodies

    def test_add_comment_ticket_not_found(self, client):
        r = client.post("/api/tickets/99999/comments", json={"body": "X"})
        assert r.status_code == 404

    def test_delete_comment(self, client, ticket):
        c = client.post(f"/api/tickets/{ticket['id']}/comments", json={"body": "To delete"}).json()
        r = client.delete(f"/api/tickets/{ticket['id']}/comments/{c['id']}")
        assert r.status_code == 204

    def test_delete_comment_not_found(self, client, ticket):
        r = client.delete(f"/api/tickets/{ticket['id']}/comments/99999")
        assert r.status_code == 404

    def test_delete_comment_wrong_ticket(self, client, ticket, project):
        c = client.post(f"/api/tickets/{ticket['id']}/comments", json={"body": "C"}).json()
        t2 = client.post("/api/tickets/", json={"project_id": project["id"], "title": "T2", "requirement_ids": []}).json()
        # Try to delete comment using wrong ticket id
        r = client.delete(f"/api/tickets/{t2['id']}/comments/{c['id']}")
        assert r.status_code == 404


class TestTraceability:

    def test_traceability_empty(self, client, project):
        # Create a ticket with NO requirements
        tk = client.post("/api/tickets/", json={
            "project_id": project["id"], "title": "Empty trace", "requirement_ids": []
        }).json()
        r = client.get(f"/api/tickets/{tk['id']}/traceability")
        assert r.status_code == 200
        d = r.json()
        assert d["ticket"]["key"] == tk["key"]
        assert d["requirements"] == []
        assert d["commits"] == []
        assert d["tests"] == []

    def test_traceability_full_chain(self, client, ticket, commit, test_obj, requirement):
        # Link commit
        client.post(f"/api/tickets/{ticket['id']}/commits", json={"ids": [commit["id"]]})
        # Link test
        client.post(f"/api/tickets/{ticket['id']}/tests", json={"ids": [test_obj["id"]]})

        r = client.get(f"/api/tickets/{ticket['id']}/traceability")
        assert r.status_code == 200
        d = r.json()
        assert len(d["requirements"]) == 1
        assert d["requirements"][0]["key"] == "SRS-001"
        assert d["requirements"][0]["url"] == "https://spec.example.com/SRS-001"
        assert len(d["commits"]) == 1
        assert d["commits"][0]["sha"] == commit["sha"][:12]
        assert d["commits"][0]["author"] == "jdoe"
        assert d["commits"][0]["git_url"] == commit["git_url"]
        assert len(d["tests"]) == 1
        assert d["tests"][0]["result"] == "passed"
        assert d["tests"][0]["tester"] == "jdoe"

    def test_traceability_commit_without_author(self, client, ticket):
        c = client.post("/api/commits/", json={"sha": "noauth000"}).json()
        client.post(f"/api/tickets/{ticket['id']}/commits", json={"ids": [c["id"]]})
        r = client.get(f"/api/tickets/{ticket['id']}/traceability")
        assert r.json()["commits"][0]["author"] is None

    def test_traceability_commit_no_committed_at(self, client, ticket):
        c = client.post("/api/commits/", json={"sha": "nodate001", "committed_at": None}).json()
        client.post(f"/api/tickets/{ticket['id']}/commits", json={"ids": [c["id"]]})
        r = client.get(f"/api/tickets/{ticket['id']}/traceability")
        assert r.json()["commits"][0]["committed_at"] is None

    def test_traceability_test_without_tester(self, client, ticket):
        t = client.post("/api/tests/", json={"title": "Anon test", "result": "pending"}).json()
        client.post(f"/api/tickets/{ticket['id']}/tests", json={"ids": [t["id"]]})
        r = client.get(f"/api/tickets/{ticket['id']}/traceability")
        assert r.json()["tests"][0]["tester"] is None
        assert r.json()["tests"][0]["run_at"] is None

    def test_traceability_not_found(self, client):
        assert client.get("/api/tickets/99999/traceability").status_code == 404

    def test_traceability_commit_sort_order(self, client, ticket, person):
        c1 = client.post("/api/commits/", json={"sha": "early00", "committed_at": "2024-01-01T00:00:00Z"}).json()
        c2 = client.post("/api/commits/", json={"sha": "later00", "committed_at": "2024-06-01T00:00:00Z"}).json()
        client.post(f"/api/tickets/{ticket['id']}/commits", json={"ids": [c2["id"], c1["id"]]})
        r = client.get(f"/api/tickets/{ticket['id']}/traceability")
        shas = [c["sha"] for c in r.json()["commits"]]
        assert shas[0].startswith("early")
        assert shas[1].startswith("later")
