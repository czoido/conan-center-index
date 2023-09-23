#!/bin/bash -e

# Función para mostrar la barra de progreso
show_progress() {
  local step_name=$1
  local total=10
  local current=$2
  local percent=$((current * 100 / total))
  local bar_length=$((current * 20 / total))
  local bar=$(printf "%0.s=" $(seq 1 $bar_length))
  local spaces=$(printf "%0.s " $(seq 1 $((20 - bar_length))))
  printf "\r\033[1;34m%-30s\033[0m [%-20s] %3d%%" "$step_name" "$bar$spaces" $percent
}

# Download conan

# get routes
script_path="$(cd "$(dirname "$0")"; pwd -P)/$(basename "$0")"
script_dir="$(dirname "$script_path")"
conan_home="$script_dir/.conan-home"
conan_exe="$script_dir/conan" 
mkdir -p "$conan_home"
show_progress "Setting up directories" 1

# create a virtual environment
virtualenv "$conan_home/.env" > /dev/null 2>&1
source "$conan_home/.env/bin/activate" > /dev/null 2>&1
show_progress "Creating environment" 2

# Install Conan
pip install git+https://github.com/memsharded/conan.git@feature/git_conancenter_remote > /dev/null 2>&1
show_progress "Installing Conan" 3

# Create symlink for conan executable
ln -s "$conan_home/.env/bin/conan" "$conan_exe"
show_progress "Creating symlink" 4

# Create a .conanrc file and set the conan_home
echo "conan_home=$conan_home/.conan2" > .conanrc
show_progress "Creating .conanrc" 5

# Create conanfile.txt
echo -e "[requires]\n#Add the libraries you want to use below this line:\n\n[generators]\nCMakeToolchain\nCMakeDeps\n" > conanfile.txt
show_progress "Creating conanfile.txt" 6

# Create default profile
"$conan_exe" profile detect --force > /dev/null 2>&1
show_progress "Creating default profile" 7

# Set-up git remote
"$conan_exe" remote remove conancenter > /dev/null 2>&1
"$conan_exe" remote add c3ifork "$PWD/conan-center-index" --type=local > /dev/null 2>&1
show_progress "Setting up git remote" 8

# checks
"$conan_exe" --version > /dev/null 2>&1
show_progress "Checking Conan version" 9
"$conan_exe" remote list > /dev/null 2>&1
show_progress "Listing Conan remotes" 10

# Nueva línea al final
echo ""
"$conan_exe" remote list
