import unittest
import os
import json
from urlparse import urlparse

# Configure our app to use the testing databse
os.environ["CONFIG_PATH"] = "posts.config.TestingConfig"

from posts import app
from posts import models
from posts.database import Base, engine, session

class TestAPI(unittest.TestCase):
    """ Tests for the posts API """

    def setUp(self):
        """ Test setup """
        self.client = app.test_client()

        # Set up the tables in the database
        Base.metadata.create_all(engine)

    def tearDown(self):
        """ Test teardown """
        # Remove the tables and their data from the database
        Base.metadata.drop_all(engine)
    """
    replaced this test with the one below 

    def testGetEmptyPosts(self):
        response = self.client.get("/api/posts")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data)
        self.assertEqual(data, [])
    """

    def testGetPosts(self):
        """getting posts from a populated database"""
        postA = models.Post(title="Example Post A", body="Just a test")
        postB = models.Post(title="Example Post B", body="Still a test")
        session.add_all([postA, postB])
        session.commit()

        response = self.client.get("/api/posts",
            headers=[("Accept", "application/json")]
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data)
        self.assertEqual(len(data), 2)

        postA = data[0]
        self.assertEqual(postA["title"], "Example Post A")
        self.assertEqual(postA["body"], "Just a test")

        postB = data[1]
        self.assertEqual(postB["title"], "Example Post B")
        self.assertEqual(postB["body"], "Still a test")

    def testPostPost(self):
        data = {
            "title": "Example Post",
            "body": "Just a test"
        }

        response = self.client.post("/api/posts",
            data=json.dumps(data),
            content_type="application/json",
            headers=[("Accept", "application/json")]
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.mimetype, "application/json")

        self.assertEqual(urlparse(response.headers.get("Location")).path, "/api/posts/1")

        data = json.loads(response.data)
        self.assertEqual(data["id"], 1)
        self.assertEqual(data["title"], "Example Post")
        self.assertEqual(data["body"], "Just a test")

        posts = session.query(models.Post).all()
        self.assertEqual(len(posts), 1)

        post = posts[0]
        self.assertEqual(post.title, "Example Post")
        self.assertEqual(post.body, "Just a test")

    def testGetPost(self):
        postA = models.Post(title="Example Post A", body="Just a test")
        postB = models.Post(title="Example Post B", body="Still a test")

        session.add_all([postA, postB])
        session.commit()

        response = self.client.get("/api/posts/{}".format(postB.id),
            headers=[("Accept", "application/json")]
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data)
        self.assertEqual(data["title"], "Example Post B")
        self.assertEqual(data["body"], "Still a test")

    def testGetPostsWithTitle(self):
        postA = models.Post(title="Post with green eggs", body="Just a test")
        postB = models.Post(title="Post with ham", body="Still a test")
        postC = models.Post(title="Post with green eggs and ham", body="Another test")
        session.add_all([postA, postB, postC])
        session.commit()

        response = self.client.get("/api/posts?title_like=ham",
            headers=[("Accept", "application/json")]
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        posts = json.loads(response.data)
        self.assertEqual(len(posts), 2)

        post = posts[0]
        self.assertEqual(post["title"], "Post with ham")
        self.assertEqual(post["body"], "Still a test")

        post = posts[1]
        self.assertEqual(post["title"], "Post with green eggs and ham")
        self.assertEqual(post["body"], "Another test")

    def testGetPostWithTitleAndBody(self):
        postA = models.Post(title="Post with green eggs", body="We have eggs")
        postB = models.Post(title="Post with ham", body="We have eggs")
        postC = models.Post(title="Post with green eggs and ham", body="Another test")
        session.add_all([postA, postB, postC])
        session.commit()

        response = self.client.get("/api/posts?title_like=ham&body_like=eggs",
            headers=[("Accept", "application/json")]
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        posts = json.loads(response.data)
        self.assertEqual(len(posts), 1)

        post = post[0]
        self.assertEqual(post["title"], "Post with ham")
        self.assertEqual(post["body"], "We have eggs")

    def testGetNonExistentPost(self):
        response = self.client.get("/api/posts/1",
            headers=[("Accept", "application/json")]
            )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data)
        self.assertEqual(data["message"], "Could not find post with id 1")

    def testUnsupportedAcceptHeader(self):
        response = self.client.get("/api/posts", 
            headers=[("Accept", "application/xml")]
            )

        self.assertEqual(response.status_code, 406)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data)
        self.assertEqual(data["message"], "Request must accept application/json data")

    def testInvalidData(self):
        data = {
            "title": "Example Post",
            "body": 32
        }

        response = self.client.post("/api/posts",
            data=json.dumps(data),
            content_type="application/json",
            headers=[("Accept", "application/json")]
            )

        self.assertEqual(response.status_code, 422)

        data = json.loads(response.data)
        self.assertEqual(data["message"], "32 is not of type 'string'")

    def testMissingData(self):
        data = {
            "title": "Example Post",
        }

        response = self.client.post("/api/posts",
            data=json.dumps(data),
            content_type="application/json",
            headers=[("Accept", "application/json")]
            )

        self.assertEqual(response.status_code, 422)

        data = json.loads(response.data)
        self.assertEqual(data["message"], "'body' is a required property")

    def testUnsupportedMimetype(self):
        data="<xml></xml>"
        response = self.client.post("/api/posts",
            data=json.dumps(data),
            content_type="application/xml",
            headers=[("Accept", "application/json")]
            )

        self.assertEqual(response.status_code, 415)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data)
        self.assertEqual(data["message"], "Request must contain application/json data")



if __name__ == "__main__":
    unittest.main()