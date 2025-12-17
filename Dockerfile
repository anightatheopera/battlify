FROM python:3.12-slim

WORKDIR /code

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app folder into /code/app
COPY ./app ./app

# Expose port
EXPOSE 8000

# Run command changes: looking for "app.main:app"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]