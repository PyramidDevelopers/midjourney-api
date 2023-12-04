# Use an official Python runtime as a parent image
FROM python:3.9-slim


# Set the working directory in the container
WORKDIR /app

# Copy the /bot contents into the container at /app
COPY . /app

RUN python -m pip install --upgrade pip wheel

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

ENV TERM=xterm-256color


ENV FAST_APP=service:app
ENV PORT 8062
EXPOSE $PORT

# Run the bot when the container launches
CMD ["python", "start_bot.py"]
