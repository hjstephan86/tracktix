"""
End-to-End browser tests using Playwright (sync API).

Each test gets a *fresh browser context* (not just a new page) so that
session storage, cookies, and – crucially – any unclosed modal from a
previous test cannot bleed through.
"""
import pytest
from playwright.sync_api import sync_playwright, Page, expect

BASE = "http://127.0.0.1:8765"


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def browser_instance(live_server):
    """One Chromium browser for the whole session."""
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture
def page(browser_instance):
    """Fresh context + page per test – no modal / state bleed."""
    ctx = browser_instance.new_context(base_url=BASE)
    p = ctx.new_page()
    p.goto(BASE)
    p.wait_for_selector("#sidebar", timeout=8000)
    p.wait_for_selector("#page-dashboard.active", timeout=8000)
    p.wait_for_timeout(200)
    yield p
    p.close()
    ctx.close()


# ── Helpers ───────────────────────────────────────────────────────────────────

def nav(page: Page, section: str):
    page.locator(f"#sidebar nav a[data-page='{section}']").click()
    page.wait_for_selector(f"#page-{section}.active", timeout=5000)
    page.wait_for_timeout(150)


def dismiss_modal(page: Page):
    """Close any open modal safely."""
    if page.locator(".modal-backdrop").count() > 0:
        page.locator(".modal-close").first.click()
        page.wait_for_timeout(200)


def fill_and_create_project(page: Page, key: str, name: str,
                             desc: str = "desc", git: str = "https://github.com/x/y"):
    nav(page, "projects")
    page.locator("button:has-text('Neues Projekt')").click()
    page.wait_for_selector(".modal", timeout=3000)
    page.locator("#nproj-key").fill(key)
    page.locator("#nproj-name").fill(name)
    page.locator("#nproj-desc").fill(desc)
    page.locator("#nproj-git").fill(git)
    page.locator("button:has-text('Erstellen')").click()
    page.wait_for_timeout(500)
    assert page.locator(".modal-backdrop").count() == 0, "Modal did not close after create"


def fill_and_create_ticket(page: Page, title: str, status: str = "open",
                            priority: str = "medium"):
    nav(page, "tickets")
    page.locator("button:has-text('Neues Ticket')").click()
    page.wait_for_selector(".modal", timeout=3000)
    page.locator("#nt-title").fill(title)
    page.locator("#nt-desc").fill("E2E test description")
    page.locator("#nt-status").select_option(status)
    page.locator("#nt-priority").select_option(priority)
    page.locator("button:has-text('Ticket erstellen')").click()
    page.wait_for_timeout(500)
    assert page.locator(".modal-backdrop").count() == 0, "Modal did not close after ticket create"


def fill_and_create_person(page: Page, username: str, name: str = "",
                            email: str = "", git: str = ""):
    nav(page, "persons")
    page.locator("button:has-text('Person hinzufügen')").click()
    page.wait_for_selector(".modal", timeout=3000)
    page.locator("#np-user").fill(username)
    if name:  page.locator("#np-name").fill(name)
    if email: page.locator("#np-email").fill(email)
    if git:   page.locator("#np-git").fill(git)
    page.locator("button:has-text('Speichern')").click()
    page.wait_for_timeout(500)
    assert page.locator(".modal-backdrop").count() == 0


def fill_and_create_commit(page: Page, sha: str, msg: str = "fix: something",
                            git_url: str = ""):
    nav(page, "commits")
    page.locator("button:has-text('Commit erfassen')").click()
    page.wait_for_selector(".modal", timeout=3000)
    page.locator("#nc-sha").fill(sha)
    page.locator("#nc-msg").fill(msg)
    if git_url:
        page.locator("#nc-url").fill(git_url)
    page.locator("button:has-text('Speichern')").click()
    page.wait_for_timeout(500)
    assert page.locator(".modal-backdrop").count() == 0


def fill_and_create_test(page: Page, title: str, test_type: str = "unit",
                          result: str = "pending"):
    nav(page, "tests")
    page.locator("button:has-text('Neuer Test')").click()
    page.wait_for_selector(".modal", timeout=3000)
    page.locator("#ntest-title").fill(title)
    page.locator("#ntest-type").select_option(test_type)
    page.locator("#ntest-result").select_option(result)
    page.locator("button:has-text('Speichern')").click()
    page.wait_for_timeout(500)
    assert page.locator(".modal-backdrop").count() == 0


def fill_and_create_requirement(page: Page, key: str, title: str,
                                 url: str = "", desc: str = ""):
    nav(page, "requirements")
    page.locator("button:has-text('Neue Anforderung')").click()
    page.wait_for_selector(".modal", timeout=3000)
    page.locator("#nr-key").fill(key)
    page.locator("#nr-title").fill(title)
    if desc: page.locator("#nr-desc").fill(desc)
    if url:  page.locator("#nr-url").fill(url)
    page.locator("button:has-text('Speichern')").click()
    page.wait_for_timeout(500)
    assert page.locator(".modal-backdrop").count() == 0


