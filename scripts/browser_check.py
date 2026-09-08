from __future__ import annotations

import os
from pathlib import Path

from playwright.sync_api import sync_playwright


URL = os.environ.get("AIGIS_BRIDGE_BROWSER_URL", "http://127.0.0.1:8002/")


def browser_path() -> str | None:
    configured = os.environ.get("AIGIS_BRIDGE_BROWSER_PATH")
    candidates = [
        configured,
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    ]
    return next((candidate for candidate in candidates if candidate and Path(candidate).is_file()), None)


def main() -> None:
    console_errors: list[str] = []
    page_errors: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path=browser_path())
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.set_default_timeout(5_000)
        page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
        page.on("pageerror", lambda error: page_errors.append(str(error)))
        page.goto(URL)
        page.wait_for_load_state("networkidle")

        page.get_by_text("MOCK SDK").wait_for()
        gt3 = page.get_by_role("button", name="生成 GT3 演示")
        gt4 = page.get_by_role("button", name="生成 GT4 演示")
        assert gt3.is_disabled() and gt4.is_disabled(), "Consent must gate both challenge actions."
        page.get_by_role("checkbox").check()

        gt3.click()
        page.get_by_role("heading", name="完成真人验证").wait_for()
        page.get_by_role("button", name="完成 GT3 模拟真人验证").click()
        page.get_by_text("服务端已生成 Aigis 值").wait_for()

        gt4.click()
        page.get_by_role("heading", name="完成真人验证").wait_for()
        page.get_by_role("button", name="取消本次操作").click()
        page.get_by_role("heading", name="完成真人验证").wait_for(state="detached")
        gt4.click()
        page.get_by_role("button", name="完成 GT4 模拟真人验证").click()
        page.get_by_text("服务端已生成 Aigis 值").wait_for()

        page.set_viewport_size({"width": 390, "height": 844})
        assert page.evaluate("document.documentElement.scrollWidth <= document.documentElement.clientWidth")
        browser.close()

    assert not console_errors, f"Browser console errors: {console_errors}"
    assert not page_errors, f"Page errors: {page_errors}"
    print("BROWSER_CHECK_OK: consent, GT3, GT4, cancel, server-only proof, desktop, mobile, console")


if __name__ == "__main__":
    main()
