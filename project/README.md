# Multi-Agent Action Programs Analysis System

A desktop application for designing and analyzing action programs in multi-agent systems, built with Python and PyQt5.

## Features

- Domain representation using action language
- Program analysis with query language
- State simulation and visualization
- Built-in database of example problems
- Modern and intuitive user interface

## Requirements

- Python 3.8 or higher
- PyQt5
- SQLite3

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd project
```

2. Initialize the project:
```bash
python init.py
```

This will:
- Create the required directory structure
- Initialize the SQLite database with example problems
- Install all required dependencies

## Running the Application

```bash
python main.py
```

## Usage

1. Select a problem from the database or create a new one
2. Edit the domain definition using the action language
3. Run queries to analyze the program
4. View state transitions and simulation results

### Action Language Syntax

```
causes action(agent) effect [if conditions]
releases action(agent) fluent
impossible action(agent) if conditions
always effect
```

### Query Language Syntax

```
always executable program
sometimes accessible goal from initial in program
realisable program by group
active agent in action by group
```

## Example Problems

The system comes with several pre-defined example problems:

- Tank Crew Mission
- Football Team
- Rescue Team
- Fire Brigade
- Medical Diagnosis

## Development

### Project Structure

```
project/
│
├── main.py                 # Main application
├── ui/                     # User interface files
├── engine/                 # Core logic
│   ├── parser.py          # Language parser
│   ├── executor.py        # Action executor
│   └── semantics.py       # Semantic analyzer
├── db/                     # Database
│   ├── problems.db        # SQLite database
│   ├── schema.sql         # Database schema
│   └── database.py        # Database manager
├── tests/                  # Unit tests
│   └── test_core.py       # Core functionality tests
└── assets/                # Resources
```

### Running Tests

```bash
pytest tests/
```

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request 