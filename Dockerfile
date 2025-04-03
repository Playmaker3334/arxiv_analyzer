FROM python:3.10-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Crear estructura de directorios
RUN mkdir -p /app/input/papers
RUN mkdir -p /app/output/results

# Copiar código fuente
COPY . .

# Volúmenes para papers de entrada y resultados
VOLUME ["/app/input/papers", "/app/output/results"]

# Usuario no root para seguridad
RUN useradd -m appuser
RUN chown -R appuser:appuser /app
USER appuser

# Puerto para posible interfaz web futura
EXPOSE 8000

# Comando por defecto
ENTRYPOINT ["python", "main.py"]
CMD ["--process-all"]