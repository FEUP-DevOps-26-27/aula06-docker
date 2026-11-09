# Aula 6 — Containerization with Docker
### Luís Gomes · MESW0023 · 11 Nov 2026

You'll containerize a small training pipeline and an inference server with Docker: train a Wine classifier,
serve it with Flask, and orchestrate both containers with Docker Compose. The focus is **volume
management**: you'll use a named volume and a bind mount to share data between containers and persist
files on the host.

To get credit for this lab, demonstrate your work to me during the class. The last part of the class is the
project progress presentation, so be ready to show where your group's microservice stands.

## Deliverables

- [ ] **Deliverable 1**: Run the training script in a container and save the resulting model to a shared
  named volume. Be able to explain why Docker helps with reproducibility and portability here.
- [ ] **Deliverable 2**: Containerize the inference service so it serves predictions on a port, and show the
  `./logs/predictions.log` file on your host. Explain what your Dockerfile does, line by line.
- [ ] **Deliverable 3**: Call the inference service's `/health` endpoint before and after destroying the
  named volume, and show how model availability changes. Explain the difference between named volumes
  and bind mounts.

## Repository layout

```
docker/
  training/   Dockerfile (almost done), train.py (TODOs), requirements.txt
  inference/  server.py (TODOs) — you'll add a Dockerfile and requirements.txt here
docker-compose.yml   (TODOs)
```

All `docker build` commands run from the repository root, so the build context is `.` and paths inside the
Dockerfiles start with `docker/...`.

## Step 0: Set up Docker

