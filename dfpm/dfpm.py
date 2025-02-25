# Simple package installer!

import requests
import os, sys
import zipfile
import shutil
import socket


def dl_repo(user_name, repo_name, branch="master", use_branch_name=True, location="."):
    zip_url = (
        f"https://github.com/{user_name}/{repo_name}/archive/refs/heads/{branch}.zip"
    )

    try:
        print("Validating connection...")
        socket.create_connection(("8.8.8.8", 53), timeout=5)
    except Exception as e:
        print("Must be connected to the internet!")
        return

    destination_dir = os.path.join(
        location, f"{repo_name}-{branch}" if use_branch_name else repo_name
    )
    if os.path.exists(destination_dir):
        if os.path.isfile(destination_dir):
            print(
                "Error: A file has the same name as the repo. Please rename the file."
            )
            return
        else:
            print(
                "A directory has the same name.\nThis will be treated as a reinstallation."
            )
            if input("Enter [y] to continue: ").lower() not in {"y", "yes"}:
                return
            print(f"{destination_dir}: Deleting the directory...")
            shutil.rmtree(destination_dir)
    print(f"{repo_name}: Downloading zip...")
    try:
        response = requests.get(zip_url)
    except Exception as e:
        print(e)
        return
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)
    print(f"{repo_name}: Done!")
    if response.status_code == 200:
        zip_path = os.path.join(destination_dir, f"{repo_name}-{branch}.zip")
        print(f"{repo_name}: Writing to {destination_dir}.zip...")
        with open(zip_path, "wb") as file:
            file.write(response.content)

        print(f"{destination_dir}: Extracting...")
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(destination_dir)

        inner_folder = os.path.join(destination_dir, f"{repo_name}-{branch}")

        print(f"{inner_folder}: Unwrapping...")
        if os.path.isdir(inner_folder):
            for item in os.listdir(inner_folder):
                item_path = os.path.join(inner_folder, item)
                shutil.move(item_path, os.path.join(destination_dir, item))

            print(f"{inner_folder}: Deleting inner folder...")
            os.rmdir(inner_folder)

        print(f"{destination_dir}: Deleting zipfile...")
        os.remove(zip_path)
        print(f"Done!\nInstalled as: {destination_dir}")
    else:
        print(f"Failed to download repository. Status code: {response.status_code}")


def delete(path):
    shutil.rmtree(path)


def main():
    if len(sys.argv) != 2:
        print("Invalid invocation!\nFor help: dfpm help")
        return 1
    elif sys.argv[1] == "help":
        print(
            "DFPM (DPLs Friendly Package Manager) v0.0.1\nFormat: https://github.com/<user>/<repo>=<branch>"
        )
    elif "=" not in sys.argv[0]:
        print("Format: https://github.com/<user>/<repo>=<branch>\nFor more: dfpm help")
        return 1
    else:
        repo_url, branch_name = sys.argv[1].split("=", maxsplit=1)
        dl_repo(repo_url, branch_name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
