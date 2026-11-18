# MIDTERM-SP23-BAI-049: Automated ML Retraining Pipeline

CSC418 lab midterm. A push of new data to `dataset/train.csv` triggers Jenkins through a GitHub webhook. Jenkins retrains the model, tests it, builds a Docker image, redeploys the FastAPI service on AWS EC2, pushes the image to Docker Hub, and emails the result.

| Item | Value |
|---|---|
| Student Reg No | SP23-BAI-049 |
| Jenkins job | `MIDTERM-SP23-BAI-049` |
| Live metrics | http://13.233.51.253:8000/metrics |
| Docker Hub image | `msyedtaha/midterm-sp23-bai-049` |

## Repository contents

- `config.json` is the individually assigned configuration (`configs/SP23-BAI-049.json` from the starter repository).
- `dataset/train.csv` was generated with `python generate_dataset.py --config config.json`.
- `app.py`, `train.py`, `generate_dataset.py` and `requirements.txt` are the unchanged starter code.
- `Dockerfile` has three stages: cached dependencies, a CI image for training and tests, and the runtime API image.
- `Jenkinsfile` defines the pipeline. `tests/test_pipeline.py` checks the trained artifacts and the API.

## Pipeline stages

1. **Fetch latest data**: Jenkins checks out the pushed commit.
2. **Prepare CI environment**: builds the `ci` Docker stage (dependencies are cached).
3. **Retrain model**: runs `train.py` inside the CI container with `GIT_COMMIT` set to the pushed commit.
4. **Test**: runs `pytest` inside the CI container.
5. **Build Docker image**: builds the `runtime` stage containing the new model.
6. **Deploy on EC2**: replaces the `midterm-api` container on port 8000 and waits until `/metrics` reports the new commit.
7. **Push to Docker Hub**: pushes the build-number tag and `latest`.
8. **Email**: sent after every build from `johnndoeehere@gmail.com`, with the Reg No in the subject.

## API

- `GET /metrics` returns `student_id`, `accuracy`, `training_rows`, `model_version`, `dataset_sha256` and `git_sha`.
- `POST /predict` accepts `{"records": [{"basket_volatility": 0.1, "stock_gap": -0.3, "promotion_load": 1.2, "delivery_delay": 0.4}]}`.
- `GET /health` reports whether a model is loaded.

## Run locally

```sh
docker build --target ci -t midterm-ci .
docker run --rm -v "$PWD":/app midterm-ci sh -c "python train.py && python -m pytest -q"
docker build --target runtime -t midterm-api .
docker run -p 8000:8000 midterm-api
```
