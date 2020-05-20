import argparse
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


def get_pkgs_vers(image_name):
    """parse dpkg to get installed package names and version from a docker image"""
    docker_run = f"docker run -t {image_name}"
    get_pkgs_vers = "'dpkg -l | tail -n +6 | '"
    get_pkgs_vers += 'sort | awk  \'BEGIN{ OFS=";"}{ printf "%s,%s\\n", $2, $3 }\''
    docker_get_pkgs_vers = f"{docker_run} bash -c {get_pkgs_vers}"
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
    if base_image and final_image:
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
    docker_run = f"docker run -t {image_name} bash -c "
    get_pkg_license = (
        "'cat /usr/share/doc/{}/copyright | "
        "grep -Ew -m1 "
        '"(BSD|GPL|MPL|Mozilla|'
        "Apache|Creative|Artistic|"
        "Boost|Public|License|MIT)\"'"
    )
    name = pkg["name"].split(":")[0]
    license_file = get_pkg_license.format(name)
    cat_license_cmd = docker_run + license_file
    # TODO(rahulunair): please fix this
    cat_license = subprocess.run(
        cat_license_cmd, stdout=subprocess.PIPE, shell=True
    ).stdout.decode("utf-8")
    return name, cat_license


def print_final_pkgs(final_image, uniq_pkgs, file=None):
    """print pkgs one per line"""
    pkgs_vers = pd.DataFrame(columns=["name", "version", "license"])
    final_pkgs_vers = pd.DataFrame(uniq_pkgs, columns=["name_version"])
    pkgs_vers["name"], pkgs_vers["version"] = (
        final_pkgs_vers["name_version"].str.split(",", 1).str
    )
    for _, pkg in pkgs_vers.iterrows():
        _, license_text = get_pkg_license(final_image, pkg)
        pkgs_vers.loc[
            pkgs_vers["name"] == pkg["name"], "license"
        ] = license_text.rstrip()
    pkgs_vers.to_csv(file)
    with pd.option_context("display.max_rows", None, "display.max_columns", None):
        print(pkgs_vers)


if __name__ == "__main__":
    args = cf_parse()
    uniq_pkgs = get_user_added_pkgs(args.base_image, args.final_image)
    if args.final_image is None:
        print_final_pkgs(args.base_image, uniq_pkgs, file="pkg_licenses.csv")
    else:
        print_final_pkgs(args.final_image, uniq_pkgs, file="pkg_licenses.csv")
