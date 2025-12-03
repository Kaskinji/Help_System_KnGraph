import requests

import requests


def clear_repository(repository="KNgraph"):
    GRAPHDB_URL = "http://localhost:7200"
    with requests.Session() as session:
        session.auth = ('admin', 'root')
        sparql_update = """
        DELETE {
          ?s ?p ?o
        }
        WHERE {
          ?s ?p ?o
        }
        """

        headers = {
            'Content-Type': 'application/sparql-update',
            'Accept': '*/*'
        }

        response = session.post(
            f"{GRAPHDB_URL}/repositories/{repository}/statements",
            data=sparql_update,
            headers=headers
        )
        if response.status_code == 204:
            print(f"Done")
        return None


GRAPHDB_URL = "http://localhost:7200"
REPOSITORY = "KNgraph"
session = requests.Session()
session.auth = ('admin', 'root')

with open("..\TTL\определение_подключения_к_000.ttl", 'rb') as f:
    content = f.read()
    response = session.post(
        f"{GRAPHDB_URL}/repositories/{REPOSITORY}/statements",
        data=content,
        headers={'Content-Type': 'application/x-turtle'}
    )

# Проверяем количество троек
size = session.get(f"{GRAPHDB_URL}/repositories/{REPOSITORY}/size")
print(f"Размер репозитория: {size.text} троек")