FROM ubuntu:20.04
RUN apt-get update
RUN apt-get install -y python3 python3-pip
RUN pip3 install flask pymongo
RUN pip3 install --upgrade pip
RUN mkdir /app
RUN mkdir -p /app/data
COPY DigitalNotes.py /app/DigitalNotes.py
EXPOSE 5000
WORKDIR /app
ENTRYPOINT ["python3" , "-u" , "DigitalNotes.py" ]

