FROM python:3.9-slim
COPY . /
RUN pip3 install flask
CMD ["python","app.py"]

