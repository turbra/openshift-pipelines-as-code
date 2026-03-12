# OpenShift App Template

This repository is a reusable OpenShift application template with a minimal FastAPI sample app, OpenShift runtime manifests, and Pipelines as Code configuration.
Fork it, replace the template placeholders, bootstrap the PaC resources in your namespace, and let the pipeline build and deploy your image.
The sample app follows the `hello-openshift` pattern: it listens on port `8080` and renders the homepage from the `RESPONSE` environment variable.

## Workflow

Use the repository in this order:

1. Review the delivery model and template files.
2. Replace every `<...>` placeholder with values for your own app, namespace, Git provider, and registry.
3. Apply the PaC bootstrap resources in your target namespace.
4. Configure your Git provider webhook to the cluster-wide PaC route.
5. Push changes to the branch configured in `.tekton/pipelinerun.yaml` and validate the resulting deployment.

## Project Structure

- `app/` - minimal FastAPI application modeled after the `hello-openshift` example
- `Dockerfile` - UBI9 Python image for the sample app with OpenShift-safe permissions
- `requirements.txt` - Python runtime dependencies
- `.tekton/` - Pipelines as Code entrypoint plus reusable Pipeline and Task definitions
- `deployment/app/` - runtime OpenShift manifests applied by the pipeline
- `deployment/optional/` - optional manifests not applied by default
- `deployment/pac/` - namespace-scoped Pipelines as Code bootstrap resources

## [OpenShift Pipelines as Code (PaC) CI/CD Model](https://pipelinesascode.com/)

On pushes to the branch configured in `.tekton/pipelinerun.yaml`, PaC creates a `PipelineRun` only when one of these paths changes:

- `Dockerfile`
- `app/**/*`

The blueprint is split into:

- `.tekton/pipelinerun.yaml` - PaC trigger and runtime parameters
- `.tekton/pipeline.yaml` - reusable standard delivery pipeline
- `.tekton/tasks/openshift-binary-build.yaml` - OpenShift binary build task
- `.tekton/tasks/openshift-deploy.yaml` - generic deploy task

Execution model:

- `Pipeline` is the reusable blueprint.
- `PipelineRun` is the runtime instance created by PaC for each matching Git event.
- In OpenShift you should expect to see new `PipelineRun` objects for each execution, not a new `Pipeline`.

The pipeline then:

- clones the repo using PaC-provided Git credentials
- starts an OpenShift binary `BuildConfig` build from the checked out source
- pushes the image to the registry repository configured in `.tekton/pipelinerun.yaml`
- applies all manifests in `deployment/app/`
- updates the deployment image and waits for rollout

## Customize After Forking

Replace every `<...>` placeholder before applying the manifests.

Update these files first:

- `.tekton/pipelinerun.yaml` - set your app name, branch, namespace, image repository, BuildConfig name, deployment name, and container name
- `deployment/pac/00-secrets-example.yaml` - replace the example token, webhook secret, and registry auth payload with your own secrets
- `deployment/pac/01-serviceaccount-rbac.yaml` - set the target namespace for the shared `pipeline` service account and `pipeline-edit` role binding
- `deployment/pac/02-repository.yaml` - set the repository name, repository URL, Git provider type, and Git provider API URL
- `deployment/app/20-deployment.yaml` - set the deployment name, app label, container name, and base image reference
- `deployment/app/10-service.yaml`, `deployment/app/30-route.yaml`, and `deployment/optional/*.yaml` - update app names, route names, and route hosts to match your application

Recommended conventions:

- keep the same value for `<app-name>` across labels and service references
- keep `<deployment-name>` and `<container-name>` aligned with the values used in `.tekton/pipelinerun.yaml`
- keep the image repository in `.tekton/pipelinerun.yaml` and `deployment/app/20-deployment.yaml` pointed at the same registry location

## PaC Bootstrap

After customizing the template files, bootstrap the namespace resources that Pipelines as Code needs.

Bootstrap resources:

- `deployment/pac/00-secrets-example.yaml` - example Git provider and image registry secrets with placeholder values
- `deployment/pac/01-serviceaccount-rbac.yaml` - service account and namespace RBAC for pipeline execution
- `deployment/pac/02-repository.yaml` - PaC `Repository` custom resource template for your Git repository and provider

Apply them in your target namespace:

```bash
oc project <target-namespace>
oc apply -f deployment/pac/00-secrets-example.yaml
oc apply -f deployment/pac/01-serviceaccount-rbac.yaml
oc apply -f deployment/pac/02-repository.yaml
```

After the `Repository` resource exists, configure the GitLab or GitHub webhook to the cluster-wide Pipelines as Code route and use the same shared secret configured in `git-provider-pac-config`.

You can find the cluster-wide PaC route via:
```bash
oc get routes -n openshift-pipelines
NAME                           HOST/PORT                                                                    PATH   SERVICES                       PORT            TERMINATION     WILDCARD
pipelines-as-code-controller   pipelines-as-code-controller-openshift-pipelines.apps.ocp.example.com          pipelines-as-code-controller   http-listener   edge/Redirect   None
```

## Runtime Manifests

The deploy step applies everything in `deployment/app/`.

Add new runtime resources there instead of editing the pipeline logic.
For other applications, the normal reuse point is the `PipelineRun` params and the contents of `deployment/app/`, not the pipeline stages themselves.

Current runtime resources:

- `deployment/app/10-service.yaml`
- `deployment/app/20-deployment.yaml`
- `deployment/app/30-route.yaml`

Optional manifests:

- `deployment/optional/40-networkpolicy.yaml`

## Validation

```bash
oc get repository <repository-name> -n <target-namespace>
oc get pipeline <pipeline-name> -n <target-namespace>
oc get pipelineruns -n <target-namespace>
oc get taskruns -n <target-namespace>
oc get builds -n <target-namespace>
oc rollout status deployment/<deployment-name> -n <target-namespace>
oc get route <route-name> -n <target-namespace>
```

To inspect the relationship between the reusable pipeline and an execution:

```bash
oc get pipelinerun <name> -n <target-namespace> -o jsonpath='{.spec.pipelineRef.name}{"\n"}'
oc get pipeline <pipeline-name> -n <target-namespace>
```

## Reuse In Another Repo

If you already have an application repository, copy `.tekton/`, `deployment/app/`, `deployment/optional/`, and `deployment/pac/` into that repo, then follow the same customization, bootstrap, and validation workflow described above.

Reuse rule:

- treat `.tekton/pipeline.yaml` and `.tekton/tasks/` as the shared delivery standard
- treat `.tekton/pipelinerun.yaml` and `deployment/app/` as the application-specific customization points

## Security Notes

- Container runs as non-root (`USER 1001`) and supports OpenShift arbitrary UID model.
- File permissions are set with `chgrp -R 0` and `chmod -R g=u` for OpenShift compatibility.
- Deployment drops Linux capabilities and disallows privilege escalation.
- Root filesystem is read-only in the pod security context.
- `registry-auth` is consumed by the OpenShift build as the image push secret.

## Health Endpoints

- `GET /healthz` - liveness/readiness/startup probe endpoint
- `GET /` - sample hello page driven by the `RESPONSE` environment variable
