import os
import time
import requests
from kubernetes import client, config
from kubernetes.client.rest import ApiException

# Seuils pour la décision de migration
CPU_USAGE_THRESHOLD = 0.75  # 75%
MEMORY_USAGE_THRESHOLD = 0.75  # 75%
SLEEP_INTERVAL = 60  # Intervalle de surveillance en secondes

def get_kube_client():
    # Charge la configuration Kubernetes du contexte par défaut
    config.load_kube_config()
    # Crée une instance de l'API Kubernetes
    return client.CoreV1Api()

def get_node_resources(api_instance):
    nodes = api_instance.list_node().items
    resources = {}
    for node in nodes:
        node_name = node.metadata.name
        cpu_capacity = int(node.status.capacity['cpu'])
        memory_capacity = int(node.status.capacity['memory'][:-2])  # Converti en Mi
        cpu_allocatable = int(node.status.allocatable['cpu'])
        memory_allocatable = int(node.status.allocatable['memory'][:-2])  # Converti en Mi

        resources[node_name] = {
            'cpu_capacity': cpu_capacity,
            'memory_capacity': memory_capacity,
            'cpu_allocatable': cpu_allocatable,
            'memory_allocatable': memory_allocatable
        }
    return resources

def get_pod_usage(api_instance, namespace):
    pod_usage = {}
    pods = api_instance.list_namespaced_pod(namespace).items
    for pod in pods:
        pod_name = pod.metadata.name
        try:
            # Récupère les métriques des ressources du pod
            metrics = api_instance.read_namespaced_pod_metrics(name=pod_name, namespace=namespace)
            if metrics and metrics.containers:
                cpu_usage = metrics.containers[0].usage['cpu']
                memory_usage = metrics.containers[0].usage['memory']
                pod_usage[pod_name] = {
                    'cpu_usage': cpu_usage,
                    'memory_usage': memory_usage
                }
        except ApiException as e:
            print(f"Exception when calling Metrics API for pod {pod_name}: {e}")
    return pod_usage

def check_migration_needed(pod_usage, node_resources):
    for pod_name, usage in pod_usage.items():
        for node_name, resources in node_resources.items():
            if (parse_cpu_quantity(usage['cpu_usage']) / resources['cpu_capacity'] > CPU_USAGE_THRESHOLD or
                    parse_memory_quantity(usage['memory_usage']) / resources['memory_capacity'] > MEMORY_USAGE_THRESHOLD):
                return True
    return False

def parse_cpu_quantity(quantity):
    if quantity.endswith('m'):
        return float(quantity[:-1]) / 1000  # Converti milli-CPU en CPU
    return float(quantity)

def parse_memory_quantity(quantity):
    if quantity.endswith('Mi'):
        return float(quantity[:-2])
    if quantity.endswith('Gi'):
        return float(quantity[:-2]) * 1024  # Converti Gio en Mio
    return float(quantity)

def trigger_migration(jenkins_url, pipeline_name):
    url = f"{jenkins_url}/job/{pipeline_name}/build"
    response = requests.post(url, auth=('your-username', 'your-api-token'))
    if response.status_code == 201:
        print(f"Migration triggered successfully for {pipeline_name}")
    else:
        print(f"Failed to trigger migration for {pipeline_name}. Status code: {response.status_code}")

def main(namespace, pod_name, jenkins_url):
    try:
        # Initialise le client Kubernetes avec le contexte par défaut
        api = get_kube_client()

        while True:
            # Surveillance des ressources du cluster
            print("Checking resources in the cluster...")
            node_resources = get_node_resources(api)
            pod_usage = get_pod_usage(api, namespace)
            if check_migration_needed(pod_usage, node_resources):
                print("High resource usage detected, triggering migration...")
                trigger_migration(jenkins_url, 'migration-job')

            time.sleep(SLEEP_INTERVAL)

    except ApiException as ex:
        print(f"Exception when calling Kubernetes API: {ex}")

if __name__ == "__main__":
    # Récupère les arguments du script depuis l'environnement
    namespace = os.getenv('NAMESPACE', 'default')
    pod_name = os.getenv('POD_NAME', 'my-pod')
    jenkins_url = os.getenv('JENKINS_URL', 'http://your-jenkins-url')

    print(f"Namespace: {namespace}")
    print(f"Pod Name: {pod_name}")
    print(f"Jenkins URL: {jenkins_url}")

    main(namespace, pod_name, jenkins_url)
