# 🎯 QuestBot — Telegram Quest System with Role-Based Access and Stations

## 📖 Project Overview

**QuestBot** is a Telegram bot designed for managing quest-style events with multiple user roles:

- 👤 **Curator (Participant)** — represents a team, selects stations, and earns points.  
- 🧑‍💼 **Station Organizer** — manages an assigned station, confirms completions, and awards points.  
- 👑 **Main Organizer (Admin)** — oversees the entire event, opens/closes registration, broadcasts announcements, and manually adjusts scores.

The project is fully containerized using **Docker**, utilizes **PostgreSQL** for data storage, and runs in an isolated environment.

---

## ⚙️ Main Features

### 🧭 General Commands

| Command | Description |
|----------|-------------|
| `/start` | Displays a greeting message (varies by user role) |
| `/help` | Shows available commands |
| `/free` | Displays a list of free stations |

### 🧍 For Curators (Participants)

| Command | Description |
|----------|-------------|
| `/reg_user [group_number]` | Registers a participant (group format: `1XX`) |
| `/info` | Shows current points and progress history |
| `/take [N]` | Takes a free station number **N** for the quest |

### 🧑‍🏫 For Station Organizers

| Command | Description |
|----------|-------------|
| `/reg_org [N]` | Registers the user as the organizer of station **N** |
| `/station` | Shows information about the assigned station |
| `/reward [N]` | Adds **N** base points to a group |
| `/reward_bonus [N]` | Adds **N** bonus points |
| *(Button)* “Station Free” | Marks the station as available again |

### 👑 For Main Organizers (Admins)

| Command | Description |
|----------|-------------|
| `/open` | Opens organizer registration |
| `/close` | Closes registration |
| `/begin` | Starts the quest |
| `/end` | Ends the quest |
| `/pay [group] [N]` | Manually adds **N** points to a group |
| `/mailing [text]` | Sends a broadcast message to all users |
| `/stats` | Displays global statistics |

## 🐳 Deployment via Docker

### 1️⃣ Create a `.env` file

```env
BOT_TOKEN=your_bot_token
POSTGRES_USER=quest_user
POSTGRES_PASSWORD=quest_password
POSTGRES_DB=quest_db
POSTGRES_HOST=db
POSTGRES_PORT=5432
```
2️⃣ Build and start containers
```bash
docker-compose build
docker-compose up -d
```
After startup, the bot automatically connects to the database and initializes all required tables.

🧰 Database Management
Check that the database is running
```bash
docker ps
```
Access the PostgreSQL container
```bash
docker exec -it questbot-db psql -U quest_user -d quest_db
```
Add an admin manually
```sql
INSERT INTO users (tg_id, role) VALUES (123456789, 'admin')
ON CONFLICT (tg_id) DO UPDATE SET role = EXCLUDED.role;
```
🧱 Initial Data
At initialization, the system populates test stations with the following locations:

1. 329
2. above room 101
3. near the ping-pong tables
4. 253
5. above the cafeteria
6. E-hall
7. 210D
8. 235
9. E-hall
10. 217
11. E-hall
12. 212D
13. "Bank" area (2nd floor)
14. 2nd floor above the entrance (windows to Math Dept.)
15. 248
16. 240
17. outside
18. outside

🛡️ Security

Commands are protected by role-based decorators (@require_role(...)).
Admin commands are restricted from regular users.
Secrets and credentials are securely stored in .env.
Database access is limited to internal Docker networking.

🧠 Requirements:
Python 3.11+
PostgreSQL 15+
Docker / Docker Compose

Python packages:
```bash
python-telegram-bot
SQLAlchemy
psycopg2-binary
python-dotenv
dotenv
```

📊 Project Status
✅ Core functionality implemented
🚀 Ready for deployment via Docker
🔧 Future enhancement: web-based admin dashboard

👨‍💻 Author
Dmitry
Software Engineer — specializing in Python backend and Telegram bot development.
