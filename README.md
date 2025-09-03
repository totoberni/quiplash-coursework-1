# Gaming Platform API

A multilingual gaming platform built with Azure Functions, similar to Quiplash. Players create prompts, get AI suggestions, and compete on leaderboards with automatic translation support.

## What This Does

This backend handles player accounts, multilingual prompt creation, AI-powered suggestions, and competitive rankings. Everything gets automatically translated into 11 languages.

## Tech Stack

- **Azure Functions** - Serverless API
- **Cosmos DB** - Player and prompt storage  
- **Azure Translator** - Multi-language support
- **Azure OpenAI** - Smart prompt suggestions
- **Python 3.x**

## Project Structure

```
function_app.py              # Main API endpoints
shared_code/
├── db_utils.py             # Database connections
├── translator_utils.py      # Translation service
├── prompt_advisor.py        # AI prompt generation
├── podium_utils.py          # Player rankings
└── get_prompts_utils.py     # Prompt retrieval
tests/                       # Unit tests for everything
```

## API Endpoints

### Player Management

**Register a new player**
```
POST /api/player/register
{
    "username": "string (5-15 chars)",
    "password": "string (8-15 chars)"
}
```

**Login**
```
POST /api/player/login  
{
    "username": "string",
    "password": "string"
}
```

**Update player stats**
```
PUT /api/player/update
{
    "username": "string",
    "add_to_games_played": 1,
    "add_to_score": 150
}
```

### Prompts

**Create a prompt** (gets auto-translated to all languages)
```
POST /api/prompt/create
{
    "text": "string (20-100 chars)",
    "username": "string"
}
```

**Get AI suggestion**
```
POST /api/prompt/suggest
{
    "keyword": "technology"
}
```

**Delete all player's prompts**
```
POST /api/prompt/delete
{
    "player": "username"
}
```

### Game Utilities

**Get leaderboard**
```
GET /api/utils/podium
```

**Get prompts for gameplay**
```
POST /api/utils/get
{
    "players": ["username1", "username2"],
    "language": "en"
}
```

## Supported Languages

English, Spanish, Italian, Swedish, Russian, Indonesian, Bulgarian, Chinese (Simplified), Hindi, Irish, Polish

## Database Setup

You need two Cosmos DB containers:

**Players**
```json
{
    "id": "uuid",
    "username": "string",
    "password": "string", 
    "games_played": 0,
    "total_score": 0
}
```

**Prompts**
```json
{
    "id": "uuid",
    "username": "string",
    "texts": [
        {"language": "en", "text": "What's your favorite pizza topping?"},
        {"language": "es", "text": "¿Cuál es tu ingrediente favorito para la pizza?"}
    ]
}
```

## Environment Variables

Create a `local.settings.json` file:

```json
{
    "Values": {
        "AzureCosmosDBConnectionString": "your_cosmos_connection_string",
        "DatabaseName": "your_database_name",
        "PlayerContainerName": "players",
        "PromptContainerName": "prompts",
        "TranslationKey": "your_translator_key",
        "TranslationEndpoint": "your_translator_endpoint", 
        "TranslationRegion": "your_region",
        "OAIKey": "your_openai_key",
        "OAIEndpoint": "your_openai_endpoint",
        "gpt-35-turbo": "your_model_deployment_name"
    }
}
```

## How the Ranking System Works

Players are ranked by points per game ratio (total_score / games_played). Tiebreakers:
1. Fewer games played wins
2. Alphabetical username wins

The podium shows gold, silver, and bronze positions with all tied players.

## Key Features

**Smart Prompt Creation**: When you create a prompt, it automatically detects the language and translates it to all supported languages.

**AI Suggestions**: Give it a keyword and get back a creative prompt suggestion that includes your keyword.

**Flexible Player Updates**: Add or subtract from player stats. Negative totals get reset to zero.

**Multi-player Queries**: Get prompts from multiple players in any supported language for gameplay.

## Running Tests

```bash
python -m unittest discover tests/
```

Tests cover database connections, translations, AI generation, player operations, and prompt retrieval.

## Quick Start Example

```bash
# Register
curl -X POST /api/player/register -d '{"username": "alice", "password": "password123"}'

# Create a prompt (auto-translates)  
curl -X POST /api/prompt/create -d '{"text": "What makes you laugh?", "username": "alice"}'

# Get AI suggestion
curl -X POST /api/prompt/suggest -d '{"keyword": "food"}'

# Update stats after game
curl -X PUT /api/player/update -d '{"username": "alice", "add_to_games_played": 1, "add_to_score": 200}'

# Check leaderboard
curl -X GET /api/utils/podium
```

## Things to Know

- Passwords are stored in plain text (you might want to fix this)
- All responses use 200 status codes, even for errors
- Language detection needs 70% confidence to work
- AI suggestions try multiple times if the keyword doesn't appear
- Zero games played gives you a ranking of zero

## Dependencies

```
azure-functions
azure-cosmos  
azure-ai-translation-text
openai
uuid
```

This is a solid foundation for a multilingual gaming platform. The automatic translation and AI features make it pretty flexible for different types of word games.
