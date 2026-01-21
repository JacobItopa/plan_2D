# NanoBanana Plan Scaler (Plan 2D)

A FastAPI-based web application that acts as a middleware for the NanoBanana API. It allows users to upload rough floor plan sketches, processes them using NanoBanana's AI to clean, dimension, and label them, and provides a polished result.

## Features

-   **Image Upload**: Simple drag-and-drop interface for uploading sketches.
-   **NanoBanana Integration**: Wraps the NanoBanana API to handle "clean and dimension" prompts.
-   **Production Ready**: Uses `httpx` for asynchronous non-blocking I/O.
-   **Render Compatible**: Includes configuration (`render.yaml`, HTTPS header handling) for easy deployment on Render.
-   **Auto-Cleanup**: Automatically cleans up old uploaded files to manage disk space.
-   **Developer API**: Exposes endpoints for other developers to consume your scaled plan service.

## Tech Stack

-   **Backend**: Python, FastAPI, Uvicorn, Gunicorn
-   **Async Client**: httpx
-   **Frontend**: HTML5, Vanilla JavaScript, CSS
-   **Deployment**: Render (Docker/Python Environment)

## Setup

### Prerequisites

-   Python 3.9+
-   A NanoBanana API Key

### Local Development

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/JacobItopa/plan_2D.git
    cd plan_2D
    ```

2.  **Create a `.env` file**:
    ```bash
    NANOBANANA_API_KEY=your_api_key_here
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the server**:
    ```bash
    python run_app.py
    ```
    Or manually:
    ```bash
    uvicorn app.main:app --reload
    ```

5.  **Expose to Internet (Required for NanoBanana)**:
    Since NanoBanana needs to fetch the image from your server, your `localhost` must be exposed.
    ```bash
    ngrok http 8000
    ```
    Use the `ngrok` URL in your browser.

## Deployment on Render

This project is pre-configured for Render.

1.  Create a new **Web Service** on Render.
2.  Connect this repository.
3.  Add the Environment Variable: `NANOBANANA_API_KEY`.
4.  Deploy!

## API Usage for Developers

You can use the provided `example_usage.py` script to test the API programmatically.

```bash
# Upload and process a file
python example_usage.py path/to/your/plan.jpg

# Check status of an existing task
python example_usage.py <TASK_ID>
```

### Endpoints

-   `POST /api/process`: Upload an image file. Returns a Task ID.
-   `GET /api/status/{task_id}`: Check the status of the generation task.

## License

[MIT](LICENSE)
