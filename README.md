# OmniCampus 🎓

**SDxUCSD Agent Hackathon · Track 2: Omnara**

A parallel AI agent network that connects CSU students to the right campus resources instantly. Three specialized agents — Academic Advising, Financial Aid, and Student Wellness — run simultaneously in the cloud, each powered by AWS Bedrock RAG against real CSU documents, and all orchestrated through Omnara's command center with live mobile monitoring and human-in-the-loop oversight.

---

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Fill in your AWS credentials and Omnara API key
```

### 3. Provision AWS Knowledge Bases (one-time)
```bash
python scripts/setup_knowledge_bases.py
```
Copy the output KB IDs into your `.env` file.

### 4. Run the app
```bash
streamlit run app.py
```

---

## Architecture

```
Student (Streamlit UI)
        ↓
OmniCampus Orchestrator  (Python ThreadPoolExecutor)
        ↓ parallel
┌──────────────────────────────────────────┐
│  📚 Advising   💰 FinAid   🧠 Wellness  │
└──────┬───────────┬──────────┬────────────┘
       ↓           ↓          ↓
  Bedrock KB   Bedrock KB  Bedrock KB
       ↓           ↓          ↓
  Claude Haiku 4.5 (per agent)
        ↓
┌──────────────────────────────────────────┐
│        Omnara Command Center             │
│ Live stream · HITL · Push Notifications  │
└──────────────────────────────────────────┘
```

---

## Environment Variables

| Variable | Description |
|---|---|
| `AWS_ACCESS_KEY_ID` | AWS credentials |
| `AWS_SECRET_ACCESS_KEY` | AWS credentials |
| `AWS_REGION` | Default: `us-east-1` |
| `S3_BUCKET_NAME` | S3 bucket holding CSU documents |
| `BEDROCK_KB_ROLE_ARN` | IAM role for Bedrock Knowledge Bases |
| `OPENSEARCH_COLLECTION_ARN` | OpenSearch Serverless collection |
| `KB_ADVISING_ID` | Bedrock KB ID for Advising agent |
| `KB_FINAID_ID` | Bedrock KB ID for FinAid agent |
| `KB_WELLNESS_ID` | Bedrock KB ID for Wellness agent |
| `OMNARA_API_KEY` | Omnara SDK key for monitoring + HITL |

---

## Project Structure

```
omnicampus/
├── app.py                        # Streamlit UI (3 tabs)
├── agents/
│   ├── base_agent.py             # Shared RAG + Omnara logic
│   ├── advising_agent.py
│   ├── finaid_agent.py
│   └── wellness_agent.py
├── core/
│   ├── bedrock_client.py         # retrieve_and_generate wrapper
│   └── omnara_client.py          # Omnara SDK wrapper + HITL fallback
├── data/
│   ├── advising/                 # Source PDFs (gitignored)
│   ├── finaid/
│   └── wellness/
├── scripts/
│   └── setup_knowledge_bases.py  # One-time AWS provisioning
├── requirements.txt
└── .env.example
```

---

## Features

- **Parallel Execution** — All three agents fire simultaneously via `ThreadPoolExecutor`. Total time = slowest agent, not the sum.
- **Human-in-the-Loop** — Any agent can pause and push a notification to a supervisor via Omnara. Supervisor replies from their phone; agent resumes.
- **Omnara Live Dashboard** — Every event streams to Omnara web + mobile + watchOS in real time.
- **Source Citations** — Every answer shows which S3 document it was retrieved from.
- **Broadcast Mode** — Tab 2 sends one question to all three agents and displays a side-by-side comparison.

---

*Built for SDxUCSD Agent Hackathon · Track 2: Omnara · April 2026*  
*Stack: AWS Bedrock · Claude Haiku 4.5 · Omnara · Streamlit · Python*
