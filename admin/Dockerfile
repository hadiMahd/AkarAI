FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

RUN mkdir -p /app/admin
# Create the admin package with a real __init__.py
RUN touch /app/admin/__init__.py

# Copy library modules into the admin package so "from admin.xxx" imports work
COPY api_client.py auth.py components.py insights_view.py audit_logs_view.py role_access_view.py /app/admin/
# Copy Streamlit entry point and view modules to top-level /app
COPY app.py /app/
COPY insights_view.py audit_logs_view.py role_access_view.py /app/
# Reuse the main entry point inside the admin package for tests
RUN cp /app/app.py /app/admin/
# Copy test suite for testability
COPY tests/ /app/tests/
COPY requirements.txt /app/

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
