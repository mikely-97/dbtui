import uuid

lorem = open('src/frontend/lorem.txt', 'r').read()

def rand_uuid() -> str:

    raw = uuid.uuid4()
    return raw.urn
