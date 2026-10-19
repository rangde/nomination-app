### Nomination

Nomination app

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch develop
bench install-app nomination
```

### Public dashboard

Open `/public-dashboard` on a site with Nomination installed to view site-wide
nomination, training, and loan summary metrics without signing in. The page uses
`nomination.api.public_dashboard.get_public_dashboard_metrics`, a guest-accessible
GET endpoint cached for 60 seconds. Only numeric aggregates are published;
individual records remain behind the existing authenticated dashboard APIs.
Unavailable training or loan metrics display as `—` while nomination counts remain
available. Pending counts overlap with the preceding approval stage and should
not be summed.

After deploying the app changes, clear the website cache with
`bench --site <site> clear-cache` and restart the web processes using your normal
deployment procedure. No new roles or DocType permissions are required.

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/nomination
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### License

mit
