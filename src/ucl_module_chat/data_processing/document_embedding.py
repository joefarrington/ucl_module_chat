from pathlib import Path

import hydra
import omegaconf
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings.embeddings import Embeddings
from loguru import logger

from ucl_module_chat.utils.resolve_paths import get_abs_path_using_repo_root

load_dotenv()


def embed_documents(input_dir: str | Path, embedding_model: Embeddings) -> FAISS:
    """Create a FAISS vectorstore from a directory of markdown documents."""
    input_dir = Path(input_dir)

    all_module_document_paths = list(input_dir.glob("*.md"))

    module_docs = []

    for module_md_path in all_module_document_paths:
        with open(module_md_path, "r") as f:
            module_md = f.read()
        module_docs.append(module_md)

    logger.info(f"Embedding {len(module_docs)} documents")
    vectorstore = FAISS.from_texts(module_docs, embedding=embedding_model)
    logger.info(f"Vectorstore created with {vectorstore.index.ntotal} vectors")
    return vectorstore


@hydra.main(version_base=None, config_path="../conf", config_name="config")
def main(cfg: omegaconf.DictConfig) -> None:
    """Run the document embedding process."""
    embedding_model = hydra.utils.instantiate(cfg.models.embedding)
    cfg.setup.embed_documents.input_dir = get_abs_path_using_repo_root(
        cfg.setup.embed_documents.input_dir
    )
    cfg.vectorstore.dir = get_abs_path_using_repo_root(cfg.vectorstore.dir)
    vectorstore = embed_documents(cfg.setup.embed_documents.input_dir, embedding_model)
    vectorstore.save_local(cfg.vectorstore.dir)
    logger.info(f"Vectorstore saved to {cfg.vectorstore.dir}")


if __name__ == "__main__":
    main()
