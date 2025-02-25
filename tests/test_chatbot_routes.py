
def test_example(app):
    # TODO: this test fails because we need to authenticate the user first (not sure how to do that now)

    # SO example...
    # class LoginTestCase(TestCase):
    #     def setUp(self):
    #         self.client = Client()
    #         self.user = User.objects.create_user('john', 'lennon@thebeatles.com', 'johnpassword')
    #
    #     def testLogin(self):
    #         self.client.login(username='john', password='johnpassword')
    #         response = self.client.get(reverse('testlogin-view'))
    #         self.assertEqual(response.status_code, 200)

    with app.test_client() as client:
        response = client.get('/auth/login?next=%2Fadmin%2F')
        assert response.status_code == 200
