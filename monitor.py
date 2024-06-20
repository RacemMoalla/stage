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
        
        # Converti les allocations CPU et mémoire en Mi, si nécessaire
        cpu_allocatable = parse_cpu_quantity(node.status.allocatable['cpu'])
        memory_allocatable = parse_memory_quantity(node.status.allocatable['memory'])

        resources[node_name] = {
            'cpu_capacity': cpu_capacity,
            'memory_capacity': memory_capacity,
            'cpu_allocatable': cpu_allocatable,
            'memory_allocatable': memory_allocatable
        }
    return resources

def parse_cpu_quantity(quantity):
    if quantity.endswith('m'):
        return float(quantity[:-1]) / 1000  # Converti milli-CPU en CPU
    return float(quantity)

def parse_memory_quantity(quantity):
    if quantity.endswith('Ki'):
        return float(quantity[:-2]) / 1024  # Converti en Mi
    elif quantity.endswith('Mi'):
        return float(quantity[:-2])
    elif quantity.endswith('Gi'):
        return float(quantity[:-2]) * 1024  # Converti en Mi
    elif quantity.endswith('Ti'):
        return float(quantity[:-2]) * 1024 * 1024  # Converti en Mi
    else:
        raise ValueError(f"Unsupported memory unit: {quantity}")

def get_pod_usage(api_instance, namespace):
    pods = api_instance.list_namespaced_pod(namespace)
    for pod in pods.items:
        if pod.metadata.name == pod_name:
            # Here you can access pod usage metrics if they are available in the pod status
            print(f"Pod CPU usage: {pod.status.container_statuses[0].usage.cpu}")
            print(f"Pod Memory usage: {pod.status.container_statuses[0].usage.memory}")


def check_migration_needed(pod_usage, node_resources):
    for pod_name, usage in pod_usage.items():
        for node_name, resources in node_resources.items():
            if (parse_cpu_quantity(usage['cpu_usage']) / resources['cpu_capacity'] > CPU_USAGE_THRESHOLD or
                    parse_memory_quantity(usage['memory_usage']) / resources['memory_capacity'] > MEMORY_USAGE_THRESHOLD):
                return True
    return False



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

def get_pod_usage(api_instance, namespace):
    pods = api_instance.list_namespaced_pod(namespace)
    for pod in pods.items:
        if pod.metadata.name == pod_name:
            # Here you can access pod usage metrics if they are available in the pod status
            print(f"Pod CPU usage: {pod.status.container_statuses[0].usage.cpu}")
            print(f"Pod Memory usage: {pod.status.container_statuses[0].usage.memory}")

