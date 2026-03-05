import asyncio
from playwright.async_api import async_playwright

USER_DATA_DIR = "./meta_session"
META_URL = "https://www.meta.ai"

async def login_session():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = await context.new_page()
        
        print("Opening Meta AI...")
        await page.goto(META_URL)
        print("\n👉 Please log in to Meta AI manually in the browser window.")
        print("👉 After you're logged in and can see the chat interface, press ENTER here to save the session.")
        
        input()  # Wait for user to press enter
        
        await context.close()
        print("✅ Session saved! You can now set headless=True and run the automation.")

if __name__ == "__main__":
    asyncio.run(login_session())
