# Chat with the 2024/2025 UCL module catalogue

## NOTE
This is a demonstration developed for educational purposes only and is not affiliated with or endorsed by University College London (UCL). The model may provide incorrect or outdated information. Interactions should therefore not be used to inform decisions such as programme choices or module selection.

Please refer to the official [UCL module catalogue](https://www.ucl.ac.uk/module-catalogue) for accurate and up-to-date information.

The code is licensed under Apache License 2.0 but the module catalogue content is copyright UCL. 

## Get started

### Hugging Face Space

The easiest way to chat with the model is using the Hugging Face space.

### Local use

You can use the code snippet below to run the app locally. This project uses [uv](https://docs.astral.sh/uv/) to manage dependencies and the snippet assumes that you have [uv installed](https://docs.astral.sh/uv/getting-started/installation/). 

The app requires an [OpenAI API key](https://help.openai.com/en/articles/4936850-where-do-i-find-my-openai-api-key) to run locally.

```bash
# Clone repo and install dependencies in venv
git clone https://github.com/joefarrington/ucl_module_chat.git
cd ucl_module_chat

uv venv
source .venv/bin/activate
uv pip install .

# Add API keys as environment variables
# Alternatively, create a .env file in the main directory
export OPENAI_API_KEY=<Your API key>

# Run the app
python app.py
```
One advantage of LangChain is that you could easily substitute the embedding model and/or LLM for alternatives including locally hosted models using [Hugging Face](https://python.langchain.com/docs/integrations/providers/huggingface/), [llama.cpp](https://python.langchain.com/docs/integrations/providers/llamacpp/) or [Ollama](https://python.langchain.com/docs/integrations/providers/ollama/). 

### Rerun scraping and embedding

The repository includes the vectorstore with pages from the module catalogue embedded using OpenAI's [text-embedding-3-small](https://platform.openai.com/docs/guides/embeddings).

The process for downloading the pages from the module catalogue, converting the pages to markdown documents, and embedding the documents can be re-run using the script `setup.py`. There is no need to run this script unless you want to change the way data is extracted from the HTML pages to markdown, or embed the documents using an alternative model. 

## Implementation details

### Document scraping

The documents in the vectorstore used to provide context to the LLM are based on the publicly available webpages describing each module offered by UCL. 

The URLs for the individual module catalogue pages are identified from the module catalogue search page. The modules pages are then visited in sequence and the HTML is downloaded for each page. 

There are more efficient ways to scrape the content from the module catalogue (e.g. [scrapy](https://scrapy.org/)). The current method is designed to minimise the effect on the server. There is long wait time between requests and the raw HTML is saved so that alternative methods of extracting the content can be considered without needing to request additional data from the server.

### Document conversion

The raw HTML for each module page is converted to a markdown document using [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) to parse the HTML and a [Jinja](https://jinja.palletsprojects.com/en/stable/intro/) template to format the extracted information.  

### Document embedding

The module pages are relatively short documents and therefore each is treated as a single chunk and embedded as a whole. 

Each page is embedded using [text-embedding-3-small](https://platform.openai.com/docs/guides/embeddings). [FAISS](https://faiss.ai/) is used to store and search the embedded documents. 

### Q&A based using RAG

The chat interface is a simple [Gradio](https://www.gradio.app/) app, and uses OpenAI's [gpt-4o-mini](https://openai.com/index/gpt-4o-mini-advancing-cost-efficient-intelligence/) as the underlying LLM. 

At each turn of the conversation the following steps are performed, managed using [Langchain](https://python.langchain.com/docs/introduction/):

* Call the LLM to rephrase the user's query, given the conversation history, so that it includes relevant context from the conversation.

* Embed the rephrased query and retrieve relevant documents from the vectorstore.

* Call the LLM with the current user input, retrieved documents for context and conversation history.  Output the result as the LLM's response in the chat interface.

## Potential extensions

* Add [course descriptions](https://www.ucl.ac.uk/prospective-students/undergraduate/undergraduate-courses) to the vectorstore so that the app is more useful to potential applicants and can explain, for example, which modules are mandatory on certain courses.

* Provide links to the module catalogue for modules suggested by the application, either within the conversation or as a separate interface element.

* Use a agent-based approach to avoid unnecessary retrieval steps and/or support more complex queries that require multiple retrieval steps. 

* Use a LangGraph app to manage the conversation history and state. 

## Useful resources

* [UCL module catalogue](https://www.ucl.ac.uk/module-catalogue?collection=drupal-module-catalogue&facetsort=alpha&num_ranks=20&daat=10000&sort=title)

* [Langchain official tutorials](https://python.langchain.com/docs/tutorials/)

* Hands-On Large Language Models [book](https://learning.oreilly.com/library/view/hands-on-large-language/9781098150952/) and [GitHub repository](https://github.com/HandsOnLLM/Hands-On-Large-Language-Models)