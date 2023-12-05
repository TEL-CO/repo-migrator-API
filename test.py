import sys
import platform
import pkg_resources

def gather_environment_info():
    info = {}

    # Python version
    info['python_version'] = sys.version

    # Operating system details
    info['os_info'] = platform.platform()

    # Installed packages and their versions
    info['installed_packages'] = {pkg.key: pkg.version for pkg in pkg_resources.working_set}

    return info

def save_environment_info(filename="environment_info.txt"):
    info = gather_environment_info()
    with open(filename, "w") as file:
        for key, value in info.items():
            if isinstance(value, dict):
                file.write(f"{key}:\n")
                for subkey, subvalue in value.items():
                    file.write(f"  {subkey}: {subvalue}\n")
            else:
                file.write(f"{key}: {value}\n")
    print(f"Environment information saved to {filename}")

if __name__ == "__main__":
    save_environment_info()
