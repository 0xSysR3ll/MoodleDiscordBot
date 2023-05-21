# Use an official Python runtime as a parent image
FROM python:3-slim-buster

# Set the working directory in the container
WORKDIR /app

# Add the current directory contents into the container at /app
ADD app/ .

# Set the timezone
RUN ln -snf /usr/share/zoneinfo/Europe/Paris /etc/localtime && echo Europe/Paris > /etc/timezone

# Install locales package and generate French locale
RUN apt-get update && apt-get upgrade -y && apt-get install -y locales && rm -rf /var/lib/apt/lists/* \
    && echo "fr_FR.UTF-8 UTF-8" > /etc/locale.gen && locale-gen

# Set environment variables for locale
ENV LC_ALL fr_FR.UTF-8
ENV LANG fr_FR.UTF-8
ENV LANGUAGE fr_FR.UTF-8

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && pip install --no-cache-dir -U pip

# Run main.py when the container launches
CMD ["python", "-u", "main.py"]