# ══════════════════════════════════════════════════════════════════════════════
# Dashboard
# ══════════════════════════════════════════════════════════════════════════════

class TestDashboard:

    def test_dashboard_renders_metrics_grid(self, page):
        assert page.locator(".metrics").count() == 1

    def test_dashboard_has_at_least_6_metric_tiles(self, page):
        assert page.locator(".metric").count() >= 6

    def test_dashboard_tickets_label_exists(self, page):
        assert page.locator(".label:has-text('Tickets gesamt')").count() == 1

    def test_dashboard_shows_ticket_table(self, page):
        assert page.locator("table").count() >= 1

    def test_dashboard_shows_commits_metric(self, page):
        assert page.locator(".label:has-text('Commits')").count() == 1

    def test_dashboard_shows_requirements_metric(self, page):
        assert page.locator(".label:has-text('Anforderungen')").count() == 1

    def test_dashboard_shows_tests_metric(self, page):
        assert page.locator(".label:has-text('Tests')").count() == 1


# ══════════════════════════════════════════════════════════════════════════════
# Navigation
# ══════════════════════════════════════════════════════════════════════════════

class TestNavigation:

    def test_navigate_to_tickets(self, page):
        nav(page, "tickets")
        assert page.locator("#page-tickets.active").count() == 1
        assert page.locator("a[data-page='tickets'].active").count() == 1

    def test_navigate_to_requirements(self, page):
        nav(page, "requirements")
        assert page.locator("#page-requirements.active").count() == 1

    def test_navigate_to_commits(self, page):
        nav(page, "commits")
        assert page.locator("#page-commits.active").count() == 1

    def test_navigate_to_tests(self, page):
        nav(page, "tests")
        assert page.locator("#page-tests.active").count() == 1

    def test_navigate_to_persons(self, page):
        nav(page, "persons")
        assert page.locator("#page-persons.active").count() == 1

    def test_navigate_to_projects(self, page):
        nav(page, "projects")
        assert page.locator("#page-projects.active").count() == 1

    def test_navigate_back_to_dashboard(self, page):
        nav(page, "tickets")
        nav(page, "dashboard")
        assert page.locator("#page-dashboard.active").count() == 1

    def test_sidebar_logo_visible(self, page):
        assert "TrackTix" in page.locator(".logo").inner_text()

    def test_api_docs_link_exists(self, page):
        assert page.locator("a[href='/docs']").count() >= 1

    def test_project_filter_dropdown_exists(self, page):
        assert page.locator("#project-filter").count() == 1

    def test_topbar_rendered(self, page):
        assert page.locator("#topbar").count() == 1


# ══════════════════════════════════════════════════════════════════════════════
# Projects
# ══════════════════════════════════════════════════════════════════════════════

class TestProjectsUI:

    def test_projects_page_loads(self, page):
        nav(page, "projects")
        assert page.locator("button:has-text('Neues Projekt')").count() == 1

    def test_create_project_appears_in_list(self, page):
        fill_and_create_project(page, "SHOWP", "Shown Project")
        nav(page, "projects")
        page.wait_for_timeout(300)
        assert page.locator("text=Shown Project").count() >= 1

    def test_project_key_displayed(self, page):
        fill_and_create_project(page, "KEYP", "Key Project")
        nav(page, "projects")
        page.wait_for_timeout(300)
        assert page.locator(".ticket-key:has-text('KEYP')").count() >= 1

    def test_project_git_url_as_link(self, page):
        fill_and_create_project(page, "GITP", "Git Project",
                                 git="https://github.com/git/repo")
        nav(page, "projects")
        page.wait_for_timeout(300)
        assert page.locator("a[href='https://github.com/git/repo']").count() >= 1

    def test_project_description_shown(self, page):
        fill_and_create_project(page, "DESCP", "Desc Project", desc="My description here")
        nav(page, "projects")
        page.wait_for_timeout(300)
        assert page.locator("text=My description here").count() >= 1

    def test_cancel_project_modal_closes(self, page):
        nav(page, "projects")
        page.locator("button:has-text('Neues Projekt')").click()
        page.wait_for_selector(".modal")
        page.locator("button:has-text('Abbrechen')").click()
        page.wait_for_timeout(200)
        assert page.locator(".modal-backdrop").count() == 0

    def test_close_project_modal_via_x_button(self, page):
        nav(page, "projects")
        page.locator("button:has-text('Neues Projekt')").click()
        page.wait_for_selector(".modal")
        page.locator(".modal-close").first.click()
        page.wait_for_timeout(200)
        assert page.locator(".modal-backdrop").count() == 0

    def test_edit_project_changes_name(self, page):
        fill_and_create_project(page, "EDTP", "Edit Original")
        nav(page, "projects")
        page.wait_for_timeout(300)
        page.locator(".card:has-text('Edit Original') button:has-text('✏️')").click()
        page.wait_for_selector(".modal", timeout=3000)
        page.locator("#ep-pname").clear()
        page.locator("#ep-pname").fill("Edit Updated")
        page.locator("button:has-text('Speichern')").click()
        page.wait_for_timeout(500)
        assert page.locator(".modal-backdrop").count() == 0
        nav(page, "projects")
        page.wait_for_timeout(300)
        assert page.locator("text=Edit Updated").count() >= 1

    def test_delete_project(self, page):
        fill_and_create_project(page, "DELP", "Delete Me Project")
        nav(page, "projects")
        page.wait_for_timeout(300)
        page.once("dialog", lambda d: d.accept())
        page.locator(".card:has-text('Delete Me Project') button:has-text('🗑')").click()
        page.wait_for_timeout(500)
        assert page.locator("text=Delete Me Project").count() == 0

    def test_project_filter_populated(self, page):
        fill_and_create_project(page, "FILTX", "Filter Project X")
        nav(page, "tickets")
        page.wait_for_timeout(300)
        opts = page.locator("#project-filter option")
        texts = [opts.nth(i).inner_text() for i in range(opts.count())]
        assert any("FILTX" in t for t in texts)


