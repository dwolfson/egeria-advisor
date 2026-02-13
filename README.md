# Egeria Advisor

AI-powered advisor for the egeria-python repository using local LLMs (Ollama).

## Overview

Egeria Advisor helps users and maintainers work with the egeria-python repository by providing:
- **Query Assistance**: Answer questions about Egeria concepts and metadata
- **Code Examples**: Generate working code examples using pyegeria
- **Conversational Help**: Multi-turn conversations for complex tasks
- **Maintenance Support**: Assist with codebase navigation and refactoring

## Architecture

- **LLM**: Ollama (local) @ localhost:11434
  - Query Agent: llama3.1:8b (fast, general purpose)
  - Code Agent: codellama:13b (code-specialized)
- **Vector Store**: Milvus @ localhost:19530
- **Experiment Tracking**: MLflow @ localhost:5000
- **Metadata Platform**: Egeria @ localhost:9443
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2 (local)

## Quick Start

### Prerequisites

Ensure these Docker containers are running:
```bash
# Milvus
docker ps | grep milvus

# MLflow
curl http://localhost:5000

# Egeria
curl -k https://localhost:9443/open-metadata/platform-services/users/garygeeke/server-platform/origin

# Ollama
docker ps | grep ollama
curl http://localhost:11434/api/tags
```

### Installation

```bash
# Clone and navigate
cd /home/dwolfson/localGit/egeria-v6/egeria-advisor

# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Copy and configure environment
cp .env.example .env
# Edit .env with your settings

# Verify setup
python -c "from advisor.config import settings; print('✓ Config loaded')"
```

### Pull Ollama Models

```bash
# If using Docker
docker exec ollama ollama pull llama3.1:8b
docker exec ollama ollama pull codellama:13b

# If using native Ollama
ollama pull llama3.1:8b
ollama pull codellama:13b
```

## Usage

### Run Data Preparation

```bash
# Parse egeria-python repository
python -m advisor.data_prep.pipeline

# This will:
# - Parse Python code files
# - Extract documentation
# - Generate embeddings
# - Populate Milvus collections
```

### Query the Advisor

```bash
# Direct query
egeria-advisor "What is a glossary term in Egeria?"

# Interactive mode
egeria-advisor --interactive

# Use specific agent
egeria-advisor --agent=code "Show me how to create a glossary"

# With context
egeria-advisor --context=glossary "Give me examples"
```

## Development Status

- ✅ Phase 1: Architecture & Design (Complete)
- 🚧 Phase 2: Data Preparation Pipeline (In Progress)
- ⏳ Phase 3: Vector Store Integration (Pending)
- ⏳ Phase 4: RAG System (Pending)
- ⏳ Phase 5: Agent Framework (Pending)
- ⏳ Phase 6: CLI Interface (Pending)
- ⏳ Phase 7: Query Understanding (Pending)
- ⏳ Phase 8: Observability (Pending)
- ⏳ Phase 9: Testing (Pending)
- ⏳ Phase 10: Documentation (Pending)

## Project Structure

```
egeria-advisor/
├── advisor/                 # Main package
│   ├── data_prep/          # Data preparation pipeline
│   ├── vector_store/       # Milvus integration
│   ├── rag/                # RAG system
│   ├── agents/             # Agent implementations
│   ├── observability/      # MLflow & monitoring
│   └── cli/                # CLI interface
├── config/                 # Configuration files
├── data/                   # Processed data cache
├── tests/                  # Test suite
├── docs/                   # Documentation
├── examples/               # Usage examples
└── scripts/                # Utility scripts
```

## Configuration

See `config/advisor.yaml` for full configuration options.

Key settings:
- **Data Source**: Path to egeria-python repository
- **LLM Models**: Which Ollama models to use for each agent
- **Vector Store**: Milvus connection settings
- **RAG Parameters**: Chunk size, similarity threshold, etc.
- **Observability**: MLflow tracking configuration

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=advisor --cov-report=html

# Run specific test file
pytest tests/test_code_parser.py -v
```

## Monitoring

- **MLflow UI**: http://localhost:5000
  - View experiments
  - Compare model performance
  - Track metrics over time

- **Ollama API**: http://localhost:11434
  - Check available models
  - Monitor generation

## Documentation

- [Architecture Plan](../bob-ai/egeria-advisor-plan.md)
- [Implementation Roadmap](../bob-ai/implementation-roadmap.md)
- [MLflow Tracking Guide](../bob-ai/mlflow-experiment-tracking-guide.md)
- [Ollama Setup Guide](../bob-ai/ollama-setup-guide.md)
- [Quick Start Guide](../bob-ai/quick-start-guide.md)

## Contributing

This project follows the egeria-python contribution guidelines. See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## Support

- **Project Lead**: dan.wolfson@pdr-associates.com
- **Egeria Community**: http://egeria-project.org/guides/community/

## License

Apache License 2.0 - See [LICENSE](LICENSE) for details.

---

**Current Version**: 0.1.0  
**Last Updated**: 2026-02-13  
**Status**: Phase 2 - Data Preparation Pipeline in development