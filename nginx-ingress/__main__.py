"""A Python Pulumi program"""

import pulumi
import pulumi_kubernetes as k8s
import pulumi_kubernetes.helm.v3 as helm
from app import ProductionAppArgs, ProductionApp


def remove_status_field(obj):
	if obj["kind"] == "CustomResourceDefinition" and 'status' in obj:
		del obj["status"]


"""
create a namespace to run nginx-ingress
"""
ns = k8s.core.v1.Namespace("nginx-ingress", metadata={
	"name": "nginx-ingress"
})

"""
deploy the nginx-ingress helm chart
"""
nginx = helm.Chart("nginx-ingress", helm.ChartOpts(
	chart="nginx-ingress",
	namespace=ns.metadata.name,
	fetch_opts=helm.FetchOpts(
		repo="https://helm.nginx.com/stable"
	),
	transformations=[remove_status_field]
))

kuard = ProductionApp("kuard", ProductionAppArgs(image="gcr.io/kuar-demo/kuard-amd64:blue"))
