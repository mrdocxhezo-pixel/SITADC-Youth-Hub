# Security Checks

We use `bandit` to find common security issues in Python code.

## Running Bandit
To scan the `apps` and `config` directories:
```bash
bandit -r apps config -ll
```

Bandit is also run automatically via GitHub Actions on every pull request and push to the main branches.

## Dealing with False Positives
If bandit reports a false positive, you can skip the specific line by appending `# nosec` to it. However, you should provide a valid reason as a comment.
