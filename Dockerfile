# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install Poetry
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -

# Set PATH for Poetry
ENV PATH="$HOME/.poetry/bin:$PATH"

# Set the working directory in the container
WORKDIR /app

# Copy only the dependencies definition files
COPY poetry.lock pyproject.toml /app/

# Install dependencies
RUN poetry install --no-root --no-dev

# Copy the rest of the application code into the container at /app
COPY . /app/

# Expose the port that FastAPI runs on
EXPOSE 8000

# Command to run the FastAPI application using Poetry
CMD ["poetry", "run", "python3", "-B", "app/main.py"]
