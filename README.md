# SAI Voice OS

Streamlit-ready interface for SAI Voice OS.

## Run on Streamlit Community Cloud

1. Create/select this GitHub repository.
2. Choose **Create app**.
3. Main file: `app.py`.
4. Python: 3.11+.

## Optional Claude service

Set this Streamlit secret:

```toml
SAI_CLAUDE_URL = "https://your-supabase-project.supabase.co/functions/v1/sai-claude"
```

Do not put API keys directly in the repository.

## Included now

- Local current time response
- Local current date response
- Safe basic calculator
- Optional external SAI/Claude answer service
- Mobile-friendly Streamlit interface

Source assistant behavior was adapted from the provided SAI/Jarvis Python code.
