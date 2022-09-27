# Use the official Python image from the Docker Hub
FROM python:3.9-slim-bullseye

RUN apt-get update && apt-get upgrade -y && apt-get install -y python3-dev gcc libev-dev libpq-dev

# make a new directory to put our code in.
RUN mkdir /service/

# copy the rest of the code
COPY . /service/

# change the working directory. 
WORKDIR /service

# upgrade pip
RUN pip install --upgrade pip && pip install wheel 

# install the requirements
RUN pip install -r requirements.txt

# make the file executable
RUN chmod +x bootstrap.sh

# bootstarp the application
ENTRYPOINT ["/service/bootstrap.sh"]

# exposing port
EXPOSE 8050

