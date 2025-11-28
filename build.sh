ARG_VERSION=$1
ARG_TARGET=$2

APP_NAME=translator
REGISTRY=ccr.ccs.tencentyun.com

if [ "$ARG_TARGET" = "dev" ]; then
echo "build development image, version: $ARG_VERSION"
	docker build -t $REGISTRY/idemo/$APP_NAME:dev-$ARG_VERSION .
elif [ "$ARG_TARGET" = "prod" ]; then
echo "build production image, version: $ARG_VERSION"
	docker build -t $REGISTRY/gzjww/$APP_NAME:prod-$ARG_VERSION .
	docker push $REGISTRY/idemo/$APP_NAME:prod-$ARG_VERSION
fi
