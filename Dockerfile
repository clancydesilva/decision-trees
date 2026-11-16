# Stage 1: Build the React/Vite visualiser frontend
FROM node:22-alpine AS frontend-builder
WORKDIR /app/visualiser
COPY visualiser/package.json visualiser/package-lock.json ./
RUN npm ci
COPY visualiser/ ./
RUN npm run build

# Stage 2: Python runtime precomputing n=1..7 static datasets and serving the app as non-root
FROM python:3.12-slim
WORKDIR /app

RUN adduser --disabled-password --gecos "" --uid 10001 appuser

COPY --chown=appuser:appuser tracked_list.py algorithms.py decision_tree.py evaluate.py main.py export_runner.py test.py ./
COPY --from=frontend-builder --chown=appuser:appuser /app/visualiser/dist ./visualiser/dist

USER appuser
RUN python export_runner.py --output visualiser/dist/data

ENV HOST=0.0.0.0
ENV PORT=5001
EXPOSE 5001

CMD ["python", "export_runner.py", "--serve", "--production"]
