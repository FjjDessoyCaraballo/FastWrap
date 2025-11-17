FROM python:3.12.3-slim
   
WORKDIR /app
   
RUN apt-get update && apt-get install -y curl && \
     curl -LsSf https://astral.sh/uv/install.sh | sh  
   
COPY pyproject.toml uv.lock ./
   
ENV PATH="/root/.cargo/bin:$PATH"
   
RUN /root/.cargo/bin/uv sync --frozen
  
COPY . .
   
EXPOSE 8555
 
CMD . $HOME/.cargo/env && uv run main.py
