import hydra
import omegaconf
from dotenv import load_dotenv
from loguru import logger

from ucl_module_chat.data_processing.document_conversion import (
    convert_all_documents_html_to_markdown,
)
from ucl_module_chat.data_processing.document_embedding import embed_documents
from ucl_module_chat.data_processing.document_scraping import scrape_documents
from ucl_module_chat.utils.resolve_paths import get_abs_path_using_repo_root

load_dotenv()


@hydra.main(version_base=None, config_path="conf", config_name="config")
def main(cfg: omegaconf.DictConfig) -> None:
    """Scrape module catalogue, convert HTML to markdown, and embed in vectorstore."""

    cfg.setup.scrape_documents.output_dir = get_abs_path_using_repo_root(
        cfg.setup.scrape_documents.output_dir
    )
    cfg.setup.convert_documents.input_dir = get_abs_path_using_repo_root(
        cfg.setup.convert_documents.input_dir
    )
    cfg.setup.convert_documents.output_dir = get_abs_path_using_repo_root(
        cfg.setup.convert_documents.output_dir
    )
    cfg.setup.embed_documents.input_dir = get_abs_path_using_repo_root(
        cfg.setup.embed_documents.input_dir
    )
    cfg.vectorstore.dir = get_abs_path_using_repo_root(cfg.vectorstore.dir)

    scrape_documents(**cfg.setup.scrape_documents)
    convert_all_documents_html_to_markdown(**cfg.setup.convert_documents)

    embedding_model = hydra.utils.instantiate(cfg.models.embedding)
    vectorstore = embed_documents(cfg.setup.embed_documents.input_dir, embedding_model)
    vectorstore.save_local(cfg.vectorstore.dir)
    logger.info(f"Vectorstore saved to {cfg.vectorstore.dir}")


if __name__ == "__main__":
    main()
