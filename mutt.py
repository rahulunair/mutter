import argparse
from functools import lru_cache
import re
import subprocess

import pandas as pd


def cf_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "base_image",
        metavar="base_image",
        type=str,
        help="give docker image_name:tag",
        nargs="?",
    )
    parser.add_argument(
        "final_image",
        metavar="final_image",
        type=str,
        help="give docker image_name:tag",
        nargs="?",
    )
    args = parser.parse_args()
    return args

@lru_cache
def docker_run(image_name):
    """spawn a docker image in daemon mode and return id"""
    docker_run = f"docker run -dt {image_name}"
    container_id = (
        subprocess.run(docker_run, stdout=subprocess.PIPE, shell=True)
        .stdout.decode("utf-8")
        .rstrip()
    )
    return container_id


def get_os_version(container_id):
    os_meta = {}
    docker_attach = f"docker exec -t {container_id} bash -c "
    release_file = "cat /etc/os-release 2>/dev/null"
    run_cmd = f"{docker_attach}'{release_file}"
    os_meta["name"] = f"{run_cmd} | grep -i -m1 name | cut -d= -f2'"
    os_meta["version"] = f"{run_cmd} | grep -i -m1 version | cut -d= -f2'"
    os_meta["name"] = (
        subprocess.run(os_meta["name"], stdout=subprocess.PIPE, shell=True)
        .stdout.decode("utf-8")
        .lower()
        .rstrip()
        .replace('"', "")
    )
    os_meta["version"] = (
        subprocess.run(os_meta["version"], stdout=subprocess.PIPE, shell=True)
        .stdout.decode("utf-8")
        .lower()
        .rstrip()
        .replace('"', "")
    )
    os_name = os_meta["name"].lower()
    if os_name == "fedora" or os_name == "centos":
        os_meta["pkg_tool"] = "rpm"
    elif os_name == "ubuntu" or os_name == "debian":
        os_meta["pkg_tool"] = "dpkg"
    return os_meta


def get_pkgs_vers(container_id):
    """parse dpkg to get installed package names and version from a docker image"""
    docker_attach = f"docker exec -t {container_id} bash -c "
    get_pkgs_vers = "'dpkg -l | tail -n +6 | '"
    get_pkgs_vers += 'sort | awk  \'BEGIN{ OFS=";"}{ printf "%s,%s\\n", $2, $3 }\''
    docker_get_pkgs_vers = f"{docker_attach} bash -c {get_pkgs_vers}"
    pkgs_vers = set()
    try:
        vals = (
            subprocess.run(
                docker_get_pkgs_vers, stdout=subprocess.PIPE, shell=True
            ).stdout.decode("utf-8")
        ).split("\n")
        pkgs_vers.update(vals)
        return pkgs_vers
    except Exception as e:
        print("exceptions..", e)


def get_user_added_pkgs(base_image, final_image=None):
    """get unique packages that were installed in the final image"""
    if final_image is not None:
        base_pkgs_vers, final_pkgs_vers = (
            get_pkgs_vers(base_image),
            get_pkgs_vers(final_image),
        )
    else:
        final_pkgs_vers = base_pkgs_vers = get_pkgs_vers(base_image)
    base_pkgs, final_pkgs = set(), set()
    for bpkg in base_pkgs_vers:
        base_pkgs.add(bpkg.split(",")[0])
    for fpkg in final_pkgs_vers:
        final_pkgs.add(fpkg.split(",")[0])
    if final_pkgs_vers != base_pkgs_vers:
        uniq_pkgs = final_pkgs - base_pkgs
    else:
        uniq_pkgs = base_pkgs
    uniq_pkgs_vers = set()
    for pkg in uniq_pkgs:
        for fpkg in final_pkgs_vers:
            if fpkg.startswith(pkg):
                uniq_pkgs_vers.add(fpkg)
    return sorted(uniq_pkgs_vers)


def get_pkg_license(image_name, pkg):
    """a terrible fuzzy search of licenses"""
    docker_attach = f"docker exec -t {container_id} bash -c "
    get_pkg_license = (
        '\'cat /usr/share/doc/{}/copyright 2>/dev/null || echo "No License file" | '
        "grep -Ew -m1 "
        '"(BSD|GPL|MPL|Mozilla|'
        "Apache|Creative|Artistic|"
        "Boost|Public|License|MIT)\"'"
    )
    name = pkg["name"].split(":")[0]
    license_file = get_pkg_license.format(name)
    cat_license_cmd = docker_attach + license_file
    # TODO(rahulunair): please fix this
    cat_license = subprocess.run(
        cat_license_cmd, stdout=subprocess.PIPE, shell=True
    ).stdout.decode("utf-8")
    return name, cat_license


def print_final_pkgs(container_id, uniq_pkgs, file=None):
    """print pkgs one per line"""
    pkgs_vers = pd.DataFrame(columns=["name", "version", "license"])
    final_pkgs_vers = pd.DataFrame(uniq_pkgs, columns=["name_version"])
    pkgs_vers["name"], pkgs_vers["version"] = (
        final_pkgs_vers["name_version"].str.split(",", 1).str
    )
    for _, pkg in pkgs_vers.iterrows():
        _, license_text = get_pkg_license(container_id, pkg)
        pkgs_vers.loc[
            pkgs_vers["name"] == pkg["name"], "license"
        ] = license_text.rstrip()
    pkgs_vers.to_csv(file)


if __name__ == "__main__":
    args = cf_parse()
    base_cid = docker_run(args.base_image)
    if args.final_image is not None:
        final_cid = docker_run(args.final_image)
        uniq_pkgs = get_user_added_pkgs(base_cid, final_cid)
        print_final_pkgs(args.base_image, uniq_pkgs, file="pkg_licenses.csv")
    else:
        uniq_pkgs = get_user_added_pkgs(base_cid)
        print_final_pkgs(args.final_image, uniq_pkgs, file="pkg_licenses.csv")
