import pulumi
import pulumi_kubernetes as k8s
import pulumi_aws as aws
from pulumi_kubernetes import networking
from pulumi_kubernetes.core.v1.Service import Service


class ProductionAppArgs:
    url: pulumi.Output[str]
    def __init__(
        self,
        image: pulumi.Input[str],
        loadbalancer: pulumi.Input[str],
        port: pulumi.Input[int] = 80,
        replicas: pulumi.Input[int] = 1,
        domain: pulumi.Input[str] = "aws.briggs.work", 
    ):
        self.image = image
        self.replicas = replicas
        self.domain = domain
        self.port = port
        self.loadbalancer = loadbalancer


class ProductionApp(pulumi.ComponentResource):
    def __init__(
        self, name: str, args: ProductionAppArgs, opts: pulumi.ResourceOptions = None
    ):
        super().__init__("productionapp:index:ProductionApp", name, {}, opts)

        app_labels = {"name": name}

        namespace = k8s.core.v1.Namespace(
            name,
            opts=pulumi.ResourceOptions(
                parent=self,
            ),
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=name,
            ),
        )

        deployment = k8s.apps.v1.Deployment(
            name,
            opts=pulumi.ResourceOptions(
                parent=namespace,
            ),
            metadata=k8s.meta.v1.ObjectMetaArgs(
                namespace=namespace.metadata.name, labels=app_labels
            ),
            spec=k8s.apps.v1.DeploymentSpecArgs(
                replicas=args.replicas,
                selector=k8s.meta.v1.LabelSelectorArgs(match_labels=app_labels),
                template=k8s.core.v1.PodTemplateSpecArgs(
                    metadata=k8s.meta.v1.ObjectMetaArgs(labels=app_labels),
                    spec=k8s.core.v1.PodSpecArgs(
                        containers=[
                            k8s.core.v1.ContainerArgs(
                                name=name,
                                image=args.image,
                                ports=[
                                    k8s.core.v1.ContainerPortArgs(
                                        name="http", container_port=8080
                                    )
                                ],
                            )
                        ]
                    ),
                ),
            ),
        )

        svc = k8s.core.v1.Service(
            name,
            opts=pulumi.ResourceOptions(
                parent=namespace,
            ),
            metadata=k8s.meta.v1.ObjectMetaArgs(
                labels=app_labels, namespace=namespace.metadata.name
            ),
            spec=k8s.core.v1.ServiceSpecArgs(
                ports=[
                    k8s.core.v1.ServicePortArgs(
                        port=80,
                        target_port=8080,
                    )
                ],
                selector=app_labels,
            ),
        )

        ingress = k8s.networking.v1.Ingress(
                name,
                opts=pulumi.ResourceOptions(parent=namespace),
                metadata=k8s.meta.v1.ObjectMetaArgs(
                    labels=app_labels,
                    namespace=namespace.metadata.name,
                    annotations={
                        "kubernetes.io/ingress.class": "nginx",
                    }
                ),
                spec=k8s.networking.v1.IngressSpecArgs(
                    rules=[
                        k8s.networking.v1.IngressRuleArgs(
                            host=f"{name}.{args.domain}",
                            http=k8s.networking.v1.HTTPIngressRuleValueArgs(
                                paths=[
                                    k8s.networking.v1.HTTPIngressPathArgs(
                                        path="/",
                                        path_type="ImplementationSpecific",
                                        backend=k8s.networking.v1.IngressBackendArgs(
                                            service=k8s.networking.v1.IngressServiceBackendArgs(
                                                name=svc.metadata.name,
                                                port=k8s.networking.v1.ServiceBackendPortArgs(
                                                    number=80
                                                )
                                            )
                                        ),
                                    )
                                ]
                                
                            ),
                        )
                    ],
                ),
            ),

        # Get the existing zone
        zone = aws.route53.get_zone(
            name=args.domain
        )

        record = aws.route53.Record(
            name,
            opts=pulumi.ResourceOptions(
                parent=self,
            ),
            zone_id=zone.id,
            name=f"{name}",
            type="CNAME",
            records=[args.loadbalancer],
            ttl=1,
        )

        self.url = record.fqdn

        self.register_outputs({
            'url': record.fqdn
        })

