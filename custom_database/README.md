# evaluation-dataset-generation

This folder contains code and prompts for generating your own evaluation dataset used to benchmark MCP server implementations.

We use LLMs to generate:

* Natural language questions across multiple categories
* Ground truth answers (in Cypher or plain text, depending on the task)

### Code Structure

* `dataset_generation.ipynb` – Main notebook for generating the dataset
* `prompts.py` – Prompt templates for question and answer generation
* `utils.py` – Helper functions for database access and formatting
* `generated_dataset_<timestamp>.json` – Final output containing questions, answers, and metadata
* `template.env` - example on how to provide the parameters with your LLMs and databases
* 
### env file Structure

* LLM_CREATE_QUESTIONS: list of LLMs to be used to generate questions. Defined as a list of LLM description following the pattern {model_provider}:{model} based on [Langchain](https://python.langchain.com/api_reference/langchain/chat_models/langchain.chat_models.base.init_chat_model.html)
* LLM_CREATE_ANSWERS: LLM used for creating the answers. Defined as a LLM description following the pattern {model_provider}:{model} based on [Langchain](https://python.langchain.com/api_reference/langchain/chat_models/langchain.chat_models.base.init_chat_model.html)
* xxx_API_KEY: list of API key used for this LLM
* DATABASES: list of databases used for the Q&A generation. Defined as a list of dictionary {"uri", "username", "password", "database (optional, default is neo4j)"}

The generated dataset is used to evaluate how well MCP-compatible servers support agent-based querying over real-world knowledge graphs.
