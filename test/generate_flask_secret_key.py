# import os
# secret_key = os.urandom(24).hex()
# print(secret_key)

curl -X POST http://127.0.0.1:5000/api/divisions   -H "Content-Type: application
/json"   -d '{
        "title": "Intermediate Division (Div B)",
        "description": "Middle division",
        "minRating": 700,
        "maxRating": 1300,
        "price": 750
      }'