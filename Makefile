update_images:
	docker-compose pull

check_config: update_images
	docker-compose run --rm check-config

lint: update_images
	docker-compose run --rm yamllint

test: lint check_config

.PHONY: check_config lint test
