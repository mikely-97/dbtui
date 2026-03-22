import uuid

with open('src/frontend/lorem.txt') as f:
    lorem = f.read()

def rand_uuid() -> str:

    raw = uuid.uuid4()
    return raw.urn
