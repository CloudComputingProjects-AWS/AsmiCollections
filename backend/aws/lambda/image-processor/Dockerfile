FROM public.ecr.aws/lambda/python:3.11

# Install Pillow (includes WebP support in the prebuilt wheel)
RUN pip install --no-cache-dir Pillow==10.4.0

# Copy function code
COPY lambda_function.py ${LAMBDA_TASK_ROOT}/

# Set the handler
CMD ["lambda_function.lambda_handler"]
