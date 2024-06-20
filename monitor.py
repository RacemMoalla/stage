from kubernetes import client, config
from kubernetes.client.rest import ApiException

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

def main():
    try:
        # Charge la configuration Kubernetes du contexte par défaut
        config.load_kube_config()

        # Crée une instance de l'API Kubernetes
        api = client.CoreV1Api()

        # Récupère les ressources des nodes
        node_resources = get_node_resources(api)
        
        # Affiche les informations des ressources par node
        for node_name, resources in node_resources.items():
            print(f"Node: {node_name}")
            print(f"  CPU Capacity: {resources['cpu_capacity']} CPUs")
            print(f"  Memory Capacity: {resources['memory_capacity']} Mi")
            print(f"  CPU Allocatable: {resources['cpu_allocatable']} CPUs")
            print(f"  Memory Allocatable: {resources['memory_allocatable']} Mi")
            print()

    except ApiException as ex:
        print(f"Exception when calling Kubernetes API: {ex}")

if __name__ == "__main__":
    main()
