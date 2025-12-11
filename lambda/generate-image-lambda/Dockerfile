FROM public.ecr.aws/lambda/python:3.13

# install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# copy requirements file
COPY lambda/generate-image-lambda/pyproject.toml ${LAMBDA_TASK_ROOT}/

# install dependencies
RUN uv sync
# copy function code
COPY lambda/generate-image-lambda/handler.py ${LAMBDA_TASK_ROOT}/
COPY lambda/generate-image-lambda/secret_loader.py ${LAMBDA_TASK_ROOT}/
COPY ai_helper/ ${LAMBDA_TASK_ROOT}/ai_helper/
# sync the project
RUN uv sync --locked --no-install-project --no-editable

# set PYTHONPATH to include the virtual environment site-packages
ENV PYTHONPATH="${LAMBDA_TASK_ROOT}/.venv/lib/python3.13/site-packages"

# set the CMD to your handler
CMD ["handler.main_handler"]