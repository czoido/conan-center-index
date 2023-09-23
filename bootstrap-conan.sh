#!/bin/bash -e

# Download conan, in this case we are installing it with pip because we
# dont have the binaries, but the idea is to download from the conan release

# get routes
script_path="$(cd "$(dirname "$0")"; pwd -P)/$(basename "$0")"
script_dir="$(dirname "$script_path")"
conan_home="$script_dir/.conan-home"
conan_exe="$script_dir/conan" 
mkdir -p "$conan_home"

# create a virtual environment
virtualenv "$conan_home/.env"
source "$conan_home/.env/bin/activate"
pip install git+https://github.com/memsharded/conan.git@feature/git_conancenter_remote
ln -s "$conan_home/.env/bin/conan" "$conan_exe"

# Create a .conanrc file and set the conan_home
echo "conan_home=$conan_home/.conan2" > .conanrc

echo -e "[requires]\n#Add the libraries you want to use below this line:\n\n[generators]\nCMakeToolchain\nCMakeDeps\n" > conanfile.txt

# Create default profile

"$conan_exe" profile detect --force

# Set-up git remote

"$conan_exe" remote remove conancenter
"$conan_exe" remote add c3ifork "$PWD/conan-center-index" --type=local

# checks

"$conan_exe" --version
"$conan_exe" remote list
