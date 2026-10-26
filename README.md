# Rule-Based Queue Management System

A queue monitoring application using Django, React, OpenCV, and YOLO person detection.

## Features

- Detect people in a configured counter region using YOLO.
- Estimate queue occupancy from sampled video frames.
- Generate alerts when the configured queue threshold is reached.
- Save evidence images for newly created alerts.
- Display queue measurements and alert history on the dashboard.

## Project Structure

- `backend/` - Django backend and queue detection services.
- `frontend/` - React dashboard.
- `data/videos/` - Input video files.
- `data/evidence/` - Alert evidence images.
- `docs/` - Project documentation.
- `tests/` - Test files.

## Backend Setup

1. Install a compatible Python version.
2. Install the backend dependencies:

   `pip install -r requirements.txt`

3. Configure the required environment variables in `backend/.env`.
4. Run database migrations:

   `python manage.py migrate`

5. Start the backend:

   `python manage.py runserver`

## Frontend Setup

1. Navigate to `frontend/`.
2. Install dependencies using `npm install`.
3. Start the frontend using `npm run dev`.

## Important Notes

- Configure the video source and counter ROI for your environment.
- Install a PyTorch build compatible with the target machine's GPU and CUDA setup if GPU inference is required.
- Do not commit secrets, virtual environments, or generated test outputs.
