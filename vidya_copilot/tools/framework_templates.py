"""Framework scaffolding templates for QA automation."""

from __future__ import annotations

SELENIUM_PYTEST_STRUCTURE = {
    "config": {
        "__init__.py": "",
        "settings.py": '''"""Framework configuration."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
BROWSER = os.getenv("BROWSER", "chrome")
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
BASE_URL = os.getenv("BASE_URL", "https://example.com")
IMPLICIT_WAIT = int(os.getenv("IMPLICIT_WAIT", "10"))
''',
    },
    "pages": {
        "__init__.py": "",
        "base_page.py": '''"""Base Page Object."""
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class BasePage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)

    def open(self, path: str = "/") -> None:
        from config.settings import BASE_URL
        self.driver.get(f"{BASE_URL}{path}")

    def find(self, locator):
        return self.wait.until(EC.visibility_of_element_located(locator))
''',
        "login_page.py": '''"""Login Page Object."""
from selenium.webdriver.common.by import By
from pages.base_page import BasePage


class LoginPage(BasePage):
    USERNAME = (By.ID, "username")
    PASSWORD = (By.ID, "password")
    SUBMIT = (By.CSS_SELECTOR, "button[type='submit']")

    def login(self, username: str, password: str) -> None:
        self.open("/login")
        self.find(self.USERNAME).send_keys(username)
        self.find(self.PASSWORD).send_keys(password)
        self.find(self.SUBMIT).click()
''',
    },
    "tests": {
        "__init__.py": "",
        "conftest.py": '''"""Pytest fixtures."""
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from config.settings import HEADLESS


@pytest.fixture
def driver():
    options = Options()
    if HEADLESS:
        options.add_argument("--headless=new")
    browser = webdriver.Chrome(options=options)
    browser.maximize_window()
    yield browser
    browser.quit()
''',
        "test_login.py": '''"""Login tests."""
import allure
from pages.login_page import LoginPage


@allure.feature("Authentication")
@allure.story("Login")
def test_valid_login(driver):
    page = LoginPage(driver)
    page.login("testuser", "password123")
    assert "dashboard" in driver.current_url
''',
    },
    ".github": {
        "workflows": {
            "ci.yml": '''name: Selenium CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v --alluredir=allure-results
      - uses: actions/upload-artifact@v4
        with:
          name: allure-results
          path: allure-results
''',
        },
    },
    "requirements.txt": (
        "selenium>=4.27.0\npytest>=8.3.0\npytest-html>=4.1.0\n"
        "allure-pytest>=2.13.0\nwebdriver-manager>=4.0.0\n"
    ),
    "pytest.ini": "[pytest]\ntestpaths = tests\naddopts = -v --tb=short\n",
    "README.md": "# Selenium Python Framework\n\nPytest + POM + Allure + CI\n",
}

PLAYWRIGHT_PYTHON_STRUCTURE = {
    "pages": {
        "__init__.py": "",
        "login_page.py": '''"""Playwright Login Page."""
from playwright.sync_api import Page


class LoginPage:
    def __init__(self, page: Page):
        self.page = page
        self.username = page.locator("#username")
        self.password = page.locator("#password")
        self.submit = page.locator("button[type='submit']")

    def login(self, username: str, password: str) -> None:
        self.page.goto("/login")
        self.username.fill(username)
        self.password.fill(password)
        self.submit.click()
''',
    },
    "tests": {
        "test_login.py": '''"""Playwright login test."""
import pytest
from pages.login_page import LoginPage


def test_login(page, base_url):
    login = LoginPage(page)
    login.login("user", "pass")
    assert "dashboard" in page.url
''',
        "conftest.py": '''import pytest


@pytest.fixture(scope="session")
def base_url():
    return "https://example.com"
''',
    },
    "playwright.config.py": '''from playwright.sync_api import sync_playwright

def pytest_configure(config):
    pass
''',
    "requirements.txt": "playwright>=1.49.0\npytest>=8.3.0\npytest-playwright>=0.5.0\n",
    "README.md": "# Playwright Python Framework\n",
}

API_FRAMEWORK_STRUCTURE = {
    "clients": {
        "__init__.py": "",
        "base_client.py": '''"""Base API client."""
import httpx


class BaseAPIClient:
    def __init__(self, base_url: str, token: str | None = None):
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self.client = httpx.Client(base_url=base_url, headers=headers, timeout=30.0)

    def get(self, path: str, **kwargs):
        return self.client.get(path, **kwargs)

    def post(self, path: str, **kwargs):
        return self.client.post(path, **kwargs)
''',
        "user_client.py": '''"""User API client."""
from clients.base_client import BaseAPIClient


class UserClient(BaseAPIClient):
    def get_user(self, user_id: int):
        return self.get(f"/users/{user_id}")

    def create_user(self, payload: dict):
        return self.post("/users", json=payload)
''',
    },
    "tests": {
        "test_users_api.py": '''"""User API tests."""
import pytest
from clients.user_client import UserClient


@pytest.fixture
def api_client():
    client = UserClient("https://jsonplaceholder.typicode.com")
    yield client
    client.client.close()


def test_get_user(api_client):
    response = api_client.get_user(1)
    assert response.status_code == 200
    assert response.json()["id"] == 1
''',
    },
    "requirements.txt": "httpx>=0.28.0\npytest>=8.3.0\n",
    "README.md": "# API Automation Framework\n",
}


def get_framework_structure(framework_type: str) -> dict:
    mapping = {
        "selenium": SELENIUM_PYTEST_STRUCTURE,
        "playwright": PLAYWRIGHT_PYTHON_STRUCTURE,
        "api": API_FRAMEWORK_STRUCTURE,
    }
    return mapping.get(framework_type.lower(), SELENIUM_PYTEST_STRUCTURE)
