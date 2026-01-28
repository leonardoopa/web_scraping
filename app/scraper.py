import asyncio
import os
import logging
from typing import List, Set
from playwright.async_api import async_playwright, Page

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CMCScraper:

    MIN_POST_LENGTH = 30
    MAX_POST_LENGTH = 2000
    SCROLL_PIXELS = 4000
    SCROLL_DELAY_SECONDS = 2.5

    # Seletor CSS (Estratégia 'dir=auto' para pegar comentários de usuário)
    POST_CONTENT_SELECTOR = 'div[dir="auto"], p'

    # Blacklist
    IGNORED_KEYWORDS = {
        "Leaderboards",
        "Trending",
        "Upcoming",
        "Recently Added",
        "Gainers & Losers",
        "Community Sentiment",
        "Fear and Greed",
        "Log In",
        "Sign Up",
        "Copyright",
        "Policies",
        "DexScan",
        "Read all",
        "Show more",
        "Followers",
        "Bullish",
        "Bearish",
        "Cookies",
        "Privacy",
        "Terms",
        "Download",
        "Portfolio",
    }

    def __init__(self, url: str = None):
        self.target_url = url or os.getenv("CMC_URL")
        self._validate_config()

    def _validate_config(self):
        if not self.target_url:
            raise ValueError(
                "Configuration Error: The variable 'CMC_URL' was not found in the .env file."
            )

    async def _scroll_page(self, page: Page, scroll_count: int):
        logger.info(f"Starting scroll of {scroll_count} steps...")

        for i in range(scroll_count):
            logger.info(f"Scrollando {i + 1}/{scroll_count}...")
            await page.mouse.wheel(0, self.SCROLL_PIXELS)
            await asyncio.sleep(self.SCROLL_DELAY_SECONDS)

    def _is_valid_post(self, text: str) -> bool:
        clean_text = text.strip()
        text_len = len(clean_text)

        # Validação (Tamanho)
        if not (self.MIN_POST_LENGTH <= text_len <= self.MAX_POST_LENGTH):
            return False

        # Validação (Blacklist)
        if any(keyword in clean_text for keyword in self.IGNORED_KEYWORDS):
            return False

        return True

    async def _extract_and_filter_posts(self, page: Page) -> List[str]:
        """Extrai os elementos do DOM e aplica os filtros Python."""
        logger.info("Extracting raw text from the page...")

        try:
            # Pega todos os textos que batem com o seletor
            raw_elements = await page.locator(
                self.POST_CONTENT_SELECTOR
            ).all_inner_texts()
        except Exception as e:
            logger.error(f"Failed to fetch selectors from the page: {e}")
            return []

        valid_posts: List[str] = []
        seen_posts: Set[str] = set()

        for raw_text in raw_elements:
            clean_text = raw_text.strip()

            # Aplica filtro e remove duplicatas
            if self._is_valid_post(clean_text) and clean_text not in seen_posts:
                valid_posts.append(clean_text)
                seen_posts.add(clean_text)

        logger.info(
            f"Filter completed: {len(valid_posts)} valid posts from {len(raw_elements)} raw elements."
        )
        return valid_posts

    async def run(self, scroll_attempts: int = 3, headless: bool = False) -> List[str]:
        async with async_playwright() as playwright:
            logger.info("Starting Playwright engine...")

            # Configuração do Browser
            browser = await playwright.chromium.launch(headless=headless)

            # Cria contexto com User-Agent para evitar bloqueios simples
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

            try:
                logger.info(f"Navigating to: {self.target_url}")
                # 'networkidle' espera as conexões de rede baixarem (bom para sites dinâmicos)
                await page.goto(
                    self.target_url, wait_until="networkidle", timeout=60000
                )

                await self._scroll_page(page, scroll_attempts)
                posts = await self._extract_and_filter_posts(page)

                return posts

            except Exception as e:
                logger.error(f"Critical error during execution: {e}")
                return []
            finally:
                await browser.close()
                logger.info("Browser closed.")
