FROM python:3-alpine

WORKDIR /app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY ./website ./website

EXPOSE 5000

CMD ["python3", "website/app.py"]
