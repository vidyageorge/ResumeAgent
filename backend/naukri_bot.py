"""Naukri.com browser automation for job search and apply."""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright

from backend.config import settings

NAUKRI_LOGIN_URL = "https://www.naukri.com/nlogin/login"
NAUKRI_SEARCH_URL = "https://www.naukri.com/jobs-in-india"


@dataclass
class JobListing:
    title: str
    company: str
    location: str
    experience: str
    url: str
    has_easy_apply: bool = False


@dataclass
class ApplyResult:
    job_title: str
    company: str
    status: str
    message: str


@dataclass
class NaukriSession:
    playwright: Playwright
    browser: Browser
    context: BrowserContext
    page: Page
    is_logged_in: bool = False


class NaukriBot:
    def __init__(self) -> None:
        self._session: NaukriSession | None = None
        self._lock = asyncio.Lock()

    @property
    def is_active(self) -> bool:
        return self._session is not None

    @property
    def is_logged_in(self) -> bool:
        return bool(self._session and self._session.is_logged_in)

    async def start(self) -> str:
        async with self._lock:
            if self._session:
                return "Browser session is already running."

            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=settings.headless)
            context = await browser.new_context(
                viewport={"width": 1280, "height": 900},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            )
            page = await context.new_page()
            self._session = NaukriSession(
                playwright=playwright,
                browser=browser,
                context=context,
                page=page,
            )
            return "Browser started. Use 'login' to sign in to Naukri."

    async def stop(self) -> str:
        async with self._lock:
            if not self._session:
                return "No active browser session."

            session = self._session
            self._session = None
            await session.context.close()
            await session.browser.close()
            await session.playwright.stop()
            return "Browser session closed."

    async def login(self, email: str | None = None, password: str | None = None) -> str:
        async with self._lock:
            page = self._require_page()
            email = email or settings.naukri_email
            password = password or settings.naukri_password

            if not email or not password:
                return (
                    "Naukri credentials missing. Set NAUKRI_EMAIL and NAUKRI_PASSWORD "
                    "in .env or say: login with email@example.com password yourpass"
                )

            await page.goto(NAUKRI_LOGIN_URL, wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)

            username_input = page.locator('input[type="text"], input[name="username"], #usernameField')
            password_input = page.locator('input[type="password"], input[name="password"], #passwordField')

            await username_input.first.fill(email)
            await password_input.first.fill(password)

            login_button = page.locator(
                'button[type="submit"], button:has-text("Login"), .loginButton'
            )
            await login_button.first.click()
            await page.wait_for_timeout(4000)

            if await self._is_logged_in(page):
                self._session.is_logged_in = True
                return f"Logged in to Naukri as {email}."

            return (
                "Login may have failed or needs manual verification (CAPTCHA/OTP). "
                "Complete login in the browser window, then try again."
            )

    async def search_jobs(
        self,
        keywords: str,
        location: str = "",
        experience: str = "",
        max_results: int = 10,
    ) -> list[JobListing]:
        async with self._lock:
            page = self._require_page()
            query = keywords.replace(" ", "-").lower()
            loc = location.replace(" ", "-").lower() if location else ""
            search_url = f"https://www.naukri.com/{query}-jobs"
            if loc:
                search_url += f"-in-{loc}"

            await page.goto(search_url, wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)

            jobs: list[JobListing] = []
            cards = page.locator(".srp-jobtuple-wrapper, .jobTuple, article.jobTuple")
            count = await cards.count()

            for i in range(min(count, max_results)):
                card = cards.nth(i)
                title = await self._safe_text(card, ".title, a.title, .jobTitle")
                company = await self._safe_text(card, ".comp-name, .companyInfo, a.subTitle")
                job_location = await self._safe_text(card, ".locWdth, .location, .loc")
                exp = await self._safe_text(card, ".expwdth, .experience, .exp")
                link_el = card.locator("a.title, a.jobTitle, a").first
                href = await link_el.get_attribute("href") if await link_el.count() else ""
                url = href or ""
                if url and not url.startswith("http"):
                    url = f"https://www.naukri.com{url}"

                easy_apply = await card.locator(
                    ':text("Apply"), :text("Easy Apply"), .apply-button'
                ).count() > 0

                if title:
                    jobs.append(
                        JobListing(
                            title=title.strip(),
                            company=company.strip() or "Unknown",
                            location=job_location.strip() or location or "N/A",
                            experience=exp.strip() or experience or "N/A",
                            url=url,
                            has_easy_apply=easy_apply,
                        )
                    )

            return jobs

    async def apply_to_jobs(
        self,
        keywords: str,
        location: str = "",
        max_applications: int = 5,
    ) -> list[ApplyResult]:
        if not self.is_logged_in:
            return [
                ApplyResult(
                    job_title="",
                    company="",
                    status="error",
                    message="You must be logged in first. Say 'login' to sign in.",
                )
            ]

        jobs = await self.search_jobs(keywords, location, max_results=max_applications * 2)
        if not jobs:
            return [
                ApplyResult(
                    job_title="",
                    company="",
                    status="error",
                    message=f"No jobs found for '{keywords}' in '{location or 'any location'}'.",
                )
            ]

        results: list[ApplyResult] = []
        applied = 0

        for job in jobs:
            if applied >= max_applications:
                break
            if not job.url:
                continue

            result = await self._apply_single_job(job)
            results.append(result)
            if result.status == "applied":
                applied += 1
            await asyncio.sleep(2)

        if not results:
            return [
                ApplyResult(
                    job_title="",
                    company="",
                    status="error",
                    message="Could not apply to any jobs. Try different keywords.",
                )
            ]
        return results

    async def apply_to_url(self, url: str) -> ApplyResult:
        if not self.is_logged_in:
            return ApplyResult(
                job_title="",
                company="",
                status="error",
                message="You must be logged in first.",
            )

        job = JobListing(
            title="Job",
            company="Unknown",
            location="",
            experience="",
            url=url,
        )
        return await self._apply_single_job(job)

    async def _apply_single_job(self, job: JobListing) -> ApplyResult:
        async with self._lock:
            page = self._require_page()
            try:
                await page.goto(job.url, wait_until="domcontentloaded")
                await page.wait_for_timeout(2000)

                title = await self._safe_text(page, ".jd-header-title, h1, .styles_jd-header-title__")
                company = await self._safe_text(page, ".jd-header-comp-name, .comp-name, a.comp-name")
                job_title = title or job.title
                job_company = company or job.company

                apply_btn = page.locator(
                    'button:has-text("Apply"), '
                    'button:has-text("Easy Apply"), '
                    '.styles_apply-button__, '
                    '#apply-button'
                ).first

                if await apply_btn.count() == 0:
                    return ApplyResult(
                        job_title=job_title,
                        company=job_company,
                        status="skipped",
                        message="No apply button found (may require company site apply).",
                    )

                await apply_btn.click()
                await page.wait_for_timeout(2000)

                resume_path = settings.resume_file
                if resume_path.exists():
                    file_input = page.locator('input[type="file"]')
                    if await file_input.count():
                        await file_input.first.set_input_files(str(resume_path.resolve()))

                submit = page.locator(
                    'button:has-text("Submit"), '
                    'button:has-text("Apply"), '
                    'button:has-text("Save and Apply")'
                ).last
                if await submit.count():
                    await submit.click()
                    await page.wait_for_timeout(2000)

                return ApplyResult(
                    job_title=job_title,
                    company=job_company,
                    status="applied",
                    message="Application submitted (or pending confirmation).",
                )
            except Exception as exc:
                return ApplyResult(
                    job_title=job.title,
                    company=job.company,
                    status="error",
                    message=str(exc),
                )

    def _require_page(self) -> Page:
        if not self._session:
            raise RuntimeError("Browser not started. Say 'start browser' first.")
        return self._session.page

    async def _is_logged_in(self, page: Page) -> bool:
        url = page.url
        if "nlogin" not in url and "login" not in url.lower():
            profile = page.locator('[data-ga-track="spa-event"], .nI-gNb-drawer__user, .avatar')
            if await profile.count():
                return True
        return "my naukri" in (await page.title()).lower() or "mnjuser" in url

    async def _safe_text(self, locator: Any, selector: str) -> str:
        try:
            el = locator.locator(selector).first
            if await el.count():
                return (await el.inner_text()).strip()
        except Exception:
            pass
        return ""


def parse_login_from_text(text: str) -> tuple[str | None, str | None]:
    email_match = re.search(r"[\w.+-]+@[\w.-]+\.\w+", text)
    password_match = re.search(
        r"password\s+(\S+)",
        text,
        re.IGNORECASE,
    )
    return (
        email_match.group(0) if email_match else None,
        password_match.group(1) if password_match else None,
    )
