#Start with a ready-made computer that already has Python 3.11 installed
FROM python:3.11-slim  
#Prevents Python from creating .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
#Makes logs appear immediately in terminal
ENV PYTHONUNBUFFERED=1
#All work will happen inside /app folder
WORKDIR /app
#Copies requirements.txt from the PC to container
COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

    #Copies entire project code into container
COPY . .

EXPOSE 8000

#Default command when container starts
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
