# 3CLOUD-LANGCHAIN

## Overview
This repository contains a collection of demos, notebooks, and scripts showcasing the use of LangChain and related technologies for building advanced AI-driven systems. The focus is on multi-agent collaboration, data analysis, and integration with external systems such as databases and APIs.

## Repository Structure

### AQ DEMOS
This folder contains Jupyter notebooks and Python scripts demonstrating various use cases of LangChain. Key files include:

- **MAIN NOTEBOOKS/**: A series of Jupyter notebooks covering topics such as:
  - Basics of LangChain
  - Introduction to Retrieval-Augmented Generation (RAG)
  - Single and Multi-Agent Systems
  - SQL Database Agents
  - Hierarchical Multi-Agent Teams
- **data/**: Contains datasets and resources used in the demos, such as:
  - `bloomberg_financial_news_1k.pkl`
  - `Chinook.db`
  - `finance.db`
  - `imdb_top_1000.csv`
  - `titanic.csv`
- **tmp/**: Temporary files and resources for ongoing experiments and analysis.

### MCP
This folder contains Python scripts for Model Context Protocol (MCP) servers, including:

- `mcp_agent_gradio.py`: A Gradio-based interface for MCP agents.
- `mcp_exchange_rate_fetcher_server.py`: Fetches exchange rates.
- `mcp_math_server.py`: Performs mathematical computations.
- `mcp_weather_server.py`: Provides weather information.
- `mcp_yt_transcript_server.py`: Processes YouTube transcripts.

## Getting Started

### Prerequisites
- Python 3.11 or later
- Anaconda (optional but recommended)

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/3CLOUD-LANGCHAIN.git
   ```
2. Navigate to the repository:
   ```bash
   cd 3CLOUD-LANGCHAIN
   ```
3. Install dependencies:
   ```bash
   pip install -r MCP/requirements.txt
   ```

## Usage

### Running Notebooks
Open any notebook in the `AQ DEMOS/MAIN NOTEBOOKS/` folder using Jupyter Notebook or JupyterLab to explore the demos.

### Running MCP Servers
Run any MCP server script from the `MCP/` folder to start the respective service. For example:
```bash
python MCP/mcp_weather_server.py
```

## Contributing
Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## License
This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgments
Special thanks to the contributors and the open-source community for their support and inspiration.

