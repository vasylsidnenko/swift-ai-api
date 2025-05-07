# Application Frontend

This directory contains the frontend web application for interacting with the MCP server.

## Overview

The frontend is a Flask-based web app that provides a user-friendly interface for generating, validating, and quizzing programming questions using AI agents (OpenAI, Claude, Gemini) via the MCP server API.

### Features
- Select AI provider and model
- Generate programming questions
- Validate answers
- Generate follow-up (user_quiz) questions with various styles including "Humor"
- Enhanced error handling with detailed error messages
- View results in a modern, responsive UI

### Structure
- `app.py` — Main Flask application
- `templates/` — HTML templates (main UI in `index.html`)
- `static/js/` — JavaScript files for UI logic
- `static/css/` — CSS styles

## Usage

1. Ensure the MCP server is running and accessible (see its README for details).
2. Start the frontend app:
   ```sh
   python app.py
   ```
3. Open [http://localhost:10000](http://localhost:10000) in your browser.

The app will automatically fetch available providers and models from the MCP server and update the UI accordingly.

## Environment Variables
- `MCP_SERVER_URL` — URL of the MCP backend (default: `http://localhost:10001`)
- `MOCK_MCP` — Set to `1` to use mock MCP server for frontend development

## Recent Updates

### May 2025
- Added "Humor" style to quiz results with a cheerful yellow theme and emoji icon
- Improved error handling on frontend to display detailed error messages
- Enhanced MCP server to properly handle API quota exceeded errors (429)
- Fixed compatibility issue with 'ai' parameter handling in API requests
- Improved visual representation of different quiz result styles

---

For backend/API details, see the `../mcp_server/README.md` file.
