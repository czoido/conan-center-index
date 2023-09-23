# Delete conan symlink and ./conan-home

script_path="$(cd "$(dirname "$0")"; pwd -P)/$(basename "$0")"
script_dir="$(dirname "$script_path")"
conan_home="$script_dir/.conan-home"

rm "$script_dir/conan"
rm -rf "$conan_home"
