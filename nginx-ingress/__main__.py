"""A Python Pulumi program"""

import pulumi
import pulumi_kubernetes as k8s
from pulumi_kubernetes import provider
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
    opts=pulumi.ResourceOptions(parent=ns)
)

loadbalancer_address = ingress_service_ip = nginx.get_resource(
            "v1/Service", "nginx-ingress-nginx-ingress", ns.metadata.name).apply(lambda service: service.status.load_balancer.ingress[0].hostname)


app = ProductionApp("kuard", ProductionAppArgs(image="gcr.io/kuar-demo/kuard-amd64:blue", loadbalancer=loadbalancer_address))

pulumi.export("url", app.url)