# ══════════════════════════════════════════════════════════════════════════════
# Requirements
# ══════════════════════════════════════════════════════════════════════════════

class TestRequirementsUI:

    def test_requirements_page_loads(self, page):
        nav(page, "requirements")
        assert page.locator("button:has-text('Neue Anforderung')").count() == 1

    def test_create_requirement_appears_in_table(self, page):
        fill_and_create_project(page, "REQP", "Req Project")
        fill_and_create_requirement(page, "SRS-E01", "System shall do E2E")
        nav(page, "requirements")
        page.wait_for_timeout(300)
        assert page.locator("text=SRS-E01").count() >= 1

    def test_requirement_title_shown(self, page):
        fill_and_create_project(page, "REQT", "Req Title Project")
        fill_and_create_requirement(page, "SRS-T01", "Requirement Title E2E")
        nav(page, "requirements")
        page.wait_for_timeout(300)
        assert page.locator("text=Requirement Title E2E").count() >= 1

    def test_requirement_url_shown_as_link(self, page):
        fill_and_create_project(page, "REQU", "Req URL Project")
        fill_and_create_requirement(page, "SRS-U01", "URL Requirement",
                                     url="https://myspec.example.com/SRS-U01")
        nav(page, "requirements")
        page.wait_for_timeout(300)
        assert page.locator("a:has-text('🔗 Öffnen')").count() >= 1

    def test_requirement_without_url_shows_dash(self, page):
        fill_and_create_project(page, "REQD", "Req Dash Project")
        fill_and_create_requirement(page, "SRS-D01", "No URL Requirement")
        nav(page, "requirements")
        page.wait_for_timeout(300)
        assert page.locator("td:has-text('–')").count() >= 1

    def test_cancel_requirement_modal(self, page):
        nav(page, "requirements")
        page.locator("button:has-text('Neue Anforderung')").click()
        page.wait_for_selector(".modal")
        page.locator("button:has-text('Abbrechen')").click()
        page.wait_for_timeout(200)
        assert page.locator(".modal-backdrop").count() == 0

    def test_edit_requirement(self, page):
        fill_and_create_project(page, "REQE", "Req Edit Project")
        fill_and_create_requirement(page, "SRS-E02", "Original Req Title")
        nav(page, "requirements")
        page.wait_for_timeout(300)
        page.locator("tr:has-text('SRS-E02') button:has-text('✏️')").click()
        page.wait_for_selector(".modal", timeout=3000)
        page.locator("#er-title").clear()
        page.locator("#er-title").fill("Updated Req Title")
        page.locator("button:has-text('Speichern')").click()
        page.wait_for_timeout(500)
        assert page.locator(".modal-backdrop").count() == 0
        nav(page, "requirements")
        page.wait_for_timeout(300)
        assert page.locator("text=Updated Req Title").count() >= 1

    def test_delete_requirement(self, page):
        fill_and_create_project(page, "REQX", "Req Delete Project")
        fill_and_create_requirement(page, "SRS-DEL", "Delete This Requirement")
        nav(page, "requirements")
        page.wait_for_timeout(300)
        page.once("dialog", lambda d: d.accept())
        page.locator("tr:has-text('SRS-DEL') button:has-text('🗑')").click()
        page.wait_for_timeout(500)
        nav(page, "requirements")
        page.wait_for_timeout(300)
        assert page.locator("text=Delete This Requirement").count() == 0

    def test_requirement_key_is_monospace(self, page):
        fill_and_create_project(page, "REQM", "Req Mono Project")
        fill_and_create_requirement(page, "SRS-M01", "Mono Key Req")
        nav(page, "requirements")
        page.wait_for_timeout(300)
        assert page.locator(".ticket-key:has-text('SRS-M01')").count() >= 1


# ══════════════════════════════════════════════════════════════════════════════
# Persons
# ══════════════════════════════════════════════════════════════════════════════

