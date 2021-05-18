import pulumi
import pulumi_kubernetes as k8s


class ProductionAppArgs:
    def __init__(
        self,
        image: pulumi.Input[str],
        replicas: pulumi.Input[int] = 5,
        domain: pulumi.Input[str] = "pulumi-demos.net",
    ):
        self.image = image
        self.replicas = replicas
        self.domain = domain


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
                        port=8080,
                        target_port="http",
                    )
                ],
                selector=app_labels,
            ),
        )

        ingress = (
            k8s.networking.v1beta1.Ingress(
                name,
                opts=pulumi.ResourceOptions(parent=namespace),
                metadata=k8s.meta.v1.ObjectMetaArgs(
                    labels=app_labels,
                    namespace=namespace.metadata.name,
                ),
                spec=k8s.networking.v1.IngressSpecArgs(
                    rules=[
                        k8s.networking.v1.IngressRuleArgs(
                            host=f"{name}.{args.domain}",
                            http=k8s.networking.v1.HTTPIngressRuleValueArgs(
                                paths=[
                                    k8s.networking.v1.HTTPIngressPathArgs(
                                        path="/",
                                        backend=k8s.networking.v1beta1.IngressBackendArgs(
                                            service_name=svc.metadata.name,
                                            service_port="http",
                                        ),
                                    )
                                ]
                            ),
                        )
                    ],
                ),
            ),
        )
