FROM python:3.10-slim

WORKDIR /app

# 複製並安裝依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製程式碼
COPY . .

# 曝露 8000 port 給 Fly.io 內部轉發
EXPOSE 8000

# 啟動伺服器
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
