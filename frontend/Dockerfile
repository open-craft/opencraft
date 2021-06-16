FROM node:11.15.0

# https://github.com/Automattic/node-canvas#compiling
RUN apt-get update \
    && apt-get install -y \
        build-essential \
        libcairo2-dev \
        libpango1.0-dev \
        libjpeg-dev \
        libgif-dev \
        librsvg2-dev

WORKDIR /usr/src/ocim-frontend
COPY ./ /usr/src/ocim-frontend

# Move node_modules out of the source path
RUN npm install -g --unsafe-perm

CMD [ "npm", "start" ]