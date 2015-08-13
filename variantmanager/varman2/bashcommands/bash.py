__author__ = 'matt'

import os
import subprocess

# -----------------------------------------------------------
# ----------- FUNCTIONS DEFINED HERE ------------------------
# -----------------------------------------------------------


def make_dir(directory):
    if not os.path.isdir(directory):
        return subprocess.call(("mkdir " + directory).split())

def make_tmp_dir(directory):
    tmp_dir = '%s/.tmp' % directory
    remove_dir(tmp_dir)
    if not os.path.isdir(tmp_dir):
        subprocess.call(("mkdir %s" % tmp_dir).split())
        return tmp_dir


def remove_dir(directory):
    if os.path.isdir(directory):
        return subprocess.call(("rm -r " + directory).split())


def remove_tmp_dir(directory):
    tmp_dir = '%s/.tmp' % directory
    if os.path.isdir(tmp_dir):
        return subprocess.call(("rm -r %s" % tmp_dir).split())


def make_file(file):
    if not os.path.isfile(file):
        with open(file, "w"):
            pass

def remove_file(file):
    if os.path.isfile(file):
        return subprocess.call(("rm " + file).split())


def rename_file(file_name, new_name):
    print file_name, new_name
    if os.path.isfile(file_name):
        return subprocess.call(("mv %s %s" % (file_name, new_name)).split())


def copy_file(orig_path, copy_path):
    if os.path.isdir(copy_path):
        copy_path = '%s/%s' % (copy_path, os.path.basename(orig_path))
    command = ("cp %s %s") % (orig_path, copy_path)
    subprocess.call(command.split())
    return copy_path




