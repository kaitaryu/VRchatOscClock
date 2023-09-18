
cd /d %~dp0
if exist "./.venv" (
    call .\.venv\Scripts\activate 
) else (
    python -m venv .venv
    call .\.venv\Scripts\activate 
    pip install -r requirements.txt
)
python .\main_client.py 
