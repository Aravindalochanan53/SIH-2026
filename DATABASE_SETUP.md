# TRANSLARA — Database Setup & MSSQL Configuration

## 1. Database Configuration
TRANSLARA uses **SQLAlchemy ORM** to connect to **Microsoft SQL Server (MSSQL)** with automatic local **SQLite** fallback.

### MSSQL Connection String
Set `DATABASE_URL` in your `.env` file:
```env
# MSSQL with ODBC Driver 17 / 18
DATABASE_URL=mssql+pyodbc://sa:YourStrongPassword123@localhost:1433/translara_db?driver=ODBC+Driver+17+for+SQL+Server

# Or SQLite for local/offline testing:
DATABASE_URL=sqlite:///./data/translara.db
```

---

## 2. Relational Schema & Tables
| Table | Description |
| :--- | :--- |
| `users` | User accounts, roles (`teacher`, `admin`, `student`), preferred language pairs |
| `languages` | Registered pan-Indian languages, scripts, active statuses |
| `translations` | Persisted translations and verified classroom expressions |
| `translation_history` | Audit log of text, voice, video, and chatbot translation requests |
| `classroom_phrases` | Pre-cached classroom instructions, FLN numeracy, and literacy phrases |
| `entities` | Named entities, proper names, and school gazetteer entries |
| `video_jobs` | Video translation job lifecycle, statuses, and generated artifact URLs |
| `chat_history` | AI Assistant vernacular pedagogical conversations |
| `worksheets` | Generated printable A4 FLN PDF worksheets |
| `flashcards` | Multilingual vocabulary and classroom flashcards |

---

## 3. Database Initialization
```bash
# Start backend to initialize tables and seed offline phrases
python -m uvicorn backend.server:app --host 0.0.0.0 --port 8000 --reload
```
