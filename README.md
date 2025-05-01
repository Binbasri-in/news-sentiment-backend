## References:

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Docker Docs](https://docs.docker.com/)

## TODO
- [ ] Finalise the model of the Article data, what exactly to be stored.
- [ ] fill it with dump data
- [ ] Design the API endpoints
- [ ] Write the API endpoints

## Frontend:
- [ ] A single page for browsing the articles, like a blog with filters and search maybe.
- [ ] a page to display each article with different details and actions.
- [ ] login page
- [ ] implementation of the login page with the backend.
- [ ] implementation of the article page with the backend.
- [ ] implementation of the article list page with the backend.


### To Run

```bash
docker build -t fastapi-example .
docker run -d -p 8000:8000 fastapi-example
```

OR

```bash
pip install -r requirements.txt
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

The expose with Ngrok (google it and log in then see the setup steps)

```bash
ngrok http 8000
```