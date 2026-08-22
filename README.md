# Period-Tracking-and-PCOS-Endometriosis-risk-detection-system
Period tracking app with ML-powered cycle prediction, PCOS risk screening, and symptom clustering — built with Flask & scikit-learn.

## Vercel Deployment Setup

This application requires PostgreSQL for Vercel deployment. SQLite is not supported on Vercel.

### Required Environment Variables

Set these environment variables in your Vercel project settings:

1. **DATABASE_URL** or **POSTGRES_URL** - Your PostgreSQL connection string
   - Format: `postgresql://username:password@host:port/database`
   - You can use Vercel Postgres or any external PostgreSQL database

### Setting up Vercel Postgres

1. Go to your Vercel project dashboard
2. Navigate to **Storage** → **Create Database**
3. Select **Postgres** and create a new database
4. Vercel will automatically set the `POSTGRES_URL` environment variable
5. Redeploy your application

### Using External PostgreSQL

If you prefer to use an external PostgreSQL database:

1. Set the `DATABASE_URL` environment variable in Vercel:
   ```
   DATABASE_URL=postgresql://username:password@host:port/database
   ```
2. Redeploy your application

## Local Development

For local development, the app supports:
- **SQLite** (default, no configuration needed)
- **MySQL** (set `DATABASE_HOST`, `DATABASE_USER`, `DATABASE_PASSWORD`, `DATABASE_NAME`, `DATABASE_PORT`)
- **PostgreSQL** (set `DATABASE_URL` or `POSTGRES_URL`)

## Installation

```bash
pip install -r requirements.txt
python app.py
```

The application will run on `http://localhost:5000`
