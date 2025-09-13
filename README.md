# Dossier

A web application for personal research and OSINT (Open Source Intelligence) investigations.

## Project Structure

- `dossier_api/` - FastAPI backend with PostgreSQL database
- `dossier-frontend/` - SvelteKit frontend application

## Features

- User authentication and management
- Person records with contact information
- Social media account validation via Sherlock Project
- Address geocoding and mapping
- Background job processing for username searches

## Development

### Backend API
```bash
cd dossier_api
poetry install
poetry run uvicorn dossier.main:app --reload
```

### Frontend
```bash
cd dossier-frontend/dossier
npm install
npm run dev
```

## License

MIT
