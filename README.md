# Monitoring Lab Configuration

 - Prerequisites
 - Deployment
 - Configuration

## Prerequisites

### Minikube configuration

Kubelet configuration must contain these flags:

* `--authentication-token-webhook=true` This flag enables, that a `ServiceAccount` token can be used to authenticate against the kubelet(s).  This can also be enabled by setting the kubelet configuration value `authentication.webhook.enabled` to `true`.
* `--authorization-mode=Webhook` This flag enables, that the kubelet will perform an RBAC request with the API to determine, whether the requesting entity (Prometheus in this case) is allow to access a resource, in specific for this project the `/metrics` endpoint.  This can also be enabled by setting the kubelet configuration value `authorization.mode` to `Webhook`.

This stack provides [resource metrics](https://github.com/kubernetes/metrics#resource-metrics-api) by deploying the [Prometheus Adapter](https://github.com/DirectXMan12/k8s-prometheus-adapter/).
This adapter is an Extension API Server and Kubernetes needs to be have this feature enabled, otherwise the adapter has no effect, but is still deployed.

Prerequisites:
1. swap disabled
2. AppArmor/SELinux disabled
3. kubectl and kubelet are installed and its version is 1.22.2
4. Docker installed
  
Start minikube with the following parameters:
`minikube start --kubernetes-version=v1.22.2 --memory=6g --bootstrapper=kubeadm --extra-config=kubelet.authentication-token-webhook=true --extra-config=kubelet.authorization-mode=Webhook --extra-config=scheduler.address=0.0.0.0 --extra-config=controller-manager.address=0.0.0.0`

The kube-prometheus stack includes a resource metrics API server, so the metrics-server addon is not necessary. Ensure the metrics-server addon is disabled on minikube:
`$ minikube addons disable metrics-server`

### Helm

[Install Helm for windows](https://helm.sh/docs/intro/install/#from-chocolatey-windows)
[Install Helm from source](https://helm.sh/docs/intro/install/#from-source-linux-macos)

https://helm.sh/blog/new-location-stable-incubator-charts/

```sh
$ helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
$ helm repo add stable https://kubernetes-charts.storage.googleapis.com/
$ helm repo update
```

## Deployment

### Elastic stack

1. Install custom resource definitions and the operator with its RBAC rules: `$ kubectl apply -f https://download.elastic.co/downloads/eck/1.0.1/all-in-one.yaml`
2. Namespace for Elastic: `$ kubectl apply -f ./namespace-kube-logging.yaml`
3. Elastic cluster: `$ kubectl apply -f ./elastic-cluster.yaml`
4. Kibana: `$ kubectl apply -f ./kibana.yaml`

5.   Filebeat deployment set: `kubectl apply -f ./filebeat-kubernetes.yaml`
        > **NOTE**: checkout password for "elastic" user:
        > `$ kubectl get secret -n kube-logging quickstart-es-elastic-user -o=jsonpath='{.data.elastic}' | base64 --decode`
        > replace password in the configuration file `filebeat-kubernetes.yaml` line 93

6. Expose ports for elastic and kibana:
```sh
$ kubectl -n kube-logging port-forward service/quickstart-es-http --address 0.0.0.0 9200 &
$ kubectl -n kube-logging port-forward service/quickstart-kb-http --address 0.0.0.0 5601 &
```


### Prometheus stack

1. Create namespace for Prometheus and Grafana `$ kubectl apply -f ./namespace-kube-graph.yaml`
2. Run installation `$ helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack --namespace kube-graph`
3. Expose ports for prometheus and grafana web UI:
```sh
$ kubectl port-forward -n kube-graph prometheus-kube-prometheus-stack-prometheus-0 --address 0.0.0.0 9090 &
$ kubectl port-forward -n kube-graph kube-prometheus-stack-grafana-77f995c9c-m48gx --address 0.0.0.0 3000 &
```
## Configuration

### Kibana

1. Open Kibana UI `https://127.0.0.1:5601/`
2. list indices and create index pattern:
> Management: Stack Management, Data: Index Management. To see the list.
> Management: Stack Management, Kibana: Index patterns. To create pattern.

3. Visualize:
> Kibana: Visualize, Pie chart.
 - Aggregation: Count
 - Add bucket: Split slices: Aggregation: Terms, Field: kubernetes.pods.name, Size: 10

### Data sets and Dashboard
https://www.elastic.co/guide/en/kibana/7.2/tutorial-build-dashboard.html


### Grafana

Grafana default credentials
USERNAME: `admin`
PASSWORD: `prom-operator`

Prometheus configuration file:
`$ kubectl exec -it prometheus-kube-prometheus-stack-prometheus-0 -n kube-grafana -- /bin/sh`

### Dashboard

1. Login to grafana web UI: `http://127.0.0.1:3000/`.
2. On the left plane click "+" Create dashboard.
3. Convert to Row and name it "PODs".
4. Repeat the same (or top right corner "Add panel") naming them as "Nodes", "Namespaces", "Clusters".
5. Right top corner "Dashboard Settings" and name the dashboard as "Kubernetes".
6. Add two more pannels in the settings tab set Pannel title as "CPU" and "Memory" accordingly.
7. For CPU set parameters and "Apply" (top right corner):
   - Data source: `Prometheus`
   - Metrics: `sum(rate(container_cpu_usage_seconds_total{container!="POD",pod!=""}[5m])) by (pod)`
   - Legend: `{{pod}}`
8. Duplicate "CPU" panel CPU > More > Duplicate and name it as "CPU requests"
   - Metrics: `sum(kube_pod_container_resource_requests_cpu_cores) by (pod)`
   - Legend: `{{pod}}`
9. For Memory set parameters and "Apply" (top right corner):
   - Data source: `Prometheus`
   - Metrics: `sum(container_memory_usage_bytes{container!="POD",container!=""}) by (pod)`
   - Legend: `{{pod}}`
10. Duplicate "Memory" panel Memory > More > Duplicate and name it as "Memory requests"
 - `sum(container_memory_usage_bytes{container!="POD",container!=""}) by (node)`


## Appenidx

### Minikibe tuning

`$ minikube delete && minikube start --kubernetes-version=v1.19.2 --memory=6g --bootstrapper=kubeadm --extra-config=kubelet.authentication-token-webhook=true --extra-config=kubelet.authorization-mode=Webhook --extra-config=scheduler.address=0.0.0.0 --extra-config=controller-manager.address=0.0.0.0`

`$ minikube addons disable metrics-server`

### Filebeat settings for linux container

 - Grant users the required privileges `$ kubectl apply -f ./filebeat_setup.yuml`
 - Client Machine (centos) `$ kubectl apply -f ./client-01.yaml`


[reference](https://www.elastic.co/guide/en/cloud-on-k8s/1.0/k8s-quickstart.html)

Install filebeat
```sh
$ sudo rpm --import https://packages.elastic.co/GPG-KEY-elasticsearch
```

Create repository file /etc/yum.repos.d/elastic.repo:
```sh
[elastic-7.x]
name=Elastic repository for 7.x packages
baseurl=https://artifacts.elastic.co/packages/7.x/yum
gpgcheck=1
gpgkey=https://artifacts.elastic.co/GPG-KEY-elasticsearch
enabled=1
autorefresh=1
type=rpm-md
```
[reference](https://www.elastic.co/guide/en/beats/filebeat/current/filebeat-installation-configuration.html)
[reference](https://www.elastic.co/guide/en/beats/filebeat/current/setup-repositories.html)

Filebeat configuration: filebeat.yaml
```sh
# =================================== Kibana ===================================

setup.kibana:

  host: "https://172.17.0.5:5601"
  ssl.verification_mode: none

# -------------+--------------- Elasticsearch Output ----------------------------
output.elasticsearch:
  hosts: ["172.17.0.4:9200"]

  protocol: "https"
  ssl.verification_mode: none

  username: "elastic"
  password: "7r4gJKMl3VRm806i0V0Y6Dg1"

```

 - Install nginx to collect logs from: `$ yum install nginx`

 - Enable modules: `$ filebeat modules enable system nginx`

 - Load assets: `$ filebeat setup -e`

 - Start filebeat: `$ filebeat -e`

 - Start nginx and start genereting logs:
```sh
[root@client-01 /]# nginx
nginx: [emerg] bind() to 0.0.0.0:80 failed (98: Address already in use)
nginx: [emerg] bind() to [::]:80 failed (98: Address already in use)
nginx: [emerg] bind() to 0.0.0.0:80 failed (98: Address already in use)
nginx: [emerg] bind() to [::]:80 failed (98: Address already in use)
nginx: [emerg] bind() to 0.0.0.0:80 failed (98: Address already in use)
nginx: [emerg] bind() to [::]:80 failed (98: Address already in use)
nginx: [emerg] bind() to 0.0.0.0:80 failed (98: Address already in use)
nginx: [emerg] bind() to [::]:80 failed (98: Address already in use)
nginx: [emerg] bind() to 0.0.0.0:80 failed (98: Address already in use)
nginx: [emerg] bind() to [::]:80 failed (98: Address already in use)
nginx: [emerg] still could not bind()
```


### Prometheus Configuration file
```sh
/prometheus $ cat /etc/prometheus/prometheus.yml
# my global config
global:
  scrape_interval:     15s # Set the scrape interval to every 15 seconds. Default is every 1 minute.
  evaluation_interval: 15s # Evaluate rules every 15 seconds. The default is every 1 minute.
  # scrape_timeout is set to the global default (10s).

# Alertmanager configuration
alerting:
  alertmanagers:
  - static_configs:
    - targets:
      # - alertmanager:9093

# Load rules once and periodically evaluate them according to the global 'evaluation_interval'.
rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

# A scrape configuration containing exactly one endpoint to scrape:
# Here it's Prometheus itself.
scrape_configs:
  # The job name is added as a label `job=<job_name>` to any timeseries scraped from this config.
  - job_name: 'prometheus'

    # metrics_path defaults to '/metrics'
    # scheme defaults to 'http'.

    static_configs:
    - targets: ['localhost:9090']
```
