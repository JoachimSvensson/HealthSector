FROM python:3.9.18-slim


WORKDIR /flask-app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .


# WORKDIR /flask-app/name_of_final_app_folder?

# RUN flask db init
# RUN flask db migrate
# RUN flask db upgrade
ENV FLASK_APP=run.py 
ENV FLASK_RUN_HOST=0.0.0.0
EXPOSE 5000
CMD ["flask", "run"]