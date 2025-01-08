# External PRs

A Github App that allows us to accept external PRs by enabling PR checks by an
out of band process. We need this because some of the checks require _some_ form
of authentication.

## Usage

This is generally only supposed to be used on Github Actions. However, if you're
developing this locally it's useful to know the available commands.

Remember to populate `.env` first.

### General commands

```bash
# Initialize a check with a given check name
# If the user has write access then it automatically is listed as "queued"
# If the user does not have write access then it automatically fails and waits for approval
pnpm external-prs initialize-check {sha} {login} {check-name}
```

### OSO Specific

```bash
# Handle oso comments
pnpm tools oso parse-comment {comment} {output}

# Refresh gcp credentials for the test deployment infrastructure
pnpm tools oso refresh-gcp-credentials {environment} {creds-path} {name}

# Test deployment sub commands
pnpm tools oso test-deploy --help

# Test deployment setup
pnpm tools oso test-deploy setup {pr} {sha} {profile-path} {service-account-path} {checkout-path}

# Test deployment teardown
pnpm tools oso test-deploy teardown {pr}

# Test deployment clean
pnpm tools oso test-deploy clean {ttl-seconds}
```

### OSS-Directory Specific

First configure `.env`.

Then `git clone` to 2 different paths on your filesystem,
the oss-directory main branch
and the PR branch to compare.

You can run the app via:

```bash
# Handle PR validations
pnpm tools ossd validate-prs {pr_number} {commit_sha} {main_path} {pr_path}
```

If you've configured your GitHub secrets correctly,
this should post a comment in the PR with the results
