import asyncio
import os
import logging
from typing import List, Dict
from playwright.async_api import async_playwright, Page
import os
from dotenv import load_dotenv


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()


class CMCScraper:
    # URLs Oficiais do CoinMarketCap
    URL_COMMUNITY = os.getenv("CMC_URL")
    URL_GAINERS = os.getenv("CMC_URL_GAINERS")
    URL_NEWS = os.getenv("CMC_URL_NEWS")

    # Configurações
    MIN_POST_LENGTH = 40
    MAX_POST_LENGTH = 2000

    # Blacklist para limpar menus
    IGNORED_KEYWORDS = {
        "Leaderboards",
        "Trending",
        "Upcoming",
        "Recently Added",
        "Log In",
        "Sign Up",
        "Copyright",
        "Policies",
        "DexScan",
        "Read all",
        "Show more",
        "Followers",
        "Cookies",
        "Privacy",
    }

    async def _extract_gainers_losers(self, page: Page) -> Dict[str, List[str]]:
        """Extrai as tabelas de maiores altas e baixas."""
        logger.info("Extraindo dados de Gainers & Losers...")

        # Geralmente a primeira tabela é Gainers e a segunda é Losers.
        try:
            # Pega todas as linhas de todas as tabelas na página
            rows = await page.locator("table tbody tr").all_inner_texts()

            half = len(rows) // 2
            gainers = [r.replace("\n", " ") for r in rows[:10]]  # Top 10 Gainers
            losers = [
                r.replace("\n", " ") for r in rows[half : half + 10]
            ]  # Top 10 Losers

            return {"gainers": gainers, "losers": losers}
        except Exception as e:
            logger.error(f"Erro ao ler tabelas: {e}")
            return {"gainers": [], "losers": []}

    async def _extract_news(self, page: Page) -> List[str]:
        """Extrai manchetes da página de notícias."""
        logger.info("Extraindo Notícias (Headlines)...")
        candidates = await page.locator("a, h2, h3, p").all_inner_texts()

        news = []
        seen = set()
        for text in candidates:
            clean = text.strip()
            # Filtra títulos curtos demais ou muito longos
            if 20 < len(clean) < 300 and clean not in seen:
                if not any(bad in clean for bad in self.IGNORED_KEYWORDS):
                    news.append(clean)
                    seen.add(clean)

        return news[:15]  # Retorna as 15 notícias mais relevantes

    async def run_comprehensive_scan(self, headless: bool = True) -> Dict:
        """
        Executa uma varredura completa: Comunidade, Mercado e Notícias.
        """
        data_package = {
            "community_posts": [],
            "market_movements": {},
            "latest_news": [],
        }

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

            try:
                # 1. PEGAR GAINERS & LOSERS
                await page.goto(self.URL_GAINERS, wait_until="domcontentloaded")
                data_package["market_movements"] = await self._extract_gainers_losers(
                    page
                )

                # 2. PEGAR NOTÍCIAS
                await page.goto(self.URL_NEWS, wait_until="domcontentloaded")
                data_package["latest_news"] = await self._extract_news(page)

                # 3. PEGAR SENTIMENTO DA COMUNIDADE (Scroll necessário)
                await page.goto(self.URL_COMMUNITY, wait_until="networkidle")
                # Scroll rápido
                for _ in range(3):
                    await page.mouse.wheel(0, 3000)
                    await asyncio.sleep(2)

                # Reutilizando lógica de filtro de posts (simplificada aqui)
                posts_raw = await page.locator('div[dir="auto"], p').all_inner_texts()
                data_package["community_posts"] = [
                    p.strip()
                    for p in posts_raw
                    if len(p) > 30 and not any(b in p for b in self.IGNORED_KEYWORDS)
                ][:20]

            except Exception as e:
                logger.error(f"Erro no fluxo de scraping: {e}")
            finally:
                await browser.close()

        return data_package
