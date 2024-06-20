import time
import requests
import subprocess
import yaml
from kubernetes import client, config

# Configurez les seuils pour les décisions de migration
CPU_USAGE_THRESHOLD = 0.75  # 75%
MEMORY_USAGE_THRESHOLD = 0.75  # 75%
SLEEP_INTERVAL = 60  # Intervalle de surveillance en secondes

def get_kube_client(config_file):
    config.load_kube_config(config_file=config_file)
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
    pods = api_instance.list_namespaced_pod(namespace).items
    pod_usage = {}
    for pod in pods:
        pod_name = pod.metadata.name
        metrics = api_instance.read_namespaced_pod_status(pod_name, namespace)
        # Supposez que vous avez une méthode pour obtenir l'utilisation des ressources du pod
        cpu_usage = 0  # Remplacez par l'utilisation réelle du CPU
        memory_usage = 0  # Remplacez par l'utilisation réelle de la mémoire

        pod_usage[pod_name] = {
            'cpu_usage': cpu_usage,
            'memory_usage': memory_usage
        }
    return pod_usage

def check_migration_needed(pod_usage, node_resources):
    for pod_name, usage in pod_usage.items():
        for node_name, resources in node_resources.items():
            if (usage['cpu_usage'] / resources['cpu_capacity'] > CPU_USAGE_THRESHOLD or
                    usage['memory_usage'] / resources['memory_capacity'] > MEMORY_USAGE_THRESHOLD):
                return True
    return False

def trigger_migration(jenkins_url, pipeline_name):
    url = f"{jenkins_url}/job/{pipeline_name}/build"
    response = requests.post(url, auth=('your-username', 'your-api-token'))
    if response.status_code == 201:
        print(f"Migration triggered successfully for {pipeline_name}")
    else:
        print(f"Failed to trigger migration for {pipeline_name}. Status code: {response.status_code}")

def node_pingable(node_ip):
    response = subprocess.run(['ping', '-c', '1', node_ip], stdout=subprocess.PIPE)
    return response.returncode == 0

def main():
    eu_config = 'path/to/eu/config'
    na_config = 'path/to/na/config'
    namespace = 'default'
    pod_name = 'my-pod'
    jenkins_url = 'http://your-jenkins-url'
    
    # Initialisation des clients Kubernetes pour chaque cluster
    eu_api = get_kube_client(eu_config)
    na_api = get_kube_client(na_config)
    
    while True:
        # Surveillance des ressources dans le cluster EU
        print("Checking resources in EU cluster...")
        eu_node_resources = get_node_resources(eu_api)
        eu_pod_usage = get_pod_usage(eu_api, namespace)
        if check_migration_needed(eu_pod_usage, eu_node_resources):
            print("High resource usage detected in EU cluster, triggering migration to NA...")
            trigger_migration(jenkins_url, 'migration-eu-na')
        
        # Surveillance des ressources dans le cluster NA
        print("Checking resources in NA cluster...")
        na_node_resources = get_node_resources(na_api)
        na_pod_usage = get_pod_usage(na_api, namespace)
        if check_migration_needed(na_pod_usage, na_node_resources):
            print("High resource usage detected in NA cluster, triggering migration to EU...")
            trigger_migration(jenkins_url, 'migration-na-eu')

        time.sleep(SLEEP_INTERVAL)

if __name__ == "__main__":
    main()
