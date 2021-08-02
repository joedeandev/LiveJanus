# LiveJanus

![](./livejanus/static/icon192.png)

The Multi-User Censusing Tool - *[livejanus.joedean.dev](https://livejanus.joedean.dev/)*

# Description

LiveJanus is a real-time, multi-user censusing tool, built on [Flask](https://flask.palletsprojects.com/), and prepared for deployment via [Docker](https://docs.docker.com/). Built in a weekend for [Furesø Løbefest](https://www.furesolobefest.dk/), to assist pandemic crowd limit compliance.

# Usage

This repository is ready to use out of the box, with `python app.py` or `docker build . -t livejanus && docker run -p 8000:8000 livejanus`. The configurations in `deployment` are prepared to be used via [SideProjectDeployment](https://github.com/joedeandev/SideProjectDeployment/) (using [Docker Compose](https://docs.docker.com/compose/) and [NGINX](https://www.nginx.com/)), but should be customized before use.

LiveJanus integrates with [Stripe](https://stripe.com/docs) to paywall advanced features; the environment variables `STRIPE_PRIVATE_KEY` and `STRIPE_PRICE_ID` can be configured to enable this integration, although the server can run without them.
