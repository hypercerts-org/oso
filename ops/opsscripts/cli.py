import subprocess
import sys

import click
import requests

flux_instance_yaml = """
apiVersion: fluxcd.controlplane.io/v1
kind: FluxInstance
metadata:
  name: flux
  namespace: flux-system
spec:
  distribution:
    version: "2.x"
    registry: "ghcr.io/fluxcd"
  components:
    - source-controller
    - kustomize-controller
    - helm-controller
    - notification-controller
  cluster:
    type: kubernetes
    multitenant: false
    networkPolicy: true
    domain: "cluster.local"
  sync:
    interval: "30s"
    kind: GitRepository
    url: "https://github.com/{repo_owner}/{repo_name}.git"
    ref: "refs/heads/{branch_name}"
    path: "./ops/clusters/local"
"""


@click.option("--branch-name", required=False)
@click.option("--cluster-name", default="oso-local-test-cluster")
@click.option("--repo-owner", default="opensource-observer")
@click.option("--repo-name", default="oso")
def cluster_setup(branch_name, cluster_name, repo_owner, repo_name):
    if not branch_name:
        branch_name = (
            subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
            .strip()
            .decode("utf-8")
        )

    github_api_url = "https://api.github.com"
    response = requests.get(
        f"{github_api_url}/repos/{repo_owner}/{repo_name}/branches/{branch_name}"
    )

    if response.status_code == 200:
        click.echo(
            f"Branch '{branch_name}' found on remote. Using this branch for the cluster setup"
        )
    elif response.status_code == 404:
        click.echo(
            f"Branch '{branch_name}' does not exist in the repository. Push this branch first"
        )
        sys.exit(1)
    else:
        click.echo(f"An error occurred: HTTP status code {response.status_code}.")
        sys.exit(1)

    click.echo("Ensure kind cluster is running")

    get_clusters_output = subprocess.run(
        ["kind", "get", "clusters"], check=True, stdout=subprocess.PIPE
    ).stdout
    clusters_list = map(lambda a: a.decode("utf-8"), get_clusters_output.split(b"\n"))
    if cluster_name in clusters_list:
        click.echo("Kind cluster already exists. Skipping cluster creation")
    else:
        subprocess.run(
            ["kind", "create", "cluster", "--config", "ops/kind/cluster.yaml"],
            check=True,
        )

    click.echo("Switching kubectl context to the kind cluster")
    subprocess.run(
        ["kubectl", "config", "use-context", f"kind-{cluster_name}"], check=True
    )

    click.echo("Ensure kind cluster is ready")
    subprocess.run(
        ["kubectl", "wait", "--for=condition=Ready", "node", "--all", "--timeout=5m"],
        check=True,
    )

    # Check if flux is already installed
    helm_list_flux_output = subprocess.run(
        ["helm", "list", "-n", "flux-system"], stdout=subprocess.PIPE
    ).stdout
    # This is not a very good way to check if flux is installed. But it works for now
    rows_and_columns = [row.split() for row in helm_list_flux_output.split(b"\n")]
    if len(rows_and_columns) < 2:
        click.echo("helm returned an unexpected output. Exiting")
        sys.exit(1)
    else:
        names = [
            row[0].decode("utf-8")
            for row in filter(lambda r: len(r) > 0, rows_and_columns)
        ]
        if "flux-operator" in names:
            click.echo(
                "Flux Operator is already installed. Attempting to flux with the new configuration"
            )
        else:
            subprocess.run(
                [
                    "helm",
                    "install",
                    "flux-operator",
                    "oci://ghcr.io/controlplaneio-fluxcd/charts/flux-operator",
                    "--namespace",
                    "flux-system",
                    "--create-namespace",
                ],
                check=True,
            )

    rendered_flux_instance = flux_instance_yaml.format(
        repo_owner=repo_owner, repo_name=repo_name, branch_name=branch_name
    )

    subprocess.run(
        ["kubectl", "apply", "-f", "-"],
        input=rendered_flux_instance.encode("utf-8"),
        check=True,
    )

    click.echo(
        "The flux instance should now be syncing the repository if everything is going as planned. Check k9s for details"
    )
