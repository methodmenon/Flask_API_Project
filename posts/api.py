import json

from flask import request, Response, url_for
from jsonschema import validate, ValidationError
from sqlalchemy import and_, or_

import models
import decorators
from posts import app
from database import session

"""
Endpoint for getting a posts , optionally filtering by title and/or body
"""
@app.route("/api/posts", methods=["GET"])
@decorators.accept("application/json")
def posts_get():
	title_like = request.args.get("title_like")
	body_like = request.args.get("body_like")

	posts = session.query(models.Post)
	if title_like:
		if body_like:
			posts = posts.filter((models.Post.title.contains(title_like), models.Post.body.contains(body_like)))
		else:
			posts = posts.filter(models.Post.title.contains(title_like))
	posts = posts.all()

	data = json.dumps([post.as_dictionary() for post in posts])
	return Response(data, 200, mimetype="application/json")

"""
Endpoint for getting a post with a specifi id
"""
@app.route("/api/posts/<int:id>", methods=["GET"])
@decorators.accept("application/json")
def post_get(id):
	post = session.query(models.Post).get(id)

	if not post:
		message = "Could not find post with id {}".format(id)
		data = json.dumps({"message": message})
		return Response(data, 404, mimetype="application/json")

	data = json.dumps(post.as_dictionary())
	return Response(data, 200, mimetype="application/json")

post_schema = {
	"properties": {
		"title": {"type": "string"},
		"body": {"type": "string"}
	},
	"required": ["title", "body"]
}	

"""
Endpoint for adding a post
"""
@app.route("/api/posts", methods=["POST"])
@decorators.accept("application/json")
@decorators.require("application/json")
def posts_post():
	data = request.json

	try:
		validate(data, post_schema)
	except ValidationError as error:
		data = {"message": error.message}
		return Response(json.dumps(data), 422, mimetype="application/json")

	post = models.Post(title=data["title"], body=data["body"])
	session.add(post)
	session.commit()

	data = json.dumps(post.as_dictionary())
	headers = {"Location": url_for("post_get", id=post.id)}

	return Response(data, 201, headers=headers, mimetype="application/json")

	