import gradio as gr
import hydra
import omegaconf
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from ucl_module_chat.chains.rag_chain import build_rag_chain
from ucl_module_chat.utils.resolve_paths import get_abs_path_using_repo_root

load_dotenv()

# Text paragraph to be added below the title
description = """
<b>NOTE</b>: This is a demonstration developed for educational purposes only 
and is not affiliated with or endorsed by University College London (UCL).
The model may provide incorrect or outdated information.  Interactions should 
therefore not be used to inform decisions such as programme choices or module selection.

Please refer to the official [UCL module catalogue](https://www.ucl.ac.uk/module-catalogue)
for accurate and up-to-date information.
"""

examples = [
    "When can I take a module on medical statistics?",
    "What are the prerequisites for taking Supervised Learning?",
    "What is the difference between the two modules on Trauma for \
        paediatric dentistry?",
]


def convert_history(history: list[dict]) -> list[BaseMessage]:
    """Convert conversation history into Langchain messages"""
    lc_history = []
    for msg in history:
        if msg["role"] == "user":
            lc_history.append(HumanMessage(msg["content"]))
        elif msg["role"] == "assistant":
            lc_history.append(AIMessage(msg["content"]))
    return lc_history


@hydra.main(
    version_base=None, config_path="src/ucl_module_chat/conf", config_name="config"
)
def main(cfg: omegaconf.DictConfig) -> None:
    """Run the UCL module chatbot in a Gradio interface."""

    vectorstore_dir = get_abs_path_using_repo_root(cfg.vectorstore.dir)
    llm = hydra.utils.instantiate(cfg.models.llm)
    embedding_model = hydra.utils.instantiate(cfg.models.embedding)
    rag_chain = build_rag_chain(
        llm=llm, embedding_model=embedding_model, vectorstore_dir=vectorstore_dir
    )

    def chat(input: str, history: list[dict] = None) -> str:
        result = rag_chain.invoke(
            {"input": input, "chat_history": convert_history(history)},
        )
        return result["answer"]

    with gr.Blocks(fill_height=True) as module_chat:
        gr.Markdown("# Chat with the module catalogue")
        gr.Markdown(description)
        gr.ChatInterface(
            fn=chat,
            type="messages",
            examples=examples,
        )

    module_chat.launch()


if __name__ == "__main__":
    main()