class TestPersonsUI:

    def test_persons_page_loads(self, page):
        nav(page, "persons")
        assert page.locator("button:has-text('Person hinzufügen')").count() == 1

    def test_create_person_username_shown(self, page):
        fill_and_create_person(page, "pw_user_a", "Alice A", "a@test.com",
                                "https://github.com/alice")
        nav(page, "persons")
        page.wait_for_timeout(300)
        assert page.locator("text=pw_user_a").count() >= 1

    def test_create_person_full_name_shown(self, page):
        fill_and_create_person(page, "pw_user_b", "Bob Builder")
        nav(page, "persons")
        page.wait_for_timeout(300)
        assert page.locator("text=Bob Builder").count() >= 1

    def test_create_person_email_as_mailto_link(self, page):
        fill_and_create_person(page, "pw_user_c", email="carol@example.com")
        nav(page, "persons")
        page.wait_for_timeout(300)
        assert page.locator("a[href='mailto:carol@example.com']").count() >= 1

    def test_create_person_git_server_as_link(self, page):
        fill_and_create_person(page, "pw_user_d", git="https://gitlab.com/dave")
        nav(page, "persons")
        page.wait_for_timeout(300)
        assert page.locator("a[href='https://gitlab.com/dave']").count() >= 1

    def test_cancel_person_modal(self, page):
        nav(page, "persons")
        page.locator("button:has-text('Person hinzufügen')").click()
        page.wait_for_selector(".modal")
        page.locator("button:has-text('Abbrechen')").click()
        page.wait_for_timeout(200)
        assert page.locator(".modal-backdrop").count() == 0

    def test_edit_person_name(self, page):
        fill_and_create_person(page, "pw_edit_user", "Old Name Edit")
        nav(page, "persons")
        page.wait_for_timeout(300)
        page.locator("tr:has-text('pw_edit_user') button:has-text('✏️')").click()
        page.wait_for_selector(".modal", timeout=3000)
        page.locator("#ep-name").clear()
        page.locator("#ep-name").fill("New Name Updated")
        page.locator("button:has-text('Speichern')").click()
        page.wait_for_timeout(500)
        assert page.locator(".modal-backdrop").count() == 0
        nav(page, "persons")
        page.wait_for_timeout(300)
        assert page.locator("text=New Name Updated").count() >= 1

    def test_delete_person(self, page):
        fill_and_create_person(page, "pw_del_user", "Delete Me")
        nav(page, "persons")
        page.wait_for_timeout(300)
        page.once("dialog", lambda d: d.accept())
        page.locator("tr:has-text('pw_del_user') button:has-text('🗑')").click()
        page.wait_for_timeout(500)
        nav(page, "persons")
        page.wait_for_timeout(300)
        assert page.locator("text=pw_del_user").count() == 0

    def test_person_without_git_shows_dash(self, page):
        fill_and_create_person(page, "pw_no_git_user")
        nav(page, "persons")
        page.wait_for_timeout(300)
        assert page.locator("td:has-text('–')").count() >= 1


# ══════════════════════════════════════════════════════════════════════════════
# Commits
# ══════════════════════════════════════════════════════════════════════════════

class TestCommitsUI:

    def test_commits_page_loads(self, page):
        nav(page, "commits")
        assert page.locator("button:has-text('Commit erfassen')").count() == 1

    def test_create_commit_sha_shown(self, page):
        fill_and_create_commit(page, "aabbccdd1122")
        nav(page, "commits")
        page.wait_for_timeout(300)
        assert page.locator("text=aabbccdd11").count() >= 1

    def test_create_commit_message_shown(self, page):
        fill_and_create_commit(page, "deadbeef0001", "feat: add traceability feature")
        nav(page, "commits")
        page.wait_for_timeout(300)
        assert page.locator("text=feat: add traceability feature").count() >= 1

    def test_commit_with_url_renders_as_link(self, page):
        fill_and_create_commit(page, "linksha00001", "fix: bug",
                                git_url="https://github.com/org/repo/commit/linksha00001")
        nav(page, "commits")
        page.wait_for_timeout(300)
        assert page.locator("a.sha-link").count() >= 1

    def test_cancel_commit_modal(self, page):
        nav(page, "commits")
        page.locator("button:has-text('Commit erfassen')").click()
        page.wait_for_selector(".modal")
        page.locator("button:has-text('Abbrechen')").click()
        page.wait_for_timeout(200)
        assert page.locator(".modal-backdrop").count() == 0

    def test_delete_commit(self, page):
        fill_and_create_commit(page, "delcommit9999", "del: remove feature")
        nav(page, "commits")
        page.wait_for_timeout(300)
        # Register dialog handler before clicking
        page.once("dialog", lambda d: d.accept())
        page.locator("tr:has-text('del: remove feature') button:has-text('🗑')").click()
        page.wait_for_timeout(600)
        nav(page, "commits")
        page.wait_for_timeout(300)
        assert page.locator("text=del: remove feature").count() == 0

    def test_commit_without_url_shows_plain_sha(self, page):
        # sha.slice(0,10) → first 10 chars of "plainsha12" = "plainsha12"
        fill_and_create_commit(page, "plainsha1234567", "plain commit no url")
        nav(page, "commits")
        page.wait_for_timeout(300)
        assert page.locator("text=plainsha12").count() >= 1

    def test_commit_with_person_author_shown(self, page):
        fill_and_create_person(page, "commit_author_x", "Author X")
        nav(page, "commits")
        page.locator("button:has-text('Commit erfassen')").click()
        page.wait_for_selector(".modal")
        page.locator("#nc-sha").fill("authorsha12345")
        # select by value (person id) via partial text match using JS
        author_sel = page.locator("#nc-author")
        options = author_sel.locator("option")
        for i in range(options.count()):
            if "commit_author_x" in options.nth(i).inner_text():
                val = options.nth(i).get_attribute("value")
                author_sel.select_option(value=val)
                break
        page.locator("button:has-text('Speichern')").click()
        page.wait_for_timeout(500)
        nav(page, "commits")
        page.wait_for_timeout(300)
        assert page.locator("text=commit_author_x").count() >= 1


