FROM python:3-alpine

WORKDIR /app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY ./imageserver ./imageserver

EXPOSE 8080

CMD ["python3", "imageserver/app.py"]
