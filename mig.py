import yaml
import sys

def modify_yaml(input_file, output_file, node_param):
    with open(input_file, "r") as f:
        yaml_content = f.read()

    documents = yaml.safe_load_all(yaml_content)
    modified_documents = []

    for doc in documents:
        if doc.get("kind") == "Deployment":
            node_selector = doc["spec"]["template"]["spec"].get("nodeSelector")
            if node_selector:
                node_selector["kubernetes.io/hostname"] = node_param
            else:
                doc["spec"]["template"]["spec"]["nodeSelector"] = {"kubernetes.io/hostname": node_param}
        modified_documents.append(doc)

    with open(output_file, "w") as f:
        yaml.dump_all(modified_documents, f, default_flow_style=False)
    print("Modified content has been written to", output_file)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python modify_yaml.py input_file output_file node_param")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    node_param = sys.argv[3]

    modify_yaml(input_file, output_file, node_param)