# ══════════════════════════════════════════════════════════════════════════════
# Tests page
# ══════════════════════════════════════════════════════════════════════════════

class TestTestsUI:

    def test_tests_page_loads(self, page):
        nav(page, "tests")
        assert page.locator("button:has-text('Neuer Test')").count() == 1

    def test_create_unit_test_shown(self, page):
        fill_and_create_test(page, "Unit Test E2E Alpha", "unit", "passed")
        nav(page, "tests")
        page.wait_for_timeout(300)
        assert page.locator("text=Unit Test E2E Alpha").count() >= 1

    def test_create_integration_test(self, page):
        fill_and_create_test(page, "Integration Test Beta", "integration", "failed")
        nav(page, "tests")
        page.wait_for_timeout(300)
        assert page.locator(".badge-integration").count() >= 1

    def test_create_system_test(self, page):
        fill_and_create_test(page, "System Test Gamma", "system", "pending")
        nav(page, "tests")
        page.wait_for_timeout(300)
        assert page.locator(".badge-system").count() >= 1

    def test_passed_result_badge(self, page):
        fill_and_create_test(page, "Pass Badge Test", result="passed")
        nav(page, "tests")
        page.wait_for_timeout(300)
        assert page.locator(".badge-passed").count() >= 1

    def test_failed_result_badge(self, page):
        fill_and_create_test(page, "Fail Badge Test", result="failed")
        nav(page, "tests")
        page.wait_for_timeout(300)
        assert page.locator(".badge-failed").count() >= 1

    def test_pending_result_badge(self, page):
        fill_and_create_test(page, "Pending Badge Test", result="pending")
        nav(page, "tests")
        page.wait_for_timeout(300)
        assert page.locator(".badge-pending").count() >= 1

    def test_cancel_test_modal(self, page):
        nav(page, "tests")
        page.locator("button:has-text('Neuer Test')").click()
        page.wait_for_selector(".modal")
        page.locator("button:has-text('Abbrechen')").click()
        page.wait_for_timeout(200)
        assert page.locator(".modal-backdrop").count() == 0

    def test_edit_test_result(self, page):
        fill_and_create_test(page, "Editable E2E Test", result="pending")
        nav(page, "tests")
        page.wait_for_timeout(300)
        page.locator("tr:has-text('Editable E2E Test') button:has-text('✏️')").click()
        page.wait_for_selector(".modal", timeout=3000)
        page.locator("#etest-result").select_option("passed")
        page.locator("button:has-text('Speichern')").click()
        page.wait_for_timeout(500)
        assert page.locator(".modal-backdrop").count() == 0

    def test_delete_test(self, page):
        fill_and_create_test(page, "Deletable Test ZZZDEL")
        nav(page, "tests")
        page.wait_for_timeout(300)
        page.once("dialog", lambda d: d.accept())
        page.locator("tr:has-text('Deletable Test ZZZDEL') button:has-text('🗑')").click()
        page.wait_for_timeout(500)
        nav(page, "tests")
        page.wait_for_timeout(300)
        assert page.locator("text=Deletable Test ZZZDEL").count() == 0

    def test_test_with_tester_person(self, page):
        fill_and_create_person(page, "tester_person_x")
        nav(page, "tests")
        page.locator("button:has-text('Neuer Test')").click()
        page.wait_for_selector(".modal")
        page.locator("#ntest-title").fill("Tester Person Test")
        page.locator("#ntest-tester").select_option(label="tester_person_x")
        page.locator("button:has-text('Speichern')").click()
        page.wait_for_timeout(500)
        nav(page, "tests")
        page.wait_for_timeout(300)
        assert page.locator("text=tester_person_x").count() >= 1

    def test_edit_test_type(self, page):
        fill_and_create_test(page, "Type Change Test", test_type="unit")
        nav(page, "tests")
        page.wait_for_timeout(300)
        page.locator("tr:has-text('Type Change Test') button:has-text('✏️')").click()
        page.wait_for_selector(".modal", timeout=3000)
        page.locator("#etest-type").select_option("system")
        page.locator("button:has-text('Speichern')").click()
        page.wait_for_timeout(500)
        nav(page, "tests")
        page.wait_for_timeout(300)
        assert page.locator(".badge-system").count() >= 1


# ══════════════════════════════════════════════════════════════════════════════
# Tickets
# ══════════════════════════════════════════════════════════════════════════════

