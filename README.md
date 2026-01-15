# AI Self-Review Generator

A tool to help engineers write their performance self-reviews by analyzing merged PRs and generating summaries aligned with job requirements.

## Quick Start (Local Development)

### 1. Install Dependencies

```bash
make install
```

### 2. Configure Secrets

Create a `secrets.json` file in the project root:

```json
{
  "openai_api_key": "sk-xxx"
}
```

### 3. Start the Servers

**Terminal 1 - Start the API server:**
```bash
make api
```

**Terminal 2 - Start the frontend:**
```bash
make frontend
```

### 4. Open the App

Open http://localhost:5173 in your browser.

## Usage

1. Enter your **GitHub repositories** (e.g., `myorg/myrepo`) - supports multiple repos
2. Enter the **year** to analyze
3. Enter your **GitHub username** and **Personal Access Token**
4. Edit the **Role Requirements** to match your job criteria
5. Click **Generate Self-Review**

The app will:
1. Fetch all your merged PRs from that year across all specified repositories
2. Group them by label/project
3. Generate AI summaries aligned with your role requirements
4. Display the result (which you can copy)
