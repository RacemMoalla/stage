import argparse
from kubernetes import client, config
from kubernetes.client.rest import ApiException

# Charger la configuration depuis ~/.kube/config
config.load_kube_config()

# Créer une instance de la classe API
v1 = client.CoreV1Api()

def create_pod_from_existing(existing_pod_name, new_pod_name, new_node_name):
    try:
        # Obtenir la configuration du Pod existant
        existing_pod = v1.read_namespaced_pod(name=existing_pod_name, namespace='default')
        
        # Supprimer l'ancien Pod
        v1.delete_namespaced_pod(name=existing_pod_name, namespace='default')
        print(f"Pod '{existing_pod_name}' deleted successfully.")
        
        # Modifier la configuration du Pod
        new_pod = client.V1Pod(
            api_version=existing_pod.api_version,
            kind=existing_pod.kind,
            metadata=client.V1ObjectMeta(name=new_pod_name, labels=existing_pod.metadata.labels),
            spec=existing_pod.spec
        )
        new_pod.spec.node_name = new_node_name

        # Ajouter le volume persistant si non existant
        volume_names = [volume.name for volume in new_pod.spec.volumes]
        if "counter-data" not in volume_names:
            volume = client.V1Volume(
                name="counter-data",
                persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(claim_name="counter-pvc")
            )
            new_pod.spec.volumes.append(volume)

        # Ajouter le montage de volume si non existant
        mount_paths = [mount.mount_path for mount in new_pod.spec.containers[0].volume_mounts]
        if "/data" not in mount_paths:
            volume_mount = client.V1VolumeMount(
                name="counter-data",
                mount_path="/data"
            )
            new_pod.spec.containers[0].volume_mounts.append(volume_mount)

        # Supprimer les champs qui ne devraient pas être copiés
        if new_pod.metadata.creation_timestamp:
            new_pod.metadata.creation_timestamp = None
        if new_pod.status:
            new_pod.status = None
        
        # Créer le nouveau Pod
        v1.create_namespaced_pod(namespace='default', body=new_pod)
        print(f"Pod '{new_pod_name}' created successfully on node '{new_node_name}'.")
    
    except ApiException as e:
        print(f"Exception when creating or deleting pod: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate a Kubernetes pod to a new node.")
    parser.add_argument('--existing_pod_name', type=str, required=True, help="Name of the existing pod to migrate")
    parser.add_argument('--new_pod_name', type=str, required=True, help="Name of the new pod to create")
    parser.add_argument('--new_node_name', type=str, required=True, help="Name of the new node to migrate the pod to")
    
    args = parser.parse_args()

    # Créer le nouveau Pod basé sur le Pod existant et supprimer l'ancien Pod
    create_pod_from_existing(args.existing_pod_name, args.new_pod_name, args.new_node_name)
