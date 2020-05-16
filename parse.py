import csv
import argparse
import subprocess

import pandas as pd

def cf_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("base_image", metavar="base_image", type=str, help="give docker image_name:tag", nargs='?')
    parser.add_argument("final_image", metavar="final_image", type=str, help="give docker image_name:tag", nargs='?')
    args = parser.parse_args()
    return args


def get_pkgs_vers(image_name):
    """parse dpkg to get installed package names and version from a docker image"""
    docker_run = f"docker run -t {image_name}"
    get_pkgs_vers = "\'dpkg -l | tail -n +6 | \'"
    get_pkgs_vers += "sort | awk  \'BEGIN{ OFS=\";\"}{ printf \"%s,%s\\n\", $2, $3 }\'"
    docker_get_pkgs_vers = f"{docker_run} bash -c {get_pkgs_vers}"
    pkgs_vers = set()
    try:
        vals = (
            subprocess.run(
                docker_get_pkgs_vers, stdout=subprocess.PIPE, shell=True
                ).stdout.decode("utf-8")).split("\n")
        pkgs_vers.update(vals)
        return pkgs_vers
    except Exception as e:
        print("exceptions..", e)


def get_user_added_pkgs(base_image, final_image):
    """get unique packages that were installed in the final image"""
    base_pkgs_vers, final_pkgs_vers = get_pkgs_vers(base_image), get_pkgs_vers(final_image)
    base_pkgs, final_pkgs = set(), set()
    for bpkg in base_pkgs_vers:
        base_pkgs.add(bpkg.split(",")[0])
    for fpkg in final_pkgs_vers:
        final_pkgs.add(fpkg.split(",")[0])
    uniq_pkgs = final_pkgs - base_pkgs
    uniq_pkgs_vers = set()
    for pkg in uniq_pkgs:
        for fpkg in final_pkgs_vers:
            if fpkg.startswith(pkg):
                uniq_pkgs_vers.add(fpkg)
    return sorted(uniq_pkgs_vers)

def print_final_pkgs(uniq_pkgs):
    """print pkgs one per line"""
    pkgs_vers = pd.DataFrame(columns=["name", "version", "license"])
    final_pkgs_vers = pd.DataFrame(uniq_pkgs, columns=["name_version"])
    pkgs_vers["name"], pkgs_vers["version"] = final_pkgs_vers["name_version"].str.split(",", 1).str
    print(pkgs_vers)
    #for pkg in uniq_pkgs:
    #    print(pkg)


if __name__ == "__main__":
    args = cf_parse()
    uniq_pkgs = get_user_added_pkgs(args.base_image, args.final_image)
    print_final_pkgs(uniq_pkgs)
