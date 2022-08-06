en caso de usar gitpod usar los comando de pipenv

pipenv shell
pipenv installs


iniciacion de projecto en local

python -m venv venv
.\venv\Scripts\activate

en caso de reiniciar la dba adjunta 
flask db init
flask db migrate
flask db upgrade 

con base de datos creada inicias la api con 
python app.py runserver