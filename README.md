# LobbyLens — EU Lobbying Transparency Platform

44% of European citizens say they don't understand how the EU works. Meanwhile, thousands of organizations are spending hundreds of millions of euros every year trying to influence its policies. That information is technically publicly available — but it's scattered across databases, buried in jargon, and hard to access for the average person to find.

That's why we built LobbyLens.

LobbyLens is a web application that allows you to filter and track lobbying activity by policy area and country. It lets you see exactly what organizations are spending, predict how many EU Parliament meetings an organization is likely to get, and track how political parties across the EU shape their national governments.

Information is power, and LobbyLens puts it back in the hands of the people.

## Major Features

- **Meeting Prediction** — Enter an organization's lobbying spend, EP access passes, and staff size to predict how many European Parliament meetings they are likely to secure using our ML model
- **Interactive Scatter Plot** — Compare your organization against every lobbying org in the dataset visually
- **Organization Comparison** — Save and compare two organizations side by side across lobbying spend, policy areas, and ML influence scores
- **Who is Shaping EU Policies?** — Search by policy area and country to see which organizations are lobbying on issues that matter to you
- **Party Parliament Prediction** — Predict whether a European political party is likely to hold parliamentary seats based on ideology scores
- **Which Lobbyists Are Influencing EU Party Groups?** — See which lobbying organizations have met most with each EP political group

## Prerequisites

See [docs/PreReq.md](docs/PreReq.md) for full setup instructions, including Python environment setup with Anaconda/Miniconda or the standard Python virtual environment tool, required tools, and IDE configuration.

## Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/greenbear26/RAMM-Project.git
cd RAMM-Project
```

### 2. Set up your `.env` file
Create a `.env` file in the root of the project based on the `.env.template` file:
```bash
cp .env.template .env
```
Fill in your database credentials in the `.env` file.

### 3. Run the app
```bash
docker compose up -d
```

The Streamlit frontend will be available at `http://localhost:8501` and the Flask API at `http://localhost:4000`.

### 4. Shut down
```bash
docker compose down
```

## How to Use the App

1. Go to `http://localhost:8501`
2. Select a persona (European Citizen, Political Science Researcher, or Political Party Journalist) and log in
3. Each persona has access to different pages tailored to their needs
4. Researchers can use the ML Influence Prediction page to predict EP meetings and compare organizations
5. Journalists can explore party ideology, predict parliamentary representation, and see which lobbyists target which party groups
6. Citizens can explore which organizations are shaping EU policies in their country

## Structure of the Repo

- `./app` - the Streamlit frontend app
- `./api` - the Flask REST API
- `./database-files` - SQL scripts to initialize the MySQL database
- `./datasets` - datasets used for ML model training and EDA
- `./ml-src` - Jupyter notebooks and Python scripts for ML model development
- `./docs` - project documentation

## Deployment

The app is deployed to the course Coolify server and is reachable at `lobbylens.neu-in-leuven.cloud`.

See [docs/StudentDeployment.md](docs/StudentDeployment.md) for full deployment instructions.

## Blog

Our team blog with full project documentation and phase updates can be found at:
[https://rishi.ponnapalli.me/RAMM-DoC-2026/](https://rishi.ponnapalli.me/RAMM-DoC-2026/)

## Team Contributions

| Name | Role | Contributions |
|------|------|---------------|
| Alyssa D. | CS | ER diagrams, wireframes, frontend pages, and data modeling |
| Manav | CS | SQL DDL, database schema, Flask REST API routes, and backend development |
| Mihika | DS | Data cleaning and pipeline, feature engineering, ML 1 development, prediction UI and scatter plot |
| Rishi | DS | Data sourcing from LobbyFacts and World Bank API, EDA, data visualizations, and ML 2 development |

## Data Sources

- [LobbyFacts.eu](https://lobbyfacts.eu) — EU lobbying organization data
- [World Bank API](https://data.worldbank.org) — GDP, population, and economic indicators
- [Integrity Watch EU](https://www.integritywatch.eu) — MEP lobby meeting data
- [Populist Dataset](https://popu-list.org) — European political party ideology scores
- [ParlFacts](http://www.parlgov.org) — Party characteristics and positioning