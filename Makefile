run-api:
	uv run uvicorn api.fast:app --reload
docker_build_local:
	docker build -t api .
docker_run:
	docker run -p 8111:8080 api
docker_build_cloud:
	docker build \
  --platform linux/amd64 \
  -t ${GAR_IMAGE_NAME}:prod .
docker_push:
	docker push ${GAR_IMAGE_NAME}:prod
docker_deploy:
	gcloud run deploy \
  --image ${GAR_IMAGE_NAME}:prod \
  --region ${GCP_REGION}
