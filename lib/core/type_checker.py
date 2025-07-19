
def check_schema(data, schema):
    if isinstance(schema, type):
        return isinstance(data, schema)

    if isinstance(schema, list):
        if not isinstance(data, list) or len(schema) != 1:
            return False
        return all(check_schema(item, schema[0]) for item in data)

    if isinstance(schema, dict):
        if not isinstance(data, dict):
            return False
        for key, val_schema in schema.items():
            if key not in data or not check_schema(data[key], val_schema):
                return False
        return True

    return False

if __name__ == "__main__":
    struct = {
        "name": str,
        "age": int
    }
    
    person = {
        "name": "Darren",
        "age": 16
    }
    
    print(check_schema(person, struct))