# MailMind 

## Overview:
A powerful AI-powered email management system that combines intelligent email organization with conversational AI capabilities. MailMind helps you manage your emails more efficiently by providing smart categorization, search, and chat-based interactions with your email data.

## UI Demo:
### Light Mode:
![image](public/light_mode.png)
### Dark Mode:
![image](public/dark_mode.png)
### Chatbot:
![image](public/chatbot.png)


## 🌟 Features

- **Smart Email Management**: Organize emails with intelligent categorization and filtering
- **AI-Powered Chat**: Ask questions about your emails and get intelligent responses
- **Real-time Synchronization**: Seamless email sync with popular email providers via Aurinko
- **Modern UI**: Clean, responsive interface built with Next.js and shadcn/ui
- **Virtual Scrolling**: Efficient handling of large email lists
- **Advanced Search**: Powerful search capabilities across your email data
- **RAG (Retrieval-Augmented Generation)**: AI-powered email content analysis and responses

## 🏗️ Tech Stack

### Frontend

- **Framework**: Next.js 15 with TypeScript
- **UI Components**: shadcn/ui with Radix UI primitives
- **Styling**: Tailwind CSS 4
- **State Management**: Jotai, SWR for data fetching
- **Virtual Scrolling**: React Window for performance optimization
- **Form Handling**: React Hook Form with Zod validation
- **Icons**: Lucide React




### Backend

- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL (Neon)
- **ORM**: SQLAlchemy 2.0 with async support
- **Authentication**: JWT with python-jose
- **Email Integration**: Aurinko API
- **AI/ML**: OpenAI GPT integration for RAG service
- **Database Migrations**: Alembic
- **CORS**: FastAPI CORS middleware

### Development Tools

- **Package Manager**: pnpm (frontend), pip (backend)
- **Code Quality**: ESLint, TypeScript
- **Database**: PostgreSQL with async SQLAlchemy
- **Environment**: Python dotenv for configuration

## 🚀 Getting Started

### Prerequisites

- **Node.js** 18+ and **pnpm**
- **Python** 3.10+
- **PostgreSQL** database (or Neon account)
- **Aurinko API** credentials
- **OpenAI API** key (optional, for AI features)

### Backend Setup

1. **Navigate to the backend directory**:

   ```bash
   cd backend
   ```

2. **Create a virtual environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirement.txt
   ```

4. **Environment Configuration**:
   Create a `.env` file in the project root with:

   ```env
   # System
   DEBUG=False

   # Aurinko Email API
   AURINKO_CLIENT_ID=your_aurinko_client_id
   AURINKO_CLIENT_SECRET=your_aurinko_client_secret
   AURINKO_BASE_URL=https://api.aurinko.io
   AURINKO_SYNC_DAYS_WITHIN=3

   # Application URLs
   FRONTEND_URL=http://localhost:3000
   BACKEND_URL=http://localhost:8000

   # Database
   DATABASE_URL=postgresql://username:password@host:port/database
   DATABASE_POOL_SIZE=10
   DATABASE_POOL_TIMEOUT=30
   DATABASE_MAX_OVERFLOW=20

   # AI (Optional)
   OPENAI_API_KEY=your_openai_api_key
   OPENAI_MODEL=gpt-3.5-turbo

   # Security
   SECRET_KEY=your_secret_key_here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```

5. **Initialize the database**:

   ```bash
   # Run migrations
   alembic upgrade head

   # Initialize database (if needed)
   python -m app.init_db
   ```

6. **Start the backend server**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. **Navigate to the frontend directory**:

   ```bash
   cd frontend
   ```

2. **Install dependencies**:

   ```bash
   pnpm install
   ```

3. **Environment Configuration**:
   Create a `.env.local` file:

   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

4. **Start the development server**:
   ```bash
   pnpm dev
   ```

The application will be available at:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📁 Project Structure

```
mailmind/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/               # API routes
│   │   │   └── routes/        # Route handlers
│   │   ├── core/              # Core configurations
│   │   ├── services/          # Business logic (RAG, etc.)
│   │   ├── models.py          # SQLAlchemy models
│   │   ├── crud.py            # Database operations
│   │   └── main.py            # FastAPI app
│   ├── alembic/               # Database migrations
│   └── requirement.txt        # Python dependencies
├── frontend/                   # Next.js frontend
│   ├── src/
│   │   ├── app/               # Next.js app router
│   │   ├── components/        # React components
│   │   ├── hooks/             # Custom React hooks
│   │   └── lib/               # Utility functions
│   └── package.json           # Node.js dependencies
└── public/                    # Static assets
```

## 🔧 API Documentation

Once the backend is running, visit http://localhost:8000/docs for interactive API documentation powered by FastAPI's automatic OpenAPI generation.

### Key Endpoints

- `POST /api/auth/login` - User authentication
- `GET /api/mail/threads` - Fetch email threads
- `POST /api/chat/ask` - AI chat interface
- `GET /api/mail/sync` - Sync emails from provider

## 🤖 AI Features

MailMind includes a RAG (Retrieval-Augmented Generation) service that allows you to:

- Ask questions about your emails
- Get summaries of conversations
- Find specific information across your email history
- Generate smart replies based on context

## 🔒 Security

- JWT-based authentication
- CORS protection
- SQL injection prevention through SQLAlchemy ORM
- Environment-based configuration management

## 🧪 Development

### Running Tests

Backend:

```bash
cd backend
pytest
```

### Database Migrations

Create a new migration:

```bash
cd backend
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:

```bash
alembic upgrade head
```

## 📝 License

This project is licensed under the terms specified in the LICENSE file.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For support or questions about MailMind, please open an issue on the GitHub repository.

---

Built with ❤️ using FastAPI, Next.js, and modern web technologies.
