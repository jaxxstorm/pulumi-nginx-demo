"""A Python Pulumi program"""

import pulumi
import pulumi_kubernetes as k8s
import pulumi_kubernetes.helm.v3 as helm
import pulumi_kubernetes.yaml as yaml
from app import ProductionApp, ProductionAppArgs


# removes the status field from the nginx-ingress crd
def remove_status(obj):
    if obj["kind"] == "CustomResourceDefinition" and "status" in obj:
        try:
            del obj["status"]
        except KeyError:
            pass


# create a namespace to run nginx-ingress
ns = k8s.core.v1.Namespace("nginx-ingress", metadata={"name": "nginx-ingress"})


# # deploy the nginx-ingress helm chart
nginx = helm.Chart(
    "nginx-ingress",
    helm.ChartOpts(
        chart="nginx-ingress",
        namespace=ns.metadata.name,
        fetch_opts=helm.FetchOpts(repo="https://helm.nginx.com/stable"),
        values={
            "controller": {
                "nginxplus": False,
            }
        },
        transformations=[remove_status],
    ),
)

# app = ProductionApp("nginx", ProductionAppArgs(image="nginx:latest"))