Install Docker ([docs.docker.com/get-docker](https://docs.docker.com/get-docker/)) and check it works:

```bash
docker run hello-world
```

## Step 1: Containerize the training pipeline

When launched, the training container trains a Wine classifier and saves the model file to a shared
volume. Start from the partially completed files in `docker/training/`.

### 1a. Complete `train.py`

- Create a `RandomForestClassifier` and train it on the Wine training split.
- Save the trained model with `joblib.dump()` to `/app/models/wine_model.pkl`.

### 1b. Complete the training Dockerfile

Open `docker/training/Dockerfile`. It's nearly complete: fill in the `CMD` that runs the training script.

### 1c. Build and run with a named volume

```bash
docker build -t aula06-training -f docker/training/Dockerfile .
docker run --rm -v wine_model_storage:/app/models aula06-training
```

You should see the test accuracy and a message saying the model was saved.

**What is a named volume?** With `-v wine_model_storage:/app/models`, Docker creates a volume called
`wine_model_storage` that Docker manages. Its data survives after the container exits (and `--rm` deletes
the container).

## Step 2: Containerize the inference server

This container loads the trained model from the shared volume and serves predictions through a Flask API.
It also writes every prediction to a bind-mounted directory, so you can read the log from the host.

### 2a. Complete `server.py`

In `docker/inference/server.py`:
- Load the model from the shared volume (only if the file exists, so the server still starts without it).
- Extract the features from the incoming JSON request and run inference.
- Append each prediction to `/app/logs/predictions.log`.

The `/health` endpoint reports whether the model file exists. It's your main tool for debugging volume
issues.

### 2b. Write the inference Dockerfile

Create `docker/inference/Dockerfile` from scratch. It should:

- Use `python:3.11-slim` as the base image.
- Set the working directory to `/app`.
- Copy and install the dependencies from a requirements file.
- Copy `server.py` into the working directory.
- `EXPOSE 8080` (the port Flask listens on *inside* the container).
- Set the command that runs `server.py`.

Use the training Dockerfile as a reference. Remember that the build context is the repo root, so paths are
`docker/inference/...`.

You also need `docker/inference/requirements.txt` (Flask, scikit-learn, joblib, numpy).

> **Pin the same `scikit-learn` version as the training image.** The model is a pickle: loading it with a
> different scikit-learn version may print warnings or fail. This is exactly the kind of "works on my
> machine" problem containers are meant to remove.

### 2c. Build and run with both volume types

```bash
mkdir -p ./logs
docker build -t aula06-inference -f docker/inference/Dockerfile .
docker run --rm -p 8081:8080 \
  -v wine_model_storage:/app/models \
  -v "$(pwd)/logs":/app/logs \
  aula06-inference
```

(On Windows PowerShell, use `${PWD}/logs` instead of `$(pwd)/logs`.)

- `-p 8081:8080`: **host** port 8081 → **container** port 8080. You call the API on `localhost:8081`.
- `wine_model_storage:/app/models`: **named volume** (managed by Docker, shared with training).
- `$(pwd)/logs:/app/logs`: **bind mount** (your local `./logs/` folder, seen from inside the container).

### 2d. Test the inference server

Health check:
```bash
curl http://localhost:8081/health
```

Prediction (13 Wine features):
```bash
curl -X POST http://localhost:8081/predict \
  -H 'Content-Type: application/json' \
  -d '{"input": [13.2, 1.78, 2.14, 11.2, 100, 2.65, 2.76, 0.26, 1.28, 4.38, 1.05, 3.40, 1050]}'
```

Bad request (should return 400 with an error message):
```bash
curl -X POST http://localhost:8081/predict \
  -H 'Content-Type: application/json' \
  -d '{"bad_key": [1,2,3]}'
```

Then open `./logs/predictions.log` on your machine: the container wrote to `/app/logs/`, and the file shows
up on your host. That's the bind mount at work.

## Step 3: Docker Compose

Docker Compose describes a multi-container application in one file, instead of long `docker run`
commands. Complete `docker-compose.yml`:

- Build context and Dockerfile path for each service.
- The **named volume** `wine_model_storage` mounted at `/app/models` in both services.
- The **bind mount** `./logs` → `/app/logs` in the inference service.
- The port mapping for the inference service (8081 → 8080).
- The named volume declared in the top-level `volumes:` section.

`depends_on` with `condition: service_completed_successfully` is already there: inference only starts once
training has finished and exited cleanly. A plain `depends_on: [training]` would only wait for the
training container to *start*, and inference could come up before the model exists.

```bash
docker compose up --build
```

Test it with the curl commands from Step 2d. Check that:
- `/predict` returns a wine class;
- `./logs/predictions.log` on your host keeps growing.

Stop everything:
```bash
docker compose down
```

## Step 4: Volume lifecycle

### 4a. Inspect the named volume

```bash
docker volume ls
docker volume inspect <name>
```

Compose prefixes volume names with the project name (the folder name), so look for something like
`aula06-docker_wine_model_storage`. The `Mountpoint` field shows where Docker keeps the data. On macOS and
Windows that path is inside Docker's Linux VM, not on your own disk.

### 4b. Persistence

```bash
docker compose up -d --build       # trains, then serves (in the background)
curl http://localhost:8081/health  # healthy
docker compose down                # removes the containers, keeps the volume
docker compose up -d inference --no-deps
curl http://localhost:8081/health  # still healthy?
```

The training container is gone, but the model is still there: it lives in the named volume, not in the
container.

### 4c. Removing volumes

```bash
docker compose down -v
docker compose up -d inference --no-deps
curl http://localhost:8081/health
```

`-v` deletes the named volume. What does `/health` say now, and why? Is `./logs/predictions.log` still on
your host? Be ready to explain both answers.

## Troubleshooting

- **`Cannot connect to the Docker daemon`**: Docker Desktop isn't running.
- **`port is already allocated`**: something else uses 8081. Change the *host* side of the mapping
  (e.g. `8082:8080`).
- **Inference keeps restarting**: check `docker compose logs inference`. Usually `joblib.load` failed
  because the model file isn't there.
- **Model missing**: check the volume is mounted on both services (`docker volume ls`,
  `docker compose exec inference ls /app/models`).
- **No logs on the host**: check the bind mount path, and that `./logs` exists.

## Additional resources

1. [Docker for beginners](https://docker-curriculum.com/)
2. [Dockerfile reference](https://docs.docker.com/reference/dockerfile/)
3. [Volumes](https://docs.docker.com/engine/storage/volumes/) and
   [bind mounts](https://docs.docker.com/engine/storage/bind-mounts/)
4. [Compose `depends_on`](https://docs.docker.com/reference/compose-file/services/#depends_on)

---
Adapted from the [MLIP Docker lab](https://github.com/BhuvanashreeM/mlip-docker-lab-s26) (Carnegie Mellon
University, Machine Learning in Production).
