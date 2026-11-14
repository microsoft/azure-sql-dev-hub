FROM node:22-bookworm-slim AS node

FROM ruby:3.3-bookworm

COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm

WORKDIR /workspace
COPY Gemfile ./
RUN bundle install
COPY package.json package-lock.json ./
ARG NPM_CONFIG_REGISTRY=https://registry.npmjs.org
RUN npm ci --registry="$NPM_CONFIG_REGISTRY"

CMD ["npm", "start"]
