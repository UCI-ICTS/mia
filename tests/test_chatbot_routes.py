
def test_example(app):
    with app.test_client() as client:
        response = client.get('/admin/')
        assert response.status_code == 200
