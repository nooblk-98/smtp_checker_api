# smtp-tester
sample

````yaml
curl -X POST http://localhost:5000/check-smtp \
  -H "Content-Type: application/json" \
  -d '{
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "username": "youremail@gmail.com",
    "password": "yourpassword",
    "from_email": "youremail@gmail.com",
    "to_email": "test@example.com"
}'

````

