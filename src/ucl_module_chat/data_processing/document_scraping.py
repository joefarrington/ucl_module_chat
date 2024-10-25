import re
import time
from pathlib import Path

import hydra
import omegaconf
import requests
from bs4 import BeautifulSoup
from loguru import logger
from tqdm import tqdm

from ucl_module_chat.utils.resolve_paths import get_abs_path_using_repo_root


def _get_index_page_html(index_page_url: str):
    """Get the HTML content of the index page."""
    response = requests.get(index_page_url)
    index_page_html = response.text
    return index_page_html


def _get_module_urls_from_index_page(index_page_html: str, regex_url_pattern: str):
    """Extract module URLs from the index page HTML using regex."""
    regex_url_pattern = re.compile(regex_url_pattern)
    soup = BeautifulSoup(index_page_html, "html.parser")
    pattern = re.compile(regex_url_pattern)

    module_urls = []
    for cite_tag in soup.find_all("cite"):
        url = cite_tag["data-url"]
        if pattern.match(url):
            module_urls.append(url)

    return module_urls


def _save_module_page_html(module_url: str, output_dir: str | Path):
    """Save the HTML content of a module page to a text file."""
    output_dir = Path(output_dir)

    # Send a GET request to fetch the HTML content
    response = requests.get(module_url)
    response.raise_for_status()  # Raise an exception for HTTP errors

    # Extract the part of the URL after "/modules/" for the filename
    module_id = module_url.split("/modules/")[1]

    # Save the HTML content to a text file
    file_path = output_dir / f"{module_id}.html"
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(response.text)


def scrape_documents(
    index_page_url: str | Path,
    output_dir: str | Path,
    regex_url_pattern: str,
    wait_time_seconds: int = 2,
):
    """Scrape module pages and save HTML content to text files."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Identifying module pages from {index_page_url}")
    index_page_html = _get_index_page_html(index_page_url)

    module_urls = _get_module_urls_from_index_page(index_page_html, regex_url_pattern)
    n_modules = len(module_urls)
    logger.info(f"Identified {len(module_urls)} module pages to save to {output_dir}.")

    errors = 0

    for url in tqdm(module_urls):
        try:
            _save_module_page_html(url, output_dir)
            time.sleep(wait_time_seconds)  # Pause to avoid abusing the server
        except requests.exceptions.RequestException as e:
            logger.error(f"Error saving HTML for {url}: {e}")
            errors += 1

    logger.info(f"{n_modules - errors} module pages successfully saved")
    logger.info(f"{errors} module pages could not be saved.")


@hydra.main(version_base=None, config_path="../conf", config_name="config")
def main(cfg: omegaconf.DictConfig) -> None:
    """Run the document scraping process."""
    cfg = cfg.setup.scrape_documents
    cfg.output_dir = get_abs_path_using_repo_root(cfg.output_dir)
    scrape_documents(**cfg)


if __name__ == "__main__":
    main()
