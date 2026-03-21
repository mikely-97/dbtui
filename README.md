# dbt-tui

A Terminal User Interface (TUI) for navigating and managing [dbt (data build tool)](https://www.getdbt.com/) projects.

**dbt-tui** provides an interactive command-line interface for exploring dbt models, their relationships, and configurations without leaving your terminal.

## Features

- **Model Explorer**: Browse all models in your dbt project with search capabilities
- **Dependency Visualization**: View parent and child relationships for any model
- **Model Preview**: Read model SQL and configuration inline
- **Quick Navigation**: Jump between related models with keyboard shortcuts
- **New Model Creation**: Create new models with automatic ref() generation
- **Property Discovery**: View effective configurations from all sources (dbt_project.yml, schema.yml, model config)
- **Session Persistence**: Automatically saves and restores your last viewed project and model
- **External Editor Integration**: Open models in your preferred editor

## Installation

### Requirements

- Python 3.12 or higher
- A dbt project to explore

### Install from source

```bash
# Clone the repository
git clone <repository-url>
cd dbt-tui

# Install dependencies using pip
pip install -e .

# Or using poetry
poetry install
```

## Usage

### Basic Usage

Navigate to a dbt project directory and run:

```bash
python -m dbt_tui
```

Or if installed via poetry:

```bash
poetry run python -m dbt_tui
```

### First Launch

On first launch, dbt-tui will:
1. Load the test project (if no cached project exists)
2. Open the model search screen
3. Allow you to search for and select a model

### Keyboard Shortcuts

#### Global Bindings

| Key | Action | Description |
|-----|--------|-------------|
| `o` | Options | Open options/settings screen |
| `f` | Find Model | Open model search screen |
| `p` | Project Search | Select a different dbt project |
| `q` | Quit | Exit the application |

#### Model View Screen

| Key | Action | Description |
|-----|--------|-------------|
| `E` | External Edit | Open current model in external editor |
| `n` | New Model | Create a new model that refs the current one |
| `Tab` | Switch Focus | Cycle between parents list, model content, and children list |
| `↑↓` | Navigate Lists | Move up/down in parent/child lists |
| `Enter` | Select Model | Navigate to the selected parent/child model |

#### Model Search Screen

| Key | Action | Description |
|-----|--------|-------------|
| Type to search | Live Search | Filter models by name as you type |
| `↑↓` | Navigate Results | Move through search results |
| `Enter` | Select Model | Open the selected model |

#### New Model Screen

| Key | Action | Description |
|-----|--------|-------------|
| Type path | Enter Path | Specify relative path for new model (e.g., `models/staging/stg_users.sql`) |
| `Enter` | Create Model | Create the model and open it |
| `Esc` | Cancel | Close modal without creating |

## Configuration

### Cache and Settings

dbt-tui stores its configuration in your system's cache directory:

- **Linux**: `~/.cache/dbt-tui/cache.json`
- **macOS**: `~/Library/Caches/dbt-tui/cache.json`
- **Windows**: `%LOCALAPPDATA%\dbt-tui\cache.json`

The cache stores:
- Last opened project path
- Last viewed model
- External editor command (default: `vi`)

### External Editor

To configure your preferred external editor, open the options screen (`o` key) and set the editor command. Examples:

- `code` - Visual Studio Code
- `vim` or `vi` - Vim
- `nano` - Nano
- `subl` - Sublime Text

## Project Structure

```
dbt-tui/
├── src/
│   ├── dbt_tui/
│   │   ├── backend/          # Core dbt project logic
│   │   │   ├── project.py    # DbtProject class
│   │   │   ├── model.py      # DbtModel class
│   │   │   ├── fetch.py      # Property fetching utilities
│   │   │   ├── property_claim.py      # Property precedence logic
│   │   │   └── property_discovery.py  # Property discovery from configs
│   │   ├── frontend/         # TUI screens and widgets
│   │   │   ├── main.py       # Main application
│   │   │   ├── model_search/ # Model search interface
│   │   │   ├── model_tree/   # Model dependency tree view
│   │   │   ├── new_model/    # New model creation
│   │   │   └── options/      # Settings screen
│   │   └── common/           # Shared abstractions and utilities
│   │       ├── model.py      # Abstract model interface
│   │       ├── project.py    # Abstract project interface
│   │       └── cache.py      # Configuration persistence
├── tests/                # Test suite
│   └── testing/          # Test dbt project
└── pyproject.toml        # Project dependencies
```

## Architecture

### Backend

The backend implements the core dbt project parsing logic:

- **DbtProject**: Represents a dbt project, loads models from configured model-paths
- **DbtModel**: Represents a single model, parses Jinja2 templates to extract refs and configs
- **PropertyClaim**: Represents a property claim from any configuration source
- **Property Discovery**: Collects properties from dbt_project.yml, schema.yml, and model SQL

### Frontend

Built with [Textual](https://textual.textualize.io/), the frontend provides:

- **Screen-based navigation**: Each feature is a separate screen
- **Reactive state management**: Changes to project/model automatically update UI
- **Keyboard-driven workflow**: All actions accessible via keyboard

### Property Precedence

dbt-tui correctly implements dbt's configuration precedence rules:

1. **Model-level** (highest): `{{ config(...) }}` in SQL files
2. **Schema-level**: `config:` blocks in schema.yml
3. **Project-level** (lowest): `models:` section in dbt_project.yml
   - More specific paths override general ones
   - Example: `models.project.staging.stg_users` > `models.project.staging` > `models.project`

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_property_claims.py

# Run with coverage
pytest --cov=src

# Run with verbose output
pytest -v
```

### Test Project

The `tests/testing/` directory contains a sample dbt project used for testing:

- Multiple model directories (vanilla, complex_config, invalid)
- Models with various configurations
- Schema.yml files with properties and configs
- Project-level configurations in dbt_project.yml

### Adding New Features

1. **Backend changes**: Extend DbtProject or DbtModel in `src/dbt_tui/backend/`
2. **Frontend changes**: Create new screens/widgets in `src/dbt_tui/frontend/`
3. **Add tests**: Write tests in `tests/` following existing patterns
4. **Update abstractions**: Modify `src/dbt_tui/common/` interfaces if needed

## Roadmap

- [x] Enhanced model search (fuzzy matching, filters)
- [x] Property viewer showing all effective configs with sources
- [x] DAG visualization (ASCII graph)
- [x] Model execution (dbt run, dbt test)
- [x] Column-level lineage
- [x] Documentation viewer
- [x] Git integration
- [x] Multiple project workspace

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass (`pytest`)
5. Submit a pull request

## License

[Add your license here]

## Acknowledgments

Built with:
- [Textual](https://textual.textualize.io/) - TUI framework
- [Jinja2](https://jinja.palletsprojects.com/) - Template parsing
- [NetworkX](https://networkx.org/) - Graph operations
- [PyYAML](https://pyyaml.org/) - YAML parsing
