# Claw Autolearn - Autonomous Learning System

Proactively researches topics and builds knowledge without being asked.

## Overview

`claw_autolearn.py` is an autonomous learning system that:
- Periodically picks topics from a curated list
- Researches them using web search (Brave API)
- Fetches and reads relevant articles
- Extracts key insights and synthesizes knowledge
- Stores structured knowledge in `memory/learned_knowledge/`
- Tracks learned topics to avoid duplicates

## Installation

The tool is installed at `/config/clawd/tools/claw_autolearn.py` with a symlink:
```bash
autolearn  # Global command
```

## CLI Usage

```bash
# Learn about a random topic
autolearn

# Learn about a specific topic
autolearn --topic "machine learning"

# List all learned topics
autolearn --list

# Show system status
autolearn --status

# Read knowledge about a topic
autolearn --read "python"

# Force relearn an already-learned topic
autolearn --topic "AI" --force
```

## Cron Setup

### Option 1: Run Setup Script
```bash
/config/clawd/tools/setup-autolearn-cron.sh
```

### Option 2: Home Assistant Automation
Add to `configuration.yaml`:
```yaml
shell_command:
  claw_autolearn: 'cd /config/clawd && python3 tools/claw_autolearn.py >> /config/clawd/logs/autolearn_cron.log 2>&1'

automation:
  - alias: 'Claw Daily Autolearn'
    trigger:
      platform: time
      at: '09:00:00'
    action:
      service: shell_command.claw_autolearn
```

### Option 3: Systemd Timer
```bash
sudo cp /config/clawd/data/autolearn-daily.service /etc/systemd/system/
sudo cp /config/clawd/data/autolearn-daily.timer /etc/systemd/system/
sudo systemctl enable --now autolearn-daily.timer
```

### Option 4: Docker Host Cron
```bash
# On the Docker host, add to crontab:
0 9 * * * docker exec <container_name> /usr/local/bin/autolearn
```

## Configuration

### Environment Variables
- `BRAVE_API_KEY` - Brave Search API key for web search

### Files
- `memory/learned_knowledge/autolearn_state.json` - Learning state and history
- `memory/learned_knowledge/topic_queue.json` - Topic queue management
- `memory/learned_knowledge/<id>.json` - Individual topic knowledge files
- `logs/autolearn_cron.log` - Cron execution logs

## Topic Categories

The system comes with 71 pre-seeded topics across:
- AI & Machine Learning (11 topics)
- Programming & Software Engineering (15 topics)
- DevOps & Infrastructure (12 topics)
- Data & Databases (6 topics)
- Security (5 topics)
- Web & Frontend (6 topics)
- Emerging Tech (6 topics)
- Productivity & Tools (6 topics)
- Philosophy of Technology (5 topics)

Topics are automatically cycled through. When all are learned, the queue resets.

## Knowledge Format

Each learned topic is stored as JSON:
```json
{
  "id": "abc123...",
  "topic": "topic name",
  "learned_at": "2026-02-09T21:30:00",
  "knowledge": {
    "summary": "...",
    "themes": {
      "definitions": [...],
      "concepts": [...],
      "practices": [...],
      "tools": [...],
      "considerations": [...]
    },
    "sources": [...]
  },
  "articles_read": 3,
  "version": "1.0"
}
```

## Logs

- **Cron logs**: `/config/clawd/logs/autolearn_cron.log`
- **State**: `/config/clawd/memory/learned_knowledge/autolearn_state.json`

## Requirements

- Python 3.8+
- Brave API key (optional but recommended)
- Internet connection for web search

## API Key Setup

Add to `/config/clawd/.env`:
```
BRAVE_API_KEY=your_api_key_here
```

Get a free API key at: https://brave.com/search/api/
