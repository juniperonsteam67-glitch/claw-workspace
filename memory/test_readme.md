# OpenClaw

OpenClaw is a personal AI assistant framework designed to be extensible, secure, and human-friendly.

## Description

OpenClaw provides a modular architecture where AI agents can interact with various tools and services while maintaining privacy and security. The framework is designed to be self-hosted and gives users full control over their data.

## Installation

```bash
# Clone the repository
git clone https://github.com/example/openclaw.git
cd openclaw

# Install dependencies
pip install -r requirements.txt

# Configure your environment
cp .env.example .env
# Edit .env with your settings
```

## Usage

### Basic Commands

```bash
# Start the gateway
openclaw gateway start

# Check status
openclaw gateway status

# Run a command
openclaw run "your command here"
```

### Configuration

Edit the `SOUL.md` file to customize your agent's personality and capabilities.

## Commands

- `openclaw gateway start` - Start the gateway daemon
- `openclaw gateway stop` - Stop the gateway daemon
- `openclaw gateway status` - Check gateway status
- `openclaw learn <source>` - Learn from documentation
- `openclaw query <keyword>` - Query learned knowledge

## Options

| Option | Description |
|--------|-------------|
| `--verbose` | Enable verbose output |
| `--config PATH` | Use custom config file |
| `--debug` | Enable debug mode |

## Examples

### Example 1: Start the gateway with verbose logging

```bash
openclaw gateway start --verbose
```

### Example 2: Learn from a man page

```bash
openclaw learn man:curl
```

### Example 3: Query for file operations

```bash
openclaw query "list files"
```

## API Reference

### Core Classes

```python
from openclaw import Agent, Tool

agent = Agent()
agent.load_tools()
result = agent.run("Hello")
```

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## License

MIT License - see LICENSE file for details.
