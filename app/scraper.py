import asyncio
import os
import logging
from typing import List, Set
from playwright.async_api import async_playwright, Page

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CMCScraper:
    """
    Classe responsável por realizar o scraping da comunidade do CoinMarketCap.
    Segue o princípio de responsabilidade única (SRP) e Clean Code.
    """

    MIN_POST_LENGTH = 30
    MAX_POST_LENGTH = 2000
    SCROLL_PIXELS = 4000
    SCROLL_DELAY_SECONDS = 2.5
    
    # Seletor CSS (Estratégia 'dir=auto' para pegar comentários de usuário)
    POST_CONTENT_SELECTOR = 'div[dir="auto"], p'
    
    # Blacklist: Termos que indicam que o texto NÃO é um post de usuário
    IGNORED_KEYWORDS = {
        "Leaderboards", "Trending", "Upcoming", "Recently Added", 
        "Gainers & Losers", "Community Sentiment", "Fear and Greed",
        "Log In", "Sign Up", "Copyright", "Policies", "DexScan",
        "Read all", "Show more", "Followers", "Bullish", "Bearish",
        "Cookies", "Privacy", "Terms", "Download", "Portfolio"
    }

    def __init__(self, url: str = None):
        self.target_url = url or os.getenv("CMC_URL")
        self._validate_config()

    def _validate_config(self):
        if not self.target_url:
            raise ValueError("Erro de Configuração: A variável 'CMC_URL' não foi encontrada no .env")

    async def _scroll_page(self, page: Page, scroll_count: int):
        """Executa a rolagem da página para carregar o 'infinite scroll'."""
        logger.info(f"Iniciando scroll de {scroll_count} etapas...")
        
        for i in range(scroll_count):
            logger.info(f"Scrollando {i + 1}/{scroll_count}...")
            await page.mouse.wheel(0, self.SCROLL_PIXELS)
            await asyncio.sleep(self.SCROLL_DELAY_SECONDS)

    def _is_valid_post(self, text: str) -> bool:
        """
        Filtro de Regras de Negócio.
        Retorna True se o texto parecer um post genuíno, False se for lixo/menu.
        """
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
        logger.info("Extraindo textos brutos da página...")
        
        try:
            # Pega todos os textos que batem com o seletor
            raw_elements = await page.locator(self.POST_CONTENT_SELECTOR).all_inner_texts()
        except Exception as e:
            logger.error(f"Falha ao buscar seletores na página: {e}")
            return []

        valid_posts: List[str] = []
        seen_posts: Set[str] = set()

        for raw_text in raw_elements:
            clean_text = raw_text.strip()
            
            # Aplica filtro e remove duplicatas
            if self._is_valid_post(clean_text) and clean_text not in seen_posts:
                valid_posts.append(clean_text)
                seen_posts.add(clean_text)
        
        logger.info(f"Filtro concluído: {len(valid_posts)} posts válidos de {len(raw_elements)} elementos brutos.")
        return valid_posts

    async def run(self, scroll_attempts: int = 3, headless: bool = False) -> List[str]:
        """
        Método Principal (Entry Point).
        Orquestra a abertura do browser, navegação e extração.
        """
        async with async_playwright() as playwright:
            logger.info("Iniciando motor do Playwright...")
            
            # Configuração do Browser
            browser = await playwright.chromium.launch(headless=headless)
            
            # Cria contexto com User-Agent para evitar bloqueios simples
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

            try:
                logger.info(f"Navegando para: {self.target_url}")
                # 'networkidle' espera as conexões de rede baixarem (bom para sites dinâmicos)
                await page.goto(self.target_url, wait_until="networkidle", timeout=60000)
                
                await self._scroll_page(page, scroll_attempts)
                posts = await self._extract_and_filter_posts(page)
                
                return posts

            except Exception as e:
                logger.error(f"Erro crítico durante a execução: {e}")
                return []
            finally:
                await browser.close()
                logger.info("Navegador encerrado.")