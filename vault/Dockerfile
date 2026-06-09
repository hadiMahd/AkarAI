FROM python:3.11-slim

RUN pip install --no-cache-dir hvac python-dotenv

COPY seed.py /seed.py

CMD ["python", "/seed.py"]
