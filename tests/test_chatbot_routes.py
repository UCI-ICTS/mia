
def test_example(app):
    # TODO: this test fails because we need to authenticate the user first (not sure how to do that now)
    with app.test_client() as client:
        response = client.get('/admin/')
        assert response.status_code == 200
