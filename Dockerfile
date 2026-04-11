FROM python:3.11-slim

WORKDIR /app

# Set PYTHONPATH so python can resolve the 'bank_env' package
ENV PYTHONPATH="/app"

# Install system dependencies for Tesseract, Poppler
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the rest of the application code into the bank_env directory
COPY . /app/bank_env/

# Set working directory to where app.py lives
WORKDIR /app/bank_env

# Generate a dummy excel file for the mock database
RUN python -c "import pandas as pd; import os; os.makedirs('data', exist_ok=True); pd.DataFrame({'bank_name':['Test Bank'],'date':['10-04-2026'],'payee_name':['John Doe'],'amount_words':['One Thousand Only'],'amount_numbers':[1000],'account_number':['1234567890'],'ifsc_code':['TEST0001234'],'cheque_number':['000001']}).to_excel('data/cheque_data.xlsx', index=False)"

# Expose Streamlit port for Hugging Face Spaces
EXPOSE 7860

# Run the Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port", "7860", "--server.address", "0.0.0.0"]
