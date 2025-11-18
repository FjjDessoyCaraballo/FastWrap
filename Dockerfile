FROM python:3.12.3-slim
   
WORKDIR /app
   
COPY pyproject.toml uv.lock ./
   
RUN apt-get update && apt-get install -y curl && \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    /root/.local/bin/uv sync --frozen
  
COPY . .
   
EXPOSE 8555
 
ENV PATH="/root/.local/bin:$PATH"

CMD ["uv", "run", "main.py"]