class TestTicketsUI:

    def test_tickets_page_loads(self, page):
        nav(page, "tickets")
        assert page.locator("button:has-text('Neues Ticket')").count() == 1

    def test_create_ticket_appears_in_table(self, page):
        fill_and_create_project(page, "TKA", "Ticket Project A")
        fill_and_create_ticket(page, "Ticket Alpha Created")
        nav(page, "tickets")
        page.wait_for_timeout(300)
        assert page.locator("text=Ticket Alpha Created").count() >= 1

    def test_ticket_key_format_shown(self, page):
        fill_and_create_project(page, "TKK", "Ticket Project K")
        fill_and_create_ticket(page, "Key Ticket Test")
        nav(page, "tickets")
        page.wait_for_timeout(300)
        assert page.locator(".ticket-key").count() >= 1

    def test_ticket_status_badge_in_progress(self, page):
        fill_and_create_project(page, "TKS", "Ticket Project S")
        fill_and_create_ticket(page, "Status Ticket", status="in_progress")
        nav(page, "tickets")
        page.wait_for_timeout(300)
        assert page.locator(".badge-in_progress").count() >= 1

    def test_ticket_priority_badge_high(self, page):
        fill_and_create_project(page, "TKP", "Ticket Project P")
        fill_and_create_ticket(page, "Priority Ticket", priority="high")
        nav(page, "tickets")
        page.wait_for_timeout(300)
        assert page.locator(".badge-high").count() >= 1

    def test_ticket_priority_badge_critical(self, page):
        fill_and_create_project(page, "TKPC", "Ticket Project PC")
        fill_and_create_ticket(page, "Critical Ticket", priority="critical")
        nav(page, "tickets")
        page.wait_for_timeout(300)
        assert page.locator(".badge-critical").count() >= 1

    def test_cancel_ticket_modal(self, page):
        nav(page, "tickets")
        page.locator("button:has-text('Neues Ticket')").click()
        page.wait_for_selector(".modal")
        page.locator("button:has-text('Abbrechen')").click()
        page.wait_for_timeout(200)
        assert page.locator(".modal-backdrop").count() == 0

    def test_ticket_search_filter(self, page):
        fill_and_create_project(page, "TKSF", "Search Filter Project")
        fill_and_create_ticket(page, "Unique Search XYZABC")
        fill_and_create_ticket(page, "Other Ticket DEFGH")
        nav(page, "tickets")
        page.wait_for_timeout(300)
        page.locator("#ticket-search").fill("XYZABC")
        page.wait_for_timeout(300)
        assert page.locator("text=Unique Search XYZABC").count() >= 1
        assert page.locator("text=Other Ticket DEFGH").count() == 0

    def test_ticket_status_filter(self, page):
        fill_and_create_project(page, "TKSTF", "Status Filter Project")
        fill_and_create_ticket(page, "Status Filter Ticket", status="testing")
        fill_and_create_ticket(page, "Open One", status="open")
        nav(page, "tickets")
        page.wait_for_timeout(300)
        page.locator("#ticket-status-filter").select_option("testing")
        page.wait_for_timeout(300)
        assert page.locator(".badge-testing").count() >= 1
        assert page.locator("text=Open One").count() == 0

    def test_ticket_priority_filter(self, page):
        fill_and_create_project(page, "TKPRF", "Priority Filter Project")
        fill_and_create_ticket(page, "Low Ticket", priority="low")
        fill_and_create_ticket(page, "High Priority", priority="high")
        nav(page, "tickets")
        page.wait_for_timeout(300)
        page.locator("#ticket-priority-filter").select_option("low")
        page.wait_for_timeout(300)
        assert page.locator(".badge-low").count() >= 1
        assert page.locator("text=High Priority").count() == 0

    def test_open_ticket_detail_modal(self, page):
        fill_and_create_project(page, "TKDET", "Detail Project")
        fill_and_create_ticket(page, "Detail Modal Ticket")
        nav(page, "tickets")
        page.wait_for_timeout(300)
        page.locator("tbody tr").last.click()
        page.wait_for_selector(".modal", timeout=4000)
        assert page.locator(".modal").count() >= 1

    def test_ticket_detail_shows_key(self, page):
        fill_and_create_project(page, "TKDKY", "Detail Key Project")
        fill_and_create_ticket(page, "Key Detail Ticket")
        nav(page, "tickets")
        page.wait_for_timeout(300)
        page.locator("tbody tr").last.click()
        page.wait_for_selector(".modal", timeout=4000)
        assert page.locator(".ticket-key").count() >= 1

    def test_ticket_detail_has_tabs(self, page):
        fill_and_create_project(page, "TKTAB", "Tab Project")
        fill_and_create_ticket(page, "Tab Test Ticket")
        nav(page, "tickets")
        page.wait_for_timeout(300)
        page.locator("tbody tr").last.click()
        page.wait_for_selector(".modal", timeout=4000)
        for tab in ["Details", "Traceability", "Commits", "Tests", "Kommentare"]:
            assert page.locator(f".tab:has-text('{tab}')").count() >= 1

    def test_ticket_detail_switch_to_traceability_tab(self, page):
        fill_and_create_project(page, "TKTR", "Trace Project")
        fill_and_create_ticket(page, "Trace Ticket")
        nav(page, "tickets")
        page.wait_for_timeout(300)
        page.locator("tbody tr").last.click()
        page.wait_for_selector(".modal", timeout=4000)
        page.locator(".tab:has-text('Traceability')").click()
        page.wait_for_timeout(200)
        assert page.locator(".tab.active:has-text('Traceability')").count() == 1

    def test_ticket_traceability_shows_anforderungen_label(self, page):
        fill_and_create_project(page, "TKTRL", "Trace Label Project")
        fill_and_create_ticket(page, "Trace Label Ticket")
        nav(page, "tickets")
        page.wait_for_timeout(300)
        page.locator("tbody tr").last.click()
        page.wait_for_selector(".modal", timeout=4000)
        page.locator(".tab:has-text('Traceability')").click()
        page.wait_for_timeout(200)
        assert page.locator("text=ANFORDERUNGEN").count() >= 1

    def test_ticket_detail_switch_to_commits_tab(self, page):
        fill_and_create_project(page, "TKCMT", "Commit Tab Project")
        fill_and_create_ticket(page, "Commit Tab Ticket")
        nav(page, "tickets")
        page.wait_for_timeout(300)
        page.locator("tbody tr").last.click()
        page.wait_for_selector(".modal", timeout=4000)
        page.locator(".tab:has-text('Commits')").click()
        page.wait_for_timeout(200)
        assert page.locator(".tab.active:has-text('Commits')").count() == 1

    def test_ticket_detail_switch_to_tests_tab(self, page):
        fill_and_create_project(page, "TKTST", "Tests Tab Project")
        fill_and_create_ticket(page, "Tests Tab Ticket")
        nav(page, "tickets")
        page.wait_for_timeout(300)
        page.locator("tbody tr").last.click()
        page.wait_for_selector(".modal", timeout=4000)
        page.locator(".tab:has-text('Tests')").click()
        page.wait_for_timeout(200)
        assert page.locator(".tab.active:has-text('Tests')").count() == 1

    def test_ticket_detail_close_via_backdrop(self, page):
        fill_and_create_project(page, "TKBCK", "Backdrop Project")
        fill_and_create_ticket(page, "Backdrop Ticket")
        nav(page, "tickets")
        page.wait_for_timeout(300)
        page.locator("tbody tr").last.click()
        page.wait_for_selector(".modal", timeout=4000)
        page.locator(".modal-backdrop").click(position={"x": 5, "y": 5})
        page.wait_for_timeout(400)
        assert page.locator(".modal-backdrop").count() == 0

    def test_ticket_detail_close_via_x(self, page):
        fill_and_create_project(page, "TKXCL", "X Close Project")
        fill_and_create_ticket(page, "X Close Ticket")
        nav(page, "tickets")
        page.wait_for_timeout(300)
        page.locator("tbody tr").last.click()
        page.wait_for_selector(".modal", timeout=4000)
        page.locator(".modal-close").first.click()
        page.wait_for_timeout(300)
        assert page.locator(".modal-backdrop").count() == 0

    def test_ticket_add_comment(self, page):
        fill_and_create_project(page, "TKCMT2", "Comment Project")
        fill_and_create_ticket(page, "Comment Ticket")
        nav(page, "tickets")
        page.wait_for_timeout(300)
        page.locator("tbody tr").last.click()
        page.wait_for_selector(".modal", timeout=4000)
        page.locator(".tab:has-text('Kommentare')").click()
        page.wait_for_timeout(200)
        page.locator("#comment-text").fill("This is an E2E test comment")
        page.locator("button:has-text('Kommentar senden')").click()
        page.wait_for_timeout(700)
        assert page.locator("text=This is an E2E test comment").count() >= 1

    def test_ticket_add_comment_with_author(self, page):
        fill_and_create_project(page, "TKCMTA", "Comment Author Project")
        fill_and_create_person(page, "comment_author_e2e")
        fill_and_create_ticket(page, "Comment Author Ticket")
        nav(page, "tickets")
        page.wait_for_timeout(300)
        page.locator("tbody tr:has-text('Comment Author Ticket')").click()
        page.wait_for_selector(".modal", timeout=4000)
        page.locator(".tab:has-text('Kommentare')").click()
        page.wait_for_timeout(200)
        page.locator("#comment-author-sel").select_option(label="comment_author_e2e")
        page.locator("#comment-text").fill("Comment from specific author")
        page.locator("button:has-text('Kommentar senden')").click()
        page.wait_for_timeout(700)
        assert page.locator("text=comment_author_e2e").count() >= 1

    def test_ticket_edit_via_detail_modal(self, page):
        fill_and_create_project(page, "TKEDIT", "Edit Ticket Project")
        fill_and_create_ticket(page, "Original Ticket Title")
        nav(page, "tickets")
        page.wait_for_timeout(300)
        page.locator("tbody tr").last.click()
        page.wait_for_selector(".modal", timeout=4000)
        page.locator("button:has-text('✏️ Bearbeiten')").click()
        page.wait_for_selector("#et-title", timeout=3000)
        page.locator("#et-title").clear()
        page.locator("#et-title").fill("Edited Ticket Title")
        page.locator("#et-status").select_option("closed")
        page.locator("button:has-text('Speichern')").click()
        page.wait_for_timeout(600)
        assert page.locator(".modal-backdrop").count() == 0

    def test_ticket_delete_via_detail_modal(self, page):
        fill_and_create_project(page, "TKDEL", "Delete Ticket Project")
        fill_and_create_ticket(page, "Delete Me Ticket XYZ")
        nav(page, "tickets")
        page.wait_for_timeout(300)
        page.locator("tbody tr:has-text('Delete Me Ticket XYZ')").click()
        page.wait_for_selector(".modal", timeout=4000)
        page.once("dialog", lambda d: d.accept())
        page.locator("button:has-text('🗑 Löschen')").click()
        page.wait_for_timeout(700)
        nav(page, "tickets")
        page.wait_for_timeout(300)
        assert page.locator("text=Delete Me Ticket XYZ").count() == 0

    def test_link_commit_to_ticket(self, page):
        fill_and_create_project(page, "TKLNK", "Link Commit Project")
        fill_and_create_commit(page, "linkcommit99abc", "feat: linked commit")
        fill_and_create_ticket(page, "Link Commit Ticket")
        nav(page, "tickets")
        page.wait_for_timeout(300)
        page.locator("tbody tr:has-text('Link Commit Ticket')").click()
        page.wait_for_selector(".modal", timeout=4000)
        page.locator(".tab:has-text('Commits')").click()
        page.wait_for_timeout(200)
        # Select by value: find option whose text contains our sha
        sel = page.locator("#link-commit-sel")
        options = sel.locator("option")
        for i in range(options.count()):
            if "linkcommit99" in options.nth(i).inner_text():
                val = options.nth(i).get_attribute("value")
                sel.select_option(value=val)
                break
        page.locator(".tab-content.active button:has-text('Verknüpfen')").click()
        page.wait_for_timeout(700)
        assert page.locator("text=feat: linked commit").count() >= 1

    def test_link_test_to_ticket(self, page):
        fill_and_create_project(page, "TKLTST", "Link Test Project")
        fill_and_create_test(page, "Linked Test Object", "integration", "passed")
        fill_and_create_ticket(page, "Link Test Ticket")
        nav(page, "tickets")
        page.wait_for_timeout(300)
        page.locator("tbody tr:has-text('Link Test Ticket')").click()
        page.wait_for_selector(".modal", timeout=4000)
        page.locator(".tab:has-text('Tests')").click()
        page.wait_for_timeout(200)
        sel = page.locator("#link-test-sel")
        options = sel.locator("option")
        for i in range(options.count()):
            if "Linked Test Object" in options.nth(i).inner_text():
                val = options.nth(i).get_attribute("value")
                sel.select_option(value=val)
                break
        page.locator(".tab-content.active button:has-text('Verknüpfen')").click()
        page.wait_for_timeout(700)
        assert page.locator("text=Linked Test Object").count() >= 1

    def test_ticket_with_requirement_linked_shown_in_detail(self, page):
        fill_and_create_project(page, "TKREQ", "Req Link Project")
        fill_and_create_requirement(page, "SRS-LINK", "Linked Requirement")
        nav(page, "tickets")
        page.locator("button:has-text('Neues Ticket')").click()
        page.wait_for_selector(".modal")
        page.locator("#nt-title").fill("Ticket with Requirement")
        # Check the requirement checkbox
        page.locator("#nt-reqs input[type='checkbox']").first.check()
        page.locator("button:has-text('Ticket erstellen')").click()
        page.wait_for_timeout(600)
        nav(page, "tickets")
        page.wait_for_timeout(300)
        page.locator("tbody tr:has-text('Ticket with Requirement')").click()
        page.wait_for_selector(".modal", timeout=4000)
        assert page.locator("text=SRS-LINK").count() >= 1

    def test_ticket_status_all_values(self, page):
        fill_and_create_project(page, "TKALL", "All Status Project")
        for status in ["in_review", "testing", "rejected"]:
            fill_and_create_ticket(page, f"Ticket {status}", status=status)
        nav(page, "tickets")
        page.wait_for_timeout(300)
        assert page.locator(".badge-in_review").count() >= 1
        assert page.locator(".badge-testing").count() >= 1
        assert page.locator(".badge-rejected").count() >= 1

    def test_dashboard_updated_after_ticket_create(self, page):
        fill_and_create_project(page, "TKDSH", "Dashboard Ticket Project")
        fill_and_create_ticket(page, "Dashboard Counter Ticket")
        nav(page, "dashboard")
        page.wait_for_timeout(300)
        # The dashboard "Tickets gesamt" value should be > 0
        value_text = page.locator(".metric .value").first.inner_text()
        assert int(value_text) > 0
