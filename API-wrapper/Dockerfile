FROM python:3.12.3-slim
   
WORKDIR /app
   
RUN apt-get update && apt-get install -y curl && \
     curl -LsSf https://astral.sh/uv/install.sh | sh
   
ENV PATH="/root/.cargo/bin:$PATH"
   
COPY pyproject.toml uv.lock ./
   
RUN uv sync --frozen
   
COPY . .
   
EXPOSE 8555
   
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8555"]
