FROM node:12

WORKDIR /usr/src/app

RUN npm install npm@6.13.6
RUN rm -rf /usr/local/lib/node_modules/npm
RUN mv node_modules/npm /usr/local/lib/node_modules/npm

COPY . .

RUN npm install
RUN pwd && npm build

EXPOSE 4200

ENTRYPOINT npm run start:docker
