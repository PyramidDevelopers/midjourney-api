# Use an official Python runtime as a parent image
FROM python:3.9-slim

RUN apt-get update && \
    apt-get install -y sudo vim make git zip tree curl wget jq gcc libpq-dev build-essential cmake libcurl4-openssl-dev libssl-dev && \
    apt-get autoremove -y && \
    apt-get clean -y


ARG USERNAME=athenaDev
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Create the user with passwordless sudo privileges
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME -s /bin/bash \
    && usermod -aG sudo $USERNAME \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME


# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

RUN python -m pip install --upgrade pip wheel

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

ENV TERM=xterm-256color

USER $USERNAME

ENV FAST_APP=service:app
ENV PORT 8062
EXPOSE $PORT

# Run the bot when the container launches
CMD ["python", "server.py"]
