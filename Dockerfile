FROM python:3.12.3-slim
   
WORKDIR /app
   
COPY pyproject.toml uv.lock ./
   
RUN apt-get update && apt-get install -y curl && \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    mv /root/.local/bin/uv /usr/local/bin/uv
  
COPY . .
   
EXPOSE 8555
 
ENV UV_CACHE_DIR=/tmp/uv-cache

CMD ["uv", "run", "main.py"]
