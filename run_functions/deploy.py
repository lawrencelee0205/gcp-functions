import yaml
import subprocess
import os

def prepare_fn_configs(deploy_config):
    print("➡️  Preparing function configs... ", end=" ")
    default_fn_configs = deploy_config.get("default_function_configs")
    fn_configs = {}

    fn_configs["name"] = fn.get("name")
    fn_configs["entry_point"] = fn.get("entry_point", default_fn_configs.get("entry_point", "main"))
    fn_configs["runtime"] = fn.get("runtime", default_fn_configs.get("runtime", "python311"))
    fn_configs["memory"] = fn.get("memory", default_fn_configs.get("memory", "256MB"))
    fn_configs["timeout"] = fn.get("timeout", default_fn_configs.get("timeout", 300))
    fn_configs["max_instances"] = fn.get("max_instances", "5")
    fn_configs["is_trigger_http"] = fn.get("is_trigger_http", default_fn_configs.get("is_trigger_http", False))
    fn_configs["allow_unauthenticated"] = fn.get("allow_unauthenticated", default_fn_configs.get("allow_unauthenticated", False))
    fn_configs["region"] = fn.get("region", default_fn_configs.get("region", "us-central1"))
    fn_configs["is_gen_two"] = fn.get("is_gen_two", default_fn_configs.get("is_gen_two", True))
    fn_configs["source"] = fn.get("source")

    print("✅")

    return fn_configs

def create_build_folder():
    print("➡️  Creating build folder... ", end=" ")

    build_folder = ".build"
    if os.path.exists(build_folder):
        subprocess.run(["rm", "-rf", build_folder], check=True)

    os.makedirs(build_folder, exist_ok=True)

    print("✅")

def prepare_deploy_fn_command(fn_configs):
    print("➡️  Preparing deploy fn command ...", end=" ")

    command = f"{fn_configs.get('name')} --region={fn_configs.get('region')} --runtime={fn_configs.get('runtime')} --source=.build/{fn_configs.get('source').split('/')[-1]} --entry-point={fn_configs.get('entry_point')} --memory={fn_configs.get('memory')} --timeout={fn_configs.get('timeout')} --max-instances={fn_configs.get('max_instances')} "
    if fn_configs.get("is_gen_two"):
        command += "--gen2 "
    if fn_configs.get("is_trigger_http"):
        command += "--trigger-http "
    if fn_configs.get("allow_unauthenticated"):
        command += "--allow-unauthenticated "

    print("✅")

    return command

def compile_fn_directory(fn, default_fn_configs):
    print("➡️  Compiling function directory ...", end=" ")
    fn_source = fn.get("source")  
    fn_dir = fn_source.split("/")[-1]
    
    subprocess.run(["cp", "-r", f"{fn_source}", ".build"], check=True)

    include_default_files = default_fn_configs.get("include_files", [])
    for include_default_files in include_default_files:
        subprocess.run(["cp", "--parents", f"{include_default_files}", f".build/{fn_dir}"], check=True)

    include_dirs = fn.get("include_dirs", [])
    for include_dir in include_dirs:
        subprocess.run(["rsync", "-aR", f"{include_dir}", f".build/{fn_dir}"], check=True)

    include_files = fn.get("include_files", [])
    for include_file in include_files:
        subprocess.run(["cp", "--parents", f"{include_file}", f".build/{fn_dir}"], check=True)

    print("✅")

def check_fns_to_deploy(deploy_config):
    print("➡️  Checking functions to deploy ...", end=" ")
    fns_to_deploy = deploy_config.get("functions_to_deploy")
    fn_names = set(fn.get("name") for fn in deploy_config.get("functions"))

    if fns_to_deploy is None:
        print("🛑")
        print("➡️  No functions to deploy. Exiting ...")
        exit(0)
    else:
        fns_to_deploy = set(fns_to_deploy)
    
    invalid_fns = fns_to_deploy.difference(fn_names)
    if invalid_fns:
        print("❌")
        print(f"Invalid functions to deploy: {', '.join(invalid_fns)}")
        print("Please check the deploy_config.yaml file.")
        exit(1)

    print("✅")
    return fns_to_deploy

if __name__ == "__main__":
    project = "gcp-functions-450107"
    with open("deploy_config.yaml") as f:
        deploy_config = yaml.safe_load(f)

    fns_to_deploy = check_fns_to_deploy(deploy_config)

    if len(fns_to_deploy)==0:
        print("No functions to deploy. Exiting ...")
        exit(0)

    create_build_folder()
    default_fn_configs = deploy_config.get("default_function_configs")

    for fn in deploy_config.get("functions"):
        if fn.get("name") not in fns_to_deploy:
            continue

        print(f"⚙️  Preparing {fn.get('name')} ...")

        fn_configs = prepare_fn_configs(deploy_config)
        compile_fn_directory(fn, default_fn_configs)
        deploy_fn_command = prepare_deploy_fn_command(fn_configs)
        subprocess.run(["echo", f"➡️  Deploying {fn.get('name')} ..."])
        try:
            subprocess.run(["gcloud", "functions", "deploy", *deploy_fn_command.split()], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error: command failed with exit code {e.returncode}")
            exit(1)

        print("✅")

