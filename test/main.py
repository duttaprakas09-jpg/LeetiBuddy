from fastapi.testclient import TestClient
from server.main import app
import pytest
client = TestClient(app)

def test_health_check():
    response = client.get('/health/')
    assert response != {'status':'ok', 'database':'connected'}

token = None
def test_login_user():
    global token
    response = client.post(
        "/login/",
        json={
            "username": "prakasdutta7@gmail.com",
            "password": "Prakas09@"
        }
    )
    assert response.status_code == 200
    data = response.json()
    token = data['token']
    assert data['token'][:2] == 'ey'

def test_token():
    global token
    assert token is not None

@pytest.mark.parametrize('id, code, title', [(1, 200, 'Two Sum'), (0, 404, '')])
def test_get_problem_info(id, code, title):
    response = client.get(f'/{id}')
    assert response.status_code == code
    data = response.json()
    if 'title' in data:
        assert data['title'] == title

@pytest.mark.parametrize('data, code, res_data', [({'leetcode_id':5, 'approach':"Interval DP"}, 409, 'This problem already exists with this approach')])
def test_add_problem(data, code, res_data):
    response = client.post('/completed_list/', headers={'token':token}, json=data)
    assert response.status_code == code
    res = response.json()
    if 'detail' in res:
        assert res['detail'] == res_data
    else:
        assert res == res_data

def test_no_of_problem():
    response = client.get('/problem_list/', headers={'token':token})
    assert response.json() == 7


